from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Any, List, Union, Dict, Literal
from typing_extensions import Annotated
from enum import Enum


class StorageType(Enum):
    """
    Enum for storage types
    """
    LOCAL = "local"
    MINIO = "minio"
    DB = "db"


class DataType(Enum):
    """
    Enum for data types
    """
    IMAGE = "image"
    GENOME = "genome"
    FHIR = "fhir"
    CSV = "csv"
    STRUCTURED = "structured"
    UNSTRUCTURED = "unstructured"
    HYBRID = "hybrid"


class DataSetBase(BaseModel):
    name: str
    data_type: Optional[DataType] = None
    storage_type: Optional[StorageType] = None
    proposal_id: Optional[str] = None
    access_path: Optional[str] = None

    class Config:
        use_enum_values = True


class DataSetCreate(DataSetBase):
    pass


class DataSetUpdate(DataSetBase):
    pass


class MinioFile(BaseModel):
    file_name: str
    full_path: Optional[str] = None
    size: Optional[int] = None
    updated_at: Optional[datetime] = None


class FigureData(BaseModel):
    layout: dict
    data: list


class DataSetFigure(BaseModel):
    fig_data: Optional[FigureData]


class DataSetColumn(BaseModel):
    title: Optional[str]
    not_na_elements: Optional[int]
    figure: Optional[DataSetFigure]


class DataSetUniqueColumn(DataSetColumn):
    type: Literal['unique']
    number_of_duplicates: Optional[int]


class DataSetEqualColumn(DataSetColumn):
    type: Literal['equal']
    value: Optional[str]


class DataSetCategoricalColumn(DataSetColumn):
    type: Literal['categorical']
    number_categories: Optional[int]
    value_counts: Optional[Dict[str, int]]
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


class DataSet(DataSetBase):
    id: Any
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
