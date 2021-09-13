from fastapi import APIRouter, Depends, File, UploadFile
from station.clients.airflow.client import airflow_client
from station.app.schemas.local_trains import LocalTrainBase
from station.app.local_train_builder.TrainBuilder import train_builder_local
router = APIRouter()


@router.post("/local_trains/{local_train_id}/run")
def run_docker_train(local_train_id: str):
    print(local_train_id)
    airflow_client.trigger_dag("run_local")


@router.get("/local_trains/master_images")
def get_master_images():
    # TODO get all avialabel master images
    pass


@router.post("/local_trains/upload_endpoint")
async def upload_endpoint_file( upload_file: UploadFile = File(...)):
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
def get_endpoint_file():
    pass


@router.get("/local_trains/get_all_uploaded_file_names")
def get_all_uploaded_file_names():
    return train_builder_local.get_all_uploaded_files()
