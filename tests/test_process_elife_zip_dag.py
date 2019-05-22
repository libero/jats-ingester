from io import BytesIO

import pytest
from lxml import etree

from dags.process_elife_zip_dag import (
    extract_zipped_files_to_bucket,
    prepare_jats_xml_for_libero
)
from tests.assets import get_asset
from tests.mocks import s3ClientMock


def test_extract_zipped_files_to_bucket(mocker, context):
    mocker.patch('boto3.client', new_callable=s3ClientMock)
    context['dag_run'].conf = {'file': 'elife-666-vor-r1.zip'}
    result = extract_zipped_files_to_bucket(**context)
    assert result == 'elife-666-vor-r1/elife-666.xml'


def test_extract_zipped_files_to_bucket_raises_exception(context):
    """
    Should raise an exception if dag_run.conf is None.
    """
    dag_run = context['dag_run']
    msg = '%s triggered without a file name passed to conf' % dag_run.dag_id
    with pytest.raises(ValueError) as error:
        extract_zipped_files_to_bucket(**context)
        assert str(error.value) == msg


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
    with pytest.raises(ValueError) as error:
        prepare_jats_xml_for_libero(**context)
        assert str(error.value) == msg
