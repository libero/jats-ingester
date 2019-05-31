from io import BytesIO
from pathlib import Path

import pytest
from lxml import etree

from dags.process_elife_zip_dag import (
    extract_archived_files_to_bucket,
    prepare_jats_xml_for_libero,
    ALLOWED_EXTENSIONS
)
from tests.assets import get_asset
from tests.mocks import s3ClientMock


def test_extract_archived_files_to_bucket(mocker, context):
    mocker.patch('boto3.client', new_callable=s3ClientMock)
    context['dag_run'].conf = {'file': 'elife-666-vor-r1.zip'}
    result = extract_archived_files_to_bucket(**context)
    assert result == 'elife-666-vor-r1/elife-666.xml'


def test_extract_archived_files_to_bucket_raises_exception_if_file_name_not_passed(context):
    # should raise an exception if dag_run.conf is None
    dag_run = context['dag_run']
    msg = '%s triggered without a file name passed to conf' % dag_run.dag_id
    with pytest.raises(AssertionError) as error:
        extract_archived_files_to_bucket(**context)
        assert str(error.value) == msg


def test_extract_archived_files_to_bucket_raises_exception_if_more_than_one_xml_in_zip(mocker, context):
    mocker.patch('boto3.client', new_callable=s3ClientMock)
    file_name = 'elife-666-vor-r1.zip'
    xml_files = ['test1.xml', 'test2.xml']
    context['dag_run'].conf = {'file': file_name}
    namelist = mocker.patch('zipfile.ZipFile.namelist')
    namelist.return_value = xml_files
    msg = ('only 1 XML file supported. %s XML files found in %s: %s' %
           (len(xml_files), file_name, xml_files))
    with pytest.raises(AssertionError) as error:
        extract_archived_files_to_bucket(**context)
        assert str(error.value) == msg


def test_extract_archived_files_to_bucket_raises_exception_if_no_xml_files_in_zip(mocker, context):
    mocker.patch('boto3.client', new_callable=s3ClientMock)
    file_name = 'elife-666-vor-r1.zip'
    xml_files = []
    context['dag_run'].conf = {'file': file_name}
    namelist = mocker.patch('zipfile.ZipFile.namelist')
    namelist.return_value = xml_files
    msg = ('only 1 XML file supported. %s XML files found in %s: %s' %
           (len(xml_files), file_name, xml_files))
    with pytest.raises(AssertionError) as error:
        extract_archived_files_to_bucket(**context)
        assert str(error.value) == msg


def test_extract_archived_files_to_bucket_only_uploads_allowed_file_types(mocker, context):
    client = mocker.patch('boto3.client', new_callable=s3ClientMock)
    context['dag_run'].conf = {'file': 'elife-666-vor-r1.zip'}
    extract_archived_files_to_bucket(**context)
    assert all(Path(uf).suffix in ALLOWED_EXTENSIONS for uf in client.uploaded_files)


def test_prepare_jats_xml_for_libero(mocker, context):
    mocker.patch('boto3.client', new_callable=s3ClientMock)
    # populate expected return value of previous task
    file_name = 'elife-666.xml'
    ti = context['dag_run'].get_task_instances()[0]
    ti.xcom_push(key='return_value', value=file_name)
    result = prepare_jats_xml_for_libero(**context)
    expected = etree.parse(BytesIO(get_asset(file_name)))
    assert result == etree.tostring(expected)


def test_prepare_jats_xml_for_libero_raises_exception(context):
    msg = 'path to xml document was not passed from task previous_task'
    with pytest.raises(AssertionError) as error:
        prepare_jats_xml_for_libero(**context)
        assert str(error.value) == msg
