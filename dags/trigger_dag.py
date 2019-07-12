"""
DAG identify zip files to process from s3 bucket and trigger dag for each zip file
"""
import json
import logging
import re
from datetime import timedelta
from uuid import uuid4

from airflow import DAG, configuration
from airflow.api.common.experimental.trigger_dag import trigger_dag
from airflow.models import DagRun
from airflow.operators import python_operator
from airflow.settings import Session
from airflow.utils import timezone

import process_zip_dag
from aws import list_bucket_keys_iter
from sqlalchemy import and_
from task_helpers import get_return_value_from_previous_task

SCHEDULE_INTERVAL = timedelta(minutes=1)
# formula to start this DAG at server start up.
# More info at https://gtoonstra.github.io/etl-with-airflow/gotchas.html
START_DATE = timezone.utcnow().replace(second=0, microsecond=0) - SCHEDULE_INTERVAL
SOURCE_BUCKET = configuration.conf.get('libero', 'source_bucket_name')
DESTINATION_BUCKET = configuration.conf.get('libero', 'destination_bucket_name')

SUPPORTED_ARCHIVE_FORMATS = {'.zip', '.meca'}

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


def get_zip_files_to_process() -> set:
    """
    Compares the source and destination buckets and returns a set of file names
    to process.
    """
    incoming = {re.sub(r'\.\w+', '', key): key
                for key in list_bucket_keys_iter(Bucket=SOURCE_BUCKET)
                if any(key.endswith(ext) for ext in SUPPORTED_ARCHIVE_FORMATS)}

    expanded = {re.sub(r'/$', '', key)
                for key in
                list_bucket_keys_iter(Bucket=DESTINATION_BUCKET, Delimiter='/')}

    keys = set(incoming.keys()).difference(expanded)
    return {incoming[key] for key in keys}


def run_dag_for_each_file(dag_to_trigger, **context) -> None:
    file_names = get_return_value_from_previous_task(context)
    message = 'None type passed from previous task. Accepted types are set, list or tuple.'
    assert file_names is not None, message

    session = Session()
    files_triggered = []
    for file_name in file_names:

        # check if a file has already been triggered for processing
        if session.query(DagRun).filter(and_(DagRun.run_id.startswith(file_name + '_'),
                                             DagRun.state == 'running')).first():
            continue

        trigger_dag(dag_id=dag_to_trigger,
                    run_id='{}_{}'.format(file_name, uuid4()),
                    conf=json.dumps({'file': file_name}),
                    execution_date=None,
                    replace_microseconds=False)

        files_triggered.append(file_name)

    logger.info('triggered %s for %s files: %s' % (dag_to_trigger, len(files_triggered), files_triggered))


dag = DAG('trigger_process_zip_dag',
          default_args=default_args,
          schedule_interval=SCHEDULE_INTERVAL)

task_1 = python_operator.PythonOperator(
    task_id='get_zip_files_to_process',
    python_callable=get_zip_files_to_process,
    dag=dag
)

task_2 = python_operator.PythonOperator(
    task_id='run_dag_for_each_file',
    provide_context=True,
    python_callable=run_dag_for_each_file,
    op_args=[process_zip_dag.dag.dag_id],
    dag=dag
)

task_1.set_downstream(task_2)
