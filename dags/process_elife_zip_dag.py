"""
DAG processes a zip file stored in an AWS S3 bucket and prepares the extracted xml
file for Libero content API and sends to the content store via a PUT request.
"""
import logging
from datetime import timedelta
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryFile
from zipfile import ZipFile

from airflow import DAG, configuration
from airflow.operators import python_operator
from airflow.utils import timezone
from lxml import etree

from aws import get_aws_connection, list_bucket_keys_iter
from task_helpers import get_previous_task_name

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.pdf', '.xml'}

SOURCE_BUCKET = configuration.conf.get('libero', 'source_bucket')
DESTINATION_BUCKET = configuration.conf.get('libero', 'destination_bucket')

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


def extract_zipped_files_to_bucket(**context):
    # get file name passed from trigger
    dag_run = context['dag_run']
    conf = dag_run.conf or {}
    file_name = conf.get('file')
    logger.debug('FILE PASSED= %s', file_name)
    message = '%s triggered without a file name passed to conf' % dag_run.dag_id
    assert file_name, message

    # temporary files are securely stored on disk and automatically deleted when closed
    with TemporaryFile() as temp_file:
        s3 = get_aws_connection('s3')
        # store downloaded file in temp file
        s3.download_fileobj(SOURCE_BUCKET, file_name, temp_file)
        logger.debug('ZIPPED FILES= %s', ZipFile(temp_file).namelist())

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
                with TemporaryFile() as inner_temp_file:
                    # store zipped file in temp file
                    inner_temp_file.write(ZipFile(temp_file).read(zipped_file_path))
                    inner_temp_file.seek(0)
                    s3_key = '%s/%s' % (folder_name, zipped_file_path)
                    # upload stored zipped file preserving zip file structure
                    s3.upload_fileobj(inner_temp_file, DESTINATION_BUCKET, s3_key)
                    logger.info(
                        '%s uploaded to %s/%s', zipped_file_path, DESTINATION_BUCKET, s3_key
                    )
                    if zipped_file_path.endswith('.xml'):
                        xml_path = s3_key
        return xml_path


def prepare_jats_xml_for_libero(**context):
    # get xml path passed from previous task
    previous_task = get_previous_task_name(**context)
    xml_path = context['task_instance'].xcom_pull(task_ids=previous_task)
    logger.debug('FILE PASSED= %s', xml_path)
    message = 'path to xml document was not passed from task %s' % previous_task
    assert xml_path is not None, message

    # temporary files are securely stored on disk and automatically deleted when closed
    with TemporaryFile() as temp_file:
        s3 = get_aws_connection('s3')
        # store downloaded file in temp file
        s3.download_fileobj(DESTINATION_BUCKET, xml_path, temp_file)
        temp_file.seek(0)
        xml = etree.parse(BytesIO(temp_file.read()))
    return etree.tostring(xml)


# schedule_interval is None because DAG is only run when triggered
dag = DAG('process_elife_zip_dag',
          default_args=default_args,
          schedule_interval=None)

task_1 = python_operator.PythonOperator(
    task_id='extract_zipped_files_to_bucket',
    provide_context=True,
    python_callable=extract_zipped_files_to_bucket,
    dag=dag
)

task_2 = python_operator.PythonOperator(
    task_id='prepare_jats_xml_for_libero',
    provide_context=True,
    python_callable=prepare_jats_xml_for_libero,
    dag=dag
)

task_1.set_downstream(task_2)
