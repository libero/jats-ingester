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
                     get_return_from: str = None) -> BashOperator:
    """
    A facade for the BashOperator intended for non python developers.
    :param name: name of task
    :param js_task_script_path: full path of script to run as string
    :param dag: reference to the DAG object this task belongs to
    :param env: values to pass to nodejs accessed using process.env
    :param get_return_from: gets the return value of a specified task
    :return: instantiated BashOperator configured to run a nodejs script
    """

    env_vars = {
        **os.environ.copy(),
        **{'ARCHIVE_FILE_NAME': '{{ dag_run.conf.get("file") }}',
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

    bash_command_template = 'nodejs {{ params.js_function_caller }} {{ params.js_task_script }}'

    if get_return_from:
        bash_command_template += ' {{ ti.xcom_pull(task_ids="%s") }}' % get_return_from

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
