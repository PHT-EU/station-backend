from station.app.db.session import engine
from station.app.db.base import Base


# TODO use alembic
def setup_db():
    Base.metadata.create_all(bind=engine)


def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


if __name__ == '__main__':
    # Base.metadata.drop_all(bind=engine)
    setup_db()
