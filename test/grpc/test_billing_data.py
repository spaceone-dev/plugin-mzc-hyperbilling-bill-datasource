import os
import unittest

from spaceone.core.unittest.runner import RichTestRunner
from spaceone.tester import TestCase, print_json

private_key = os.environ.get('PRIVATE_KEY', None)
email = os.environ.get('EMAIL', None)
platform = os.environ.get('PLATFORM', None)
account_id = os.environ.get('ACCOUNT_ID', None)

if private_key == None or email == None or platform == None or account_id == None:
        print("""
              ##################################################
              # ERROR
              #
              # Configure your MZC Hyperbilling API key
              ##################################################
              example)

export PRIVATE_KEY=$'<Your Private Key of Hyperbilling API Key>'
export EMAIL=<Your email form Hyperbilling API Key>
export ACCOUNT_ID=<Your Account ID>
export PLATFORM=gcp|alibaba|tencent|akamai
""")
exit


class TestBilling(TestCase):

#    def test_valify(self):
#        options = {}
#        secret_data = {
#            'Email': Email,
#            'Key': Key,
#            'Account': Account
#        }
#        self.billing.DataSource.verify({'options': options, 'secret_data': secret_data})


    def test_list(self):
        options = {}
        secret_data = {
            'private_key': private_key,
            'client_email': email,
            'account_id': account_id,
            'platform': platform
        }
        print(len(private_key))
        filter = {}
        aggregation = ["inventory.Region"]
        aggregation = ["inventory.CloudServiceType"]
        #aggregation = []
        granularity = 'DAILY'
        start = "2021-09-01"
        end = "2021-09-30"

        granularity = 'MONTHLY'
        start = '2021-09'
        end = '2021-11'
        billing_result = self.billing.Billing.get_data({'options': options,
                                                    'secret_data': secret_data,
                                                    'filter': filter,
                                                    'aggregation': aggregation,
                                                    'start': start,
                                                    'end': end,
                                                    'granularity': granularity})
        print_json(billing_result)

#
#    def test_get_data_over_limit(self):
#        options = {}
#        secret_data = {
#            'private_key': private_key,
#            'client_email': email,
#            'account_id': account_id,
#            'platform': platform
#        }
# 
#        filter = {}
#        aggregation = ["REGION"]
#        aggregation = ["SERVICE_CODE"]
#        aggregation = []
#        granularity = 'MONTHLY'
#        start = "2020-01-01"
#        end = "2022-12-14"
#        billing_result = self.billing.Billing.get_data({'options': options,
#                                                    'secret_data': secret_data,
#                                                    'filter': filter,
#                                                    'aggregation': aggregation,
#                                                    'start': start,
#                                                    'end': end,
#                                                    'granularity': granularity})
#        print_json(billing_result)
#
#    def test_get_data_over_limit_by_daily(self):
#        options = {}
#        secret_data = {
#            'private_key': private_key,
#            'client_email': email,
#            'account_id': account_id,
#            'platform': platform
#        }
#        filter = {}
#        aggregation = ["REGION"]
#        aggregation = ["SERVICE_CODE"]
#        aggregation = []
#        granularity = 'DAILY'
#        start = "2020-10-01"
#        end = "2022-12-14"
#        billing_result = self.billing.Billing.get_data({'options': options,
#                                                    'secret_data': secret_data,
#                                                    'filter': filter,
#                                                    'aggregation': aggregation,
#                                                    'start': start,
#                                                    'end': end,
#                                                    'granularity': granularity})
#        print_json(billing_result)
#
#

if __name__ == "__main__":
    unittest.main(testRunner=RichTestRunner)
