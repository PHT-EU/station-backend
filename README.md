[![Build](https://github.com/PHT-EU/station-backend/actions/workflows/Build.yml/badge.svg)](https://github.com/PHT-EU/station-backend/actions/workflows/Build.yml)
[![Tests](https://github.com/PHT-EU/station-backend/actions/workflows/tests.yml/badge.svg)](https://github.com/PHT-EU/station-backend/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/PHT-Medic/station-backend/branch/master/graph/badge.svg?token=SWJRH1V44S)](https://codecov.io/gh/PHT-Medic/station-backend)

# PHT Station Backend

This project contains the implementation of the station API, workers for training models, as well as the configuration
for the station airflow instance and related workers. A FastAPI REST API for train and station management can be found
in the `station` directory.

## Setup development environment

Checkout the repository and navigate to project directory.

```bash
git clone https://github.com/PHT-Medic/station-backend.git
```

```bash
cd station-backend
```

Make sure the following ports required for the services are open or change the port mappings in the `docker-compose_dev.yml` file.

- Postgres: 5432
- Redis: 6379
- Minio: 9000 & 9001 (Console)
- Airflow: 8080
- Blaze FHIR server: 9090
- API: 8000

### Start third party services

Spin up the backend services

#### Setup the auth server

When installing for the first time, run the following command to perform the initial setup of the auth server.
NODE_ENV=test
WRITABLE_DIRECTORY_PATH=/usr/src/app/writable
```bash
docker-compose -f docker-compose_dev.yml run auth setup
```
This should generate the files required for the auth server as well as a `seed.json` file in `service_data/auth`.
Copy the robot id and secret from the `seed.json` file into the `.env` file (`AUTH_ROBOT_ID` and `AUTH_ROBOT_SECRET`).

```bash
docker-compose -f docker-compose_dev.yml up -d
```

### Install python dependencies

[Pipenv](https://pipenv.pypa.io/en/latest/) should be used as a dependency manager for developing in the project. Install
dependencies in a new virtual environment using the following command:

```shell
pipenv install --dev
```

### Run the station API
To run the station API with hot reloading, run the following command:
```bashs
python station/app/run_station.py
```

## Third party services

### Airflow

The `airflow` directory contains the configuration file for the station airflow instance as well as the predefined
airflow DAGs responsible for executing trains and other longer running or repeating functionality.

### Minio

### Postgres DB

### Running the third party services

1. If it does not yet exist create volumes for the database `docker volume create pg_pht_station` and the
   [Blaze](https://github.com/samply/blaze) FHIR server `docker volume create blaze_data`
2. Run the development docker-compose file `docker-compose -f docker-compose_dev.yml up -d`, which will spin up the
   third party services such as the postgres db, airflow and minio, allowing for development of the station API inside
   of an IDE. The services require the following ports to be available on the machine:
    - Postgres: 5432
    - Airflow: 8080
    - Minio: 9000
    - Blaze FHIR Server: 8001

### Updating the database

After creating a new or changing and existing database model and registering it in the metadata of the base class,
perform the database migrations using alembic.

1. Create a new revision: `alembic revision --autogenerate -m "name for your migration"`
2. Update the database `alembic upgrade head`

## PHT worker

The PHT worker package contains implementations high cost operations such as loading or preparing data sets and training
models or running trains. It should expose a simple API to be used in Airflow DAGs and can also interact with the
station DB.


   
