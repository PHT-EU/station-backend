FROM python:3.6

WORKDIR /

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir /opt/pht_results
COPY . .
ENV FHIR_SERVER=''
ENV FHIR_PORT=''
ENV FHIR_TOKEN=''
#LABEL envs="[{\"name\":\"FHIR_SERVER\",\"type\":\"string\",\"required\":true},{\"name\":\"FHIR_PORT\",\"type\":\"string\",\"required\":true},{\"name\":\"FHIR_TOKEN\",\"type\":\"string\",\"required\":true}]"

CMD [ "python", "./mukoWithPython.py" ]a