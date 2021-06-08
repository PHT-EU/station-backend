from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, LargeBinary, Float, BigInteger
from sqlalchemy.orm import relationship, backref
from datetime import datetime

from station.app.db.base_class import Base


class DockerTrainConfig(Base):
    __tablename__ = "docker_train_configs"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, nullable=True)
    config_json = Column(String, nullable=True)
    trains = relationship("DockerTrain")


class DockerTrain(Base):
    __tablename__ = "docker_trains"
    id = Column(Integer, primary_key=True, index=True)
    train_id = Column(String)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, nullable=True)
    proposal_id = Column(Integer, default=0)
    config_id = Column(Integer, ForeignKey("docker_train_configs.id"), nullable=True)
    config = relationship("DockerTrainConfig", back_populates="trains")
    is_active = Column(Boolean, default=False)
    last_execution = Column(String, nullable=True)


# TODO store train executions in separate table with reference to airflow run id




