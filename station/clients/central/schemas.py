from pydantic import BaseModel


class RegistryCredentials(BaseModel):
    user: str
    password: str
    address: str
    project: str
