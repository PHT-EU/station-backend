import io

from fastapi import APIRouter, Depends, File, UploadFile
from typing import List
from station.clients.airflow.client import airflow_client
from station.app.schemas.local_trains import LocalTrainBase
from station.app.local_train_builder.TrainBuilder import train_builder_local
from fastapi.responses import Response
from fastapi.responses import FileResponse

router = APIRouter()


@router.post("/local_trains/{local_train_id}/run")
def run_docker_train(local_train_id: str):
    print(local_train_id)
    airflow_client.trigger_dag("run_local")


@router.get("/local_trains/master_images")
def get_master_images():
    # TODO get all avialabel master images
    pass


@router.post("/local_trains/upload_train_file")
async def upload_train_file(upload_file: UploadFile = File(...)):
    await train_builder_local.store_train_file(upload_file)
    return {"filename": upload_file.filename}



@router.post("/local_trains/upload_endpoint")
async def upload_endpoint_file(upload_file: UploadFile = File(...)):
    # TODO reseve and store endpoint file , save information in database
    await train_builder_local.store_endpoint(upload_file)
    return {"filename": upload_file.filename}


@router.post("/local_trains/create_local_train")
def create_local_train():
    # TODO create a databese opjekt with all the nesesery information about the local train
    # (endpoint ,querry ,master image , etc )
    print("hallo")
    return {"hallo": 42}


@router.get("/local_trains/get_endpoint")
async def get_endpoint_file():
    file = train_builder_local.read_file("endpoint.py")
    return file


@router.get("/local_trains/get_file")
async def get_file(file_name: str):
    file = train_builder_local.read_file(file_name)
    return file

@router.delete("/local_trains/delete_file/{file_name}")
async def delete_file(file_name: str):
    await train_builder_local.delete_train_file(file_name)
    return "deletetd " + file_name

@router.get("/local_trains/get_all_uploaded_file_names")
def get_all_uploaded_file_names():
    return {"files": train_builder_local.get_all_uploaded_files()}


@router.get("/local_trains/get_results/{train_id}")
def get_results(train_id: str):
    file = train_builder_local.get_results(train_id)
    return Response(file, media_type='bytes/tar')


@router.get("/local_trains/get_train_status/{train_id}")
def get_train_status(train_id: str):
    pass


