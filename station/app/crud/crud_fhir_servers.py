from .base import CRUDBase, CreateSchemaType, ModelType
from station.app.schemas.fhir import FHIRServerCreate, FHIRServerUpdate
from station.app.models.fhir_server import FHIRServer

class CRUDFHIRServers(CRUDBase[FHIRServer, FHIRServerCreate, FHIRServerUpdate]):
    pass


fhir_servers = CRUDFHIRServers(FHIRServer)
