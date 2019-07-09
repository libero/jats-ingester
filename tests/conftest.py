import os
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
def branched_context():
    """
    Generic Airflow context fixture with branched tasks that can be passed to a
    callable that requires context
    """
    with create_session() as session:
        dag = DAGFactory()

        branch_a = PythonOperatorFactory(task_id='branch_a', dag=dag)
        branch_b = PythonOperatorFactory(task_id='branch_b', dag=dag)
        current_task = PythonOperatorFactory(task_id='current_task', dag=dag)
        next_task = PythonOperatorFactory(task_id='next_task', dag=dag)

        branch_a.set_downstream(current_task)
        branch_b.set_downstream(current_task)
        # join
        current_task.set_downstream(next_task)

        dag_run = dag.create_dagrun(
            run_id="manual__",
            start_date=timezone.utcnow(),
            execution_date=timezone.utcnow(),
            state=State.RUNNING,
            conf=None,
            session=session
        )

    ti = None
    for instance in dag_run.get_task_instances():
        if instance.task_id == 'current_task':
            ti = instance
            break

    if ti is None:
        raise ValueError('Unable to find the current task')

    ti.task = current_task
    return ti.get_template_context()


@pytest.fixture
def s3_client(mocker):
    """
    mocks boto client
    """
    return mocker.patch('airflow.hooks.S3_hook.S3Hook.get_conn', new_callable=mocks.s3ClientMock)


@pytest.fixture
def set_remote_logs_env_var():
    """
    setup and teardown intended for tests that require the remote logs airflow
    connection.
    """

    # create airflow connection using environment variable
    # for more info: # https://airflow.apache.org/howto/connection/index.html#creating-a-connection-with-environment-variables
    os.environ['AIRFLOW_CONN_REMOTE_LOGS'] = 'test-uri?host=http://test-host:1234'
    yield
    del os.environ['AIRFLOW_CONN_REMOTE_LOGS']
