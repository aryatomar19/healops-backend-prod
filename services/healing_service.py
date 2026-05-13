import subprocess
import time

from services.prometheus_service import (
    get_cpu_usage,
    get_top_cpu_process
)

from utils.helpers import run_command


# =============================
# VERIFY CPU
# =============================
def verify_cpu_recovery(threshold=70):

    cpu = get_cpu_usage()

    return cpu <= threshold


# =============================
# VERIFY CONTAINER
# =============================
def verify_container_running(container_name="myapp"):

    try:

        cmd = (
            f"/usr/bin/docker ps "
            f'--filter "name={container_name}" '
            "--format '{{.Names}}'"
        )

        output = subprocess.getoutput(cmd)

        return container_name in output

    except Exception as e:

        print(
            "Container verification error:",
            e,
            flush=True
        )

        return False


# =============================
# SAFE CPU REMEDIATION
# =============================
def safe_cpu_remediation():

    try:

        top_process = get_top_cpu_process()

        print(
            f"Root cause process:\n{top_process}",
            flush=True
        )

        if "yes" in top_process.lower():

            run_command(
                "pkill -f yes"
            )

            return (
                "demo CPU stress process killed"
            )

        elif "java" in top_process.lower():

            run_command(
                "/usr/bin/docker restart myapp"
            )

            return (
                "java process detected | container restarted"
            )

        elif "python" in top_process.lower():

            run_command(
                "/usr/bin/docker restart myapp"
            )

            return (
                "python process detected | container restarted"
            )

        elif "node" in top_process.lower():

            run_command(
                "/usr/bin/docker restart myapp"
            )

            return (
                "node process detected | container restarted"
            )

        elif "myapp" in top_process.lower():

            run_command(
                "/usr/bin/docker restart myapp"
            )

            return (
                "application process detected | container restarted"
            )

        else:

            return (
                f"manual intervention required | unknown process: {top_process}"
            )

    except Exception as e:

        print(
            "Safe remediation error:",
            e,
            flush=True
        )

        return "remediation failed"
