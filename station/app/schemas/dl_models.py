from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TorchModelBase(BaseModel):
    model_id: Optional[str] = None


class TorchModelCreate(TorchModelBase):
    pass


class TorchModelUpdate(TorchModelBase):
    pass


class TorchModelCheckPoint(BaseModel):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    checkpoint: Optional[bytes]

    class Config:
        orm_mode = True


class TorchModel(TorchModelBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class DLModelBase(BaseModel):
    model_type: str
    model_name: str
    model_src: str
    train_id: Optional[str] = None


class DLModelCreate(DLModelBase):
    pass


class DLModelUpdate(DLModelBase):
    pass


class DLModel(DLModelBase):
    id: int
    model_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
