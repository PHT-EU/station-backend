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

COPY requirements.txt /tmp/requirements.txt


RUN pip install -r /tmp/requirements.txt
RUN pip install git+https://gitlab.com/PersonalHealthTrain/implementations/germanmii/difuture/train-container-library.git
# RUN pip install git+https://gitlab.com/PersonalHealthTrain/implementations/germanmii/difuture/incubating/pht-federated.git

COPY ./station /opt/station/station
COPY ./worker /opt/station/worker
COPY ./setup.py /opt/station/setup.py
RUN pip install /opt/station

COPY ./airflow/airflow.cfg /root/airflow/airflow.cfg
#COPY ./dags /root/airflow/dags
COPY ./airflow/entrypoint.sh /root/entrypoint.sh
RUN chmod +x /root/entrypoint.sh
ENTRYPOINT ["/root/entrypoint.sh"]
CMD ["webserver"]

