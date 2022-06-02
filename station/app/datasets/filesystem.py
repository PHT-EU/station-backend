import os
import s3fs
from station.app.config import settings


def get_s3_filesystem(minio_url: str = None, access_key: str = None, secret_key: str = None) -> s3fs.S3FileSystem:
    """
    Returns filesystem object to access files saved in minio
    :param minio_url: Url to the minio server
    :param access_key: Minio access key
    :param secret_key: Minio secret key
    :return: S3 Filesystem
    """
    if minio_url is None:
        minio_host = settings.config.minio.host
        minio_port = settings.config.minio.port
        minio_url = minio_host + ":" + str(minio_port)

    assert minio_url is not None, "MINIO_URL is not set"

    if access_key is None:
        access_key = settings.config.minio.access_key

    if secret_key is None:
        secret_key = settings.config.minio.secret_key.get_secret_value()

    fs = s3fs.S3FileSystem(anon=False,
                           key=access_key,
                           secret=secret_key,
                           use_ssl=True,
                           client_kwargs={'endpoint_url': f'http://{minio_url}/'})

    return fs


def get_file(path, storage_type):
    """
    Returns file independent of saved location (local or on minio server)
    :param path: Path to file
    :return: File
    """
    # access file on minio server
    if storage_type == "minio":
        fs = get_s3_filesystem()
        # get file
        try:
            file = fs.open(path)
            return file
        except:
            raise FileNotFoundError
    elif storage_type == "local":
        try:
            path = os.path.join(settings.config.station_data_dir, path)
            file = open(path)
            return file
        except:
            raise FileNotFoundError
    else:
        raise NotImplementedError
