import pytest

from dags.aws import get_aws_connection, list_bucket_keys_iter
from dags.trigger_dag import SOURCE_BUCKET, DESTINATION_BUCKET


@pytest.mark.parametrize('url, expected', [
    (None, "https://s3.eu-west-2.amazonaws.com"),
    ('http://test-url.com', 'http://test-url.com')
])
def test_get_aws_connection(url, expected):
    import dags.aws
    dags.aws.ENDPOINT_URL = url
    conn = get_aws_connection('s3')
    assert conn._endpoint._endpoint_prefix == 's3'
    assert conn._endpoint.host == expected


@pytest.mark.parametrize('params, response, expected', [
    (
        {'Bucket': SOURCE_BUCKET, 'Delimiter': '.zip'},
        {'CommonPrefixes':[{'Prefix': 'elife-666-vor-r1.zip'}]},
        ['elife-666-vor-r1.zip']
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
        {'Contents':[{'Key': 'elife-666-vor-r1.zip'}]},
        ['elife-666-vor-r1.zip']
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
