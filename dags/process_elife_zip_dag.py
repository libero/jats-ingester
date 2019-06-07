"""
DAG processes a zip file stored in an AWS S3 bucket and prepares the extracted xml
file for Libero content API and sends to the content store via a PUT request.
"""
import logging
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

from aws import get_aws_connection
from task_helpers import get_previous_task_name

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.pdf', '.xml'}

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


def extract_archived_files_to_bucket(**context):
    # get file name passed from trigger
    dag_run = context['dag_run']
    conf = dag_run.conf or {}
    file_name = conf.get('file')
    logger.info('FILE NAME PASSED FROM TRIGGER= %s', file_name)
    message = '%s triggered without a file name passed to conf' % dag_run.dag_id
    assert file_name, message

    # temporary files are securely stored on disk and automatically deleted when closed
    with TemporaryFile() as temp_file:
        s3 = get_aws_connection('s3')
        # store downloaded file in temp file
        s3.download_fileobj(SOURCE_BUCKET, file_name, temp_file)
        logger.info('ZIPPED FILES= %s', ZipFile(temp_file).namelist())

        # only one .xml file allowed
        # TODO: support supplementary xml files
        xml_files = [fn for fn in ZipFile(temp_file).namelist() if fn.endswith('.xml')]
        message = ('only 1 XML file supported. %s XML files found in %s: %s' %
                  (len(xml_files), file_name, xml_files))
        assert len(xml_files) == 1, message

        folder_name = file_name.replace('.zip', '')
        xml_path = None
        for zipped_file_path in ZipFile(temp_file).namelist():
            if Path(zipped_file_path).suffix in ALLOWED_EXTENSIONS:
                s3_key = '%s/%s' % (folder_name, zipped_file_path)
                s3.put_object(
                    Bucket=DESTINATION_BUCKET,
                    Key=s3_key,
                    Body=ZipFile(temp_file).read(zipped_file_path)
                )
                logger.info(
                    '%s uploaded to %s/%s',
                    zipped_file_path,
                    DESTINATION_BUCKET,
                    s3_key
                )
                if zipped_file_path.endswith('.xml'):
                    xml_path = s3_key
        return xml_path


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

    # add jats prefix to jats tags
    for element in article_xml.iter():
        if not element.prefix:
            element.tag = '{http://jats.nlm.nih.gov}%s' % element.tag

    # add xml:base attribute to article element
    key = Path(xml_path).parent.stem
    root = article_xml.getroot()
    root.set(
        '{%s}base' % XML_NAMESPACE,
        '%s/%s' % (BASE_URL, key)
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
