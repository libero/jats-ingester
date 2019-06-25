import pytest

from dags.task_helpers import (
    get_previous_task_name,
    get_return_value_from_previous_task,
    get_file_name_passed_to_dag_run_conf_file
)
from tests.factories import TaskInstanceFactory


def test_get_previous_task_name(context):
    result = get_previous_task_name(context)
    assert result == 'previous_task'


def test_get_previous_task_name_without_previous_task():
    context = TaskInstanceFactory().get_template_context()
    result = get_previous_task_name(context)
    assert result is None


def test_get_return_value_from_previous_task(context):
    expected = 'previous_return_value'
    context['task_instance'].xcom_pull = lambda **kwargs: expected
    result = get_return_value_from_previous_task(context)
    assert result == expected


def test_get_return_value_from_previous_task_without_return_value():
    context = TaskInstanceFactory().get_template_context()
    result = get_return_value_from_previous_task(context)
    assert result is None


def test_get_file_name_passed_to_dag_run_conf_file(context):
    file_name = 'elife-00666-vor-r1.zip'
    context['dag_run'].conf = {'file': file_name}
    result = get_file_name_passed_to_dag_run_conf_file(context)
    assert result == file_name


def test_get_file_name_passed_to_dag_run_conf_file_raises_exception_if_file_name_not_passed(context):
    error_message = 'conf={\'file\': <file_name>} not passed to %s' % context['dag_run'].dag_id
    with pytest.raises(AssertionError) as error:
        get_file_name_passed_to_dag_run_conf_file(context)
    assert str(error.value) == error_message
