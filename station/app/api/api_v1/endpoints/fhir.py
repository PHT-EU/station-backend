from typing import List
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from station.app.api import dependencies
from fhir_kindling.fhir_server.server_responses import ServerSummary
from station.app.schemas.fhir import FHIRServer, FHIRServerCreate, FHIRServerUpdate
from station.app.crud.crud_fhir_servers import fhir_servers
from station.app.fhir.server import fhir_server_from_db

router = APIRouter()


@router.get("/servers", response_model=List[FHIRServer])
def get_fhir_servers(limit: int = 100, skip: int = 0, db: Session = Depends(dependencies.get_db)):
    db_fhir_servers = fhir_servers.get_multi(db=db, skip=skip, limit=limit)
    return db_fhir_servers


@router.post("/server", response_model=FHIRServer, status_code=201)
def add_fhir_server(fhir_server_in: FHIRServerCreate, db: Session = Depends(dependencies.get_db)):
    db_fhir_server = fhir_servers.create(db=db, obj_in=fhir_server_in)
    return db_fhir_server


@router.get("/server/{server_id}", response_model=FHIRServer)
def get_fhir_server(server_id: int, db: Session = Depends(dependencies.get_db)):
    db_fhir_server = fhir_servers.get(db=db, id=server_id)
    return db_fhir_server


@router.put("/server/{server_id}", response_model=FHIRServer)
def update_fhir_server(server_id: int, update_in: FHIRServerUpdate, db: Session = Depends(dependencies.get_db)):
    db_fhir_server = fhir_servers.get(db, id=server_id)
    db_fhir_server = fhir_servers.update(db=db, db_obj=db_fhir_server, obj_in=update_in)
    return db_fhir_server


@router.delete("/server/{server_id}", status_code=202)
def delete_fhir_server(server_id: int, db: Session = Depends(dependencies.get_db)):
    fhir_servers.remove(db=db, id=server_id)
    return "Success"


@router.get("/server/{server_id}/summary", response_model=ServerSummary)
def fhir_server_summary(server_id: int, refresh: bool = True, db: Session = Depends(dependencies.get_db)):
    server = fhir_server_from_db(db=db, fhir_server_id=server_id)
    return server.summary()
