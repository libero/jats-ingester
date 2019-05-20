"""
DAG processes a zip file stored in an AWS S3 bucket and prepares the extracted xml
file for Libero content API and sends to the content store via a PUT request.
"""
import logging
from datetime import timedelta
from io import BytesIO
from tempfile import TemporaryFile
from zipfile import ZipFile

from airflow import DAG, configuration
from airflow.operators import python_operator
from airflow.utils import timezone
from lxml import etree

from aws import get_aws_connection, list_bucket_keys_iter

SOURCE_BUCKET = configuration.conf.get('elife', 'source_bucket')
DESTINATION_BUCKET = configuration.conf.get('elife', 'destination_bucket')

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
    if not file_name:
        raise ValueError('%s triggered without a file name passed to conf' % dag_run.dag_id)

    # temporary files are securely stored on disk and automatically deleted when closed
    with TemporaryFile() as temp_file:
        s3 = get_aws_connection('s3')
        # store downloaded file in temp file
        s3.download_fileobj(SOURCE_BUCKET, file_name, temp_file)
        logger.debug('ZIPPED FILES= %s', ZipFile(temp_file).namelist())

        folder_name = file_name.replace('.zip', '')
        xml_path = None
        for zipped_file_path in ZipFile(temp_file).namelist():
            # skip mac os archive files
            if '__MACOSX' not in zipped_file_path:
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
    previous_task = 'extract_zipped_files_to_bucket'
    xml_path = context['task_instance'].xcom_pull(task_ids=previous_task)
    logger.debug('FILE PASSED= %s', xml_path)
    if xml_path is None:
        raise ValueError('path to xml document was not passed from task %s' % previous_task)

    # temporary files are securely stored on disk and automatically deleted when closed
    with TemporaryFile() as temp_file:
        s3 = get_aws_connection('s3')
        # store downloaded file in temp file
        s3.download_fileobj(DESTINATION_BUCKET, xml_path, temp_file)
        temp_file.seek(0)
        xml = etree.parse(BytesIO(temp_file.read()))
    return etree.tostring(xml)


# schedule_interval is None because DAG is only run when triggered
with DAG('process_zip_dag',
         default_args=default_args,
         schedule_interval=None) as dag:

    task_1 = python_operator.PythonOperator(
        task_id='extract_zipped_files_to_bucket',
        provide_context=True,
        python_callable=extract_zipped_files_to_bucket
    )

    task_2 = python_operator.PythonOperator(
        task_id='prepare_jats_xml_for_libero',
        provide_context=True,
        python_callable=prepare_jats_xml_for_libero
    )

    # run tasks
    task_1 >> task_2
