from typing import Any, Union, Dict, List
from sqlalchemy.orm import Session

from .base import CRUDBase, CreateSchemaType, ModelType, UpdateSchemaType
from station.app.schemas.fhir import FHIRServerCreate, FHIRServerUpdate
from station.app.models.fhir_server import FHIRServer


class CRUDFHIRServers(CRUDBase[FHIRServer, FHIRServerCreate, FHIRServerUpdate]):

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        # Encrypt sensitive values
        encrypted_in = self.encrypt_sensitive_values(obj_in)
        # Add encrypted values to the db
        return super().create(db, obj_in=encrypted_in)

    def update(self, db: Session, *, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]) -> ModelType:
        obj_in = self.encrypt_sensitive_values(obj_in)
        return super().update(db, db_obj=db_obj, obj_in=obj_in)

    def encrypt_sensitive_values(self, obj_in: Union[FHIRServerCreate, FHIRServerUpdate]) -> FHIRServerCreate:
        """
        Encrypt sensitive values in the FHIRServerCreate/FHIRServerUpdate object
        Args:
            obj_in:
        Returns:
            the same object with encrypted sensitive values
        """

        from station.app.settings import settings
        fernet = settings.get_fernet()

        if obj_in.client_secret:
            obj_in.client_secret = fernet.encrypt(obj_in.client_secret.encode()).decode()
        if obj_in.password:
            obj_in.password = fernet.encrypt(obj_in.password.encode()).decode()
        if obj_in.token:
            obj_in.token = fernet.encrypt(obj_in.token.encode()).decode()

        return obj_in


fhir_servers = CRUDFHIRServers(FHIRServer)
