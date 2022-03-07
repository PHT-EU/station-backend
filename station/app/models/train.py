from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, BigInteger, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4

from station.app.db.base_class import Base


class Train(Base):
    __tablename__ = "trains"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, default=str(uuid4()), unique=True)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=False)
    proposal_id = Column(Integer, nullable=True)
    state = relationship("TrainState", uselist=False, backref="trains")
    token = Column(String, nullable=True)
    #model = relationship("DLModel", uselist=False, backref="trains")
    dataset_id = Column(Integer, ForeignKey('datasets.id'), nullable=True)
    #dataset = relationship("DataSet", back_populates="trains")
    config_id = Column(Integer, ForeignKey("federated_train_configs.id"), nullable=True)
    config = relationship("FederatedTrainConfig", back_populates="trains")


class TrainState(Base):
    __tablename__ = 'train_states'
    id = Column(Integer, primary_key=True, index=True)
    train_id = Column(Integer, ForeignKey('trains.id'))
    iteration = Column(Integer, default=0)
    round = Column(Integer, default=0)
    updated_at = Column(DateTime, nullable=True)
    signing_key = Column(String, nullable=True)
    sharing_key = Column(String, nullable=True)
    seed = Column(BigInteger, nullable=True)
    key_broadcast = Column(String, nullable=True)


class FederatedTrainConfig(Base):
    __tablename__ = 'federated_train_configs'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, nullable=True)
    airflow_config_json = Column(JSON, nullable=True)
    trains = relationship("Train")

# todo add train config
