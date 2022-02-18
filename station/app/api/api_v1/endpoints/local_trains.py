from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, File, UploadFile

from station.app.api import dependencies
from station.app.local_train_minio.LocalTrainMinIO import train_data
from fastapi.responses import Response
from station.app.schemas.local_trains import LocalTrain, LocalTrainCreate, LocalTrainConfigCreate, \
    LocalTrainAirflowConfig, \
    LocalTrainAirflowConfigs, LocalTrainUploadTrainFileResponse, AllFilesTrain, LocalTrainInfo, \
    MasterImagesList, LocalTrainSchemaList, LocalTrainBase, LocalTrainLog, LocalTrainConfigUpdate

from station.app.crud.crud_local_train import local_train
from station.clients.harbor_client import harbor_client

router = APIRouter()


@router.post("/{train_id}/uploadTrainFile", response_model=LocalTrainUploadTrainFileResponse)
async def upload_train_file(train_id: str, upload_file: UploadFile = File(...)):
    """
    upload a singel file to minIO into the subfolder of the Train

    @param train_id: Id of the train the file belongs
    @param upload_file: UploadFile that has to be stored

    @return:
    """
    await local_train.add_file_minio(upload_file, train_id)
    return {"train_id": train_id,
            "filename": upload_file.filename}


@router.post("", response_model=LocalTrain)
def create_local_train(create_msg: LocalTrainCreate, db: Session = Depends(dependencies.get_db)):
    """
    creae a database entry for a new train with preset names from the create_msg

    @param create_msg: information about the new train
    @param db: reference to the postgres database
    @return:
    """
    train = local_train.create(db, obj_in=create_msg)
    return train


@router.post("/withUuid", response_model=LocalTrain)
def create_local_train(db: Session = Depends(dependencies.get_db)):
    """
    create a database entry for a new train, the name is set as the train_id
    @param db: reference to the postgres database
    @return:
    """
    train = local_train.create(db, obj_in=None)
    return train


@router.post("/config", response_model=LocalTrainConfigCreate)
def create_local_train_config(config_msg: LocalTrainConfigCreate, db: Session = Depends(dependencies.get_db)):
    """
    create a database entry for config and if train id is defind in the config it gets added to a local train
    @parm db: reference to the postgres database
    @parm config_msg: schema for a new config
    """
    config = local_train.create_config(db, obj_in=config_msg)
    return config


@router.put("/{train_id}/{config_name}/config", response_model=LocalTrainAirflowConfig)
def put_local_train_config(train_id: str, config_name: str, db: Session = Depends(dependencies.get_db)):
    """
    assings a config to a train
    """
    config = local_train.put_config(db, train_id=train_id, config_name=config_name)
    return config


@router.put("/{config_name}/config", response_model=LocalTrainAirflowConfig)
def update_local_train_config(config_name: str, config_msg: LocalTrainConfigUpdate,
                              db: Session = Depends(dependencies.get_db)):
    """
    updates the values of a config
    """
    config = local_train.update_config(db, config_name=config_name, config_update=config_msg)
    return config


@router.put("/{train_id}/config", response_model=LocalTrainAirflowConfig)
def update_config_from_train(train_id: str, config_msg: LocalTrainConfigUpdate,
                             db: Session = Depends(dependencies.get_db)):
    """
    updates the values of a config from a train
    """
    config = local_train.update_config_from_train(db, train_id=train_id, config_update=config_msg)
    return config



@router.delete("/{train_id}/train", response_model=LocalTrain)
def delete_local_train(train_id: str, db: Session = Depends(dependencies.get_db)):
    """

    @param train_id: uid of a local train
    @param db: reference to the postgres database
    @return:
    """
    obj = local_train.remove_train(db, train_id)
    return obj


@router.delete("/{train_id}/{file_name}/file", response_model=LocalTrainUploadTrainFileResponse)
async def delete_file(train_id: str, file_name: str):
    """

    @param train_id: uid of a local train
    @param file_name:
    @return:
    """
    await train_data.delete_train_file(f"{train_id}/{file_name}")
    return {"train_id": train_id,
            "filename": file_name}


@router.delete("/{config_name}/config", response_model=LocalTrainAirflowConfig)
def delete_config(config_name: str, db: Session = Depends(dependencies.get_db)):
    """
    removes a config by it's name

    @param config_name: name of the config that has to be removed
    @param db: reference to the postgres database
    @return:
    """
    config = local_train.remove_config(db, config_name=config_name)
    return config


@router.get("/{train_id}/allUploadedFileNames", response_model=AllFilesTrain)
def get_all_uploaded_file_names(train_id: str):
    """

    @param train_id: uid of a local train
    @return:
    """
    files = local_train.get_all_uploaded_files(train_id)
    return {"files": files}


@router.get("/{train_id}/info", response_model=LocalTrainInfo)
def get_train_status(train_id: str, db: Session = Depends(dependencies.get_db)):
    """
    get all meta informaiton about the train
    @param train_id: uid of a local train
    @param db: reference to the postgres database
    @return:
    """
    obj = local_train.get_train_status(db, train_id)
    return obj


@router.get("/masterImages", response_model=MasterImagesList)
def get_master_images():
    """
    get all availabel master images
    @return:
    """
    return {"images": harbor_client.get_master_images()}


@router.get("/trains", response_model=LocalTrainSchemaList)
def get_all_local_trains(db: Session = Depends(dependencies.get_db)):
    """

    @param db: reference to the postgres database
    @return:
    """
    return {"trains": local_train.get_trains(db)}


@router.get("/{train_id}/config", response_model=LocalTrainAirflowConfig)
def get_config(train_id: str, db: Session = Depends(dependencies.get_db)):
    """

    @param train_id: uid of a local train
    @param db: reference to the postgres database
    @return:
    """
    config = local_train.get_train_config(db, train_id)
    return config


@router.get("/configs", response_model=LocalTrainAirflowConfigs)
def get_all_configs(db: Session = Depends(dependencies.get_db)):
    configs = local_train.get_configs(db)
    return configs


@router.get("/{train_id}/name", response_model=LocalTrainBase)
def get_name(train_id: str, db: Session = Depends(dependencies.get_db)):
    """

    @param train_id: uid of a local train
    @param db: reference to the postgres database
    @return:
    """
    train_name = local_train.get_train_name(db, train_id)
    return {"train_name": train_name,
            "train_id": train_id}


@router.get("/{train_name}/id", response_model=LocalTrainBase)
def get_id(train_name: str, db: Session = Depends(dependencies.get_db)):
    """

    @param train_name:
    @param db: reference to the postgres database
    @return:
    """
    train_id = local_train.get_train_id(db, train_name)
    return {"train_name": train_name,
            "train_id": train_id}


@router.get("/{train_id}/{file_name}/file")
async def get_file(train_id: str, file_name: str):
    """

    @param train_id: uid of a local train
    @param file_name:
    @return:
    """
    file = train_data.read_file(f"{train_id}/{file_name}")
    return Response(file)


@router.get("/{train_id}/logs", response_model=list[LocalTrainLog])
def get_logs(train_id: str, db: Session = Depends(dependencies.get_db)):
    """
    Returns the run logs for the runs of the train

    @param db: reference to the postgres database
    @param train_id: uid of a local train
    @return:
    """
    logs = local_train.get_train_logs(db, train_id)
    return logs


@router.get("/{train_id}/lastLogs", response_model=LocalTrainLog)
def get_last_log(train_id: str, db: Session = Depends(dependencies.get_db)):
    """
    Returns the last run logs for the train

    @param db: reference to the postgres database
    @param train_id: uid of a local train
    @return:
    """
    log = local_train.get_last_train_logs(db, train_id)
    return log
