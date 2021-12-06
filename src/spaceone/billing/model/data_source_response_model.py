from schematics.models import Model
from schematics.types import ListType, DictType, StringType, IntType
from schematics.types.compound import ModelType

__all__ = ['PluginInitResponse']

_SUPPORTED_RESOURCE_TYPE = [
    'inventory.CloudService?provider=gcp',
    'inventory.CloudService?provider=alibaba',
    'inventory.CloudService?provider=tencent',
    'inventory.CloudService?provider=akamai'
]

_SUPPORTED_AGGREGATION = [
    'inventory.Region',
    'inventory.CloudServiceType'
]

_SUPPORTED_SCHEMA = [
    'mzc_hyperbilling'
]

class PluginMetadata(Model):
    supported_resource_type = ListType(StringType, default=_SUPPORTED_RESOURCE_TYPE)
    supported_aggregation = ListType(StringType, default=_SUPPORTED_AGGREGATION)
    supported_schema = ListType(StringType, default=_SUPPORTED_SCHEMA)
    max_daily_count = IntType(default=31)
    max_monthly_count = IntType(default=24)

class PluginInitResponse(Model):
    _metadata = ModelType(PluginMetadata, default=PluginMetadata, serialized_name='metadata')
