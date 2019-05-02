"""DAG running in response to a AWS S3 bucket change."""
import logging
from datetime import timedelta

import airflow
from airflow.operators import bash_operator, python_operator


default_args = {
    'owner': 'libero',
    'depends_on_past': False,
    'start_date': airflow.utils.dates.days_ago(2),
    'email': ['libero@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(seconds=10)
}

def print_something():
    msg = 'Print something test message'
    print(msg + ' in print')
    return msg + ' in return'


def log_something():
    msg = 'Log something test message'
    logger = logging.getLogger()
    logger.info(msg + ' in log')
    return msg + 'in return'


with airflow.DAG('libero_test_dag',
                 default_args=default_args,
                 # Not scheduled, trigger only
                 schedule_interval=None) as dag:

    bash_this = bash_operator.BashOperator(task_id='bash_this',
                                           bash_command='echo "Hello World!"')

    print_this = python_operator.PythonOperator(task_id='print_this',
                                                python_callable=print_something)

    log_that = python_operator.PythonOperator(task_id='log_that',
                                                python_callable=log_something)

    # run tasks
    bash_this >> print_this >> log_that
