[![Build](https://github.com/PHT-EU/station-backend/actions/workflows/Build.yml/badge.svg)](https://github.com/PHT-EU/station-backend/actions/workflows/Build.yml)
[![Tests](https://github.com/PHT-EU/station-backend/actions/workflows/tests.yml/badge.svg)](https://github.com/PHT-EU/station-backend/actions/workflows/tests.yml)
# PHT Station
This project contains the implementation of the station API, workers for training models, as well as the configuration for the station airflow instance and related workers

## Station API
A FastAPI REST API for train and station management can be found in the `station` directory

## Airflow
The `airflow` directory contains the configuration file for the station airflow instance as well as the predefined airflow
DAGs responsible for executing trains and other longer running or repeating functionality.

## PHT worker
The PHT worker package contains implementations high cost operations such as loading or preparing data sets and training models
or running trains. It should expose a simple API to be used in Airflow DAGs and can also interact with the station DB.

## Installation
1. Create a named docker volume for the postgres database `docker volume create pg_pht_station`
1. Edit the environment variables in the `environment` section of the docker-compose file to match your configuration
1. Run the docker-compose file `docker-compose up -d`, which will start the station and associated services
1. Check the logs for any errors while bringing up the project `docker-compose logs`

## Development environment

### Running the third party services
1. If it does not yet exist create volumes for the database `docker volume create pg_pht_station` and the
   [Blaze](https://github.com/samply/blaze) FHIR server `docker volume create blaze_data`
1. Run the development docker-compose file `docker-compose -f docker-compose_dev.yml up -d`, which will spin up the third
   party services such as the postgres db, airflow and minio, allowing for development of the station API inside of an IDE.
   The services require the following ports to be available on the machine:
    - Postgres: 5432
    - Airflow: 8080
    - Minio: 9000
    - Blaze FHIR Server: 8001

### Running the station API
1. Setup a virtual environment and install the required packages `pip install -r requirements.txt`
2. Run the `run_station.py` file either in your IDE or by running `python station/run_station.py`


### Updating the database
After creating a new or changing and existing database model and registering it in the metadata of the base class, perform
the database migrations using alembic.
1. Create a new revision: `alembic revision --autogenerate -m "name for your migration"`
2. Update the database `alembic upgrade head`

   
