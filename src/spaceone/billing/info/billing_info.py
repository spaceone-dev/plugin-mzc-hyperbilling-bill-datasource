import functools
from spaceone.api.billing.plugin import billing_pb2
from spaceone.core.pygrpc.message_type import *

__all__ = ['PluginBillingDataResponse']


def BillingData(data):
    info = {
        'date': data['date'],
        'cost': data['cost']
    }
    if 'currency' in data:
        info.update({'currency': data['currency']})

    return billing_pb2.BillingData(**info)

def BillingInfo(billing_info):
    billing_data_list = list(map(functools.partial(BillingData), billing_info['billing_data']))
    name = billing_info.get('name', None)
    if name:
        return billing_pb2.BillingInfo(resource_type=billing_info['resource_type'], billing_data=billing_data_list, name=name)
    else:
        return billing_pb2.BillingInfo(resource_type=billing_info['resource_type'], billing_data=billing_data_list)


def PluginBillingDataResponse(billing_info_list):
    total_count = len(billing_info_list)
    billing_info = list(map(functools.partial(BillingInfo), billing_info_list))
    return billing_pb2.PluginBillingDataResponse(results=billing_info, total_count=total_count)
