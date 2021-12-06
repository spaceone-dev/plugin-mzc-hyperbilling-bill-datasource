import logging

from dateutil.parser import parse
from datetime import timedelta, datetime

from spaceone.core.service import *

from spaceone.billing.error import *
from spaceone.billing.manager.hyperbilling_manager import HyperbillingManager
from spaceone.billing.manager.billing_manager import BillingManager

_LOGGER = logging.getLogger(__name__)
DEFAULT_SCHEMA = 'mzc_hyperbilling'

MAX_DAILY_COUNT = 31
MAX_MONTHLY_COUNT = 24

@authentication_handler
@authorization_handler
@event_handler
class BillingService(BaseService):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hyperbilling_mgr: HyperbillingManager = self.locator.get_manager('HyperbillingManager')
        self.billing_mgr: BillingManager = self.locator.get_manager('BillingManager')

    @transaction
    @check_required(['options', 'secret_data', 'start', 'end', 'granularity'])
    def get_data(self, params):
        """Get data

        Args:
            params (dict): {
                'schema': 'str',
                'options': 'dict',
                'secret_data': 'dict',
                'filter': 'dict',
                'aggregation': 'list',
                'start': 'str',
                'end': 'str',
                'granularity': 'str'
            }

        Returns:
            plugin_billing_data_response (dict)
        """
        # Based on granularity
        # start, end format: yyyy-mm-dd if granularity=DAILY
        # start, end format: yyyy-mm if granularity=MONTHLY
        params = self._check_params(params)

        billing_data_info = self.hyperbilling_mgr.get_billing_data(params.get('schema', DEFAULT_SCHEMA), params['options'],
                                                        params['secret_data'],
                                                        params.get('filter', {}),
                                                        params.get('aggregation', []),
                                                        params['start'], params['end'], params['granularity'])

        _LOGGER.debug(f'[get_data] {billing_data_info}')
        #resource_type = 'identity.ServiceAccount?provider=aws'
        return self.billing_mgr.make_billing_data_response(billing_data_info)

    def _check_params(self, params):
        """ Check parameters
        """
        new_params = params.copy()

        try:
            start = parse(params['start'])
        except Exception as e:
            raise ERROR_WRONG_DATE_FORMAT(date=params['start'])

        try:
            end = parse(params['end'])
        except Exception as e:
            raise ERROR_WRONG_DATE_FORMAT(date=params['end'])

        if end > datetime.utcnow():
            end = datetime.utcnow()

        if start > end:
            raise ERROR_WRONG_DATE_RANGE(start=params['start'], end=params['end'])

        granularity = params['granularity']
        if granularity != 'MONTHLY' and granularity != 'DAILY':
            raise ERROR_UNSUPPORTED_FEATURE(reason = granularity)

        if granularity == 'MONTHLY':
            if end - start > timedelta(days=MAX_MONTHLY_COUNT * 31):
                # modify end to possible value
                _LOGGER.warning(f'over monthly limit, fix {end} to {MAX_MONTHLY_COUNT}')
                end = start + timedelta(days=MAX_MONTHLY_COUNT * 30)

        elif granularity == 'DAILY':
            if end - start > timedelta(days=MAX_DAILY_COUNT):
                # modify end to possible value
                _LOGGER.warning(f'over daily limit, fix {end} to {MAX_DAILY_COUNT}')
                end = start + timedelta(days=(MAX_DAILY_COUNT-1))
            # support only yyyymm ~ yyyymm
            new_params['start'] = start.strftime('%Y-%m-%d')
            new_params['end'] = end.strftime('%Y-%m-%d')

        aggregation = params.get('aggregation', [])
        if len(aggregation) > 2:
            raise ERROR_UNSUPPORTED_FEATURE(reason = 'only one aggregation is supported, REGION | SERVICE_CODE')

        if len(aggregation) == 1:
            aggr =aggregation[0]
            if aggr != 'inventory.Region' and aggr != 'inventory.CloudServiceType':
                raise ERROR_UNSUPPORTED_FEATURE(reason = aggr)
        return new_params


