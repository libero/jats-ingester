import pytest

from dags.aws import get_s3_client, list_bucket_keys_iter
from dags.trigger_dag import SOURCE_BUCKET, DESTINATION_BUCKET


def test_get_s3_client():
    conn = get_s3_client()
    assert conn._endpoint._endpoint_prefix == 's3'
    assert conn._endpoint.host == "https://s3.eu-west-2.amazonaws.com"


def test_get_s3_client_using_AIRFLOW_CONN_env_variable(set_remote_logs_env_var):
    conn = get_s3_client()
    assert conn._endpoint._endpoint_prefix == 's3'
    assert conn._endpoint.host == "http://test-host:1234"


@pytest.mark.parametrize('params, response, expected', [
    (
        {'Bucket': SOURCE_BUCKET, 'Delimiter': '.zip'},
        {'CommonPrefixes':[{'Prefix': 'elife-00666-vor-r1.zip'}]},
        ['elife-00666-vor-r1.zip']
    ),
    (
        {'Bucket': SOURCE_BUCKET, 'Delimiter': '.zip'},
        {},
        []
    ),
    (
        {'Bucket': DESTINATION_BUCKET, 'Delimiter': '/'},
        {'CommonPrefixes':[{'Prefix': 'elife-666-vor-r1/'}]},
        ['elife-666-vor-r1/']
    ),
    (
        {'Bucket': DESTINATION_BUCKET, 'Delimiter': '/'},
        {},
        []
    ),
    (
        {'Bucket': SOURCE_BUCKET},
        {'Contents':[{'Key': 'elife-00666-vor-r1.zip'}]},
        ['elife-00666-vor-r1.zip']
    ),
    (
        {'Bucket': SOURCE_BUCKET},
        {},
        []
    )
])
def test_list_bucket_keys_iter(params, response, expected, s3_client):
    keys = list_bucket_keys_iter(response=[response], **params)
    assert list(keys) == expected
