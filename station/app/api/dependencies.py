from typing import Generator
from station.app.db.session import SessionLocal
from station.app.auth import authorized_user

import os
from fastapi.security import HTTPBearer


# reusable_oauth2 = OAuth2PasswordBearer(
#     tokenUrl=f"{settings.API_V1_STR}/login/access-token"
# )


def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def fernet_key() -> bytes:
    # load fernet key from environment variables
    fernet_key = os.getenv("FERNET_KEY")
    if not fernet_key:
        # TODO load key from station config file
        pass
    return fernet_key.encode()


