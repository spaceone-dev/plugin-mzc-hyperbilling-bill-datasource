import logging

from spaceone.core.manager import BaseManager
#from spaceone.billing.model.billing_response_model import BillingDataResponseModel

_LOGGER = logging.getLogger(__name__)


class BillingManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def make_billing_data_response(billing_data_info):
        result = []
        for k,v in billing_data_info.items():
            if 'name' in v:
                result.append({'resource_type': k, 'name': v['name'], 'billing_data': v['billing_data']})
            else:
                result.append({'resource_type': k, 'billing_data': v['billing_data']})
        return result
