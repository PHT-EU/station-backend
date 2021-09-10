from pydantic import BaseModel


class LocalTrainBase(BaseModel):
    TrainID: str
