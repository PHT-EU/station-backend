import docker
import time


class DockerClient:
    """
    Get Information for the local docker instances
    """

    def __init__(self):
        self.client = docker.APIClient(base_url='unix://var/run/docker.sock')
        self.container_statuses = []
        self.containers = self.client.containers()
        self.sleep_time_for_cpu_usage_check = 3

    def get_stats_all(self):
        container_statuses_start = self._get_all_stats_all_container()
        time.sleep(self.sleep_time_for_cpu_usage_check)
        container_statuses_end = self._get_all_stats_all_container()
        return self._calculate_usage_statistics(container_statuses_start, container_statuses_end)

    def _get_all_stats_all_container(self):
        """
        returns all the stats for all containers using the APIClient
        """
        container_statuses = []
        for container in self.containers:
            container_statuses.append(self.client.stats(container["Id"], stream=False))
        return container_statuses

    def _get_all_stats_container(self, container_id):
        return self.client.stats(container_id, stream=True)

    def _calculate_usage_statistics(self, start_measurements, end_measurements):
        stats = []
        for i in range(len(start_measurements)):
            cpu_usage = self._calculate_cpu_usage(start_measurements[i],end_measurements[i])
            name_container = start_measurements[i]["name"]
            memory_usage = start_measurements[i]["memory_stats"]["usage"]/start_measurements[i]["memory_stats"]["limit"]
            status_dict = {"cpu_percent": cpu_usage, "memory_percent": memory_usage, "name": name_container}
            stats.append(status_dict)
        return stats

    def _calculate_cpu_usage(self, start_measurement, end_measurement):
        cpu_cycles_container = start_measurement["cpu_stats"]["cpu_usage"]["total_usage"] - \
                               end_measurement["cpu_stats"]["cpu_usage"]["total_usage"]
        total_cycles = start_measurement["cpu_stats"]["system_cpu_usage"] - end_measurement["cpu_stats"][
            "system_cpu_usage"]
        return cpu_cycles_container / total_cycles


dockerClient = DockerClient()
