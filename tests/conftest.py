import socket

import pytest
from airflow.utils import timezone
from airflow.utils.db import create_session
from airflow.utils.state import State
from pytest_socket import disable_socket, SocketBlockedError

from tests import mocks
from tests.factories import DAGFactory, PythonOperatorFactory


def pytest_runtest_setup():
    """
    This test suite uses pytest-socket which causes tests to fail immediately if
    a call to socket.socket is made, or in other words, tries to access the
    internet. However, the boto library tries to resolve addresses by calling
    socket.getaddrinfo which will make blocking network calls but is not covered
    by pytest-socket.

    This test setup will cause tests to fail immediately if socket.getaddrinfo
    is called.
    """

    def block_lookup(*args, **kwargs):
        raise SocketBlockedError

    disable_socket()
    socket.getaddrinfo = block_lookup


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


@pytest.fixture
def s3_client(mocker):
    """
    mocks boto client
    """
    return mocker.patch('boto3.client', new_callable=mocks.s3ClientMock)
