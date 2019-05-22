

def get_previous_task_name(**context):
    if context['task'].upstream_list:
        return context['task'].upstream_list[0].task_id
    return None


def get_return_value_from_previous_task(**context):
    previous_task = get_previous_task_name(**context)
    return context['task_instance'].xcom_pull(task_ids=previous_task)
