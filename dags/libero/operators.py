import os

from airflow import configuration, DAG
from airflow.operators.bash_operator import BashOperator


COMPLETED_TASKS_BUCKET = configuration.conf.get('libero', 'completed_tasks_bucket_name')


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
            **{'COMPLETED_TASKS_BUCKET': COMPLETED_TASKS_BUCKET}
        },
        xcom_push=True,
        dag=dag
    )
