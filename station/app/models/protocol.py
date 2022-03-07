from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from datetime import datetime

from station.app.db.base_class import Base


class BroadCastKeys(Base):
    __tablename__ = "key_broadcasts"
    id = Column(Integer, primary_key=True, index=True)
    received_at = Column(DateTime, default=datetime.now())
    iteration = Column(Integer)
    station_id = Column(Integer)
    signing_key = Column(String)
    sharing_key = Column(String)
    key_signature = Column(String, nullable=True)


class Cypher(Base):
    __tablename__ = "cyphers"
    # __table_args__ = (
    #     # this can be db.PrimaryKeyConstraint if you want it to be a primary key
    #     UniqueConstraint('train_id', 'iteration'),
    # )
    id = Column(Integer, primary_key=True, index=True)
    received_at = Column(DateTime, default=datetime.now())
    iteration = Column(Integer)
    station_id = Column(Integer)
    cypher = Column(String)
