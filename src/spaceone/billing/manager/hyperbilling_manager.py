import logging
import requests
import json
import time

import google.auth.crypt
import google.auth.jwt

from datetime import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta

from spaceone.core.manager import BaseManager
from spaceone.billing.error import *

_LOGGER = logging.getLogger(__name__)

URL = 'https://api.hb.cloudnoa.io/summary'
AUDIENCE = 'api.hb.cloudnoa.io'
EXPIRY_LENGTH = 600     # 10 min
# Service Code
# https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/index.json

GRANULARITY = {
    'MONTHLY': 'monthly_cost',
    'DAILY': 'daily_cost'
}

KINDS = {
    'inventory.Region': 'cost_by_region',
    'inventory.CloudServiceType': 'cost_by_service'
}

# SpaceONE Resource type -> Hyperbilling code

def _get_signed_jwt(secret_data):
    """ Get signed JWT from secret_data
    """
    sa_email = secret_data['client_email']
    private_key = secret_data['private_key']

    now = int(time.time())
    payload = {
        'iat': now,
        'exp': now + EXPIRY_LENGTH,
        'iss': sa_email,
        'aud': AUDIENCE,
        'sub': sa_email,
        'email': sa_email
    }

    signer = google.auth.crypt.RSASigner.from_string(private_key)
    jwt = google.auth.jwt.encode(signer, payload)
    return jwt

def _get_months(start, end):
    """
    start: yyyymm(dd)
    end: yyyymm(dd)

    return: list of month
    ex) [202110, 202111, 202112]
    """
    t_start = datetime.strptime(start, '%Y-%m')
    t_end = datetime.strptime(end, '%Y-%m')
    months = [t_start.strftime("%Y%m")]
    next_month = t_start + relativedelta(months=1)
    while next_month <= t_end:
        months.append(next_month.strftime("%Y%m"))
        next_month = next_month + relativedelta(months=1)
    _LOGGER.debug(f'months: {months}')
    return months

def _get_kinds(aggregation, granularity):
    """
    """
    kinds = []
    for aggr in aggregation:
        if aggr in KINDS:
            kinds.append(KINDS[aggr])
        else:
            __LOGGER.error(f"Unsupported aggregation: {aggr}")
    if granularity in GRANULARITY:
        kinds.append(GRANULARITY[granularity])
    else:
        __LOGGER.error(f"Unspported granularity: {granularity}")
    return kinds

def _parse_daily_cost(data, start, end):
    """
    "data": [
                    {
                        "invoice_month": "202109",
                        "date": "2021-09-10",
                        "costs": [
                            {
                                "cost": 3777.55956,
                                "credit": 0,
                                "final_cost": 3777.55956,
                                "cost_in_usd": 3.231224,
                                "credit_in_usd": 0,
                                "final_cost_in_usd": 3.231224,
                                "currency": "KRW"
                            }
                        ]
                    },
                    {
                        "invoice_month": "202109",
                        "date": "2021-09-11",
                        "costs": [
                            {
                                "cost": 4112.238968,
                                "credit": 0,
                                "final_cost": 4112.238968,
                                "cost_in_usd": 3.5175,
                                "credit_in_usd": 0,
                                "final_cost_in_usd": 3.5175,
                                "currency": "KRW"
                            }
                        ]
                    },
        """
    results = []
    t_start = datetime.fromisoformat(start)
    t_end = datetime.fromisoformat(end)
    for item in data:
        this_month = datetime.strptime(item['invoice_month'], '%Y%m')
        next_month = this_month + relativedelta(months=1)
        date = item['date']
        now = datetime.fromisoformat(date)
        # this_month >= now < next_month (otherwise, bug result)
        if now < this_month or now >= next_month:
            _LOGGER.debug(f'skip {date} in {this_month}')
            continue
        # check t_start <= now <= t_end
        if now < t_start or now > t_end:
            _LOGGER.debug(f'skip {date}')
            continue
        costs = item['costs']
        daily_cost = 0
        currency = 'USD'
        if len(costs) > 1:
            _LOGGER.error("!!!!! Contact to Developer !!!!!")
            _LOGGER.error("function: _parse_daily_cost, length of cost must be 1")
            _LOGGER.error(f"costs: {costs}")
        elif len(costs) == 1:
            daily_cost = costs[0].get('final_cost_in_usd', 0)
        result = {'cost': daily_cost, 'date': date, 'currency': currency}
        results.append(result)
    return results

def _parse_monthly_cost(data, start, end, month):
    """
    "data": 
    [
        {
            'invoice_month': '202109', 
            'costs': 
                [
                    {
                        'cost': 85949.615831, 
                        'credit': 0, 
                        'final_cost': 85949.615831, 
                        'cost_in_usd': 73.519018, 
                        'credit_in_usd': 0, 
                        'final_cost_in_usd': 73.519018, 
                        'frt': 0, 
                        'sud': 0, 
                        'cud': 0, 
                        'sbd': 0, 
                        'prm': 0, 
                        'frt_in_usd': 0, 
                        'sud_in_usd': 0, 
                        'cud_in_usd': 0, 
                        'sbd_in_usd': 0, 
                        'prm_in_usd': 0, 
                        'currency': 'KRW'
                    }
                ]
            }, 
        """
    results = []
    t_start = datetime.strptime(start, '%Y-%m')
    t_end = datetime.strptime(end, '%Y-%m')
    for item in data:
        if item['invoice_month'] != month:
            # Hyperbilling Bug
            _LOGGER.debug(f'skip {item["invoice_month"]} since {month}')
            continue

        this_month = datetime.strptime(item['invoice_month'], '%Y%m')
        t_start <= this_month <= t_end
        if t_end < this_month or this_month < t_start:
            _LOGGER.debug(f'skip {this_month} from {start} to {end}')
            continue
        costs = item['costs']
        currency = 'USD'
        monthly_cost = costs[0].get('final_cost_in_usd', 0)
        result = {'cost': monthly_cost, 'date': this_month.strftime('%Y-%m'), 'currency': currency}
        results.append(result)
    return results

def _parse_monthly_cost_by_region(data, start, end, month, key_prefix):
    """
    "data":
                "data": [
                    {
                        "region_id": "asia-east1",
                        "multi_region": false,
                        "costs": [
                            {
                                "cost": 871.038984,
                                "credit": 0,
                                "final_cost": 871.038984,
                                "cost_in_usd": 0.745064,
                                "credit_in_usd": 0,
                                "final_cost_in_usd": 0.745064,
                                "frt": 0,
                                "sud": 0,
                                "cud": 0,
                                "sbd": 0,
                                "prm": 0,
                                "frt_in_usd": 0,
                                "sud_in_usd": 0,
                                "cud_in_usd": 0,
                                "sbd_in_usd": 0,
                                "prm_in_usd": 0,
                                "currency": "KRW"
                            }
                        ]
                    },

        """
    results = []
    this_month = datetime.strptime(month, '%Y%m')
    t_start = datetime.strptime(start, '%Y-%m')
    t_end = datetime.strptime(end, '%Y-%m')

    output = {}
    for item in data:
        region_name = item.get("region_id", "N/A")
        new_key = f'{key_prefix}&inventory.Region={region_name}'
        costs = item['costs']
        currency = 'USD'
        # There is only one element on list
        monthly_cost = costs[0].get('final_cost_in_usd', 0)
        result = {'cost': monthly_cost, 'date': this_month.strftime('%Y-%m'), 'currency': currency}
        output[new_key] = [result]
    return output

def _parse_monthly_cost_by_service(data, start, end, month, key_prefix):
    """
    "data":
                "data": [
                    {
                        "region_id": "asia-east1",
                        "multi_region": false,
                        "costs": [
                            {
                                "cost": 871.038984,
                                "credit": 0,
                                "final_cost": 871.038984,
                                "cost_in_usd": 0.745064,
                                "credit_in_usd": 0,
                                "final_cost_in_usd": 0.745064,
                                "frt": 0,
                                "sud": 0,
                                "cud": 0,
                                "sbd": 0,
                                "prm": 0,
                                "frt_in_usd": 0,
                                "sud_in_usd": 0,
                                "cud_in_usd": 0,
                                "sbd_in_usd": 0,
                                "prm_in_usd": 0,
                                "currency": "KRW"
                            }
                        ]
                    },

        """
    results = []
    this_month = datetime.strptime(month, '%Y%m')
    t_start = datetime.strptime(start, '%Y-%m')
    t_end = datetime.strptime(end, '%Y-%m')

    output = {}
    for item in data:
        service_name = item.get("service_name", "N/A")
        service_name = service_name.replace(" ", "")
        new_key = f'{key_prefix}&inventory.CloudServiceType={service_name}'
        costs = item['costs']
        currency = 'USD'
        # There is only one element on list
        monthly_cost = costs[0].get('final_cost_in_usd', 0)
        result = {'cost': monthly_cost, 'date': this_month.strftime('%Y-%m'), 'currency': currency}
        output[new_key] = [result]
    return output


class HyperbillingManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def verify(self, schema, options, secret_data):
        pass

    def get_billing_data(self, schema, options, secret_data, filters, aggregation, start, end, granularity):
        # Check secret format first
        self._check_schema(secret_data, schema)

        provider = secret_data['platform']

        headers = self._get_headers(secret_data)
        my_filters = self._create_filters(secret_data, filters, aggregation, start, end, granularity)
        r = self._make_request(headers, my_filters)
        if r.status_code == 200:
            data = json.loads(r.text)
            # Convert key to resource_type
            converted_dict = self._convert_format(data, aggregation, provider, start, end, granularity)
            return converted_dict
        else:
            __LOGGER.error(f"failed API call: {r.status_code}")
            return {}

    @staticmethod
    def _convert_format(data, aggregation, provider, start, end, granularity):
        """
        aggregation(list): inventory.Region | inventory.CloudServiceType
        Granularity: DAILY | MONTHLY
        data:
        [
            {
                "kind": "monthly_cost",
                "month": "202109",
                "data": [
                    {
                        "project_id": "bluese-cloudone-20200113",
                        "project_name": "CloudOne DEV",
                        "data": [
                            {
                                "invoice_month": "202109",
                                "costs": [
                                    {
                                        "cost": 85949.615831,
                                        "credit": 0,
                                        "final_cost": 85949.615831,
                                        "cost_in_usd": 73.519018,
                                        "credit_in_usd": 0,
                                        "final_cost_in_usd": 73.519018,
                                        "currency": "KRW"
                                    }
                                ]
                            }
                        ]
                    }
                ]
            },
        """
        converted_dict = {}
        # for every month
        #billing_data_list = []
        for item in data:
            ###############################
            # Result has unnecessary data
            ###############################
            kind = item['kind']
            if granularity == 'DAILY' and kind != 'daily_cost':
                # Garbage
                # kind may be cost_by_service, cost_by_region
                _LOGGER.debug(f'granularity: {granularity}, skip: {item}')
                continue
            if 'inventory.Region' in aggregation:
                if kind != 'cost_by_region':
                    _LOGGER.debug(f'aggregation: inventory.Region, skip: {kind}')
                    continue
            if 'inventory.CloudServiceType' in aggregation:
                if kind != 'cost_by_service':
                    _LOGGER.debug(f'aggregation: inventory.CloudServiceType, skip: {kind}')
                    continue

            result_by_key = HyperbillingManager()._parse_data(item, aggregation, provider, start, end, granularity)
            # merge by key
            for key, value in result_by_key.items():
                previous_data = converted_dict.get(key, [])
                previous_data = previous_data + value
                converted_dict[key] = previous_data

        # for result format
        # inventory.CloudService?identity.Provider=gcp: 
        #    {billing_data: [{date:yyyy-mm, cost: NN, currency: USD} ....]}
        result = {}
        for key, value in converted_dict.items():
            result[key] = {'billing_data': value}
        return result

    @staticmethod
    def _parse_data(data, aggregation, provider, start, end, granularity):
        """
        # MONTHLY COST
        data:
            {
                "kind": "monthly_cost",
                "month": "202109",
                "data": [
                    {
                        "project_id": "bluese-cloudone-20200113",
                        "project_name": "CloudOne DEV",
                        "data": [
                            {
                                "invoice_month": "202109",
                                "costs": [
                                    {
                                        "cost": 85949.615831,
                                        "credit": 0,
                                        "final_cost": 85949.615831,
                                        "cost_in_usd": 73.519018,
                                        "credit_in_usd": 0,
                                        "final_cost_in_usd": 73.519018,
                                        "currency": "KRW"
                                    }
                                ]
                            }
                        ]
                    }
                ]
            },
 

        Returns:
            # No group_by
            # KEY : inventory.CloudService?identity.Provider=gcp
            {KEY: [{'date': '2020-10', 'cost': 12, 'currency': 'USD'}]}

            # group_by REGION
            # KEY : inventory.CloudService?identity.Provider=gcp&inventory.Region=APN2
            {'KEY2': [{'date': '2020-10', 'cost': 13.3, 'currency': 'USD'}],
             'KEY1': [{'date': '2020-10', 'cost': 0.2, 'currency': 'USD'}],
             ...
            }

            # group_by SERVICE_CODE
            # KEY : inventory.CloudService?identity.Provider=gcp&inventory.CloudServiceType=Compute Engine
            {'Compute Engine': [{'date': '2020-10', 'cost': 13.3, 'currency': 'USD'}],
             'Cloud DNS': [{'date': '2020-10', 'cost': 0.2, 'currency': 'USD'}],
            ...
            }
        """

        # output(dict)
        output = {}
        key_prefix = f'inventory.CloudService?identity.Provider={provider}'

        # Posssible Case
        # Case 1) Daily without aggregation
        # Case 2) Monthly without aggreation
        # Case 3) Monthly by region
        # Case 4) Monthly by service code

        # Parsing Daily
        if 'data' in data:
            _LOGGER.debug(f'length of data: {len(data["data"])}')

        result = []

        if granularity == 'DAILY':
            for data2 in data['data']:
                costs = _parse_daily_cost(data2['data'], start, end)
                result.extend(costs)
            output = {key_prefix: result}

        # Parsing Monthly & No Aggregation
        elif granularity ==  'MONTHLY' and len(aggregation) == 0:
            for data2 in data['data']:
                costs = _parse_monthly_cost(data2['data'], start, end, data['month'])
                result.extend(costs)
            output = {key_prefix: result}

        elif granularity == 'MONTHLY' and aggregation[0] == 'inventory.Region':
            for data2 in data['data']:
                # length is 1
                _LOGGER.debug(f'length: {len(data["data"])} must be 1')
                output_added = _parse_monthly_cost_by_region(data2['data'], start, end, data['month'], key_prefix)
                output = output_added

        elif granularity == 'MONTHLY' and aggregation[0] == 'inventory.CloudServiceType':
            for data2 in data['data']:
                # length is 1
                _LOGGER.debug(f'length: {len(data["data"])} must be 1')
                output_added = _parse_monthly_cost_by_service(data2['data'], start, end, data['month'], key_prefix)
                output = output_added
        return output

    @staticmethod
    def _get_headers(secret_data):
        """ Create access_token from secret_data
        """
        jwt = _get_signed_jwt(secret_data)

        headers = {
            'Authorization': 'Bearer {}'.format(jwt.decode('utf-8')),
            'content-type': 'application/json'
        }
        return headers

    @staticmethod
    def _create_filters(secret_data, filters, aggregation, start, end, granularity):
        """ Based on request filters,
        Create filter for hyperbilling

        Query Parameters
        - platform   (required): gcp | alibaba | tencent | akamai
        - account_id (required): xxxxxx-yyyyyy-ddddddd
        - month : yyyymm
        - months : ['yyyymm', 'yyyymm', 'yyyymm' ...]
        - kind: cost_by_region | cost_by_country | cost_by_service | daily_cost | monthly_cost | usage_detail
        - kinds: array of kind

        month or months is requied
        """
        platform = secret_data['platform']
        account_id = secret_data['account_id']

        start=HyperbillingManager._to_yyyy_mm_dd(start)
        end=HyperbillingManager._to_yyyy_mm_dd(end)
        kinds = [GRANULARITY[granularity]]

        my_filters = {
            "platform": platform,
            "account_id": account_id,
            "months[]": _get_months(start, end),
            "kinds[]": _get_kinds(aggregation, granularity)
        }
        return my_filters

    @staticmethod
    def _to_yyyy_mm_dd(date):
        """ convert to str to yyyy-mm-dd
        Nothing to do
        """
        #return date.strftime('%Y-%m-%d')
        return date

    @staticmethod
    def _map_region(region):
        """ Map SpaceONE region name to hyperbilling region_code
        """
        if region == None:
            return None
        if region in REGION_CODE:
            return REGION_CODE[region]
        _LOGGER.error(f'[_map_region] !!!! no region map: {reion}, {REGION_CODE} contact developer !!!!')
        raise ERROR_UNKNOWN_REGION(region=region)

    @staticmethod
    def _map_resource_type(resource_type):
        """ Map SpaceONE region_type to hyperbilling product_code
        """
        return None

    @staticmethod
    def _make_request(headers, query):
        r = requests.get(URL, headers=headers, params=query)
        return r

    @staticmethod
    def _check_schema(secret_data, schema):
        """ check schema
        """
        if schema == "mzc_hyperbilling":
            items = ["private_key", "client_email", "platform", "account_id"]
        else:
            _LOGGER.error(f"unsupported schema: {schema}")
            raise ERROR_UNSUPPORTED_FEATURE(reason = schema)

        for item in items:
            if not item in secret_data:
               raise ERROR_UNSUPPORTED_FEATURE(reason = schema)
