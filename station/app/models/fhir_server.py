from sqlalchemy import Boolean, Column, Integer, String, DateTime
from datetime import datetime

from station.app.db.base_class import Base

class FHIRServer(Base):
    __tablename__ = "fhir_servers"
    id = Column(Integer, primary_key=True, index=True)
    api_address = Column(String)
    name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, nullable=True)
    username = Column(String, nullable=True)
    client_id = Column(String, nullable=True)
    oidc_provider_url = Column(String, nullable=True)
    active = Column(Boolean, default=True)
