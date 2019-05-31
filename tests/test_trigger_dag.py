import json

import pytest

from dags.trigger_dag import get_zip_files_to_process, run_dag_for_each_file


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
    )
])
def test_identify_zip_files_to_process(mocker, source, destination, expected):
    mocker.patch('dags.trigger_dag.list_bucket_keys_iter',
                 side_effect=[source, destination])
    result = get_zip_files_to_process()
    assert result == expected


@pytest.mark.parametrize('file_names, expected', [
    (set(), 0),
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
    if trigger.called:
        call_args = trigger.call_args[1]
        file_name = json.loads(call_args['conf'])['file']
        assert file_name in file_names
        assert call_args['dag_id'] == 'test_dag_to_trigger'
        assert call_args['run_id'].startswith(file_name)
        assert call_args['execution_date'] is None
        assert call_args['replace_microseconds'] == False


def test_run_dag_for_each_file_raises_exception(context):
    msg = 'None type passed from previous task. Accepted types are set, list or tuple.'
    with pytest.raises(AssertionError) as error:
        run_dag_for_each_file(None, **context)
        assert str(error.value) == msg
