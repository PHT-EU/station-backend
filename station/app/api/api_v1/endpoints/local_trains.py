import io
import tarfile

from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, File, UploadFile
from station.app.api import dependencies
from typing import List
from station.clients.airflow.client import airflow_client
from station.app.schemas.local_trains import LocalTrainBase
from station.app.local_train_minio.LocalTrainMinIO import train_data
from fastapi.responses import Response
from fastapi.responses import FileResponse
from station.app.schemas.local_trains import LocalTrain, LocalTrainCreate, LocalTrainAddMasterImage, LocalTrainGetFile

from station.app.crud.crud_local_train import local_train

from station.clients.harbor_client import harbor_client

router = APIRouter()


@router.post("/localTrains/{train_id}/run")
def run_docker_train(train_id: str, db: Session = Depends(dependencies.get_db)):
    """
    sends a command to the the airflow client to trigger a run with the trains configurations

    @param train_id: UID of the local train
    @param db: reference to the postgres database
    @return: airflow run ID
    """
    config = local_train.get_train_config(db, train_id)
    run_id = airflow_client.trigger_dag("run_local", config)
    return run_id


@router.post("/localTrains/uploadTrainFile/{train_id}")
async def upload_train_file(train_id: str, upload_file: UploadFile = File(...)):
    """

    @param train_id:
    @param upload_file:
    @return:
    """
    await local_train.add_file_minio(upload_file, train_id)
    return {"filename": upload_file.filename}


@router.post("/localTrains/create", response_model=LocalTrain)
def create_local_train(create_msg: LocalTrainCreate, db: Session = Depends(dependencies.get_db)):
    """

    @param create_msg: information about the new train
    @param db: reference to the postgres database
    @return:
    """
    train = local_train.create(db, obj_in=create_msg)
    return train


@router.post("/localTrains/createWithUuid", response_model=LocalTrain)
def create_local_train(db: Session = Depends(dependencies.get_db)):
    """

    @param db:
    @return:
    """
    train = local_train.create(db, obj_in=None)
    return train


@router.put("/localTrains/addMasterImage")
def add_master_image(add_master_image_msg: LocalTrainAddMasterImage, db: Session = Depends(dependencies.get_db)):
    """

    @param add_master_image_msg:
    @param db:
    @return:
    """
    new_config = local_train.update_config_add_repostory(db, add_master_image_msg.train_id, add_master_image_msg.image)
    print(f"{add_master_image_msg.train_id}, {add_master_image_msg.image}")
    return new_config


@router.put("/localTrains/addTag/{train_id}/{tag}")
def add_tag_image(train_id: str, tag: str, db: Session = Depends(dependencies.get_db)):
    """

    @param train_id:
    @param tag:
    @param db:
    @return:
    """
    new_config = local_train.update_config_add_tag(db, train_id, tag)
    return new_config


@router.put("/localTrains/addEntrypoint/{train_id}/{entrypoint}")
def upload_endpoint_file(train_id: str, entrypoint: str, db: Session = Depends(dependencies.get_db)):
    """

    @param train_id:
    @param entrypoint:
    @param db:
    @return:
    """
    new_config = local_train.update_config_add_entrypoint(db, train_id, entrypoint)
    return new_config


@router.put("/localTrains/addQuery/{train_id}/{query}")
def upload_endpoint_file(train_id: str, query: str, db: Session = Depends(dependencies.get_db)):
    """

    @param train_id:
    @param query:
    @param db:
    @return:
    """
    new_config = local_train.update_config_add_query(db, train_id, query)
    return new_config


@router.delete("/localTrains/deleteTrain/{train_id}")
def delete_local_train(train_id: str, db: Session = Depends(dependencies.get_db)):
    """

    @param train_id:
    @param db:
    @return:
    """
    obj = local_train.remove_train(db, train_id)
    return f"{obj} was deleted"


@router.delete("/localTrains/deleteFile/{train_id}/{file_name}")
async def delete_file(train_id: str,file_name: str):
    """

    @param train_id:
    @param file_name:
    @return:
    """
    await train_data.delete_train_file(f"{train_id}/{file_name}")
    return "deletetd " + file_name


@router.get("/localTrains/getAllUploadedFileNames/{train_id}")
def get_all_uploaded_file_names(train_id: str):
    """

    @param train_id:
    @return:
    """
    # make search for train
    return {"files": local_train.get_all_uploaded_files(train_id)}


@router.get("/localTrains/getResults/{train_id}")
def get_results(train_id: str):
    """

    @param train_id:
    @return:
    """
    data = train_data.get_results(train_id)
    file_like_objekt = io.BytesIO(data)
    with tarfile.open(name="results.tar", fileobj=file_like_objekt, mode='a') as tar:
       print(tar)

    return FileResponse('results.tar', media_type='bytes/tar')


@router.get("/localTrains/getTrainStatus/{train_id}")
def get_train_status(train_id: str, db: Session = Depends(dependencies.get_db)):
    """

    @param train_id:
    @param db:
    @return:
    """
    obj = local_train.get_train_status(db, train_id)
    return obj


@router.get("/localTrains/masterImages")
def get_master_images():
    """

    @return:
    """
    return harbor_client.get_master_images()


@router.get("/localTrains/getAllLocalTrains")
def get_all_local_trains(db: Session = Depends(dependencies.get_db)):
    """

    @param db:
    @return:
    """
    return local_train.get_trains(db)


@router.get("/localTrains/getEndpoint")
async def get_endpoint_file():
    """

    @return:
    """
    file = train_data.read_file("endpoint.py")
    return file


@router.get("/localTrains/getConfig")
def get_config(train_id: str, db: Session = Depends(dependencies.get_db)):
    """

    @param train_id:
    @param db:
    @return:
    """
    config = local_train.get_train_config(db, train_id)
    return config


@router.get("/localTrains/getName")
def get_config(train_id: str, db: Session = Depends(dependencies.get_db)):
    """

    @param train_id:
    @param db:
    @return:
    """
    config = local_train.get_train_name(db, train_id)
    return config


@router.get("/localTrains/getID")
def get_config(train_name: str, db: Session = Depends(dependencies.get_db)):
    """

    @param train_name:
    @param db:
    @return:
    """
    config = local_train.get_train_id(db, train_name)
    return config


@router.get("/localTrains/getFile")
async def get_file(train_id: str, file_name: str):
    """

    @param train_id:
    @param file_name:
    @return:
    """
    file = train_data.read_file(f"{train_id}/{file_name}")
    return Response(file)

@router.get("/localTrains/getAirflowRun/{run_id}")
def get_airflow_run_information(run_id: str):
    """
    Get information about one local train airflow DAG execution.
    @param run_id: Airflow run ID
    @return:
    """
    run_info = airflow_client.get_run_information("run_local", run_id)
    return run_info

