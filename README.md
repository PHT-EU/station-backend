# PHT Station
This project contains the implementation of the station API, workers for training models, as well as the configuration for the station airflow instance and related workers

## Station API
A FastAPI REST API for train and station management can be found in the `station` directory

## Airflow
The `airflow` directory contains the configuration file for the station airflow instance as well as the predefined airflow
DAGs responsible for executing trains and other longer running or repeating functionality.

## Installation
1. Create a named docker volume for the postgres database `docker volume create pg_pht_station`
1. Run the docker-compose file `docker-compose up -d`, which will start the station and associated services
1. Check the logs for any errors while bringing up the project `docker-compose logs`

### Running the services for development
1. If it does not yet exist create the volume for the database `docker volume create pg_pht_station`
1. Run the development docker-compose file `docker-compose -f docker-compose_dev.yml up -d`, which will spin up the third
party services such as the postgres db, airflow and minio, allowing for development of the station API inside of an IDE.
   The services require the following ports to be available on the machine:
   - Postgres: 5432
   - Airflow: 8080
   - Minio: 9000 

   
