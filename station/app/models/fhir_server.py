import uuid

from sqlalchemy import Boolean, Column, Integer, String, DateTime
from datetime import datetime

from sqlalchemy.dialects.postgresql import UUID

from station.app.db.base_class import Base


class FHIRServer(Base):
    __tablename__ = "fhir_servers"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    api_address = Column(String)
    name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, nullable=True)
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)
    client_id = Column(String, nullable=True)
    client_secret = Column(String, nullable=True)
    oidc_provider_url = Column(String, nullable=True)
    token = Column(String)
    active = Column(Boolean, default=True)
    type = Column(String, nullable=True)
    proposal_id = Column(String, nullable=True)
