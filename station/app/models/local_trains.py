from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, LargeBinary, Float, BigInteger, JSON
from sqlalchemy.orm import relationship, backref
from datetime import datetime
import uuid
from station.app.db.base_class import Base


class LocalTrainState(Base):
    __tablename__ = "local_train_states"
    id = Column(Integer, primary_key=True, index=True)
    train_id = Column(Integer, ForeignKey('local_trains.id'))
    last_execution = Column(DateTime, nullable=True)
    num_executions = Column(Integer, default=0)
    status = Column(String, default="inactive")


class LocalTrainExecution(Base):
    __tablename__ = "local_train_executions"
    id = Column(Integer, primary_key=True, index=True)
    train_id = Column(String, ForeignKey('local_trains.train_id'))
    airflow_dag_run = Column(String, nullable=True, unique=True)
    start = Column(DateTime, default=datetime.now())
    end = Column(DateTime, nullable=True)



class LocalTrain(Base):
    __tablename__ = "local_trains"
    id = Column(Integer, primary_key=True, index=True)
    train_id = Column(String, unique=True)
    train_name = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, nullable=True)
    airflow_config_json = Column(JSON, default=None , nullable=True)
    #config_id = Column(Integer, ForeignKey("local_train_configs.id"), nullable=True)
    #config = relationship("LocalTrainConfig", back_populates="trains")
    is_active = Column(Boolean, default=False)
    #state = relationship("LocalTrainState")
    #executions = relationship("LocalTrainExecution")


'''
class LocalTrainConfig(Base):
    __tablename__ = "Local_train_configs"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, nullable=True)
    airflow_config_json = Column(JSON, nullable=True)
    trains = relationship("LocalTrain")
    cpu_requirements = Column(JSON, nullable=True)
    gpu_requirements = Column(JSON, nullable=True)
    auto_execute = Column(Boolean, default=False)
'''

