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
docker run -v $(pwd)/data/auth:/usr/src/app/writable -e "NODE_ENV=test" -e "WRITABLE_DIRECTORY_PATH=/usr/src/app/writable" ghcr.io/tada5hi/authelion-server:latest setup
```

The end of the output should contain two lines containing the robot id and secret:

```text
ℹ Robot ID: dfdd59e9-bc26-42c3-8cbb-6665f58bd62d
ℹ Robot Secret: 4ahwcc1jgobo07kori4hxw7i0f9mn1zqvgkjx5uzrv05yqbkiyl2hfn4wfd5cyq5
```

Copy the id and secret into the `.env` file.

```bash
docker-compose -f docker-compose_dev.yml up -d
```

### Install python dependencies

[Pipenv](https://pipenv.pypa.io/en/latest/) should be used as a dependency manager for developing in the project.

```shell
pipenv install --dev
```

### Start the backend services

2. Spin up the backend services
   ```shell
   docker-compose -f docker-compose_dev.yml up -d
   ```
3. Edit the station configuration file `station/example.station_config.yml` to match your service configuration and
   rename it to `station_config.yml` for it to be pucked up on station start up
4. Make sure the environment is set to `development` in the `station/example.station_config.yml` file or via the
   `ENVIRONMENT` environment variable.
5. Run the server in the activated virtual environment (or via your IDE)
   ```shell
   pipenv shell
   pipenv python station/run_station.py
   ```
6. Inspect the logs for any errors

### Running the tests

7. Run the tests
   ```shell
   pipenv shell
   pipenv run pytest station
   ```

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


   
