from typing import List

from station.app.models import local_trains as lt_models
from station.app.schemas import local_trains as lt_schema
from station.app.schemas.datasets import MinioFile


def update_configuration_status(local_train: lt_models.LocalTrain, files: List[MinioFile] = None) -> str:
    """
    Update the configuration status of a local train
    """

    state = local_train.state.configuration_state

    if local_train.master_image_id or local_train.custom_image:
        state = lt_schema.LocalTrainConfigurationStep.image_configured.value
    if files:
        state = lt_schema.LocalTrainConfigurationStep.files_uploaded.value
    if local_train.entrypoint and local_train.master_image_id:
        state = lt_schema.LocalTrainConfigurationStep.image_configured.value
    if local_train.dataset_id:
        state = lt_schema.LocalTrainConfigurationStep.dataset_selected.value

    return state
