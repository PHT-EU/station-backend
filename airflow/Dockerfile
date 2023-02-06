FROM bitnami/python:3.10
MAINTAINER michael.graf@uni-tuebingen.de

# update the image
RUN apt -y update && apt-get -y install software-properties-common && \
    apt-get upgrade -yqq && \
    apt-get install -yqq --no-install-recommends --no-install-suggests \
        libffi-dev \
        libpq-dev \
        build-essential \
        apt-utils \
        locales \
        curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /var/cache/apt/archives/*

# install python



# set poetry environment variables
ENV POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_VIRTUALENVS_IN_PROJECT=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_VERSION=1.3.2


RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="$PATH:$POETRY_HOME/bin"

COPY . /opt/station
WORKDIR /opt/station
RUN poetry install

# install airflow
RUN pip install "apache-airflow[celery,crypto,hashicorp,password,postgres,redis]==2.4.3" --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.4.3/constraints-3.10.txt"

RUN mkdir /opt/train_data
COPY ./airflow/requirements.txt /tmp/requirements.txt


RUN pip install -r /tmp/requirements.txt && \
    pip install git+https://github.com/PHT-Medic/train-container-library.git


COPY ./airflow/ /root/airflow/
RUN chmod +x /root/airflow/entrypoint.sh
ENTRYPOINT ["/root/airflow/entrypoint.sh"]
CMD ["webserver"]

