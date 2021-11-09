import requests
import os
from dotenv import find_dotenv, load_dotenv
from requests.auth import HTTPBasicAuth


class AirflowClient:
    def __init__(self, airflow_api_url: str = None, airflow_user: str = "admin", airflow_password: str = "admin"):
        self.airflow_url = airflow_api_url if airflow_api_url else os.getenv("AIRFLOW_API_URL")
        self.auth = HTTPBasicAuth(airflow_user, airflow_password)

    def trigger_dag(self, dag_id: str, config: dict = None) -> str:
        """
        Execute a dag with the given configuration

        :param dag_id: string identifier of the dag i.e. 'run_train'
        :param config: dictionary containing configuration values passed to the dag
        :return:
        """

        # create default empty config
        config_msg = {
            "conf": {},
        }
        if config:
            config_msg["conf"] = config

        url = self.airflow_url + f"dags/{dag_id}/dagRuns"
        r = requests.post(url=url, auth=self.auth, json=config_msg)
        print(r.json())
        r.raise_for_status()
        return r.json()["dag_run_id"]

    def get_dag_run(self, dag_id: str):
        pass

    def get_all_dag_runs(self, dag_id: str):
        url = self.airflow_url + f"dags/{dag_id}/dagRuns"
        r = requests.get(url=url, auth=self.auth)
        print(r.json())
        r.raise_for_status()

        return r.json()

    # TODO create arguments for individual connection options
    def create_connection(self, connection_dict: dict):
        url = self.airflow_url + "connections"
        r = requests.post(url=url, json=connection_dict)
        print(r.json())
        r.raise_for_status()

    def health_check(self)-> dict:
        """

        @return: dict: Airflow Status
        """
        url = self.airflow_url + "health"
        r = requests.get(url=url)
        return r.json()

    def get_run_information(self, dag_id: str, run_id: str)-> dict:
        """
        requests the information about a dag run state from airflow.
        @param dag_id: ID of the dag (e.g. "run_train" or "run_local"
        @param run_id: Airflow ID of the run ( has the form of e.g. " "manual__2021-11-09T14:12:24.622670+00:00")
        @return: dict: information about the run
        """
        url = self.airflow_url + f"dags/{dag_id}/dagRuns/{run_id}"
        r = requests.get(url=url, auth=self.auth)
        r.raise_for_status()
        return r.json()

airflow_client = AirflowClient()

if __name__ == '__main__':
    load_dotenv(find_dotenv())
    client = AirflowClient()

    test_config = {

    }

    dag_runs = client.get_all_dag_runs("run_train")
    dag_run_id = client.trigger_dag("run_train")
