from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from station.app.models.discovery import DataSetSummary
from station.app.schemas.discovery import SummaryCreate, SummaryUpdate

from .base import CreateSchemaType, CRUDBase, ModelType, Optional


class CRUDDiscoveries(CRUDBase[DataSetSummary, SummaryCreate, SummaryUpdate]):
    def create(self, db: Session, *, obj_in: CreateSchemaType) -> Optional[ModelType]:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        return db_obj


discoveries = CRUDDiscoveries(DataSetSummary)
