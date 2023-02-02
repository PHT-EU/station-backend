[![Build](https://github.com/PHT-EU/station-backend/actions/workflows/Build.yml/badge.svg)](https://github.com/PHT-EU/station-backend/actions/workflows/Build.yml)
[![Tests](https://github.com/PHT-EU/station-backend/actions/workflows/tests.yml/badge.svg)](https://github.com/PHT-EU/station-backend/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/PHT-Medic/station-backend/branch/master/graph/badge.svg?token=SWJRH1V44S)](https://codecov.io/gh/PHT-Medic/station-backend)

# PHT Station Backend

This project contains the implementation of the station API, workers for training models, as well as the configuration
for the station airflow instance and related workers. A FastAPI REST API als well as a command line tool for train and
station management can be found in the `station` directory.

## Setup development environment

Checkout the repository and navigate to project directory.

```bash
git clone https://github.com/PHT-Medic/station-backend.git
```

```bash
cd station-backend
```

### Prerequisites

Make sure the following ports required for the services are open or change the port mappings in the `docker-compose.yml`
file.

- Postgres: `5432`
- Redis: `6379`
- Minio: `9000` & `9001` (Console)
- Airflow: `8080`
- Blaze FHIR server: `9090`
- API: `8000`

### Start services

Start the services for development using docker-compose.

```shell
docker compose up -d
```

Check the logs of the services to see if everything is running as expected.

```shell
docker compose logs -f
```

### Configure station config for running the API in development mode

Copy the `station_config.yml.tmpl` file in the root directory to `station_config.yml` and adjust the values (especially
configuring addresses and credentials for the central api)

```yaml
# Configure authentication for central services
central:
  api_url: ""
  # Robot credentials for accessing central services, these can be obtained in the central UI
  robot_id: "central-robot-id"
  robot_secret: "central-robot-secret"
  private_key: "/path/to/private_key.pem"
  # optional password for private key
  private_key_passphrase: "admin"

######### some lines omitted #########

# Configures the address and credentials for the central container registry
registry:
  address:
  password:
  user:
  project:

```

### Install python dependencies

Install dependencies using [poetry](https://python-poetry.org/). This will also create a virtual environment for the
project.

```shell
poetry install --with dev
```

### Run the station API

To run the station API with hot reloading, run the following command:

```bash
poetry run python station/app/run_station.py
```



   
