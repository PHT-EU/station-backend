FROM python:3.8

COPY requirements.txt /home/requirements.txt
RUN pip install -r /home/requirements.txt

COPY . /home/
CMD ["python", "/home/run_station.py"]
