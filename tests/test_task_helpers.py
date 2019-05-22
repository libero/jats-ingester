import pytest

from dags.task_helpers import (
    get_previous_task_name,
    get_return_value_from_previous_task
)
from tests.factories import TaskInstanceFactory


@pytest.mark.parametrize('has_prev_task, expected', [
    (True, 'previous_task'),
    (False, None)
])
def test_get_previous_task_name(has_prev_task, expected, context):
    if not has_prev_task:
        context = TaskInstanceFactory().get_template_context()

    result = get_previous_task_name(**context)
    assert result == expected


@pytest.mark.parametrize('has_prev_task, expected', [
    (True, 'previous_return_value'),
    (False, None)
])
def test_get_return_value_from_previous_task(has_prev_task, expected, context):
    if not has_prev_task:
        context = TaskInstanceFactory().get_template_context()
    else:
        context['task_instance'].xcom_pull = lambda **kwargs: expected

    result = get_return_value_from_previous_task(**context)
    assert result == expected