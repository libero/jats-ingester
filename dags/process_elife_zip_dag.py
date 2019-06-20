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

from aws import get_aws_connection
from task_helpers import get_previous_task_name

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.pdf', '.xml'}  # only upload these file types
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tif', '.tiff'}

BASE_URL = configuration.conf.get('libero', 'base_url')
SOURCE_BUCKET = configuration.conf.get('libero', 'source_bucket')
DESTINATION_BUCKET = configuration.conf.get('libero', 'destination_bucket')
SERVICE_NAME = configuration.conf.get('libero', 'service_name')
SERVICE_URL = configuration.conf.get('libero', 'service_url')

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


def is_allowed(file_name: str) -> bool:
    return Path(file_name).suffix in ALLOWED_EXTENSIONS


def is_image(file_name: str) -> bool:
    return Path(file_name).suffix in IMAGE_EXTENSIONS


def extract_archived_files_to_bucket(**context):
    # get file name passed from trigger
    dag_run = context['dag_run']
    conf = dag_run.conf or {}
    zip_file_name = conf.get('file')
    logger.info('FILE NAME PASSED FROM TRIGGER= %s', zip_file_name)
    message = '%s triggered without a file name passed to conf' % dag_run.dag_id
    assert zip_file_name, message

    # get/validate article name
    pattern = r'^\w+-\w+'
    article_name = re.search(pattern, zip_file_name)
    error_message = ('%s is malformed. Expected archive name to start with '
                     'any number/character, hyphen, any number/character (%s)'
                     'example: name-id.extension' % (zip_file_name, pattern))
    assert article_name and zip_file_name.startswith(article_name.group()), error_message
    article_name = article_name.group() + '.xml'

    # temporary files are securely stored on disk and automatically deleted when closed
    with TemporaryFile() as temp_file:
        s3 = get_aws_connection('s3')
        # store downloaded file in temp file
        s3.download_fileobj(SOURCE_BUCKET, zip_file_name, temp_file)
        logger.info('ZIPPED FILES= %s', ZipFile(temp_file).namelist())

        # extract zip to cloud bucket
        folder_name = zip_file_name.rstrip('.zip')
        file_to_upload = None

        for zipped_file_path in ZipFile(temp_file).namelist():

            if is_image(zipped_file_path) and not is_allowed(zipped_file_path):
                # convert image to jpeg
                file_to_upload = BytesIO()
                image = Image.open(BytesIO(ZipFile(temp_file).read(zipped_file_path)))
                try:
                    image.save(file_to_upload, 'JPEG')
                except IOError:
                    image = image.convert('RGB')
                    image.save(file_to_upload, 'JPEG')
                file_to_upload = file_to_upload.getvalue()
                zipped_file_path = re.sub(r'\.\w+$', '.jpg', zipped_file_path)

            if is_allowed(zipped_file_path):
                s3_key = '%s/%s' % (folder_name, zipped_file_path)
                if not file_to_upload:
                    file_to_upload = ZipFile(temp_file).read(zipped_file_path)
                s3.put_object(
                    Bucket=DESTINATION_BUCKET,
                    Key=s3_key,
                    Body=file_to_upload
                )
                logger.info(
                    '%s uploaded to %s/%s',
                    zipped_file_path,
                    DESTINATION_BUCKET,
                    folder_name
                )

        # check if expected article in zip file
        matches = [fn for fn in ZipFile(temp_file).namelist() if article_name in fn]
        if not matches:
            error_message = '%s not in %s: %s' % (article_name, zip_file_name,
                                                  ZipFile(temp_file).namelist())
            raise FileNotFoundError(error_message)

    # pass article cloud bucket key to next task
    return '%s/%s' % (folder_name, article_name)


def wrap_article_in_libero_xml_and_send_to_service(**context):
    # get xml path passed from previous task
    previous_task = get_previous_task_name(**context)
    xml_path = context['task_instance'].xcom_pull(task_ids=previous_task)
    logger.info('XML PATH PASSED FROM PREVIOUS TASK= %s', xml_path)
    message = 'path to xml document was not passed from task %s' % previous_task
    assert xml_path is not None, message

    s3 = get_aws_connection('s3')
    response = s3.get_object(Bucket=DESTINATION_BUCKET, Key=xml_path)
    article_xml = etree.parse(BytesIO(response['Body'].read()))

    # get article id
    article_id = article_xml.xpath(
        '/article/front/article-meta/article-id[@pub-id-type="publisher-id"]'
    )[0].text

    # update image references to .jpg
    root = article_xml.getroot()
    for element in root.xpath('//*[@mimetype="image" and @mime-subtype!="jpeg"]'):
        href = '{http://www.w3.org/1999/xlink}href'
        element.attrib[href] = re.sub(r'\.\w+$', '.jpg', element.attrib[href])
        element.attrib['mime-subtype'] = 'jpeg'

    # add jats prefix to jats tags
    for element in article_xml.iter():
        if not element.prefix:
            element.tag = '{http://jats.nlm.nih.gov}%s' % element.tag

    # add xml:base attribute to article element
    key = Path(xml_path).parent.stem
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

task_1 = python_operator.PythonOperator(
    task_id='extract_archived_files_to_bucket',
    provide_context=True,
    python_callable=extract_archived_files_to_bucket,
    dag=dag
)

task_2 = python_operator.PythonOperator(
    task_id='wrap_article_in_libero_xml_and_send_to_service',
    provide_context=True,
    python_callable=wrap_article_in_libero_xml_and_send_to_service,
    dag=dag
)

task_1.set_downstream(task_2)
