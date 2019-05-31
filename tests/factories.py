import factory
import pendulum
from airflow.models import DAG, TaskInstance
from airflow.operators.python_operator import PythonOperator


class DAGFactory(factory.Factory):
    class Meta:
        model = DAG

    dag_id = factory.Sequence(lambda n: 'dag_id_%d' % n)
    start_date = pendulum.datetime(2019, 1, 1)


class PythonOperatorFactory(factory.Factory):
    class Meta:
        model = PythonOperator

    task_id = factory.Sequence(lambda n: 'task_id_%d' % n)
    python_callable = lambda x=None: x
    op_args = None
    op_kwargs = None
    provide_context = True
    templates_dict = None
    templates_exts = None
    dag = factory.SubFactory(DAGFactory)


class TaskInstanceFactory(factory.Factory):
    class Meta:
        model = TaskInstance

    task = factory.SubFactory(PythonOperatorFactory)
    execution_date = pendulum.datetime(2019, 1, 1)
