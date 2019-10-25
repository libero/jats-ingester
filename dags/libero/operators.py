import os

from airflow import configuration, DAG
from airflow.operators.bash_operator import BashOperator

ARTICLE_ASSETS_URL = configuration.conf.get('libero', 'article_assets_url')
COMPLETED_TASKS_BUCKET = configuration.conf.get('libero', 'completed_tasks_bucket_name')
DESTINATION_BUCKET = configuration.conf.get('libero', 'destination_bucket_name')
SERVICE_NAME = configuration.conf.get('libero', 'service_name')
SOURCE_BUCKET = configuration.conf.get('libero', 'source_bucket_name')


def create_node_task(name: str,
                     js_task_script_path: str,
                     dag: DAG,
                     xcom_pull: bool = False) -> BashOperator:

    bash_command_template = 'nodejs {{ params.js_function_caller}} {{ params.js_task_script }}'
    if xcom_pull:
        bash_command_template += ' {{ ti.xcom_pull() }}'

    return BashOperator(
        task_id=name,
        bash_command=bash_command_template,
        params={
            'js_function_caller': '${AIRFLOW_HOME}/dags/js/function-caller.js',
            'js_task_script': js_task_script_path
        },
        env={
            **os.environ.copy(),
            **{'ARCHIVE_FILE_NAME': '{{ dag_run.conf["file"] }}',
               'ARTICLE_ASSETS_URL': ARTICLE_ASSETS_URL,
               'COMPLETED_TASKS_BUCKET': COMPLETED_TASKS_BUCKET,
               'DESTINATION_BUCKET': DESTINATION_BUCKET,
               'SERVICE_NAME': SERVICE_NAME,
               'SOURCE_BUCKET': SOURCE_BUCKET}
        },
        xcom_push=True,
        dag=dag
    )
