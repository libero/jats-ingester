import itertools
from io import BytesIO
from xml.dom import XML_NAMESPACE
from zipfile import ZipFile

import pytest
from lxml import etree
from requests.exceptions import HTTPError

import dags.process_elife_zip_dag as pezd
from tests.assets import get_asset
from tests.helpers import add_return_value_from_previous_task


@pytest.mark.parametrize('archive_name, expected_id', [
    ('elife-00666-vor-r1.zip', '00666'),
    ('elife-36842-vor-r3.zip', '36842'),
    ('elife-40092-vor-r2.zip', '40092'),
])
def test_get_article_from_zip_in_s3(archive_name, expected_id, s3_client):
    article = pezd.get_article_from_zip_in_s3(archive_name)
    article_id = article.xpath(
        '/article/front/article-meta/article-id[@pub-id-type="publisher-id"]'
    )[0].text
    assert article_id == expected_id


def test_get_article_from_zip_in_s3_raises_exception_when_article_not_in_zip(mocker, s3_client):
    # setup
    mocker.patch('zipfile.ZipFile.namelist', return_value=[])
    # test
    with pytest.raises(FileNotFoundError) as error:
        pezd.get_article_from_zip_in_s3('elife-00666-vor-r1.zip')
    assert str(error.value) == 'Unable to find a JATS article in elife-00666-vor-r1.zip'


def test_get_article_from_previous_task(context):
    # setup
    test_asset_path = str(get_asset('elife-00666.xml').absolute())
    article_xml = etree.tostring(etree.parse(test_asset_path))
    add_return_value_from_previous_task(return_value=article_xml, context=context)
    # test
    returned_xml = pezd.get_article_from_previous_task(context)
    assert etree.tostring(returned_xml) == article_xml


@pytest.mark.parametrize('return_value', [b'', '', None])
def test_get_article_from_previous_task_raises_exception(return_value, context):
    # setup
    add_return_value_from_previous_task(return_value, context)
    message = 'Article bytes were not passed from task previous_task'
    # setup
    with pytest.raises(AssertionError) as error:
        pezd.get_article_from_previous_task(context)
    assert str(error.value) == message


def test_extract_archived_files_to_bucket(context, s3_client):
    # setup
    file_name = 'elife-00666-vor-r1.zip'
    context['dag_run'].conf = {'file': file_name}
    # test
    pezd.extract_archived_files_to_bucket(**context)
    for zipped_file in ZipFile(get_asset(file_name)).namelist():
        expected_file = '%s/%s' % (file_name.replace('.zip', ''), zipped_file)
        assert expected_file in s3_client.uploaded_files


@pytest.mark.parametrize('zip_file, sample_uploaded_file, num_of_tiffs', [
    ('elife-36842-vor-r3.zip', 'elife-36842-vor-r3/elife-36842-fig1.jpg', 25),
    ('elife-40092-vor-r2.zip', 'elife-40092-vor-r2/elife-40092-fig1.jpg', 11)
])
def test_convert_tiff_images_in_expanded_bucket_to_jpeg_images_using_article_with_tiff_images(
        zip_file, sample_uploaded_file, num_of_tiffs, s3_client, context, mocker):
    # setup
    context['dag_run'].conf = {'file': zip_file}

    folder_name = zip_file.replace('.zip', '/')
    keys = [folder_name + fn for fn in ZipFile(get_asset(zip_file)).namelist()]
    keys = itertools.chain(keys, [folder_name])
    mocker.patch('dags.process_elife_zip_dag.list_bucket_keys_iter', return_value=keys)

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
    mocker.patch('dags.process_elife_zip_dag.list_bucket_keys_iter', return_value=keys)
    # test
    pezd.convert_tiff_images_in_expanded_bucket_to_jpeg_images(**context)
    assert len(s3_client.uploaded_files) == 0


def test_update_tiff_references_to_jpeg_in_articles_using_article_with_tiff_references(context, s3_client):
    # setup
    zip_file_name = 'elife-36842-vor-r3.zip'
    context['dag_run'].conf = {'file': zip_file_name}

    # check the test asset contains tiff references
    test_asset_path = str(get_asset(zip_file_name).absolute())
    article_xml = etree.parse(BytesIO(ZipFile(test_asset_path).read('elife-36842.xml')))
    tiff_xpath = '//*[@mimetype="image" and @mime-subtype="tiff"]'
    jpeg_xpath = '//*[@mimetype="image" and @mime-subtype="jpeg"]'
    assert len(article_xml.xpath(tiff_xpath)) == 25
    assert len(article_xml.xpath(jpeg_xpath)) == 0

    # test
    returned_xml = pezd.update_tiff_references_to_jpeg_in_article(**context)
    xml = etree.parse(BytesIO(returned_xml))
    assert len(xml.xpath(tiff_xpath)) == 0
    assert len(xml.xpath(jpeg_xpath)) == 25


def test_update_tiff_references_to_jpeg_in_articles_using_article_without_tiff_references(context, s3_client):
    # setup
    zip_file_name = 'elife-00666-vor-r1.zip'
    context['dag_run'].conf = {'file': zip_file_name}

    # check the test asset does not contain tiff references
    test_asset_path = str(get_asset(zip_file_name).absolute())
    article_xml = etree.parse(BytesIO(ZipFile(test_asset_path).read('elife-00666.xml')))
    assert len(article_xml.xpath('//*[@mimetype="image" and @mime-subtype="tiff"]')) == 0
    article_xml = etree.tostring(article_xml, xml_declaration=True, encoding='UTF-8')

    # test
    returned_xml = pezd.update_tiff_references_to_jpeg_in_article(**context)
    assert returned_xml == article_xml


def test_add_missing_jpeg_extensions_in_article(context):
    # setup
    zip_file_name = 'elife-40092-vor-r2.zip'
    test_asset_path = str(get_asset(zip_file_name).absolute())
    article_xml = etree.parse(BytesIO(ZipFile(test_asset_path).read('elife-40092.xml')))
    xpath = '//*[@xlink:href="elife-40092-resp-fig1"]'
    jpg_xpath = '//*[@xlink:href="elife-40092-resp-fig1.jpg"]'
    assert len(article_xml.xpath(xpath, namespaces=pezd.XLINK)) > 0
    assert len(article_xml.xpath(jpg_xpath, namespaces=pezd.XLINK)) == 0
    add_return_value_from_previous_task(
        return_value=etree.tostring(article_xml, xml_declaration=True, encoding='UTF-8'),
        context=context
    )

    # test
    returned_xml = pezd.add_missing_jpeg_extensions_in_article(**context)
    returned_xml = etree.parse(BytesIO(returned_xml))
    assert len(returned_xml.xpath(xpath, namespaces=pezd.XLINK)) == 0
    assert len(returned_xml.xpath(jpg_xpath, namespaces=pezd.XLINK)) > 0


def test_add_missing_jpeg_extensions_in_article_without_missing_jpeg_extension(context):
    # setup
    zip_file_name = 'elife-00666-vor-r1.zip'
    test_asset_path = str(get_asset(zip_file_name).absolute())
    article_xml = etree.parse(BytesIO(ZipFile(test_asset_path).read('elife-00666.xml')))
    for element in article_xml.xpath('//*[@mimetype="image" and @mime-subtype="jpeg"]'):
        assert element.attrib[pezd.XLINK_HREF].endswith('.jpg')

    article_xml = etree.tostring(article_xml, xml_declaration=True, encoding='UTF-8')
    add_return_value_from_previous_task(return_value=article_xml,context=context)

    # test
    returned_xml = pezd.add_missing_jpeg_extensions_in_article(**context)
    assert returned_xml == article_xml


def test_strip_related_article_tags_from_article_xml_using_article_with_related_article_tag(context):
    # setup
    test_asset_path = str(get_asset('elife-36842.xml').absolute())
    article_xml = etree.parse(test_asset_path)
    xpath = '//related-article'
    assert len(article_xml.xpath(xpath)) > 0
    add_return_value_from_previous_task(
        return_value=etree.tostring(article_xml, xml_declaration=True, encoding='UTF-8'),
        context=context
    )
    # test
    return_value = pezd.strip_related_article_tags_from_article_xml(**context)
    xml = etree.parse(BytesIO(return_value))
    assert len(xml.xpath(xpath)) == 0


def test_strip_related_article_tags_from_article_xml_using_article_without_related_article_tag(context):
    # setup
    test_asset_path = str(get_asset('elife-00666.xml').absolute())
    article_xml = etree.parse(test_asset_path)
    assert len(article_xml.xpath('//related-article')) == 0
    article_xml = etree.tostring(article_xml, xml_declaration=True, encoding='UTF-8')
    add_return_value_from_previous_task(article_xml, context=context)

    # test
    return_value = pezd.strip_related_article_tags_from_article_xml(**context)
    assert return_value == article_xml


def test_strip_object_id_tags_from_article_xml_using_article_with_object_id_tag(context):
    # setup
    test_asset_path = str(get_asset('elife-36842.xml').absolute())
    article_xml = etree.parse(test_asset_path)
    xpath = '//object-id'
    assert len(article_xml.xpath(xpath)) > 0
    add_return_value_from_previous_task(
        return_value=etree.tostring(article_xml, xml_declaration=True, encoding='UTF-8'),
        context=context
    )
    # test
    return_value = pezd.strip_object_id_tags_from_article_xml(**context)
    xml = etree.parse(BytesIO(return_value))
    assert len(xml.xpath(xpath)) == 0


def test_strip_object_id_tags_from_article_xml_using_article_without_object_id_tag(context):
    # setup
    test_asset_path = str(get_asset('elife-00666.xml').absolute())
    article_xml = etree.parse(test_asset_path)
    assert len(article_xml.xpath('//object-id')) == 0
    article_xml = etree.tostring(article_xml, xml_declaration=True, encoding='UTF-8')
    add_return_value_from_previous_task(article_xml, context=context)

    # test
    return_value = pezd.strip_object_id_tags_from_article_xml(**context)
    assert return_value == article_xml


def test_add_missing_uri_schemes(context):
    # setup
    test_asset_path = str(get_asset('elife-36842.xml').absolute())
    article_xml = etree.parse(test_asset_path)
    xpath = '//*[starts-with(@xlink:href, "www.")]'
    assert len(article_xml.xpath(xpath, namespaces=pezd.XLINK)) > 0
    add_return_value_from_previous_task(
        return_value=etree.tostring(article_xml, xml_declaration=True, encoding='UTF-8'),
        context=context
    )
    # test
    return_value = pezd.add_missing_uri_schemes(**context)
    xml = etree.parse(BytesIO(return_value))
    assert len(xml.xpath(xpath, namespaces=pezd.XLINK)) == 0


def test_wrap_article_in_libero_xml(context):
    # setup
    context['dag_run'].conf = {'file': 'elife-36842-vor-r3.zip'}
    test_asset_path = str(get_asset('elife-36842.xml').absolute())
    article_xml = etree.tostring(etree.parse(test_asset_path), xml_declaration=True, encoding='UTF-8')
    add_return_value_from_previous_task(return_value=article_xml, context=context)

    # test
    libero_xml = pezd.wrap_article_in_libero_xml(**context)
    xml = etree.parse(BytesIO(libero_xml))

    namespaces = pezd.LIBERO
    namespaces.update(pezd.JATS)
    article_id = xml.xpath('//libero:item/libero:meta/libero:id', namespaces=namespaces)[0]
    assert article_id.text == '36842'

    service = xml.xpath('//libero:item/libero:meta/libero:service', namespaces=namespaces)[0]
    assert service.text == 'test-service'

    article = xml.xpath('//libero:item/jats:article', namespaces=namespaces)[0]
    assert article is not None
    assert len(article.getchildren()) > 0

    xml_base = article.attrib['{%s}base' % XML_NAMESPACE]
    expected = 'https://test-expanded-bucket.test.com/elife-36842-vor-r3/'
    assert xml_base == expected


def test_wrap_article_in_libero_xml_raises_exception_if_xml_path_not_returned_by_previous_task(context):
    msg = 'Article bytes were not passed from task previous_task'
    with pytest.raises(AssertionError) as error:
        pezd.wrap_article_in_libero_xml(**context)
    assert str(error.value) == msg


def test_send_article_to_service(context, requests_mock):
    # setup
    test_asset_path = str(get_asset('libero-00666.xml').absolute())
    article_xml = etree.tostring(etree.parse(test_asset_path), xml_declaration=True, encoding='UTF-8')
    add_return_value_from_previous_task(return_value=article_xml, context=context)
    session = requests_mock.put('http://test-service.org/items/00666/versions/1')

    # test
    pezd.send_article_to_content_service(**context)
    response = session._responses[0].get_response(session.last_request)
    assert response.status_code == 200
    request_data = bytes(session.last_request.text, encoding='UTF-8')
    etree.parse(BytesIO(request_data))  # raises exception if cannot parse xml


def test_send_article_to_service_raises_exception_for_non_200_response_code(context, requests_mock):
    # setup
    test_asset_path = str(get_asset('libero-00666.xml').absolute())
    article_xml = etree.tostring(etree.parse(test_asset_path), xml_declaration=True, encoding='UTF-8')
    add_return_value_from_previous_task(return_value=article_xml, context=context)
    requests_mock.put(
        'http://test-service.org/items/00666/versions/1',
        status_code=500,
        text='text sent from external service with error message'
    )

    with pytest.raises(HTTPError):
        pezd.send_article_to_content_service(**context)
