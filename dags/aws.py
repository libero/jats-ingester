from airflow.hooks.S3_hook import S3Hook


def get_s3_client(aws_conn_id: str = 'remote_logs'):
    return S3Hook(aws_conn_id=aws_conn_id).get_conn()


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
