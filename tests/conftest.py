import pytest
from airflow.utils import timezone
from airflow.utils.db import create_session
from airflow.utils.state import State
from pytest_socket import disable_socket

from tests.factories import DAGFactory, PythonOperatorFactory


def pytest_runtest_setup():
    disable_socket()


@pytest.fixture
def context():
    """
    Generic Airflow context fixture that can be passed to a callable that
    requires context
    """
    with create_session() as session:
        dag = DAGFactory()

        previous_task = PythonOperatorFactory(task_id='previous_task', dag=dag)
        current_task = PythonOperatorFactory(task_id='current_task', dag=dag)
        next_task = PythonOperatorFactory(task_id='next_task', dag=dag)

        current_task.set_upstream(previous_task)
        current_task.set_downstream(next_task)

        dag_run = dag.create_dagrun(
            run_id="manual__",
            start_date=timezone.utcnow(),
            execution_date=timezone.utcnow(),
            state=State.RUNNING,
            conf=None,
            session=session
        )

    ti = dag_run.get_task_instances()[1]
    ti.task = current_task
    return ti.get_template_context()
