import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from station.app.db.base_class import Base


class LocalTrainState(Base):
    __tablename__ = "local_train_states"
    id = Column(Integer, primary_key=True, index=True)
    train_id = Column(UUID(as_uuid=True), ForeignKey('local_trains.id'))
    last_execution = Column(DateTime, nullable=True)
    num_executions = Column(Integer, default=0)
    status = Column(String, default="inactive")
    configuration_state = Column(String, default="initialized")


class LocalTrainExecution(Base):
    __tablename__ = "local_train_executions"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    train_id = Column(UUID, ForeignKey('local_trains.id'))
    airflow_dag_run = Column(String, nullable=True, unique=True)
    config_id = Column(Integer, ForeignKey('docker_train_configs.id'), nullable=True)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey('datasets.id'), nullable=True)
    start = Column(DateTime, default=datetime.now())
    finish = Column(DateTime, nullable=True)


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


class LocalTrain(Base):
    __tablename__ = "local_trains"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    name = Column(String, nullable=True)
    master_image_id = Column(UUID(as_uuid=True), ForeignKey('local_train_master_images.id'), nullable=True)
    entrypoint = Column(String, nullable=True)
    custom_image = Column(String, nullable=True)
    command = Column(String, nullable=True)
    command_args = Column(String, nullable=True)
    fhir_query = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, nullable=True)
    state = relationship("LocalTrainState", cascade="all,delete", uselist=False)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey('datasets.id'), nullable=True)
    config_id = Column(UUID(as_uuid=True), ForeignKey('local_train_configs.id'), nullable=True)


class LocalTrainConfig(Base):
    __tablename__ = "local_train_configs"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    name = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, nullable=True)
    airflow_config_json = Column(JSON, nullable=True)
    trains = relationship("LocalTrain")
    cpu_requirements = Column(JSON, nullable=True)
    gpu_requirements = Column(JSON, nullable=True)
    auto_execute = Column(Boolean, default=False)
