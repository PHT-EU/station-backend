import os
from cryptography.fernet import Fernet


class Settings:
    # todo define, load and store general station configuration
    def load_station_config_yaml(self):
        pass

    @staticmethod
    def get_fernet():
        # todo get key from config file
        key = os.getenv('FERNET_KEY').encode()
        print(key)
        if key is None:
            raise ValueError("No Fernet key provided")
        return Fernet(key)


class LogConfig:
    pass


settings = Settings()
