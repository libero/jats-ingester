"""
DAG processes a zip file stored in an AWS S3 bucket and prepares the extracted xml
file for Libero content API and sends to the content store via a PUT request.
"""
import logging
import multiprocessing
import re
from datetime import timedelta
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryFile
from typing import List
from xml.dom import XML_NAMESPACE
from zipfile import ZipFile

import requests
from airflow import DAG, configuration
from airflow.operators import python_operator
from airflow.utils import timezone
from lxml import etree
from lxml.builder import ElementMaker
from lxml.etree import ElementTree
from wand.image import Image

from aws import get_s3_client, list_bucket_keys_iter
from task_helpers import (
    get_file_name_passed_to_dag_run_conf_file,
    get_previous_task_name,
    get_return_value_from_previous_task
)

# settings
ARTICLE_ASSETS_URL = configuration.conf.get('libero', 'article_assets_url')
SOURCE_BUCKET = configuration.conf.get('libero', 'source_bucket_name')
DESTINATION_BUCKET = configuration.conf.get('libero', 'destination_bucket_name')
SERVICE_NAME = configuration.conf.get('libero', 'service_name')
SERVICE_URL = configuration.conf.get('libero', 'service_url')
TEMP_DIRECTORY = configuration.conf.get('libero', 'temp_directory_path') or None
SEARCH_URL = configuration.conf.get('libero', 'search_url')

# namespaces
XLINK_HREF = '{http://www.w3.org/1999/xlink}href'

logger = logging.getLogger(__name__)

default_args = {
    'owner': 'libero',
    'depends_on_past': False,
    'start_date': timezone.utcnow(),
    'email': ['libero@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(seconds=5)
}


def get_expected_elife_article_name(file_name: str) -> str:
    pattern = r'^\w+-\w+'
    article_name = re.search(pattern, file_name)
    error_message = ('%s is malformed. Expected archive name to start with '
                     'any number/character, hyphen, any number/character (%s)'
                     'example: name-id.extension' % (file_name, pattern))
    assert article_name and file_name.startswith(article_name.group()), error_message
    return article_name.group() + '.xml'


def get_article_from_previous_task(context: dict) -> ElementTree:
    article_bytes = get_return_value_from_previous_task(context)
    previous_task = get_previous_task_name(context)
    message = 'Article bytes were not passed from task %s' % previous_task
    assert article_bytes and isinstance(article_bytes, bytes), message
    return etree.parse(BytesIO(article_bytes))


def convert_image_in_s3_to_jpeg(key) -> str:
    s3 = get_s3_client()
    with TemporaryFile(dir=TEMP_DIRECTORY) as temp_tiff_file:
        s3.download_fileobj(
            Bucket=DESTINATION_BUCKET,
            Key=key,
            Fileobj=temp_tiff_file
        )
        temp_tiff_file.seek(0)

        logger.info('converting %s to jpeg', key)

        temp_jpeg = BytesIO()
        with Image(file=temp_tiff_file) as img:
            img.format = 'jpeg'
            img.save(file=temp_jpeg)

        key = re.sub(r'\.\w+$', '.jpg', key)
        s3.put_object(
            Bucket=DESTINATION_BUCKET,
            Key=key,
            Body=temp_jpeg.getvalue()
        )
        return key


def extract_archived_files_to_bucket(**context) -> str:
    zip_file_name = get_file_name_passed_to_dag_run_conf_file(context)
    article_name = get_expected_elife_article_name(zip_file_name)

    with TemporaryFile(dir=TEMP_DIRECTORY) as temp_zip_file:
        s3 = get_s3_client()
        s3.download_fileobj(
            Bucket=SOURCE_BUCKET,
            Key=zip_file_name,
            Fileobj=temp_zip_file
        )
        logger.info('ZIPPED FILES= %s', ZipFile(temp_zip_file).namelist())

        prefix = zip_file_name.replace('.zip', '/')

        # extract zip to cloud bucket
        for zipped_file_path in ZipFile(temp_zip_file).namelist():
            # extract zipped files to disk to avoid using too much memory
            with TemporaryFile(dir=TEMP_DIRECTORY) as temp_unzipped_file:
                temp_unzipped_file.write(ZipFile(temp_zip_file).read(zipped_file_path))
                temp_unzipped_file.seek(0)

                s3_key = prefix + zipped_file_path
                s3.put_object(
                    Bucket=DESTINATION_BUCKET,
                    Key=s3_key,
                    Body=temp_unzipped_file
                )
                logger.info('%s uploaded to %s', s3_key, DESTINATION_BUCKET)

        # check if expected article in zip file
        if not [fn for fn in ZipFile(temp_zip_file).namelist() if article_name in fn]:
            error_message = '%s not in %s: %s' % (article_name, zip_file_name,
                                                  ZipFile(temp_zip_file).namelist())
            raise FileNotFoundError(error_message)

    # pass article cloud bucket key to next task
    return '%s/%s' % (prefix, article_name)


def convert_tiff_images_in_expanded_bucket_to_jpeg_images(**context) -> List[str]:
    zip_file_name = get_file_name_passed_to_dag_run_conf_file(context)
    prefix = zip_file_name.replace('.zip', '/')
    tiffs = {key
             for key in list_bucket_keys_iter(Bucket=DESTINATION_BUCKET, Prefix=prefix)
             if key.endswith('.tif')}

    with multiprocessing.Pool() as p:
        return p.map(convert_image_in_s3_to_jpeg, tiffs, chunksize=3)


def update_tiff_references_to_jpeg_in_article(**context) -> bytes:
    zip_file_name = get_file_name_passed_to_dag_run_conf_file(context)
    article_name = get_expected_elife_article_name(zip_file_name)
    prefix = zip_file_name.replace('.zip', '/')
    s3_key = prefix + article_name

    s3 = get_s3_client()
    response = s3.get_object(Bucket=DESTINATION_BUCKET, Key=s3_key)

    article_bytes = BytesIO(response['Body'].read())
    article_xml = etree.parse(article_bytes)

    for element in article_xml.xpath('//*[@mimetype="image" and @mime-subtype="tiff"]'):
        element.attrib[XLINK_HREF] = re.sub(r'\.\w+$', '.jpg', element.attrib[XLINK_HREF])
        element.attrib['mime-subtype'] = 'jpeg'

    return etree.tostring(article_xml, xml_declaration=True, encoding='UTF-8')


def add_missing_jpeg_extensions_in_article(**context) -> bytes:
    article_xml = get_article_from_previous_task(context)
    for element in article_xml.xpath('//*[@mimetype="image" and @mime-subtype="jpeg"]'):
        if not element.attrib[XLINK_HREF].endswith('.jpg'):
            element.attrib[XLINK_HREF] = element.attrib[XLINK_HREF] + '.jpg'

    return etree.tostring(article_xml, xml_declaration=True, encoding='UTF-8')


def strip_related_article_tags_from_article_xml(**context) -> bytes:
    article_xml = get_article_from_previous_task(context)
    for element in article_xml.xpath('//related-article'):
        element.getparent().remove(element)

    return etree.tostring(article_xml, xml_declaration=True, encoding='UTF-8')


def wrap_article_in_libero_xml(**context) -> bytes:
    article_xml = get_article_from_previous_task(context)

    # get article id
    article_id = article_xml.xpath(
        '/article/front/article-meta/article-id[@pub-id-type="publisher-id"]'
    )[0].text

    # add jats prefix to jats tags
    for element in article_xml.iter():
        if not element.prefix:
            element.tag = '{http://jats.nlm.nih.gov}%s' % element.tag

    # add xml:base attribute to article element
    root = article_xml.getroot()
    key = Path(get_file_name_passed_to_dag_run_conf_file(context)).stem
    root.set(
        '{%s}base' % XML_NAMESPACE,
        '%s/%s/' % (ARTICLE_ASSETS_URL, key)
    )

    # create libero xml
    doc = ElementMaker(nsmap={None: 'http://libero.pub',
                              'jats': 'http://jats.nlm.nih.gov'})
    xml = doc.item(
        doc.meta(
            doc.id(article_id),
            doc.service(SERVICE_NAME)
        ),
        root
    )

    return etree.tostring(xml, xml_declaration=True, encoding='UTF-8')


def send_article_to_content_service(**context) -> None:
    libero_xml = get_article_from_previous_task(context)

    # get article id
    xpath = '//libero:item/jats:article/jats:front/jats:article-meta/jats:article-id[@pub-id-type="publisher-id"]'
    namespaces = {'libero': 'http://libero.pub', 'jats': 'http://jats.nlm.nih.gov'}
    article_id = libero_xml.xpath(xpath, namespaces=namespaces)[0].text

    # make PUT request to service
    response = requests.put(
        '%s/items/%s/versions/1' % (SERVICE_URL, article_id),
        data=etree.tostring(libero_xml, xml_declaration=True, encoding='UTF-8'),
        headers={'content-type': 'application/xml'}
    )
    response.raise_for_status()
    logger.info('Libero wrapped article %s sent to %s with status code %s',
                article_id,
                SERVICE_URL,
                response.status_code)


def send_post_request_to_reindex_search_service():
    logger.info('Sending POST request to %s', SEARCH_URL)
    response = requests.post(SEARCH_URL)
    response.raise_for_status()
    logger.info('RESPONSE= %s %s', response.text, response.status_code)


# schedule_interval is None because DAG is only run when triggered
dag = DAG('process_elife_zip_dag',
          default_args=default_args,
          schedule_interval=None)

extract_zip_files = python_operator.PythonOperator(
    task_id='extract_archived_files_to_bucket',
    provide_context=True,
    python_callable=extract_archived_files_to_bucket,
    dag=dag
)

convert_tiff_images = python_operator.PythonOperator(
    task_id='convert_tiff_images_in_expanded_bucket_to_jpeg_images',
    provide_context=True,
    python_callable=convert_tiff_images_in_expanded_bucket_to_jpeg_images,
    dag=dag
)

update_tiff_references = python_operator.PythonOperator(
    task_id='update_tiff_references_to_jpeg_in_article',
    provide_context=True,
    python_callable=update_tiff_references_to_jpeg_in_article,
    dag=dag
)

add_missing_jpeg_extensions = python_operator.PythonOperator(
    task_id='add_missing_jpeg_extensions_in_article',
    provide_context=True,
    python_callable=add_missing_jpeg_extensions_in_article,
    dag=dag
)

strip_related_article_tags = python_operator.PythonOperator(
    task_id='strip_related_article_tags_from_article_xml',
    provide_context=True,
    python_callable=strip_related_article_tags_from_article_xml,
    dag=dag
)

wrap_article = python_operator.PythonOperator(
    task_id='wrap_article_in_libero_xml',
    provide_context=True,
    python_callable=wrap_article_in_libero_xml,
    dag=dag
)

send_article = python_operator.PythonOperator(
    task_id='send_article_to_content_service',
    provide_context=True,
    python_callable=send_article_to_content_service,
    dag=dag
)

reindex_search = python_operator.PythonOperator(
    task_id='send_post_request_to_reindex_search_service',
    python_callable=send_post_request_to_reindex_search_service,
    dag=dag
)

# set task run order
extract_zip_files.set_downstream(convert_tiff_images)
convert_tiff_images.set_downstream(update_tiff_references)
update_tiff_references.set_downstream(add_missing_jpeg_extensions)
add_missing_jpeg_extensions.set_downstream(strip_related_article_tags)
strip_related_article_tags.set_downstream(wrap_article)
wrap_article.set_downstream(send_article)
send_article.set_downstream(reindex_search)
