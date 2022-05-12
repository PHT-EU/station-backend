from pydantic import BaseModel
from typing import Optional, List, Union


class NumericalData(BaseModel):
    attribute_name: Optional[str]
    mean: Optional[float]
    min: Optional[float]
    max: Optional[float]


class CategoricalCount(BaseModel):
    category_value: Optional[str]
    count: Optional[int]


class CategoricalData(BaseModel):
    attribute_name: Optional[str]
    value_counts: Optional[List[CategoricalCount]]


class CategoricalDataLocal(CategoricalData):
    most_frequent_element: Optional[Union[str, int]]
    frequency: Optional[int]


class StructuredData(BaseModel):
    data_summary: Optional[List[Union[NumericalData, CategoricalData]]]


class UnstructuredData(BaseModel):
    target_counts: Optional[CategoricalCount]
    mean_size: Optional[float]


class DataSetSummary(BaseModel):
    proposal_id: Optional[int]
    count: Optional[int]
    information: Optional[Union[StructuredData, UnstructuredData]]


class SummaryCreate(DataSetSummary):
    pass


class SummaryUpdate(DataSetSummary):
    pass