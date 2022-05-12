from sqlalchemy import Column, Integer, JSON

from station.app.db.base_class import Base


class DataSetSummary(Base):
    __tablename__ = "datasets_summary"
    id = Column(Integer, primary_key=True, index=True)
    proposal_id = Column(Integer, default=0)
    count = Column(Integer, default=0)
    data_information = Column(JSON, default={})

