import datetime

from dateutil.tz import tzlocal

from tests.assets import get_asset


class s3ClientMock:

    def __call__(self, *args, **kwargs):
        return self

    def download_fileobj(self, bucket, key, file_obj):
        file_obj.write(get_asset(key))

    def upload_fileobj(self, *args, **kwargs):
        pass

    def get_paginator(self, *args):
        return self

    def paginate(self, *args, response=None, **kwargs):
        return response


list_objects_v2_source_bucket_delimiter = {
    'ResponseMetadata': {
        'HTTPStatusCode': 200,
        'HTTPHeaders': {
            'server': 'BaseHTTP/0.6 Python/3.6.8',
            'date': 'Fri, 24 May 2019 13:46:37 GMT',
            'content-type': 'application/xml; charset=utf-8',
            'content-length': '368',
            'access-control-allow-origin': '*',
            'access-control-allow-methods': 'HEAD,GET,PUT,POST,DELETE,OPTIONS,PATCH',
            'access-control-allow-headers': ('authorization,content-type,content'
                                             '-md5,cache-control,x-amz-content-'
                                             'sha256,x-amz-date,x-amz-security-'
                                             'token,x-amz-user-agent')
        },
        'RetryAttempts': 0
    },
    'IsTruncated': False,
    'Name': 'dev-elife-style-content-adapter-incoming',
    'Prefix': '',
    'Delimiter': '.zip',
    'MaxKeys': 1000,
    'CommonPrefixes': [
        {'Prefix': 'elife-666-vor-r1.zip'}
    ],
    'KeyCount': 0
}

list_objects_v2_source_bucket = {
    'ResponseMetadata': {
        'HTTPStatusCode': 200,
        'HTTPHeaders': {
            'server': 'BaseHTTP/0.6 Python/3.6.8',
            'date': 'Fri, 24 May 2019 13:55:27 GMT',
            'content-type': 'application/xml; charset=utf-8',
            'content-length': '487',
            'access-control-allow-origin': '*',
            'access-control-allow-methods': 'HEAD,GET,PUT,POST,DELETE,OPTIONS,PATCH',
            'access-control-allow-headers': ('authorization,content-type,content'
                                             '-md5,cache-control,x-amz-content-'
                                             'sha256,x-amz-date,x-amz-security-'
                                             'token,x-amz-user-agent')
        },
        'RetryAttempts': 0
    },
    'IsTruncated': False,
    'Contents': [
        {'Key': 'elife-666-vor-r1.zip',
         'LastModified': datetime.datetime(2019, 5, 24, 13, 55, 19, 612000, tzinfo=tzlocal()),
         'ETag': '"4022e39d21e232ebb0f696040bdb394c"',
         'Size': 214699,
         'StorageClass': 'STANDARD'}
    ],
    'Name': 'dev-elife-style-content-adapter-incoming',
    'Prefix': '',
    'MaxKeys': 1000,
    'KeyCount': 1
}

list_objects_v2_destination_bucket_delimiter = {
    'ResponseMetadata': {
        'HTTPStatusCode': 200,
        'HTTPHeaders': {
            'server': 'BaseHTTP/0.6 Python/3.6.8',
            'date': 'Fri, 24 May 2019 13:55:27 GMT',
            'content-type': 'application/xml; charset=utf-8',
            'content-length': '362',
            'access-control-allow-origin': '*',
            'access-control-allow-methods': 'HEAD,GET,PUT,POST,DELETE,OPTIONS,PATCH',
            'access-control-allow-headers': ('authorization,content-type,content'
                                             '-md5,cache-control,x-amz-content'
                                             '-sha256,x-amz-date,x-amz-security'
                                             '-token,x-amz-user-agent')
        },
        'RetryAttempts': 0
    },
    'IsTruncated': False,
    'Name': 'dev-elife-style-content-adapter-expanded',
    'Prefix': '',
    'Delimiter': '/',
    'MaxKeys': 1000,
    'CommonPrefixes': [
        {'Prefix': 'elife-666-vor-r1/'}
    ],
    'KeyCount': 0
}
