from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Any, List, Union, Dict, Literal
from typing_extensions import Annotated


class DataSetBase(BaseModel):
    name: str
    data_type: str
    # TODO in models DataSet proposal_id is a integer -> desiding if what it has to be at the ende
    proposal_id: Optional[int] = None
    # proposal_id: Optional[Any]
    # TODO improve clarity of access definition
    access_path: Optional[str]


class DataSetCreate(DataSetBase):
    pass


class DataSetFhirInformation(DataSetBase):
    fhir_user: Optional[str]
    fhir_password: Optional[str]
    fhir_server_type: Optional[str]


class DataSetUpdate(DataSetBase):
    pass


class DataSetColumn(BaseModel):
    title: Optional[str]
    number_of_elements: Optional[int]


class DataSetUniqueColumn(DataSetColumn):
    type: Literal['unique']
    number_of_duplicates: Optional[int]


class DataSetEqualColumn(DataSetColumn):
    type: Literal['equal']
    value: Optional[str]


class DataSetCategoricalColumn(DataSetColumn):
    type: Literal['categorical']
    number_categories: Optional[int]
    most_frequent_element: Optional[Union[int, str]]
    frequency: Optional[int]


class DataSetNumericalColumn(DataSetColumn):
    type: Literal['numeric']
    mean: Optional[float]
    std: Optional[float]
    min: Optional[float]
    max: Optional[float]


class DataSetStatistics(BaseModel):
    n_items: Optional[int] = 0
    n_features: Optional[int] = 0
    column_information: Optional[List[Annotated[Union[DataSetCategoricalColumn,
                                                      DataSetNumericalColumn,
                                                      DataSetEqualColumn,
                                                      DataSetUniqueColumn],
                                                Field(discriminator='type')]]]

    class Config:
        orm_mode = True


class FigureData(BaseModel):
    layout: dict
    data: list


class DataSetFigure(BaseModel):
    fig_data: Optional[FigureData]


class DataSet(DataSetBase):
    id: Any
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
