from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import time

app = Flask(__name__)
CORS(app)

COOLDOWN = 5
last_action_time = {}

# Run shell command safely
def run_command(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print("\nCMD:", cmd, flush=True)
    print("STDOUT:", result.stdout.strip(), flush=True)
    print("STDERR:", result.stderr.strip(), flush=True)
    print("RETURN CODE:", result.returncode, flush=True)
    return result.returncode

# Get CPU usage
def get_cpu_usage():
    try:
        output = subprocess.getoutput("top -bn1 | grep 'Cpu(s)'")
        idle = float(output.split("id,")[0].split()[-1])
        cpu = 100 - idle
        print(f"CPU usage: {cpu}%", flush=True)
        return cpu
    except Exception as e:
        print("CPU read error:", e, flush=True)
        return 0

# Kill high CPU processes
def kill_high_cpu_processes():
    print("Killing high CPU processes", flush=True)

    run_command("pkill -9 -f yes")
    run_command("ps -eo pid,%cpu --sort=-%cpu | awk 'NR<=6 && NR>1 {print $1}' | xargs -r kill -9")


@app.route('/')
def home():
    return "HealOps Backend Running"


@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("\nAlert received:", data, flush=True)

    if not data or 'alerts' not in data:
        return jsonify({"error": "Invalid payload"}), 400

    alert = data['alerts'][0]
    alert_name = alert['labels'].get('alertname')
    status = alert.get('status')
    now = time.time()

    if status == "resolved":
        print("Resolved alert ignored", flush=True)
        return jsonify({"status": "resolved ignored"})

    if alert_name in last_action_time:
        if now - last_action_time[alert_name] < COOLDOWN:
            print("Cooldown active", flush=True)
            return jsonify({"status": "cooldown"})

    # =============================
    # HIGH CPU
    # =============================
    if alert_name == "HighCPU":
        print("High CPU detected", flush=True)

        print("Waiting 10s before fix (for alert visibility)", flush=True)
        time.sleep(10)

        kill_high_cpu_processes()
        time.sleep(3)

        cpu_after = get_cpu_usage()

        if cpu_after > 70:
            print("CPU still high → restarting container", flush=True)
            run_command("/usr/bin/docker restart myapp")
            action = "killed processes + restarted container"
        else:
            action = "killed processes"

    # =============================
    # MEMORY
    # =============================
    elif alert_name == "HighMemory":
        print("High memory detected", flush=True)

        print("Waiting 10s before fix", flush=True)
        time.sleep(10)

        run_command("/usr/bin/docker restart myapp")
        action = "container restarted"

    # =============================
    # DISK
    # =============================
    elif alert_name == "DiskFull":
        print("Disk full detected", flush=True)

        print("Waiting 10s before cleanup", flush=True)
        time.sleep(10)

        run_command("docker system prune -af")
        action = "docker cleaned"

    # =============================
    # CONTAINER DOWN
    # =============================
    elif alert_name == "ContainerDown":
        print("Container down detected", flush=True)

        time.sleep(10)

        print("Starting container", flush=True)
        run_command("/usr/bin/docker start myapp")
        action = "container started"

    # =============================
    # TOO MANY PROCESSES
    # =============================
    elif alert_name == "TooManyProcesses":
        print("Too many processes detected", flush=True)

        time.sleep(5)

        kill_high_cpu_processes()
        action = "processes killed"

    # =============================
    # HIGH SWAP (FIXED)
    # =============================
    elif alert_name == "HighSwapUsage":
        print("High swap usage detected", flush=True)

        print("Waiting 5s before fix", flush=True)
        time.sleep(5)

        run_command("swapoff -a && swapon -a")
        run_command("sync; echo 3 > /proc/sys/vm/drop_caches")

        action = "swap reset + cache cleared"

    # =============================
    # HIGH LOAD (ADDED)
    # =============================
    elif alert_name == "HighLoadAverage":
        print("High load detected", flush=True)

        print("Waiting 5s before fix", flush=True)
        time.sleep(5)

        kill_high_cpu_processes()

        action = "load reduced"

    else:
        print("No action required", flush=True)
        action = "none"

    last_action_time[alert_name] = now

    return jsonify({
        "alert": alert_name,
        "action": action
    })


@app.route('/simulate')
def simulate():
    print("Manual simulation triggered", flush=True)
    run_command("/usr/bin/docker restart myapp")
    return jsonify({"status": "simulated"})


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
