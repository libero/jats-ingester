from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from tests.assets import get_asset, search_asset


class s3ClientMock:

    def __init__(self, *args, **kwargs):
        self.downloaded_files = []
        self.uploaded_files = []
        self.last_uploaded_file_bytes = None

    def __call__(self, *args, **kwargs):
        return self

    def _read_bytes(self, file_name):
        """
        Trys to find the file in the project and read it. If the file is not
        located, try to locate the file in a zip file if `file_name` is a path.

        :param str file_name: name of file or file path
        :return bytes: bytes of read file
        """
        try:
            return get_asset(file_name).read_bytes()
        except FileNotFoundError:
            file_name = Path(file_name)
            path_in_zip = '/'.join(file_name.parts[1:])
            for asset in search_asset('*%s*' % file_name.parts[0]):
                if asset.suffix in ['.zip', '.meca']:
                    key = asset.name
                    break

            return ZipFile(get_asset(key)).read(path_in_zip)

    def download_fileobj(self, *args, **kwargs):
        self.downloaded_files.append(kwargs['Key'])
        kwargs['Fileobj'].write(self._read_bytes(kwargs['Key']))

    def upload_fileobj(self, *args, **kwargs):
        self.uploaded_files.append(kwargs['Key'])
        self.last_uploaded_file_bytes = kwargs['Fileobj'].read()

    def get_object(self, *args, **kwargs):
        self.downloaded_files.append(kwargs['Key'])
        return {'Body': BytesIO(self._read_bytes(kwargs['Key']))}

    def put_object(self, *args, **kwargs):
        self.uploaded_files.append(kwargs['Key'])
        self.last_uploaded_file_bytes = kwargs['Body']

    def get_paginator(self, *args):
        return self

    def paginate(self, *args, response=None, **kwargs):
        return response
