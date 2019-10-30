import itertools
import re
from zipfile import ZipFile

import pytest

import dags.process_zip_dag as pezd
from tests.assets import get_asset


@pytest.mark.parametrize('zip_file, sample_uploaded_file, num_of_tiffs', [
    ('elife-36842-vor-r3.zip', 'elife-36842-vor-r3/elife-36842-fig1.jpg', 25),
    ('elife-40092-vor-r2.zip', 'elife-40092-vor-r2/elife-40092-fig1.jpg', 11),
    ('biorxiv-685172.meca', 'biorxiv-685172/content/685172v1_tbl1.jpg', 5),
])
def test_convert_tiff_images_in_expanded_bucket_to_jpeg_images_using_article_with_tiff_images(
        zip_file, sample_uploaded_file, num_of_tiffs, s3_client, context, mocker):
    # setup
    context['dag_run'].conf = {'file': zip_file}

    prefix = re.sub(r'\.\w+$', '/', zip_file)
    keys = [prefix + fn for fn in ZipFile(get_asset(zip_file)).namelist()]
    keys = itertools.chain(keys, [prefix])
    mocker.patch('dags.process_zip_dag.list_bucket_keys_iter', return_value=keys)

    # test
    uploaded_files = pezd.convert_tiff_images_in_expanded_bucket_to_jpeg_images(**context)
    assert len(uploaded_files) == num_of_tiffs
    assert sample_uploaded_file in uploaded_files


def test_convert_tiff_images_in_expanded_bucket_to_jpeg_images_using_article_without_tiff_images(context, s3_client, mocker):
    # setup
    file_name = 'elife-00666-vor-r1.zip'
    context['dag_run'].conf = {'file': file_name}

    folder_name = file_name.replace('.zip', '/')
    keys = [folder_name + fn for fn in ZipFile(get_asset(file_name)).namelist()]
    keys = itertools.chain(keys, [folder_name])
    mocker.patch('dags.process_zip_dag.list_bucket_keys_iter', return_value=keys)
    # test
    pezd.convert_tiff_images_in_expanded_bucket_to_jpeg_images(**context)
    assert len(s3_client.uploaded_files) == 0
