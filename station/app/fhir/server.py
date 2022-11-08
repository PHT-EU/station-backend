import json
from datetime import datetime


from sqlalchemy.orm import Session
from fhir_kindling.fhir_server.server_responses import ServerSummary
from fhir_kindling import FhirServer
import plotly.graph_objects as go
import plotly.io

from station.app.crud.crud_fhir_servers import fhir_servers
from station.app.config import settings
from station.app.schemas.datasets import FigureData
from station.app.schemas.fhir import ServerStatistics


def fhir_server_from_db(db: Session, fhir_server_id: str, server=None) -> FhirServer:
    if server:
        db_server = server
    else:
        db_server = fhir_servers.get(db, id=fhir_server_id)

    assert db_server
    # for each of the different options access and decrypt the sensitive values and initialize a server instance
    if db_server.username:
        password = settings.get_fernet().decrypt(db_server.password.encode()).decode()
        return FhirServer(
            api_address=db_server.api_address,
            username=db_server.username,
            password=password,
            fhir_server_type=db_server.type
        )

    if db_server.token:
        token = settings.get_fernet().decrypt(db_server.token.encode()).decode()
        return FhirServer(
            api_address=db_server.api_address,
            token=token,
            fhir_server_type=db_server.type
        )

    if db_server.client_id:
        client_secret = settings.get_fernet().decrypt(db_server.client_secret.encode())
        return FhirServer(
            api_address=db_server.api_address,
            fhir_server_type=db_server.type,
            client_id=db_server.client_id,
            client_secret=client_secret.decode("utf-8"),
            oidc_provider_url=db_server.oidc_provider_url,
        )


def get_server_statistics(db: Session, fhir_server_id: str, refresh: bool = False) -> ServerStatistics:
    db_server = fhir_servers.get(db, id=fhir_server_id)

    if db_server.summary and not refresh:
        return ServerStatistics.parse_raw(db_server.summary)

    server = fhir_server_from_db(db, fhir_server_id, db_server)
    summary = server.summary()
    obj = summary_plot(summary)
    return ServerStatistics(
        created_at=datetime.now(),
        summary=summary,
        figure=obj
    )


def summary_plot(summary: ServerSummary) -> dict:
    # sort the resources by count
    resources = sorted(summary.resources, key=lambda x: x.count)
    resources, counts = zip(*[(r.resource, r.count) for r in resources if r.count > 0])
    fig = go.Figure(go.Bar(
        x=list(counts),
        y=list(resources),
        orientation='h'))

    fig_json = plotly.io.to_json(fig)
    obj = json.loads(fig_json)
    return obj
