from tests.assets import get_asset


class s3ClientMock:

    def __init__(self, *args, **kwargs):
        self.downloaded_files = []
        self.uploaded_files = []

    def __call__(self, *args, **kwargs):
        return self

    def download_fileobj(self, bucket, key, file_obj):
        self.downloaded_files.append(key)
        file_obj.write(get_asset(key))

    def upload_fileobj(self, file_obj, bucket, key):
        self.uploaded_files.append(key)

    def get_paginator(self, *args):
        return self

    def paginate(self, *args, response=None, **kwargs):
        return response
