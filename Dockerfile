FROM python:3.9
MAINTAINER michael.graf@uni-tuebingen.de
# update python version and replace python with python 3
#RUN apt -y update && apt-get -y install software-properties-common && \
#    add-apt-repository ppa:deadsnakes/ppa && apt -y update && apt -y install git && \
#    apt-get install -y python3.9 && apt install python-is-python3 && apt install -y python3-pip && \
#    rm -rf /var/lib/apt/lists && \
RUN pip install pipenv


COPY setup_scripts/wait-for-it.sh /wait-for-it.sh
# Install the station package
COPY . /home
WORKDIR /home
RUN pipenv install --system --deploy --ignore-pipfile
RUN pip install git+https://github.com/PHT-Medic/train-container-library.git
RUN pip install git+https://github.com/migraf/fhir-kindling.git
RUN pip install /home

WORKDIR /

CMD ["python", "/home/station/run_station.py"]


