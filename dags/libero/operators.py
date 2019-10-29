import os

from airflow import configuration, DAG
from airflow.operators.bash_operator import BashOperator

ARTICLE_ASSETS_URL = configuration.conf.get('libero', 'article_assets_url')
COMPLETED_TASKS_BUCKET = configuration.conf.get('libero', 'completed_tasks_bucket_name')
DESTINATION_BUCKET = configuration.conf.get('libero', 'destination_bucket_name')
SEARCH_URL = configuration.conf.get('libero', 'search_url')
SERVICE_NAME = configuration.conf.get('libero', 'service_name')
SERVICE_URL = configuration.conf.get('libero', 'service_url')
SOURCE_BUCKET = configuration.conf.get('libero', 'source_bucket_name')


def create_node_task(name: str,
                     js_task_script_path: str,
                     dag: DAG,
                     env: dict = None,
                     use_function_caller: bool = True,
                     xcom_pull: bool = False,
                     pull_from: str = None) -> BashOperator:

    env_vars = {
        **os.environ.copy(),
        **{'ARCHIVE_FILE_NAME': '{{ getattr(dag_run, "conf", {}).get("file") }}',
           'ARTICLE_ASSETS_URL': ARTICLE_ASSETS_URL,
           'COMPLETED_TASKS_BUCKET': COMPLETED_TASKS_BUCKET,
           'DESTINATION_BUCKET': DESTINATION_BUCKET,
           'SEARCH_URL': SEARCH_URL,
           'SERVICE_NAME': SERVICE_NAME,
           'SERVICE_URL': SERVICE_URL,
           'SOURCE_BUCKET': SOURCE_BUCKET}
    }

    if env:
        env_vars.update(env)

    bash_command_template = 'nodejs'
    if use_function_caller:
        bash_command_template += ' {{ params.js_function_caller }}'
    bash_command_template += ' {{ params.js_task_script }}'

    if xcom_pull and not pull_from:
        bash_command_template += ' {{ ti.xcom_pull() }}'
    elif xcom_pull and pull_from:
        bash_command_template += ' {{ ti.xcom_pull(task_id=%s) }}' % pull_from

    return BashOperator(
        task_id=name,
        bash_command=bash_command_template,
        params={
            'js_function_caller': '${AIRFLOW_HOME}/dags/js/function-caller.js',
            'js_task_script': js_task_script_path
        },
        env=env_vars,
        xcom_push=True,
        dag=dag
    )
