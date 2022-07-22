import uuid

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, JSON
from datetime import datetime

from sqlalchemy.dialects.postgresql import UUID

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
    train_id = Column(Integer, ForeignKey('local_trains.id'))
    airflow_dag_run = Column(String, nullable=True, unique=True)
    start = Column(DateTime, default=datetime.now())
    end = Column(DateTime, nullable=True)


class LocalTrainMasterImage(Base):
    __tablename__ = "local_train_master_images"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    registry = Column(String, nullable=True)
    group = Column(String, nullable=True)
    artifact = Column(String, nullable=True)
    tag = Column(String, default="latest")
    image_id = Column(String, nullable=True, unique=True)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, nullable=True)


class LocalTrainFile(Base):
    __tablename__ = "local_train_files"
    id = Column(Integer, primary_key=True, index=True)
    train_id = Column(Integer, ForeignKey('local_trains.id'))
    access_path = Column(String)
    file_name = Column(String)
    file_size = Column(Integer, nullable=True)
    file_type = Column(String, nullable=True)


class LocalTrain(Base):
    __tablename__ = "local_trains"
    id = Column(Integer, primary_key=True, index=True)
    train_id = Column(String, unique=True)
    train_name = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, nullable=True)
    airflow_config_json = Column(JSON, default=None, nullable=True)
    # config_id = Column(Integer, ForeignKey("local_train_configs.id"), nullable=True)
    # config = relationship("LocalTrainConfig", back_populates="trains")
    is_active = Column(Boolean, default=False)
    # state = relationship("LocalTrainState")
    # executions = relationship("LocalTrainExecution")


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
