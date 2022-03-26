[![Build](https://github.com/PHT-EU/station-backend/actions/workflows/Build.yml/badge.svg)](https://github.com/PHT-EU/station-backend/actions/workflows/Build.yml)
[![Tests](https://github.com/PHT-EU/station-backend/actions/workflows/tests.yml/badge.svg)](https://github.com/PHT-EU/station-backend/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/PHT-Medic/station-backend/branch/master/graph/badge.svg?token=SWJRH1V44S)](https://codecov.io/gh/PHT-Medic/station-backend)

# PHT Station Backend

This project contains the implementation of the station API, workers for training models, as well as the configuration
for the station airflow instance and related workers. A FastAPI REST API for train and station management can be found
in the `station` directory

## Environment configuration


## Installation

1. Create a named docker volume for the postgres database `docker volume create pg_pht_station`
2. Edit the environment variables in the `environment` section of the docker-compose file to match your configuration
3. Run the docker-compose file `docker-compose up -d`, which will start the station and associated services
4. Check the logs for any errors while bringing up the project `docker-compose logs`


## Development environment

[Pipenv](https://pipenv.pypa.io/en/latest/) should be used as a dependency manager for developing in the project.

1. Install dev dependencies
   ```shell
   pipenv install --dev
   ```

2. Spin up the backend services
   ```shell
   docker-compose -f docker-compose_dev.yml up -d
   ```
3. Edit the station configuration file `station/example.station_config.yml` to match your service configuration and
   rename it to `station_config.yml` for it to be pucked up on station start up
4. Make sure the environment is set to `development` in the `station/example.station_config.yml` file or via the
   `ENVIRONMENT` environment variable.
5. Run the tests
   ```shell
   pipenv shell
   pipenv run pytest station
   ```
6. Run the server in the activated virtual environment (or via your IDE)
   ```shell
   pipenv shell
   pipenv python station/run_station.py
   ```
7. Inspect the logs for any errors

### Setup authentication server for testing

After running

```shell
docker-compose -f docker-compose_dev.yml up -d
```

shell into the station-auth container:

```shell
docker exec -it station-auth sh
```

and run the following commands to initialize the authentication server

```shell
npm run setup --workspace=packages/server
```

the output should be similar, with different keys:

```
✔ Generated rsa key-pair.
✔ Created database.
✔ Synchronized database schema.
✔ Seeded database.
ℹ Robot ID: 51dc4d96-f122-47a8-92f4-f0643dae9be5
ℹ Robot Secret: d1l33354crj1kyo58dbpflned2ocnw2yez69
```

copy and save the generated robot id and secret. Then run

```shell
npm run start
```

to reset the database and seed it with the default users. Exit the container with `exit`
and restart the authentication container.

```shell
docker-compose -f docker-compose_dev.yml restart auth
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
1. Run the development docker-compose file `docker-compose -f docker-compose_dev.yml up -d`, which will spin up the
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


   
