from sqlalchemy import Column, Integer, Float, String, ForeignKey
from sqlalchemy.orm import relationship

from station.app.db.base_class import Base


class DataSetSummary(Base):
    __tablename__ = "datasets_summary"
    id = Column(Integer, primary_key=True, index=True)
    proposal_id = Column(Integer, default=0)
    count = Column(Integer, default=0)
    structured_data = Column(Integer, ForeignKey('structured_data.id'))
    unstructured_data = Column(Integer, ForeignKey('unstructured_data.id'))


class StructuredData(Base):
    __tablename__ = "structured_data"
    id = Column(Integer, primary_key=True, index=True)
    columns = relationship("StructuredDataColumn")


class StructuredDataColumn(Base):
    __tablename__ = "structured_data_column"
    id = Column(Integer, primary_key=True, index=True)
    data_id = Column(Integer, ForeignKey('structured_data.id'))
    numerical_attributes = relationship("NumericalColumn")
    categorical_attributes = relationship("CategoricalColumn")


class NumericalColumn(Base):
    __tablename__ = "numerical_data_column"
    id = Column(Integer, primary_key=True, index=True)
    summary_id = Column(Integer, ForeignKey('structured_data_column.id'))
    name = Column(String, default="")
    mean = Column(Float, default=0.)
    min = Column(Float, default=0.)
    max = Column(Float, default=0.)


class ValueCounts(Base):
    __tablename__ = "value_counts"
    id = Column(Integer, primary_key=True, index=True)
    column_id = Column(Integer, ForeignKey('categorical_data_column.id'))
    value_int = Column(Integer, nullable=True)
    value_str = Column(String, nullable=True)
    count = Column(Integer, default=0)


class CategoricalColumn(Base):
    __tablename__ = "categorical_data_column"
    id = Column(Integer, primary_key=True, index=True)
    summary_id = Column(Integer, ForeignKey('structured_data_column.id'))
    name = Column(String, default="")
    value_counts = relationship("ValueCounts")
    most_frequent_element = Column(String, default="")
    frequency = Column(Integer, default=0)


class UnstructuredData(Base):
    __tablename__ = "unstructured_data"
    id = Column(Integer, primary_key=True, index=True)
    mean_size = Column(Float, default=0)
