import factory
import pendulum
from airflow.models import DAG, DagRun, TaskInstance
from airflow.operators.python_operator import PythonOperator
from airflow.settings import Session


class DAGFactory(factory.Factory):
    class Meta:
        model = DAG

    dag_id = factory.Sequence(lambda n: 'dag_id_%d' % n)
    start_date = pendulum.datetime(2019, 1, 1)


class DagRunFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = DagRun
        sqlalchemy_session = Session()

    dag_id = factory.Sequence(lambda n: 'dag_id_%d' % n)
    run_id = factory.Sequence(lambda n: 'scheduled_%d' % n)
    start_date = pendulum.datetime(2019, 1, 1)
    state = 'success'
    external_trigger = False


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


class TaskInstanceFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = TaskInstance
        sqlalchemy_session = Session()

    task = factory.SubFactory(PythonOperatorFactory)
    execution_date = pendulum.datetime(2019, 1, 1)
