import boto3
from airflow import configuration

ENDPOINT_URL = configuration.conf.get('elife', 'endpoint_url')


def get_aws_connection(service: str):
    """
    Helper function created because endpoint_url setting (required for local
    development) cannot be configured.
    """
    if ENDPOINT_URL:
        return boto3.client(service, endpoint_url=ENDPOINT_URL)
    else:
        return boto3.client(service)


def list_bucket_keys_iter(**list_objects_v2_params):
    """
    returns a generator that lists keys/prefixes in an AWS S3 bucket.
    """
    client = get_aws_connection('s3')
    paginator = client.get_paginator('list_objects_v2')
    for page in paginator.paginate(**list_objects_v2_params):
        if 'Contents' in page:
            for item in page['Contents']:
                yield item['Key']
        elif 'CommonPrefixes' in page:
            for item in page['CommonPrefixes']:
                yield item['Prefix']
