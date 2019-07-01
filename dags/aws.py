from airflow import configuration
from airflow.hooks.S3_hook import S3Hook

REMOTE_LOGS_CONNECTION_ID = configuration.conf.get('core', 'remote_log_conn_id') or None


def get_s3_client():
    return S3Hook(aws_conn_id=REMOTE_LOGS_CONNECTION_ID).get_conn()


def list_bucket_keys_iter(**list_objects_v2_params):
    """
    returns a generator that lists keys/prefixes in an AWS S3 bucket.
    """
    client = get_s3_client()
    paginator = client.get_paginator('list_objects_v2')
    for page in paginator.paginate(**list_objects_v2_params):
        if 'Contents' in page:
            for item in page['Contents']:
                yield item['Key']
        elif 'CommonPrefixes' in page:
            for item in page['CommonPrefixes']:
                yield item['Prefix']
