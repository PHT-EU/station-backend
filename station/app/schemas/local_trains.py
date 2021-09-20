from pydantic import BaseModel


class LocalTrainBase(BaseModel):
    name: str
    TrainID: int
