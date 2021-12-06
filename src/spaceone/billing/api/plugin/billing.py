from spaceone.api.billing.plugin import billing_pb2, billing_pb2_grpc
from spaceone.core.pygrpc import BaseAPI


class Billing(BaseAPI, billing_pb2_grpc.BillingServicer):

    pb2 = billing_pb2
    pb2_grpc = billing_pb2_grpc

    def get_data(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('BillingService', metadata) as billing_service:
            return self.locator.get_info('PluginBillingDataResponse', billing_service.get_data(params))
