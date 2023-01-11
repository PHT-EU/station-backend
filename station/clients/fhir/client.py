import os

import requests
from requests.auth import HTTPBasicAuth
from train_lib.clients.fhir import build_query_string
from train_lib.clients.fhir.fhir_client import BearerAuth


class FhirClient:
    def __init__(self, server_url: str = None, username: str = None, password: str = None, token: str = None,
                 server_type: str = None, disable_auth: bool = False):
        """
        Fhir client for station internal / health check / how many data points are in a fhir server
        The code in hear is mostly copied from the train libary fhir client .

        :param server_url: base url of the FHIR server to execute the query against
        :param username: username for use in basic auth authentication against the fhir server
        :param password: password for use in basic auth
        :param token: token to use for authenticating against a FHIR server using a bearer token
        :param server_type: the type of the server one of ["blaze", "hapi", "ibm"]
        """
        self.server_url = server_url if server_url else os.getenv("FHIR_ADDRESS")
        self.username = username if username else os.getenv("FHIR_USER")
        self.password = password if password else os.getenv("FHIR_PW")
        self.token = token if token else os.getenv("FHIR_TOKEN")
        self.server_type = server_type if server_type else os.getenv("FHIR_SERVER_TYPE")
        self.output_format = None
        # Check for correct initialization based on env vars or constructor parameters
        if not (self.username and self.password) and self.token:
            raise ValueError("Only one of username:pw or token auth can be selected")
        if not ((self.username and self.password) or self.token) and disable_auth:
            raise ValueError("Insufficient login information, either token or username and password need to be set.")
        if not self.server_url:
            raise ValueError("No FHIR server address available")

    def health_check(self):
        api_url = self._generate_api_url() + "/metadata"
        auth = self._generate_auth()

        response = {"status": None,
                    "date": None,
                    "name": None}
        try:
            # TODO remove verify false only for thesting becouse of verificaion problems with the ibm fhir server
            r = requests.get(api_url, auth=auth, verify=False)
            r.raise_for_status()
            r_json = r.json()

            # This is hear to make the response the same for all health check
            if r_json["status"] == "active":
                response["status"] = "healthy"
                response["date"] = r_json["date"]
        except requests.exceptions.ConnectionError as e:
            print(e)
            pass
        except requests.exceptions.HTTPError as e:
            print(e)
            pass
        return response

    def get_number_of_resource(self):
        api_url = self._generate_api_url() + "/Resource?_count=0"
        auth = self._generate_auth()
        r = requests.get(api_url, auth=auth, verify=False).json()
        return r["total"]

    def _generate_url(self, query: dict = None, query_string: str = None, return_format="json", limit=1000):
        """
        Generates the fhir search url to request from the server based. Either based on a previously given query string
        or based on a dictionary containing the query definition in the query.json file.

        :param query: dictionary containing the content of the query definition in the query.json file
        :param query_string: Predefined Fhir url query string to append to base server url
        :param return_format: the format in which the server should return the data.
        :param limit: the max number of entries in a paginated response
        :return: url string to perform a request against a fhir server with
        """
        url = self._generate_api_url() + "/"
        if query:
            url += build_query_string(query_dict=query)
        elif query_string:
            url += query_string
        else:
            raise ValueError("Either query dictionary or string need to be given")
        # add formatting configuration
        url += f"&_format={return_format}&_limit={limit}"

        return url

    def _generate_auth(self) -> requests.auth.AuthBase:
        """
        Generate authoriation for the request to be sent to server. Either based on a given bearer token or using basic
        auth with username and password.

        :return: Auth object to pass to a requests call.
        """
        if self.username and self.password:
            return HTTPBasicAuth(username=self.username, password=self.password)
        # TODO request token from id provider if configured
        elif self.token:
            return BearerAuth(token=self.token)

    def _generate_api_url(self) -> str:
        url = self.server_url
        if self.server_type == "ibm":
            url += "/fhir-server/api/v4"

        elif self.server_type in ["blaze", "hapi"]:
            url += "/fhir"

        else:
            raise ValueError(f"Unsupported FHIR server type: {self.server_type}")

        return url
