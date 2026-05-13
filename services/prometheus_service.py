import requests
import subprocess

from config import PROMETHEUS_URL


# =============================
# PROM QUERY
# =============================
def query_prometheus(query):

    try:

        response = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={"query": query},
            timeout=5
        )

        data = response.json()

        if (
            data["status"] == "success"
            and data["data"]["result"]
        ):

            return float(
                data["data"]["result"][0]["value"][1]
            )

        return 0

    except Exception as e:

        print(
            "Prometheus query error:",
            e,
            flush=True
        )

        return 0


# =============================
# CPU
# =============================
def get_cpu_usage():

    query = """
    100 - (
      avg(
        irate(
          node_cpu_seconds_total{mode="idle"}[5m]
        )
      ) * 100
    )
    """

    cpu = query_prometheus(query)

    print(
        f"CPU usage: {cpu}%",
        flush=True
    )

    return round(cpu, 2)


# =============================
# MEMORY
# =============================
def get_memory_usage():

    query = """
    (
      (
        node_memory_MemTotal_bytes
        -
        node_memory_MemAvailable_bytes
      )
      /
      node_memory_MemTotal_bytes
    ) * 100
    """

    memory = query_prometheus(query)

    return round(memory, 2)


# =============================
# DISK
# =============================
def get_disk_usage():

    query = """
    (
      (
        node_filesystem_size_bytes
        -
        node_filesystem_free_bytes
      )
      /
      node_filesystem_size_bytes
    ) * 100
    """

    disk = query_prometheus(query)

    return round(disk, 2)


# =============================
# RESTART COUNT
# =============================
def get_restart_count():

    query = """
    increase(
      kube_pod_container_status_restarts_total[1h]
    )
    """

    return query_prometheus(query)


# =============================
# TOP CPU PROCESS
# =============================
def get_top_cpu_process():

    try:

        cmd = (
            "ps -eo pid,comm,%cpu "
            "--sort=-%cpu | "
            "grep -vE 'ps|grep|awk|head|top|bash|sh' | "
            "head -1"
        )

        output = subprocess.getoutput(cmd)

        print(
            f"Top CPU process:\n{output}",
            flush=True
        )

        return output

    except Exception as e:

        print(
            "Process detection error:",
            e,
            flush=True
        )

        return "unknown"
