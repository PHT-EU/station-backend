import uuid

from station.app.db.session import engine, SessionLocal
from station.app.db.base import Base

from station.app.models import docker_trains


# TODO use alembic
def setup_db(dev=False):
    Base.metadata.create_all(bind=engine)
    if dev:
        seed_db_for_testing()


def reset_db(dev=False):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    if dev:
        seed_db_for_testing()


def seed_db_for_testing():
    session = SessionLocal()
    # create docker trains
    if not session.query(docker_trains.DockerTrain).all():

        dts = []
        for _ in range(3):
            dt = docker_trains.DockerTrain(
                train_id=str(uuid.uuid4()),

            )
            dts.append(dt)
        session.add_all(dts)
        session.commit()

        # Create states for the created trains
        states = []
        for dt in dts:
            state = docker_trains.DockerTrainState(
                train_id=dt.id,
                status="inactive"
            )
            states.append(state)

        session.add_all(states)

        config = docker_trains.DockerTrainConfig(
            name="default"
        )

        session.add(config)
        session.commit()

    session.close()


if __name__ == '__main__':
    # Base.metadata.drop_all(bind=engine)
    setup_db()
