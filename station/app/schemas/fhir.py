from typing import Optional

from pydantic import BaseModel
from datetime import datetime


class FHIRServerBase(BaseModel):
    """
    Base class for FHIR Server
    """
    api_address: str
    name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    type: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    oidc_provider_url: Optional[str] = None
    token: Optional[str] = None


class FHIRServerCreate(FHIRServerBase):
    pass


class FHIRServerUpdate(FHIRServerBase):
    pass


class FHIRServer(FHIRServerBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

