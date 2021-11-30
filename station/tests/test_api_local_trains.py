import pytest
import json
import time
from pathlib import Path
from fastapi.testclient import TestClient

from station.app.main import app
from station.app.api.dependencies import get_db

from .test_db import override_get_db

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


# test general geters
def test_get_master_images():
    response = client.get("/api/localTrains/masterImages")
    assert response.status_code == 200, response.json


def test_get_all_local_trains():
    response = client.get("/api/localTrains/getAllLocalTrains")
    assert response.status_code == 200, response.json


def test_create_and_run_local_train():
    # create local train
    train_creation_response = client.post("api/localTrains/create", json={"train_name": "testing_local_train"})
    assert train_creation_response.status_code == 200, train_creation_response.json
    train_creation_response_dict = json.loads(train_creation_response.text)

    # configer train train_cration_response.train_id
    add_MasterImage_response = client.put("api/localTrains/addMasterImage", json={
        "train_id": train_creation_response_dict["train_id"],
        "image": "master/python/base"})
    assert add_MasterImage_response.status_code == 200, add_MasterImage_response.json

    # upload entrypoint file
    entrypoint_name = "entrypoint.py"
    with open(f"./tests/test_files/{entrypoint_name}", "r") as f:
        upload_entrypoint_file_response = client.post(
            f"/api/localTrains/uploadTrainFile/{train_creation_response_dict['train_id']}",
            files={"upload_file": ("entrypoint.py", f, "multipart/form-data")}
        )
        assert upload_entrypoint_file_response.status_code == 200, upload_entrypoint_file_response.json

    # get uploded files and test if entrypoint was stored
    files_uploded_response = client.get(
        f"/api/localTrains/getAllUploadedFileNames/{train_creation_response_dict['train_id']}")
    assert files_uploded_response.status_code == 200, files_uploded_response.json
    entrypoint_object_name = json.loads(files_uploded_response.text)["files"][0]["_object_name"]
    assert f"{train_creation_response_dict['train_id']}/{entrypoint_name}" == entrypoint_object_name

    # set entrypoint in config
    add_entrypoint_to_config_response = client.put(
        f"/api/localTrains/addEntrypoint/{train_creation_response_dict['train_id']}/{entrypoint_name}")
    assert add_entrypoint_to_config_response.status_code == 200, add_entrypoint_to_config_response.json

    # start local train run
    start_train_response = client.post(f"/api/localTrains/{train_creation_response_dict['train_id']}/run")
    assert start_train_response.status_code == 200, start_train_response.json

    run_id = start_train_response.text.replace('"', '')

    def run_is_finisted(run_id):
        run_response = client.get(f"/api/airflow/getAirflowRun/{run_id}/run_local")
        assert run_response.status_code == 200, run_response.json
        run_dict = json.loads(run_response.text)
        task_instances = run_dict["tasklist"]["task_instances"]
        finished_successfully = True
        finished_with_failed_tasks = False
        for task in task_instances:
            finished_successfully = task["state"] == "success" and finished_successfully
            finished_with_failed_tasks = task["state"] == "failed" or finished_with_failed_tasks
        return finished_successfully, finished_with_failed_tasks

    while (True):
        finished_successfully, finished_with_failed_tasks = run_is_finisted(run_id)
        assert finished_with_failed_tasks is False
        if finished_successfully:
            break
        time.sleep(10)
        # get uploded files and test if entrypoint was stored
    files_uploded_response = client.get(
        f"/api/localTrains/getAllUploadedFileNames/{train_creation_response_dict['train_id']}")
    assert files_uploded_response.status_code == 200, files_uploded_response.json

