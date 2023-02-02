from datetime import datetime
from typing import Any, Optional

from fhir_kindling.fhir_server.server_responses import ServerSummary
from pydantic import BaseModel, root_validator


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

    @root_validator
    def validate_credentials(cls, values):
        username, password = values.get("username"), values.get("password")
        token = values.get("token")
        client_id, client_secret = values.get("client_id"), values.get("client_secret")
        oidc_provider_url = values.get("oidc_provider_url")

        if username and not password:
            raise ValueError("Password is required if username is provided")
        if password and not username:
            raise ValueError("Username is required if password is provided")

        if (username and password) and token:
            raise ValueError("Cannot provide both username and password or token")

        if (client_id and client_secret) and token:
            raise ValueError("Cannot provide both client_id and client_secret or token")

        if (client_id and client_secret) and not oidc_provider_url:
            raise ValueError(
                "Cannot provide both client_id and client_secret without oidc_provider_url"
            )
        if (username and password) and client_id:
            raise ValueError("Cannot provide both username and password and client_id")

        return values


class FHIRServerCreate(FHIRServerBase):
    pass


class FHIRServerUpdate(FHIRServerBase):
    pass


class FHIRServer(FHIRServerBase):
    id: Any
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class ServerStatistics(BaseModel):
    """
    Statistics for a FHIR Server
    """

    summary: ServerSummary
    created_at: datetime
    figure: Optional[dict] = None
