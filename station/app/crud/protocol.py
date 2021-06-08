from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
import os

from station.app.models.protocol import BroadCastKeys


def get_signing_key_from_key_broadcast(db: Session, train_id: int, station_id: int, iteration: int) -> str:
    broad_cast: BroadCastKeys = db.query(BroadCastKeys).filter(
        BroadCastKeys.iteration == iteration,
        BroadCastKeys.station_id == station_id,
        BroadCastKeys.train_id == train_id
    ).first()
    print(broad_cast.signing_key)
    return broad_cast.signing_key

