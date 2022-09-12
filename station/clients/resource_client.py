from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

import requests
import requests.auth
from pydantic import BaseModel
from requests import HTTPError

from station.clients.base import BaseClient

ModelType = TypeVar("ModelType", bound=BaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class ResourceClient(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):

    def __init__(self, base_url, resource_name: str, model: Type[ModelType], client: BaseClient):
        """
        Base class for a resource client for the station api implement
        Args:
            base_url:
            resource_name:
            model:
            client: Base client to handle authentication
        """
        self.base_url = base_url
        self.resource_name = resource_name
        self.model = model
        self._client = client

    def create(self, data: Union[CreateSchemaType, dict]) -> ModelType:
        response = requests.post(f"{self.base_url}/{self.resource_name}", json=data, headers=self._client.headers)
        response.raise_for_status()
        return self.model(**response.json())

    def get(self, resource_id) -> ModelType:
        response = requests.get(f"{self.base_url}/{self.resource_name}/{resource_id}", headers=self._client.headers)
        response.raise_for_status()
        return self.model(**response.json())

    def get_multi(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        response = requests.get(f"{self.base_url}/{self.resource_name}",
                                params={"skip": skip, "limit": limit}, headers=self._client.headers)
        response.raise_for_status()
        return [self.model(**item) for item in response.json()]

    def update(self, resource_id: Any, data: UpdateSchemaType) -> ModelType:
        response = requests.put(f"{self.base_url}/{self.resource_name}/{resource_id}", json=data,
                                headers=self._client.headers)
        response.raise_for_status()
        return self.model(**response.json())

    def delete(self, resource_id) -> ModelType:
        response = requests.delete(f"{self.base_url}/{self.resource_name}/{resource_id}", headers=self._client.headers)
        response.raise_for_status()
        return self.model(**response.json())
