"""
DAG poll s3 bucket and trigger dag to process new/updated zip files
"""
import json
import logging
import re
from datetime import timedelta
from uuid import uuid4

from airflow import DAG, configuration
from airflow.api.common.experimental.trigger_dag import trigger_dag
from airflow.operators import python_operator
from airflow.utils import timezone

from aws import list_bucket_keys_iter

SCHEDULE_INTERVAL = timedelta(minutes=1)
# formula to start this DAG at server start up.
# More info at https://gtoonstra.github.io/etl-with-airflow/gotchas.html
START_DATE = timezone.utcnow().replace(second=0, microsecond=0) - SCHEDULE_INTERVAL
SOURCE_BUCKET = configuration.conf.get('elife', 'source_bucket')
DESTINATION_BUCKET = configuration.conf.get('elife', 'destination_bucket')

logger = logging.getLogger(__name__)

default_args = {
    'owner': 'libero',
    'depends_on_past': False,
    'start_date': START_DATE,
    'email': ['libero@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(seconds=5)
}


def identify_zip_files_to_process():
    """
    Gets all zip file names from source bucket and all 'directory'
    names of extracted zip files from the destination bucket, stored in separate
    sets. Keys from the destination bucket are given the .zip extension so that
    the two sets can be compared.

    :return: set - a set of zip file names from the source bucket that are not
    in the destination.
    """
    incoming = {key for key in list_bucket_keys_iter(Bucket=SOURCE_BUCKET, Delimiter='.zip')}
    expanded = {re.sub(r'/?$', '.zip', key) for key in
                list_bucket_keys_iter(Bucket=DESTINATION_BUCKET, Delimiter='/')}
    return incoming.difference(expanded)


def run_dag_for_each_file(**context):
    file_names = context['task_instance'].xcom_pull(task_ids='identify_zip_files_to_process')
    dag_to_trigger = 'process_zip_dag'
    for file_name in file_names:
        trigger_dag(dag_id=dag_to_trigger,
                    run_id='{}_{}'.format(file_name, uuid4()),
                    conf=json.dumps({'file': file_name}),
                    execution_date=None,
                    replace_microseconds=False)
    logger.debug('triggered %s for %s files: %s' % (dag_to_trigger, len(file_names), file_names))


with DAG('trigger_process_zip_dag',
         default_args=default_args,
         schedule_interval=SCHEDULE_INTERVAL) as dag:

    task_1 = python_operator.PythonOperator(
        task_id='identify_zip_files_to_process',
        python_callable=identify_zip_files_to_process
    )

    task_2 = python_operator.PythonOperator(
        task_id='run_dag_for_each_file',
        provide_context=True,
        python_callable=run_dag_for_each_file
    )

    # run tasks
    task_1 >> task_2
