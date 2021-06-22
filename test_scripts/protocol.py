from typing import Any

import requests

STATION_1_URL = "http://localhost:8001/api/trains/"
STATION_2_URL = "http://localhost:8002/api/trains/"
STATION_3_URL = "http://localhost:8003/api/trains/"

STATION_URLS = [STATION_1_URL, STATION_2_URL, STATION_3_URL]

TRAIN_ID = 1

def add_train(train_id: Any):
    for i, url in enumerate(STATION_URLS):
        r = requests.post(url + f"federated/{train_id}")
        print(r)
        print(r.json())


def execute_protocol(train_id: Any):
    for i, url in enumerate(STATION_URLS):
        r = requests.post(url + f"{train_id}/protocol")
        print(r)
        print(r.json())


if __name__ == '__main__':
    #add_train(TRAIN_ID)
    execute_protocol(TRAIN_ID)
