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


def test_extract_archived_files_to_bucket(context, s3_client):
    context['dag_run'].conf = {'file': 'elife-666-vor-r1.zip'}
    result = extract_archived_files_to_bucket(**context)
    assert result == 'elife-666-vor-r1/elife-666.xml'


@pytest.mark.parametrize('file_name, xml_files, conf, message', [
    (
        None,
        [],
        None,
        '{dag_id} triggered without a file name passed to conf'
    ),
    (
        'elife-666-vor-r1.zip',
        ['test1.xml', 'test2.xml'],
        {'file': 'elife-666-vor-r1.zip'},
        'only 1 XML file supported. {len_files} XML files found in {file_name}: {xml_files}'
    ),
    (
        'elife-666-vor-r1.zip',
        [],
        {'file': 'elife-666-vor-r1.zip'},
        'only 1 XML file supported. {len_files} XML files found in {file_name}: {xml_files}'
    ),
])
def test_extract_archived_files_to_bucket_raises_exception(
        file_name, xml_files, conf, message, mocker, context, s3_client):

    context['dag_run'].conf = conf
    mocker.patch('zipfile.ZipFile.namelist', return_value=xml_files)
    msg = message.format(
        dag_id=context['dag_run'].dag_id,
        len_files=len(xml_files),
        xml_files=xml_files,
        file_name=file_name
    )
    with pytest.raises(AssertionError) as error:
        extract_archived_files_to_bucket(**context)
        assert str(error.value) == msg


def test_extract_archived_files_to_bucket_only_uploads_allowed_file_types(context, s3_client):
    context['dag_run'].conf = {'file': 'elife-666-vor-r1.zip'}
    extract_archived_files_to_bucket(**context)
    assert all(Path(uf).suffix in ALLOWED_EXTENSIONS for uf in s3_client.uploaded_files)


def test_prepare_jats_xml_for_libero(context, s3_client):
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
