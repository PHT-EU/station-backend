from fastapi.security import OAuth2AuthorizationCodeBearer, HTTPBearer
from station.app.config import settings

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    tokenUrl=settings.config.auth.token_url,
    authorizationUrl=settings.config.auth.authorization_url,
    auto_error=True,
    scopes={"read": "Allow read operations", "write": "Allow write operations"}
)
