# Libero JATS Ingester

This project is an implementation of Libero JATS Ingester.

Contents:
 - [Development](#development)
    - [Dependencies](#dependencies)
    - [Before getting started](#before-getting-started)
    - [Getting started](#getting-started)
    - [Running tests](#running-tests)
 - [Documentation](#documentation)
    - [Architecture](#architecture)
    - [DAGs](#dags)
    - [Configuration](#configuration)
    - [Tests](#tests)
    - [Test utilities](#test-utilities)
    - [Testing caveat](#testing-caveat)
    - [Maintenance](#maintenance)
 - [Getting help](#getting-help)

## Development

### Dependencies

* [Docker](https://www.docker.com/)
* [Git LFS](https://git-lfs.github.com/)

### Before getting started
In order to use asset files (zip files, xml files, etc), for testing or to run
the project locally, make sure you have [Git LFS](https://git-lfs.github.com/) 
installed as the `tests/assets/` will not only contain a representation of files
rather than the actual files. [Git LFS](https://git-lfs.github.com/) will take
care of downloading/uploading large files.

### Getting started
This project provides a `Makefile` with short commands to run common tasks.
Typically, MacOS and most Linux distributions come with [gnu make](https://www.gnu.org/software/make/)
installed. If you are unable to run the commands below because your system doesn't 
have `gnu make` installed, you can try to install it or copy and paste commands
found in the `Makefile` into your command line interface.

* `make start` builds and/or runs the site locally configured for development purposes.
* `make stop` stops containers and cleans up any anonymous volumes.

Once services are running, you can view what's happening in services that expose
a web interface by navigating to the following in your web browser:
 
Airflow
 - `http://localhost:8080`
 
AWS S3
 - `http://localhost:9000`
 - username: `longkey`
 - password: `verysecretkey`
 
### Running tests

* `make tests` runs unit tests.

## Documentation

### Architecture

This project uses [Apache Airflow](https://airflow.apache.org/) and has been
implemented according to the official documentation. Please refer
to the official documentation for detailed information about Apache Airflow.

In short, Apache Airflow is comprised of six main components: a web server, 
a scheduler, workers, a message broker, DAGs and a database.

The **Web Server** provides the interface to Apache Airflow at run time. This 
can done using either the [web interface](https://airflow.apache.org/ui.html) 
or [HTTP endpoints](https://airflow.apache.org/api.html).

The [Scheduler](https://airflow.apache.org/scheduler.html) is the coordinator of
tasks.

The [Workers](https://docs.celeryproject.org/en/latest/userguide/workers.html) 
are processes available to perform tasks queued by the scheduler. 

The **Message Broker** is the mechanism used for communication between the 
scheduler and the workers.

A [DAG](https://airflow.apache.org/concepts.html#dags) is a python file with a
series of functions or classes in the form of 
[Operators](https://airflow.apache.org/concepts.html#operators) 
that represent tasks. Each task is then executed according to the 
[DAG composition](https://airflow.apache.org/concepts.html#bitshift-composition).

![Simple Apache Airflow Architectural Diagram](https://miro.medium.com/max/1140/1*u6duhZD2J_i1zZ0Txq26Cg.png)

### DAGs
Airflow inspects the `dags/` folder for files that instantiate the DAG class.
Airflow expects to find this directory in the `AIRFLOW_HOME` directory.

### Configuration
Configuration files can be found in the `config/` directory. Airflow expects to 
find a file with the name `airflow.cfg` in the `AIRFLOW_HOME` directory. Libero
specific have been added under the heading of `[libero]`. These can then be read
using the following:
```python
from airflow import configuration

SEARCH_URL = configuration.conf.get('libero', 'search_url')
```

Apache Airflow uses the [boto library](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
to interface with AWS services using their AWSHook. Refer to the [boto library
documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html#configuration) 
regarding configuration relating to connecting to AWS services.

### Tests
Tests are run using [pytest](https://pytest.org/en/latest/). Test files are 
located in the `tests/` directory. Files needed for testing, such as archives and 
xml files, are placed in the `tests/assets/` directory. Before tests are run an
sqlite database is used and initialized as some operations require database
access.
 
Some operators such as the `PythonOperator` expect a callable to be parsed to 
the operator. In most scenarios, it's likely that a callable will want a `context`
object which is passed to the callable at run time. This is a python dictionary
with a lot of run time information. Adding the `context` argument to the test
function definition will make this available which can be passed to the callable
in the current test. There is also a `branched_context` fixture for testing
callables that proceed a joining of DAG branches.


### Test utilities
In the `tests/assets/` directory, the `__init__.py` file has a couple of utility functions; 
`get_asset` which returns a python [pathlib.Path](https://docs.python.org/3/library/pathlib.html) object.
This can be used to get information about the file such as its absolute path, 
extension, parent directory or even read the file bytes. `find_asset` returns a 
list of `pathlib.Path` objects that match the search query. You can reference 
these functions using the following:
```python
from tests.assets import find_asset, get_asset
```

Some tasks expect to work with the return value of the previous task.
In `tests/helpers.py` the function `populate_task_return_value` provides a 
quick way to populate the return value of the previous task during test setup like
so:
```python
from tests.helpers import populate_task_return_value

populate_task_return_value(return_value=article_xml, context=context)
```

In the case of joining branches, the `task_id` of the previous task can be 
specified to state which previous task to populate:
```python
populate_task_return_value(
    return_value=article_xml,
    context=branched_context,
    task_id='branch_a'
)
```

Some tasks use the [boto python SDK](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) to interact with AWS services such as S3. In `tests/mocks.py`
There is a custom test client used to mock the boto client methods. To use this
in tests or to stop requests being made to AWS add `s3_client` argument to the 
test definition. The following attributes have been added to help with testing:
`downloaded_files`, `uploaded_files` and `last_uploaded_file_bytes`.

### Testing caveat
One thing to be mindful of when writing tests for Apache Airflow is where files 
are located relative the working directory of the python interpreter. 

For example, when importing modules in a python file with a DAG, you 
should reference those modules relative to the DAG file rather than the 
root of the project. But, when testing, modules should be imported 
relative to the root of the project.

e.g. assuming the following directory structure:
- dags/
    - helpers.py
    - my_dag.py
- tests/
    - test_my_dag.py

You would then import modules like so:
```python
# my_dag.py

import helpers
```
```python
# test_my_dag.py

import dags.helpers
```

### Maintenance
Unfortunately there is some maintenance required when running Airflow.
[Maintenance DAGs](https://github.com/libero/airflow-maintenance-dags) have been 
created and are added to the docker image during the docker image build. More 
information can be found in the maintenance DAGs repository.


## Getting help

- Report a bug or request a feature on [GitHub](https://github.com/libero/libero/issues/new/choose).
- Ask a question on the [Libero Community Slack](https://libero.pub/join-slack).
- Read the [code of conduct](https://libero.pub/code-of-conduct).