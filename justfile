lint:
    poetry run ruff . --fix

format:
    poetry run black .

build-ctl:
  docker build -f "$(pwd)/docker/Dockerfile_ctl" . -t station-ctl:latest

ctl-build-install: build-ctl test-container-install

test-container-install:
  docker run \
    -v "$(pwd):/mnt/station:rw" \
    -v "/var/run/docker.sock:/var/run/docker.sock:rw" \
    -e "PHT_TEMPLATE_DIR=/home/station/station/ctl/templates" \
    station-ctl \
    --install-dir /mnt/station \
    --host-path "$(pwd)"

test-ctl-install-path PATH:
  docker run \
    -v "{{PATH}}:/mnt/station:rw" \
    -v "/var/run/docker.sock:/var/run/docker.sock:rw" \
    -e "PHT_TEMPLATE_DIR=/home/station/station/ctl/templates" \
    station-ctl \
    install \
    --install-dir "/mnt/station" \
    --host-path "{{PATH}}"

windows-pwd:
  $pwd