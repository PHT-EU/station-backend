
from sqlalchemy.orm import Session

from station.app.config import settings
from station.app.crud.base import CRUDBase
from station.app.models.local_trains import LocalTrainMasterImage
from station.app.schemas import local_trains as schemas
from station.clients.harbor_client import HarborClient


class CRUDLocalTrainMasterImage(
    CRUDBase[
        LocalTrainMasterImage,
        schemas.LocalTrainMasterImageCreate,
        schemas.LocalTrainMasterImageUpdate
    ]
):
    def get_by_image_id(self, db: Session, image_id: str):
        return db.query(LocalTrainMasterImage).filter(
            LocalTrainMasterImage.image_id == image_id
        ).first()

    def sync_with_harbor(self, db: Session):
        harbor_client = HarborClient(
            api_url=settings.config.registry.address,
            username=settings.config.registry.user,
            password=settings.config.registry.password,
        )
        images = harbor_client.get_master_images()
        for image in images:
            if self.get_by_image_id(db, image.image_id):
                continue
            master_image = LocalTrainMasterImage(
                registry=image.registry,
                image_id=image.image_id,
                group=image.group,
                artifact=image.artifact,
                tag=image.tag,
            )
            db.add(master_image)
            db.commit()


local_train_master_image = CRUDLocalTrainMasterImage(LocalTrainMasterImage)
