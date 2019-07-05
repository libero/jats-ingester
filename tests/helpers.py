

def add_return_value_from_previous_task(return_value, context, task_id=None):
    instances = context['dag_run'].get_task_instances()
    ti = instances[0]  # fallback
    for instance in instances:
        if not task_id:
            break
        elif task_id in instance.task_id:
            ti = instance
            break
    ti.xcom_push(key='return_value', value=return_value)
