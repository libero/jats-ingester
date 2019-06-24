"""
DAG processes a zip file stored in an AWS S3 bucket and prepares the extracted xml
file for Libero content API and sends to the content store via a PUT request.
"""
import logging
import re
from datetime import timedelta
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryFile
from xml.dom import XML_NAMESPACE
from zipfile import ZipFile

import requests
from airflow import DAG, configuration
from airflow.operators import python_operator
from airflow.utils import timezone
from lxml import etree
from lxml.builder import ElementMaker
from PIL import Image

from aws import get_aws_connection, list_bucket_keys_iter
from task_helpers import get_file_name_passed_to_dag_run_conf_file

BASE_URL = configuration.conf.get('libero', 'base_url')
SOURCE_BUCKET = configuration.conf.get('libero', 'source_bucket')
DESTINATION_BUCKET = configuration.conf.get('libero', 'destination_bucket')
SERVICE_NAME = configuration.conf.get('libero', 'service_name')
SERVICE_URL = configuration.conf.get('libero', 'service_url')
TEMP_DIRECTORY = configuration.conf.get('libero', 'temp_directory') or None

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
    assert article_name and file_name.startswith(
        article_name.group()), error_message
    return article_name.group() + '.xml'


def extract_archived_files_to_bucket(**context):
    zip_file_name = get_file_name_passed_to_dag_run_conf_file(**context)
    article_name = get_expected_elife_article_name(zip_file_name)

    with TemporaryFile(dir=TEMP_DIRECTORY) as temp_zip_file:
        s3 = get_aws_connection('s3')
        s3.download_fileobj(
            Bucket=SOURCE_BUCKET,
            Key=zip_file_name,
            Fileobj=temp_zip_file
        )
        logger.info('ZIPPED FILES= %s', ZipFile(temp_zip_file).namelist())

        folder_name = zip_file_name.replace('.zip', '/')

        # extract zip to cloud bucket
        for zipped_file_path in ZipFile(temp_zip_file).namelist():
            # extract zipped files to disk to avoid using too much memory
            with TemporaryFile(dir=TEMP_DIRECTORY) as temp_unzipped_file:
                temp_unzipped_file.write(ZipFile(temp_zip_file).read(zipped_file_path))
                temp_unzipped_file.seek(0)

                s3_key = folder_name + zipped_file_path
                s3.put_object(
                    Bucket=DESTINATION_BUCKET,
                    Key=s3_key,
                    Body=temp_unzipped_file
                )
                logger.info(
                    '%s uploaded to %s/%s',
                    zipped_file_path,
                    DESTINATION_BUCKET,
                    folder_name
                )

        # check if expected article in zip file
        if not [fn for fn in ZipFile(temp_zip_file).namelist() if article_name in fn]:
            error_message = '%s not in %s: %s' % (article_name, zip_file_name,
                                                  ZipFile(temp_zip_file).namelist())
            raise FileNotFoundError(error_message)

    # pass article cloud bucket key to next task
    return '%s/%s' % (folder_name, article_name)


def convert_tiff_images_in_expanded_bucket_to_jpeg_images(**context):
    zip_file_name = get_file_name_passed_to_dag_run_conf_file(**context)
    prefix = zip_file_name.replace('.zip', '/')

    s3 = get_aws_connection('s3')

    for key in list_bucket_keys_iter(Bucket=DESTINATION_BUCKET, Prefix=prefix):
        if key.endswith('.tif'):
            with TemporaryFile(dir=TEMP_DIRECTORY) as temp_tiff_file:
                s3.download_fileobj(
                    Bucket=DESTINATION_BUCKET,
                    Key=key,
                    Fileobj=temp_tiff_file
                )

                # tiff images are typically RGBA
                # PIL.JpegImagePlugin.RAWMODE contains modes that can be saved as jpeg
                # In order to convert from tiff we have to remove the alpha channel
                temp_jpeg = BytesIO()
                Image.open(temp_tiff_file).convert(mode='RGB').save(temp_jpeg, format='JPEG')

                key = re.sub(r'\.\w+$', '.jpg', key)
                s3.put_object(
                    Bucket=DESTINATION_BUCKET,
                    Key=key,
                    Body=temp_jpeg.getvalue()
                )
                logger.info('%s uploaded to %s',key, DESTINATION_BUCKET)


def update_tiff_references_to_jpeg_in_article(**context):
    zip_file_name = get_file_name_passed_to_dag_run_conf_file(**context)
    article_name = get_expected_elife_article_name(zip_file_name)
    folder_name = zip_file_name.replace('.zip', '/')
    s3_key = folder_name + article_name
    s3 = get_aws_connection('s3')
    response = s3.get_object(Bucket=DESTINATION_BUCKET, Key=s3_key)
    article_bytes = BytesIO(response['Body'].read())
    article_xml = etree.parse(article_bytes)

    # save a copy of the original xml document before making modifications
    key = s3_key.replace('.xml', '-original.xml')
    s3.put_object(Bucket=DESTINATION_BUCKET, Key=key, Body=article_bytes.getvalue())
    logger.info('%s uploaded to %s/%s', key, DESTINATION_BUCKET, folder_name)

    for element in article_xml.xpath(
            '//*[@mimetype="image" and @mime-subtype="tiff"]'):
        href = '{http://www.w3.org/1999/xlink}href'
        element.attrib[href] = re.sub(r'\.\w+$', '.jpg', element.attrib[href])
        element.attrib['mime-subtype'] = 'jpeg'

    # upload modified document
    s3.put_object(
        Bucket=DESTINATION_BUCKET,
        Key=s3_key,
        Body=etree.tostring(article_xml, xml_declaration=True, encoding='UTF-8')
    )
    logger.info('%s uploaded to %s/%s', s3_key, DESTINATION_BUCKET, folder_name)


def wrap_article_in_libero_xml_and_send_to_service(**context):
    zip_file_name = get_file_name_passed_to_dag_run_conf_file(**context)
    article_name = get_expected_elife_article_name(zip_file_name)
    s3_key = zip_file_name.replace('.zip', '/') + article_name
    s3 = get_aws_connection('s3')
    response = s3.get_object(Bucket=DESTINATION_BUCKET, Key=s3_key)
    article_xml = etree.parse(BytesIO(response['Body'].read()))

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
    key = Path(s3_key).parent.stem
    root.set(
        '{%s}base' % XML_NAMESPACE,
        '%s/%s/' % (BASE_URL, key)
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

    # make PUT request to service
    response = requests.put(
        '%s/items/%s/versions/1' % (SERVICE_URL, article_id),
        data=etree.tostring(xml, xml_declaration=True, encoding='UTF-8'),
        headers={'content-type': 'application/xml'}
    )
    response.raise_for_status()
    logger.info('RESPONSE= %s: %s', response.status_code, response.text)


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

wrap_article = python_operator.PythonOperator(
    task_id='wrap_article_in_libero_xml_and_send_to_service',
    provide_context=True,
    python_callable=wrap_article_in_libero_xml_and_send_to_service,
    dag=dag
)

extract_zip_files.set_downstream(convert_tiff_images)
convert_tiff_images.set_downstream(update_tiff_references)
update_tiff_references.set_downstream(wrap_article)
