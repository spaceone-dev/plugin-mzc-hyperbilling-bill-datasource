# init

~~~
{'metadata': {'max_daily_count': 31.0,
              'max_monthly_count': 24.0,
              'supported_aggregation': ['inventory.Region',
                                        'inventory.CloudServiceType'],
              'supported_resource_type': ['inventory.CloudService?provider=google_cloud'],
              'supported_schema': ['mzc_hyperbilling']}}
~~~

# Monthly Cost

~~~
{'results': [{'billing_data': [{'cost': 10000.06,
                                'currency': 'USD',
                                'date': '2020-10'},
                               {'cost': 20000.70,
                                'currency': 'USD',
                                'date': '2020-11'},
                               {'cost': 495.80,
                                'currency': 'USD',
                                'date': '2020-12'}],
              'resource_type': 'inventory.CloudService?identity.Provider=google_cloud'}],
 'total_count': 1}
 ~~~
