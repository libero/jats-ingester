

def populate_task_return_value(return_value, context, task_id=None):
    """
    Helper function for testing. Populates first task instance in list by
    default (typically the previous task). Use task_id for deterministic results
    """
    instances = context['dag_run'].get_task_instances()
    ti = instances[0]  # fallback
    for instance in instances:
        if not task_id:
            break
        elif task_id in instance.task_id:
            ti = instance
            break
    ti.xcom_push(key='return_value', value=return_value)
