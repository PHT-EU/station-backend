from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from station.app.db.base_class import Base


class DockerTrainState(Base):
    __tablename__ = "docker_train_states"
    id = Column(Integer, primary_key=True, index=True)
    train_id = Column(Integer, ForeignKey("docker_trains.id"))
    # train = relationship("DockerTrain", backref=backref("state", uselist=False))
    last_execution = Column(DateTime, nullable=True)
    num_executions = Column(Integer, default=0)
    status = Column(String, default="inactive")
    central_status = Column(String, nullable=True)


class DockerTrainExecution(Base):
    __tablename__ = "docker_train_executions"
    id = Column(Integer, primary_key=True, index=True)
    train_id = Column(Integer, ForeignKey("docker_trains.id"))
    # train_state_id = Column(Integer, ForeignKey('docker_train_states.id'), nullable=True)
    start = Column(DateTime, default=datetime.now())
    end = Column(DateTime, nullable=True)
    airflow_dag_run = Column(String, nullable=True)
    config = Column(Integer, ForeignKey("docker_train_configs.id"), nullable=True)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=True)


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
    check_results = Column(Boolean, default=False)
    auto_execute = Column(Boolean, default=False)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=True)


class DockerTrain(Base):
    __tablename__ = "docker_trains"
    id = Column(Integer, primary_key=True, index=True)
    train_id = Column(String, unique=True, index=True)
    name = Column(String, nullable=True)
    proposal = Column(String, nullable=True)
    is_active = Column(Boolean, default=False)
    image_name = Column(String, nullable=True)
    type = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, nullable=True)
    config_id = Column(Integer, ForeignKey("docker_train_configs.id"), nullable=True)
    config = relationship("DockerTrainConfig", back_populates="trains")
    state = relationship("DockerTrainState", uselist=False, cascade="all, delete")
    executions = relationship("DockerTrainExecution", cascade="all, delete")
    num_participants = Column(Integer, nullable=True)
