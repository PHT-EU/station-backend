FROM python:3.8

COPY requirements.txt /home/requirements.txt
RUN pip install -r /home/requirements.txt

COPY station/app /home/app
COPY station/clients /home/clients
COPY station/run_station.py /home/run_station.py
COPY station/.env /home/.env
COPY setup_scripts/wait-for-it.sh /home/wait-for-it.sh

WORKDIR /home

CMD ["python", "/home/run_station.py"]