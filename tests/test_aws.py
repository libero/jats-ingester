import pytest

from dags.aws import get_aws_connection, list_bucket_keys_iter
from dags.trigger_dag import SOURCE_BUCKET, DESTINATION_BUCKET
from tests import mocks


@pytest.mark.parametrize('url', [None, 'http://test-url.com'])
def test_get_aws_connection(url):
    import dags.aws
    dags.aws.ENDPOINT_URL = url

    conn = get_aws_connection('s3')

    # boto3 client should use the default address if an endpoint is not specified
    if not url:
        url = "https://s3.eu-west-2.amazonaws.com"

    assert conn._endpoint._endpoint_prefix == 's3'
    assert conn._endpoint.host == url


@pytest.mark.parametrize('params, response, expected', [
    ({'Bucket': SOURCE_BUCKET, 'Delimiter': '.zip'},
     mocks.list_objects_v2_source_bucket_delimiter,
     ['elife-666-vor-r1.zip']),
    ({'Bucket': SOURCE_BUCKET, 'Delimiter': '.zip'},
     mocks.list_objects_v2_source_bucket_delimiter,
     []),
    ({'Bucket': DESTINATION_BUCKET, 'Delimiter': '/'},
     mocks.list_objects_v2_destination_bucket_delimiter,
     ['elife-666-vor-r1/']),
    ({'Bucket': DESTINATION_BUCKET, 'Delimiter': '/'},
     mocks.list_objects_v2_destination_bucket_delimiter,
     []),
    ({'Bucket': SOURCE_BUCKET},
     mocks.list_objects_v2_source_bucket,
     ['elife-666-vor-r1.zip']),
    ({'Bucket': SOURCE_BUCKET},
     mocks.list_objects_v2_source_bucket,
     [])
])
def test_list_bucket_keys_iter(params, response, expected, mocker):
    if not expected:
        response.pop('Contents', None)
        response.pop('CommonPrefixes', None)

    mocker.patch('boto3.client', new_callable=mocks.s3ClientMock)
    keys = list_bucket_keys_iter(response=[response], **params)
    assert list(keys) == expected
