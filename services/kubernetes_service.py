import subprocess


# =============================
# SCALE DEPLOYMENT
# =============================
def scale_kubernetes_deployment(replicas=3):

    try:

        cmd = (
            f"kubectl scale deployment myapp "
            f"--replicas={replicas}"
        )

        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True
        )

        print(
            f"K8S SCALE: {result.stdout}",
            flush=True
        )

    except Exception as e:

        print(
            "Kubernetes scale error:",
            e,
            flush=True
        )


# =============================
# RESTART DEPLOYMENT
# =============================
def restart_kubernetes_deployment():

    try:

        cmd = (
            "kubectl rollout restart "
            "deployment myapp"
        )

        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True
        )

        print(
            f"K8S RESTART: {result.stdout}",
            flush=True
        )

    except Exception as e:

        print(
            "Kubernetes restart error:",
            e,
            flush=True
        )


# =============================
# VERIFY DEPLOYMENT
# =============================
def verify_kubernetes_deployment():

    try:

        cmd = (
            "kubectl get deployment myapp "
            "-o jsonpath='{.status.availableReplicas}'"
        )

        output = subprocess.getoutput(cmd)

        replicas = int(
            output.replace("'", "") or 0
        )

        return replicas > 0

    except Exception as e:

        print(
            "Kubernetes verification error:",
            e,
            flush=True
        )

        return False
