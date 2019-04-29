FROM python:3.7.3-slim as base

# change /src/app to /airflow
ENV AIRFLOW_HOME=/airflow
ENV AIRFLOW__CORE__DAGS_FOLDER=${AIRFLOW_HOME}/dags
ENV AIRFLOW__CORE__BASE_LOG_FOLDER=${AIRFLOW_HOME}/logs
ENV AIRFLOW__CORE__PLUGINS_FOLDER=${AIRFLOW_HOME}/plugins
ENV AIRFLOW__CORE__CHILD_PROCESS_LOG_DIRECTORY=${AIRFLOW_HOME}/logs/scheduler

ENV AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql+psycopg2://postgres:example@db/airflow-db
ENV AIRFLOW__CORE__LOAD_EXAMPLES=false

WORKDIR ${AIRFLOW_HOME}

COPY ./requirements ./requirements

RUN pip install -U pip \
    && set -ex \
    && apt-get update -yq \
    && apt-get install -yq --no-install-recommends build-essential \
    && pip install --no-cache-dir -r ./requirements/base.txt \
    && apt-get remove --purge --autoremove -yq build-essential \
    && rm -rf ~/.cache/* \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/*

FROM base as dev

ENV PYTHONUNBUFFERED=true
ENV PYTHONDONTWRITEBYTECODE=true

RUN pip install --no-cache-dir -r ./requirements/dev.txt \
    && rm -rf ~/.cache/* \
    && rm -rf /tmp/*

ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.5.0/wait /wait
RUN chmod +x /wait

EXPOSE 8080

CMD /wait && airflow initdb && airflow webserver -p 8080 && airflow scheduler
