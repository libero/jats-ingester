

def add_return_value_from_previous_task(return_value, context):
    ti = context['dag_run'].get_task_instances()[0]
    ti.xcom_push(key='return_value', value=return_value)
