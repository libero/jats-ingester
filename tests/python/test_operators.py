from airflow.operators.bash_operator import BashOperator

from dags.libero.operators import create_node_task
from tests.python.factories import DAGFactory


def test_create_node_task_returns_bash_operator():
    dag = DAGFactory()

    task = create_node_task('test', '/test/script', dag)

    assert isinstance(task, BashOperator)


def test_create_node_task_get_return_value_updates_bash_command():
    dag = DAGFactory()

    task1 = create_node_task('task1', '/test/script', dag)
    task2 = create_node_task('task2', '/test/script', dag, get_return_from='previous_task')

    assert '{{ ti.xcom_pull(task_ids="previous_task") }}' not in task1.bash_command
    assert '{{ ti.xcom_pull(task_ids="previous_task") }}' in task2.bash_command


def test_create_node_task_env_updates_env_vars_to_be_passed():
    dag = DAGFactory()

    task1 = create_node_task('task1', '/test/script', dag)
    task2 = create_node_task('task2', '/test/script', dag, env={'test': 'value'})

    assert task1.env.get('test') is None
    assert task2.env.get('test') == 'value'
