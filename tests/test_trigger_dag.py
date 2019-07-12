import json

import pytest

from dags.trigger_dag import get_zip_files_to_process, run_dag_for_each_file
from tests.factories import DagRunFactory


@pytest.mark.parametrize('source, destination, expected', [
    (
        {'test.zip'},
        set(),
        {'test.zip'}
    ),
    (
        set(),
        {'test/'},
        set()
    ),
    (
        {'test.zip'},
        {'test/'},
        set()
    ),
    (
        {'test1.zip', 'test2.zip'},
        {'test2/'},
        {'test1.zip'}
    ),
    (
        {'test1.zip', 'test2.zip'},
        {'test1/', 'test2/'},
        set()
    ),
    (
        {'test1.zip', 'test2.xml'},
        set(),
        {'test1.zip'}
    ),
    (
        {'test1.zip', 'test2.xml', 'test3.meca'},
        set(),
        {'test1.zip', 'test3.meca'}
    )
])
def test_identify_zip_files_to_process(mocker, source, destination, expected):
    mocker.patch('dags.trigger_dag.list_bucket_keys_iter',
                 side_effect=[source, destination])
    result = get_zip_files_to_process()
    assert result == expected


@pytest.mark.parametrize('file_names, expected', [
    ({'test.zip'}, 1),
    ({'test1.zip', 'test2.zip', 'test3.zip'}, 3)
])
def test_run_dag_for_each_file(file_names, expected, mocker, context):
    # populate expected return value of previous task
    ti = context['dag_run'].get_task_instances()[0]
    ti.xcom_push(key='return_value', value=file_names)
    trigger = mocker.patch('dags.trigger_dag.trigger_dag')
    run_dag_for_each_file(dag_to_trigger='test_dag_to_trigger', **context)

    assert trigger.call_count ==  expected
    call_args = trigger.call_args[1]
    file_name = json.loads(call_args['conf'])['file']
    assert file_name in file_names
    assert call_args['dag_id'] == 'test_dag_to_trigger'
    assert call_args['run_id'].startswith(file_name)
    assert call_args['execution_date'] is None
    assert call_args['replace_microseconds'] == False


def test_run_dag_for_each_file_does_not_trigger_without_files_to_trigger(mocker, context):
    # populate expected return value of previous task
    ti = context['dag_run'].get_task_instances()[0]
    ti.xcom_push(key='return_value', value=set())
    trigger = mocker.patch('dags.trigger_dag.trigger_dag')
    run_dag_for_each_file(dag_to_trigger='test_dag_to_trigger', **context)
    assert trigger.call_count ==  0


def test_run_dag_for_each_file_does_not_trigger_running_file(mocker, context):
    # simulate running job in db
    DagRunFactory(run_id='test-file1.zip_a1b2', state='running')
    DagRunFactory(run_id='file2.zip_a1b2', state='running')

    # populate expected return value of previous task
    ti = context['dag_run'].get_task_instances()[0]
    ti.xcom_push(key='return_value', value={'file1.zip', 'file2.zip'})
    trigger = mocker.patch('dags.trigger_dag.trigger_dag')

    run_dag_for_each_file(dag_to_trigger='test_dag_to_trigger', **context)
    assert trigger.call_count ==  1
    call_args = trigger.call_args[1]
    assert call_args['dag_id'] == 'test_dag_to_trigger'
    assert call_args['run_id'].startswith('file1.zip')


def test_run_dag_for_each_file_raises_exception(context):
    msg = 'None type passed from previous task. Accepted types are set, list or tuple.'
    with pytest.raises(AssertionError) as error:
        run_dag_for_each_file(None, **context)
    assert str(error.value) == msg
