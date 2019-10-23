from airflow.operators.bash_operator import BashOperator

from dags.libero.operators import create_node_task
from tests.python.factories import DAGFactory


def test_create_node_task_returns_bash_operator():
    dag = DAGFactory()

    task = create_node_task('test', '/test/script', dag)

    assert isinstance(task, BashOperator)


def test_create_node_task_xcom_pull_updates_bash_command():
    dag = DAGFactory()

    task1 = create_node_task('task1', '/test/script', dag)
    task2 = create_node_task('task2', '/test/script', dag, xcom_pull=True)

    assert '{{ ti.xcom_pull() }}' not in task1.bash_command
    assert '{{ ti.xcom_pull() }}' in task2.bash_command
