import os
import s3fs


def get_filesystem(minio_url: str = None, access_key: str = None, secret_key: str = None) -> s3fs.S3FileSystem:
    """
    Returns filesystem object to access files saved in minio
    :param minio_url: Url to the minio server
    :param access_key: Minio access key
    :param secret_key: Minio secret key
    :return: S3 Filesystem
    """
    if minio_url is None:
        minio_host = os.getenv("MINIO_HOST")
        minio_port = os.getenv("MINIO_PORT")
        minio_url = minio_host + ":" + minio_port

    assert minio_url is not None, "MINIO_URL is not set"

    if access_key is None:
        access_key = os.getenv("MINIO_ACCESS_KEY")

    if secret_key is None:
        secret_key = os.getenv("MINIO_SECRET_KEY")

    fs = s3fs.S3FileSystem(anon=False,
                           key=access_key,
                           secret=secret_key,
                           use_ssl=True,
                           client_kwargs={'endpoint_url': f'http://{minio_url}'})

    return fs


def get_file(path):
    """
    Returns file independent of saved location (local or on minio server)
    :param path: Path to file
    :return: File
    """

    if path.startswith("s3://"):
        fs = get_filesystem()
        # get file
        try:
            file = fs.open(path[5:])
            return file
        except:
            raise FileNotFoundError
    else:
        try:
            file = open(path)
            return file
        except:
            raise FileNotFoundError
