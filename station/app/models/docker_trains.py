from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from station.app.db.base_class import Base


class DockerTrainState(Base):
    __tablename__ = "docker_train_states"
    id = Column(Integer, primary_key=True, index=True)
    train_id = Column(Integer, ForeignKey('docker_trains.id'))
    last_execution = Column(DateTime, nullable=True)
    num_executions = Column(Integer, default=0)
    status = Column(String, default="inactive")


class DockerTrainExecution(Base):
    __tablename__ = "docker_train_executions"
    id = Column(Integer, primary_key=True, index=True)
    train_id = Column(Integer, ForeignKey('docker_trains.id'))
    start = Column(DateTime, default=datetime.now())
    end = Column(DateTime, nullable=True)
    airflow_dag_run = Column(String, nullable=True)


class DockerTrainConfig(Base):
    __tablename__ = "docker_train_configs"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, nullable=True)
    airflow_config = Column(JSON, nullable=True)
    trains = relationship("DockerTrain")
    cpu_requirements = Column(JSON, nullable=True)
    gpu_requirements = Column(JSON, nullable=True)
    auto_execute = Column(Boolean, default=False)


class DockerTrain(Base):
    __tablename__ = "docker_trains"
    id = Column(Integer, primary_key=True, index=True)
    train_id = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, nullable=True)
    proposal_id = Column(Integer, default=0)
    config_id = Column(Integer, ForeignKey("docker_train_configs.id"), nullable=True)
    config = relationship("DockerTrainConfig", back_populates="trains")
    is_active = Column(Boolean, default=False)
    state = relationship("DockerTrainState")
    executions = relationship("DockerTrainExecution")
