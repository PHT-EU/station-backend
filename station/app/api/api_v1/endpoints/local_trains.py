from fastapi import APIRouter, Depends ,  File, UploadFile
from station.clients.airflow.client import airflow_client
from station.app.schemas.local_trains import LocalTrainBase
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
def upload_endpoint_file(local_train_id: LocalTrainBase,file: UploadFile=File(...)):
    #TODO reseve and store endpoint file , save information in database
    pass

@router.post("/local_trains/create_local_train")
def create_local_train():
    #TODO create a databese opjekt with all the nesesery information about the local train
    # (endpoint ,querry ,master image , etc )
    pass

