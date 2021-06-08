FROM python:3.8

COPY ../requirements.txt /home/requirements.txt
RUN pip install -r /home/requirements.txt

COPY app /home/app
COPY clients /home/clients
COPY run_station.py /home/run_station.py
COPY .env /home/.env

WORKDIR /home

CMD ["python", "/home/run_station.py"]