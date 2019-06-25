import itertools
from io import BytesIO
from xml.dom import XML_NAMESPACE
from zipfile import ZipFile

import pytest
from airflow import configuration
from lxml import etree

from dags.process_elife_zip_dag import (
    convert_tiff_images_in_expanded_bucket_to_jpeg_images,
    extract_archived_files_to_bucket,
    get_article_from_previous_task,
    get_expected_elife_article_name,
    strip_related_article_tags_from_article_xml,
    update_tiff_references_to_jpeg_in_article,
    wrap_article_in_libero_xml_and_send_to_service
)
from tests.assets import get_asset
from tests.helpers import add_return_value_from_previous_task


@pytest.mark.parametrize('archive_name, expected', [
    ('elife-00666-vor-r1.zip', 'elife-00666.xml'),
    ('elife-00666-vor-r1', 'elife-00666.xml'),
    ('test-name', 'test-name.xml'),
    ('test123-name456', 'test123-name456.xml'),
    ('1test1-1name1', '1test1-1name1.xml'),
])
def test_get_expected_elife_article_name(archive_name, expected):
    article_name = get_expected_elife_article_name(archive_name)
    assert article_name == expected


@pytest.mark.parametrize('name', [
    'test.zip',
    'test_zip.zip',
    'test!-this.zip',
    'test-!this.zip',
    'don\'t-do-this.zip'
])
def test_get_expected_elife_article_name_raises_exception_if_zip_name_is_malformed(name):
    msg =('%s is malformed. Expected archive name to start with '
          'any number/character, hyphen, any number/character (%s)'
          'example: name-id.extension' % (name, r'^\w+-\w+'))
    with pytest.raises(AssertionError) as error:
        get_expected_elife_article_name(name)
    assert str(error.value) == msg


def test_get_article_from_previous_task(context):
    # setup
    test_asset_path = str(get_asset('elife-00666.xml').absolute())
    article_xml = etree.tostring(etree.parse(test_asset_path))
    add_return_value_from_previous_task(return_value=article_xml, context=context)
    # test
    returned_value = get_article_from_previous_task(context)
    assert etree.tostring(returned_value) == article_xml


@pytest.mark.parametrize('return_value', [b'', '', None])
def test_get_article_from_previous_task_raises_exception(return_value, context):
    # setup
    add_return_value_from_previous_task(return_value, context)
    message = 'Article bytes were not passed from task previous_task'
    # setup
    with pytest.raises(AssertionError) as error:
        get_article_from_previous_task(context)
    assert str(error.value) == message


def test_extract_archived_files_to_bucket(context, s3_client):
    # setup
    file_name = 'elife-00666-vor-r1.zip'
    context['dag_run'].conf = {'file': file_name}
    # test
    extract_archived_files_to_bucket(**context)
    for zipped_file in ZipFile(get_asset(file_name)).namelist():
        expected_file = '%s/%s' % (file_name.replace('.zip', ''), zipped_file)
        assert expected_file in s3_client.uploaded_files


def test_extract_archived_files_to_bucket_raises_exception_when_article_not_in_zip(context, mocker, s3_client):
    # setup
    context['dag_run'].conf = {'file': 'elife-00666-vor-r1.zip'}
    mocker.patch('zipfile.ZipFile.namelist', return_value=[])
    # test
    with pytest.raises(FileNotFoundError) as error:
        extract_archived_files_to_bucket(**context)
    assert str(error.value) == 'elife-00666.xml not in elife-00666-vor-r1.zip: []'


def test_convert_tiff_images_in_expanded_bucket_to_jpeg_images_using_article_with_tiff_images(context, s3_client, mocker):
    # setup
    file_name = 'elife-36842-vor-r3.zip'
    context['dag_run'].conf = {'file': file_name}

    folder_name = file_name.replace('.zip', '/')
    keys = [folder_name + fn for fn in ZipFile(get_asset(file_name)).namelist()]
    keys = itertools.chain(keys, [folder_name])
    mocker.patch('dags.process_elife_zip_dag.list_bucket_keys_iter', return_value=keys)

    # test
    convert_tiff_images_in_expanded_bucket_to_jpeg_images(**context)

    # recreate expected uploaded file names
    zipped_files = [fn.replace('.tif', '.jpg')
                    for fn in ZipFile(get_asset(file_name)).namelist()
                    if fn.endswith('.tif')]
    assert zipped_files

    for zipped_file in zipped_files:
        expected_file = file_name.replace('.zip', '/') + zipped_file
        assert expected_file in s3_client.uploaded_files


def test_convert_tiff_images_in_expanded_bucket_to_jpeg_images_using_article_without_tiff_images(context, s3_client, mocker):
    # setup
    file_name = 'elife-00666-vor-r1.zip'
    context['dag_run'].conf = {'file': file_name}

    folder_name = file_name.replace('.zip', '/')
    keys = [folder_name + fn for fn in ZipFile(get_asset(file_name)).namelist()]
    keys = itertools.chain(keys, [folder_name])
    mocker.patch('dags.process_elife_zip_dag.list_bucket_keys_iter', return_value=keys)
    # test
    convert_tiff_images_in_expanded_bucket_to_jpeg_images(**context)
    assert len(s3_client.uploaded_files) == 0


def test_update_tiff_references_to_jpeg_in_articles_using_article_with_tiff_references(context):
    # setup
    test_asset_path = str(get_asset('elife-36842.xml').absolute())
    article_xml = etree.parse(test_asset_path)
    assert len(article_xml.xpath('//*[@mimetype="image" and @mime-subtype="tiff"]')) == 25
    assert len(article_xml.xpath('//*[@mimetype="image" and @mime-subtype="jpeg"]')) == 0
    add_return_value_from_previous_task(
        return_value=etree.tostring(article_xml, xml_declaration=True, encoding='UTF-8'),
        context=context
    )
    # test
    return_value = update_tiff_references_to_jpeg_in_article(**context)
    xml = etree.parse(BytesIO(return_value))
    assert len(xml.xpath('//*[@mimetype="image" and @mime-subtype="tiff"]')) == 0
    assert len(xml.xpath('//*[@mimetype="image" and @mime-subtype="jpeg"]')) == 25


def test_update_tiff_references_to_jpeg_in_articles_using_article_without_tiff_references(context):
    # setup
    test_asset_path = str(get_asset('elife-00666.xml').absolute())
    article_xml = etree.tostring(etree.parse(test_asset_path), xml_declaration=True, encoding='UTF-8')
    add_return_value_from_previous_task(return_value=article_xml, context=context)
    # test
    return_value = update_tiff_references_to_jpeg_in_article(**context)
    assert return_value == article_xml


def test_strip_related_article_tags_from_article_xml_using_article_with_related_article_tag(context):
    # setup
    test_asset_path = str(get_asset('elife-36842.xml').absolute())
    article_xml = etree.parse(test_asset_path)
    assert len(article_xml.xpath('//related-article')) == 1
    add_return_value_from_previous_task(
        return_value=etree.tostring(article_xml, xml_declaration=True, encoding='UTF-8'),
        context=context
    )
    # test
    return_value = strip_related_article_tags_from_article_xml(**context)
    xml = etree.parse(BytesIO(return_value))
    assert len(xml.xpath('//related-article')) == 0


def test_strip_related_article_tags_from_article_xml_using_article_without_related_article_tag(context):
    # setup
    test_asset_path = str(get_asset('elife-00666.xml').absolute())
    article_xml = etree.tostring(etree.parse(test_asset_path), xml_declaration=True, encoding='UTF-8')
    # test
    add_return_value_from_previous_task(return_value=article_xml, context=context)
    return_value = strip_related_article_tags_from_article_xml(**context)
    assert return_value == article_xml


def test_wrap_article_in_libero_xml_and_send_to_service(context, s3_client, requests_mock):
    # setup
    file_name = 'elife-36842-vor-r3.zip'
    context['dag_run'].conf = {'file': file_name}

    test_asset_path = str(get_asset('elife-36842.xml').absolute())
    article_xml = etree.tostring(etree.parse(test_asset_path), xml_declaration=True, encoding='UTF-8')
    add_return_value_from_previous_task(return_value=article_xml, context=context)

    from dags import process_elife_zip_dag as pezd
    test_url = 'http://test-url.org'
    pezd.SERVICE_URL = test_url
    session = requests_mock.put('%s/items/36842/versions/1' %  test_url)

    # test
    wrap_article_in_libero_xml_and_send_to_service(**context)

    request_data = bytes(session.last_request.text, encoding='UTF-8')
    xml = etree.parse(BytesIO(request_data))
    namespaces = {'libero': 'http://libero.pub',
                  'jats': 'http://jats.nlm.nih.gov'}

    article_id = xml.xpath('//libero:item/libero:meta/libero:id',
                           namespaces=namespaces)[0]
    assert article_id.text == '36842'

    service_name = configuration.conf.get('libero', 'service_name')
    assert service_name is not None

    service = xml.xpath('//libero:item/libero:meta/libero:service',
                        namespaces=namespaces)[0]
    assert service.text == service_name

    article = xml.xpath('//libero:item/jats:article', namespaces=namespaces)[0]
    assert article is not None
    assert len(article.getchildren()) > 0
    assert article.attrib['{%s}base' % XML_NAMESPACE].endswith('/')


def test_wrap_article_in_libero_xml_and_send_to_service_raises_exception_if_xml_path_not_returned_by_previous_task(context):
    msg = 'Article bytes were not passed from task previous_task'
    with pytest.raises(AssertionError) as error:
        wrap_article_in_libero_xml_and_send_to_service(**context)
    assert str(error.value) == msg
