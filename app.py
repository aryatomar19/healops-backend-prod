from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import time
import psycopg2
import requests

from psycopg2.extras import RealDictCursor

# =============================
# JWT IMPORTS
# =============================
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity
)

import bcrypt

app = Flask(__name__)

CORS(app)

# =============================
# JWT CONFIG
# =============================
app.config["JWT_SECRET_KEY"] = "healops-secret-key"

jwt = JWTManager(app)

# =============================
# POSTGRES CONNECTION
# =============================
db = psycopg2.connect(
    host="database-1.c5ecywggqf0l.ap-south-1.rds.amazonaws.com",
    database="healops",
    user="postgres",
    password="arya007varth"
)

# =============================
# CONFIG
# =============================
COOLDOWN = 30

last_action_time = {}

# =============================
# ACTIVE ALERTS
# =============================
active_alerts = []

# =============================
# PROMETHEUS CONFIG
# =============================
PROMETHEUS_URL = "http://localhost:9090"


# =============================
# RUN COMMAND
# =============================
def run_command(cmd):

    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True
    )

    print("\nCMD:", cmd, flush=True)

    print(
        "STDOUT:",
        result.stdout.strip(),
        flush=True
    )

    print(
        "STDERR:",
        result.stderr.strip(),
        flush=True
    )

    print(
        "RETURN CODE:",
        result.returncode,
        flush=True
    )

    return result.returncode


# =============================
# WAIT HELPER
# =============================
def wait_before_fix(seconds):

    print(
        f"Waiting {seconds}s before fix",
        flush=True
    )

    time.sleep(seconds)


# =============================
# GET CPU USAGE
# =============================
def get_cpu_usage():

    try:

        output = subprocess.getoutput(
            "top -bn1 | grep 'Cpu(s)'"
        )

        idle = float(
            output.split("id,")[0].split()[-1]
        )

        cpu = 100 - idle

        print(
            f"CPU usage: {cpu}%",
            flush=True
        )

        return cpu

    except Exception as e:

        print(
            "CPU read error:",
            e,
            flush=True
        )

        return 0


# =============================
# GET TOP CPU PROCESS
# =============================
def get_top_cpu_process():

    try:

        cmd = (
            "ps -eo pid,comm,%cpu "
            "--sort=-%cpu | head -2"
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


# =============================
# KILL HIGH CPU PROCESSES
# =============================
def kill_high_cpu_processes():

    print(
        "Killing high CPU processes",
        flush=True
    )

    run_command("pkill -9 -f yes")

    run_command(
        "ps -eo pid,%cpu --sort=-%cpu | "
        "awk 'NR<=6 && NR>1 {print $1}' | "
        "xargs -r kill -9"
    )


# =============================
# KUBERNETES HELPERS
# =============================
def scale_kubernetes_deployment(replicas):

    print(
        f"Scaling Kubernetes deployment to {replicas}",
        flush=True
    )

    run_command(
        f"kubectl scale deployment myapp "
        f"--replicas={replicas}"
    )


def restart_kubernetes_deployment():

    print(
        "Restarting Kubernetes deployment",
        flush=True
    )

    run_command(
        "kubectl rollout restart deployment myapp"
    )


# =============================
# PROMETHEUS QUERY
# =============================
def query_prometheus(query):

    try:

        response = requests.get(

            f"{PROMETHEUS_URL}/api/v1/query",

            params={
                "query": query
            },

            timeout=5
        )

        data = response.json()

        result = data.get(
            "data",
            {}
        ).get(
            "result",
            []
        )

        if not result:

            return 0

        value = float(
            result[0]["value"][1]
        )

        return round(value, 2)

    except Exception as e:

        print(
            "Prometheus query error:",
            e,
            flush=True
        )

        return 0


# =============================
# GET RUNNING PODS
# =============================
def get_running_pods():

    try:

        cmd = (
            "kubectl get pods --no-headers "
            "| grep Running | wc -l"
        )

        output = subprocess.getoutput(cmd)

        return int(output)

    except Exception as e:

        print(
            "Pod count error:",
            e,
            flush=True
        )

        return 0


# =============================
# GET RESTART COUNT
# =============================
def get_restart_count():

    try:

        cmd = (
            "kubectl get pods --no-headers "
            "-o custom-columns=':status.containerStatuses[0].restartCount'"
        )

        output = subprocess.getoutput(cmd)

        counts = [

            int(x)

            for x in output.splitlines()

            if x.strip().isdigit()
        ]

        return sum(counts)

    except Exception as e:

        print(
            "Restart count error:",
            e,
            flush=True
        )

        return 0


# =============================
# SAVE ACTION TO POSTGRES
# =============================
def save_action(alert_name, action, status):

    try:

        cursor = db.cursor()

        query = """
        INSERT INTO action_history
        (
            event_time,
            alert_name,
            action_taken,
            status
        )
        VALUES (%s, %s, %s, %s)
        """

        values = (
            time.strftime("%Y-%m-%d %H:%M:%S"),
            alert_name,
            action,
            status
        )

        cursor.execute(query, values)

        db.commit()

        print(
            "Action stored in PostgreSQL",
            flush=True
        )

    except Exception as e:

        print(
            "PostgreSQL insert error:",
            e,
            flush=True
        )


# =============================
# HOME
# =============================
@app.route('/')
def home():

    return "HealOps Backend Running"


# =============================
# REGISTER
# =============================
@app.route('/register', methods=['POST'])
def register():

    try:

        data = request.json

        username = data.get("username")

        email = data.get("email")

        password = data.get("password")

        if not username or not email or not password:

            return jsonify({
                "error": "Missing fields"
            }), 400

        cursor = db.cursor()

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE email=%s
            """,
            (email,)
        )

        existing = cursor.fetchone()

        if existing:

            return jsonify({
                "error": "User already exists"
            }), 400

        password_hash = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        cursor.execute(
            """
            INSERT INTO users
            (
                username,
                email,
                password_hash
            )
            VALUES (%s, %s, %s)
            """,
            (
                username,
                email,
                password_hash
            )
        )

        db.commit()

        return jsonify({
            "message": "User registered successfully"
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# =============================
# LOGIN
# =============================
@app.route('/login', methods=['POST'])
def login():

    try:

        data = request.json

        email = data.get("email")

        password = data.get("password")

        cursor = db.cursor(
            cursor_factory=RealDictCursor
        )

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE email=%s
            """,
            (email,)
        )

        user = cursor.fetchone()

        if not user:

            return jsonify({
                "error": "Invalid credentials"
            }), 401

        password_valid = bcrypt.checkpw(
            password.encode('utf-8'),
            user["password_hash"].encode('utf-8')
        )

        if not password_valid:

            return jsonify({
                "error": "Invalid credentials"
            }), 401

        access_token = create_access_token(
            identity=user["email"]
        )

        return jsonify({

            "token": access_token,

            "user": {

                "id": user["id"],

                "username": user["username"],

                "email": user["email"]
            }
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# =============================
# CURRENT USER
# =============================
@app.route('/me')
@jwt_required()
def me():

    current_user = get_jwt_identity()

    return jsonify({
        "email": current_user
    })


# =============================
# WEBHOOK
# =============================
@app.route('/webhook', methods=['POST'])
def webhook():

    try:

        data = request.json

        print(
            "\nAlert received:",
            data,
            flush=True
        )

        if not data or 'alerts' not in data:

            return jsonify({
                "error": "Invalid payload"
            }), 400

        alert = data['alerts'][0]

        alert_name = (
            alert['labels'].get('alertname')
        )

        severity = (
            alert['labels'].get(
                'severity',
                'warning'
            )
        )

        status = alert.get('status')

        now = time.time()

        # ACTIVE ALERTS
        if status == "firing":

            active_alerts[:] = [

                item for item in active_alerts

                if item["alert"] != alert_name
            ]

            active_alerts.append({

                "alert": alert_name,

                "severity": severity,

                "status": "ACTIVE",

                "time": time.strftime("%H:%M:%S")
            })

            if len(active_alerts) > 5:

                active_alerts.pop(0)

        # RESOLVED
        if status == "resolved":

            active_alerts[:] = [

                item for item in active_alerts

                if item["alert"] != alert_name
            ]

            print(
                f"Resolved alert removed: {alert_name}",
                flush=True
            )

            return jsonify({
                "status": "resolved removed"
            })

        # COOLDOWN
        if alert_name in last_action_time:

            if (
                now -
                last_action_time[alert_name]
            ) < COOLDOWN:

                return jsonify({
                    "status": "cooldown"
                })

        # HIGH CPU
        if alert_name == "HighCPU":

            wait_before_fix(10)

            kill_high_cpu_processes()

            time.sleep(5)

            cpu_after = get_cpu_usage()

            if cpu_after > 70:

                run_command(
                    "/usr/bin/docker restart myapp"
                )

                time.sleep(10)

                cpu_final = get_cpu_usage()

                if cpu_final > 70:

                    action = (
                        "restart failed to reduce CPU"
                    )

                else:

                    action = (
                        "container restarted and CPU recovered"
                    )

            else:

                action = (
                    "CPU recovered after killing processes"
                )

        elif alert_name == "HighMemory":

            wait_before_fix(10)

            run_command(
                "/usr/bin/docker restart myapp"
            )

            action = "container restarted"

        elif alert_name == "DiskFull":

            wait_before_fix(10)

            run_command(
                "docker system prune -af"
            )

            action = "docker cleaned"

        elif alert_name == "ContainerDown":

            wait_before_fix(10)

            run_command(
                "/usr/bin/docker start myapp"
            )

            action = "container started"

        elif alert_name == "TooManyProcesses":

            wait_before_fix(5)

            kill_high_cpu_processes()

            action = "processes killed"

        elif alert_name == "HighSwapUsage":

            wait_before_fix(5)

            run_command(
                "swapoff -a && swapon -a"
            )

            run_command(
                "sync; echo 3 > /proc/sys/vm/drop_caches"
            )

            action = (
                "swap reset + cache cleared"
            )

        elif alert_name == "HighLoadAverage":

            wait_before_fix(5)

            top_process = get_top_cpu_process()

            kill_high_cpu_processes()

            action = (
                f"load reduced | root cause: {top_process}"
            )

        elif alert_name == "HighCPUUsage":

            scale_kubernetes_deployment(3)

            action = (
                "kubernetes deployment scaled"
            )

        elif alert_name == "HighMemoryUsage":

            restart_kubernetes_deployment()

            action = (
                "kubernetes deployment restarted"
            )

        elif alert_name == "PodNotRunning":

            action = (
                "kubernetes auto-healing"
            )

        else:

            action = "none"

        last_action_time[alert_name] = now

        save_action(
            alert_name,
            action,
            "success"
        )

        return jsonify({
            "alert": alert_name,
            "action": action
        })

    except Exception as e:

        print(
            "Webhook error:",
            e,
            flush=True
        )

        return jsonify({
            "error": str(e)
        }), 500


# =============================
# METRICS API
# =============================
@app.route('/metrics')
@jwt_required()
def metrics():

    try:

        # CPU
        cpu_query = (
            '100 - (avg by(instance)'
            '(rate(node_cpu_seconds_total'
            '{mode="idle"}[5m])) * 100)'
        )

        cpu_usage = query_prometheus(
            cpu_query
        )

        # MEMORY
        memory_query = (
            '(1 - (node_memory_MemAvailable_bytes '
            '/ node_memory_MemTotal_bytes)) * 100'
        )

        memory_usage = query_prometheus(
            memory_query
        )

        # PODS
        running_pods = get_running_pods()

        # RESTARTS
        restart_count = get_restart_count()

        # ALERTS
        alert_count = len(active_alerts)

        # HEALTH
        cluster_health = "healthy"

        if cpu_usage > 85:

            cluster_health = "critical"

        elif cpu_usage > 70:

            cluster_health = "warning"

        return jsonify({

            "cpu_usage": cpu_usage,

            "memory_usage": memory_usage,

            "running_pods": running_pods,

            "restart_count": restart_count,

            "active_alerts": alert_count,

            "cluster_health": cluster_health
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# =============================
# MANUAL TEST
# =============================
@app.route('/simulate')
@jwt_required()
def simulate():

    run_command(
        "/usr/bin/docker restart myapp"
    )

    return jsonify({
        "status": "simulated"
    })


# =============================
# CREATE PROJECT
# =============================
@app.route('/projects', methods=['POST'])
@jwt_required()
def create_project():

    try:

        current_email = get_jwt_identity()

        cursor = db.cursor(
            cursor_factory=RealDictCursor
        )

        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE email=%s
            """,
            (current_email,)
        )

        user = cursor.fetchone()

        if not user:

            return jsonify({
                "error": "User not found"
            }), 404

        data = request.json

        project_name = data.get("project_name")
        environment = data.get("environment")
        infra_type = data.get("infra_type")
        cloud_provider = data.get("cloud_provider")
        namespace = data.get("namespace")

        if not all([
            project_name,
            environment,
            infra_type,
            cloud_provider
        ]):

            return jsonify({
                "error": "Missing required fields"
            }), 400

        cursor.execute(
            """
            INSERT INTO projects
            (
                user_id,
                project_name,
                environment,
                infra_type,
                cloud_provider,
                namespace,
                status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                user["id"],
                project_name,
                environment,
                infra_type,
                cloud_provider,
                namespace,
                "connected"
            )
        )

        project = cursor.fetchone()

        db.commit()

        return jsonify({
            "message": "Project created successfully",
            "project_id": project["id"]
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# =============================
# GET PROJECTS
# =============================
@app.route('/projects', methods=['GET'])
@jwt_required()
def get_projects():

    try:

        current_email = get_jwt_identity()

        cursor = db.cursor(
            cursor_factory=RealDictCursor
        )

        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE email=%s
            """,
            (current_email,)
        )

        user = cursor.fetchone()

        if not user:

            return jsonify([])

        cursor.execute(
            """
            SELECT *
            FROM projects
            WHERE user_id=%s
            ORDER BY id DESC
            """,
            (user["id"],)
        )

        projects = cursor.fetchall()

        return jsonify(projects)

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# =============================
# ACTION HISTORY
# =============================
@app.route('/history')
@jwt_required()
def history():

    try:

        cursor = db.cursor(
            cursor_factory=RealDictCursor
        )

        query = """
        SELECT *
        FROM action_history
        ORDER BY id DESC
        LIMIT 10
        """

        cursor.execute(query)

        rows = cursor.fetchall()

        return jsonify(rows)

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# =============================
# ACTIVE ALERTS API
# =============================
@app.route('/active-alerts')
@jwt_required()
def active_alerts_api():

    return jsonify(active_alerts[::-1])


# =============================
# START APP
# =============================
if __name__ == '__main__':

    app.run(
        host="0.0.0.0",
        port=5000
    )
