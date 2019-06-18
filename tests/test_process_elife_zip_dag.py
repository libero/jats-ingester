from io import BytesIO
from pathlib import Path
from xml.dom import XML_NAMESPACE

import pytest
from airflow import configuration
from lxml import etree

from dags.process_elife_zip_dag import (
    extract_archived_files_to_bucket,
    wrap_article_in_libero_xml_and_send_to_service,
    ALLOWED_EXTENSIONS
)


def test_extract_archived_files_to_bucket(context, s3_client):
    context['dag_run'].conf = {'file': 'elife-00666-vor-r1.zip'}
    result = extract_archived_files_to_bucket(**context)
    assert result == 'elife-00666-vor-r1/elife-00666.xml'


def test_extract_archived_files_to_bucket_only_uploads_allowed_file_types(context, s3_client):
    context['dag_run'].conf = {'file': 'elife-00666-vor-r1.zip'}
    extract_archived_files_to_bucket(**context)
    assert all(Path(uf).suffix in ALLOWED_EXTENSIONS for uf in s3_client.uploaded_files)


@pytest.mark.parametrize('name', [
    'test.zip',
    'test_zip.zip',
    'test!-this.zip',
    'test-!this.zip',
    'don\'t-do-this.zip'
])
def test_extract_archived_files_to_bucket_raises_exception_if_zip_name_is_malformed(name, context):
    context['dag_run'].conf = {'file': name}
    msg =('%s is malformed. Expected archive name to start with '
          'any number/character, hyphen, any number/character (%s)'
          'example: name-id=version.extension' % (name, r'^\w+-\w+'))
    with pytest.raises(AssertionError) as error:
        extract_archived_files_to_bucket(**context)
        assert str(error.value) == msg


def test_extract_archived_files_to_bucket_raises_exception_when_article_not_in_zip(context, mocker, s3_client):
    context['dag_run'].conf = {'file': 'elife-00666-vor-r1.zip'}
    mocker.patch('zipfile.ZipFile.namelist', return_value=[])
    with pytest.raises(FileNotFoundError) as error:
        extract_archived_files_to_bucket(**context)
        assert str(error.value) == 'elife-00666.xml not in elife-00666-vor-r1.zip: []'


def test_extract_archived_files_to_bucket_raises_exception_when_file_not_passed_from_previous_task(context):
    msg = '%s triggered without a file name passed to conf' % context['dag_run'].dag_id
    with pytest.raises(AssertionError) as error:
        extract_archived_files_to_bucket(**context)
        assert str(error.value) == msg


def test_wrap_article_in_libero_xml_and_send_to_service(context, s3_client, requests_mock):
    # populate expected return value of previous task
    file_name = '/elife-00666-vor-r1/elife-00666.xml'
    ti = context['dag_run'].get_task_instances()[0]
    ti.xcom_push(key='return_value', value=file_name)

    from dags import process_elife_zip_dag as pezd
    test_url = 'http://test-url.org'
    pezd.SERVICE_URL = test_url
    session = requests_mock.put('%s/items/00666/versions/1' %  test_url)

    wrap_article_in_libero_xml_and_send_to_service(**context)

    request_data = bytes(session.last_request.text, encoding='UTF-8')
    xml = etree.parse(BytesIO(request_data))
    namespaces = {'libero': 'http://libero.pub',
                  'jats': 'http://jats.nlm.nih.gov'}

    article_id = xml.xpath('//libero:item/libero:meta/libero:id',
                           namespaces=namespaces)[0]
    assert article_id.text == '00666'

    service_name = configuration.conf.get('libero', 'service_name')
    assert service_name is not None

    service = xml.xpath('//libero:item/libero:meta/libero:service',
                        namespaces=namespaces)[0]
    assert service.text == service_name

    article = xml.xpath('//libero:item/jats:article', namespaces=namespaces)[0]
    assert article is not None
    assert len(article.getchildren()) > 0
    assert article.attrib['{%s}base' % XML_NAMESPACE].endswith('/')


def test_wrap_article_in_libero_xml_and_send_to_service_raises_exception(context):
    msg = 'path to xml document was not passed from task previous_task'
    with pytest.raises(AssertionError) as error:
        wrap_article_in_libero_xml_and_send_to_service(**context)
        assert str(error.value) == msg
