FROM python:3.8

EXPOSE 8080 5555 8793

RUN apt-get update -yqq \
    && apt-get dist-upgrade -yqq \
    && apt-get install -yqq --no-install-recommends --no-install-suggests \
        git \
        libffi-dev \
        libpq-dev \
        build-essential \
        apt-utils \
        netcat \
        locales

#RUN AIRFLOW_VERSION=2.1.3 && PYTHON_VERSION="$(python --version | cut -d " " -f 2 | cut -d "." -f 1-2)" && \
#    CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt" && \
#    pip install "apache-airflow[async,postgres,celery, password, redis]==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"

COPY requirements.txt /tmp/requirements.txt


RUN pip install -r /tmp/requirements.txt
RUN pip install git+https://github.com/PHT-Medic/train-container-library.git

# Install container diff library
RUN curl -LO https://storage.googleapis.com/container-diff/latest/container-diff-linux-amd64 && \
    install container-diff-linux-amd64 /usr/local/bin/container-diff

COPY ./station /opt/station/station
COPY ./station_worker /opt/station/station_worker
COPY ./setup.py /opt/station/setup.py
RUN pip install /opt/station


COPY ./airflow/ /root/airflow/
RUN chmod +x /root/airflow/entrypoint.sh
ENTRYPOINT ["/root/airflow/entrypoint.sh"]
CMD ["webserver"]

