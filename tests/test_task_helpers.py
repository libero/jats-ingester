from dags.task_helpers import (
    get_previous_task_name,
    get_return_value_from_previous_task
)
from tests.factories import TaskInstanceFactory


def test_get_previous_task_name(context):
    result = get_previous_task_name(**context)
    assert result == 'previous_task'


def test_get_previous_task_name_without_previous_task():
    context = TaskInstanceFactory().get_template_context()
    result = get_previous_task_name(**context)
    assert result is None


def test_get_return_value_from_previous_task(context):
    expected = 'previous_return_value'
    context['task_instance'].xcom_pull = lambda **kwargs: expected
    result = get_return_value_from_previous_task(**context)
    assert result == expected


def test_get_return_value_from_previous_task_without_return_value():
    context = TaskInstanceFactory().get_template_context()
    result = get_return_value_from_previous_task(**context)
    assert result is None
