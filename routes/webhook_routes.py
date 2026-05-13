import time

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from utils.helpers import (
    wait_before_fix,
    save_action,
    run_command
)

from services.healing_service import (
    safe_cpu_remediation,
    verify_cpu_recovery,
    verify_container_running
)

from services.kubernetes_service import (
    scale_kubernetes_deployment,
    restart_kubernetes_deployment,
    verify_kubernetes_deployment
)

from db import get_cursor


webhook_bp = Blueprint(
    "webhook",
    __name__
)


active_alerts = []
last_action_time = {}
COOLDOWN = 60


# =============================
# ACTIVE ALERTS
# =============================
@webhook_bp.route('/active-alerts', methods=['GET'])
@jwt_required()
def active_alerts_route():

    return jsonify(active_alerts)


# =============================
# HISTORY
# =============================
@webhook_bp.route('/history', methods=['GET'])
@jwt_required()
def history():

    try:

        cursor = get_cursor(dict_cursor=True)

        cursor.execute(
            """
            SELECT *
            FROM action_history
            ORDER BY id DESC
            LIMIT 20
            """
        )

        rows = cursor.fetchall()

        return jsonify(rows)

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# =============================
# WEBHOOK
# =============================
@webhook_bp.route('/webhook', methods=['POST'])
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

        action_status = "success"

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

        if status == "resolved":

            active_alerts[:] = [
                item for item in active_alerts
                if item["alert"] != alert_name
            ]

            return jsonify({
                "status": "resolved removed"
            })

        if alert_name in last_action_time:

            if (
                now -
                last_action_time[alert_name]
            ) < COOLDOWN:

                return jsonify({
                    "status": "cooldown"
                })

        # =============================
        # SAFE SMART HEALING
        # =============================

        if alert_name == "HighCPU":

            wait_before_fix(10)

            root_action = safe_cpu_remediation()

            time.sleep(10)

            if verify_cpu_recovery():

                action = root_action

            else:

                action = (
                    "CPU recovery failed"
                )

                action_status = "failed"

        elif alert_name == "HighMemory":

            wait_before_fix(10)

            run_command(
                "/usr/bin/docker restart myapp"
            )

            time.sleep(10)

            if verify_container_running():

                action = (
                    "container restarted successfully"
                )

            else:

                action = (
                    "container restart failed"
                )

                action_status = "failed"

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

            time.sleep(5)

            if verify_container_running():

                action = (
                    "container started successfully"
                )

            else:

                action = (
                    "container failed to start"
                )

                action_status = "failed"

        elif alert_name == "TooManyProcesses":

            wait_before_fix(5)

            action = safe_cpu_remediation()

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

            root_action = safe_cpu_remediation()

            time.sleep(5)

            if verify_cpu_recovery():

                action = root_action

            else:

                action = (
                    f"load still high | {root_action}"
                )

                action_status = "failed"

        elif alert_name == "HighCPUUsage":

            scale_kubernetes_deployment(3)

            time.sleep(10)

            if verify_kubernetes_deployment():

                action = (
                    "kubernetes deployment scaled successfully"
                )

            else:

                action = (
                    "kubernetes scaling failed"
                )

                action_status = "failed"

        elif alert_name == "HighMemoryUsage":

            restart_kubernetes_deployment()

            time.sleep(10)

            if verify_kubernetes_deployment():

                action = (
                    "kubernetes deployment restarted successfully"
                )

            else:

                action = (
                    "kubernetes restart failed"
                )

                action_status = "failed"

        elif alert_name == "PodNotRunning":

            if verify_kubernetes_deployment():

                action = (
                    "kubernetes deployment healthy"
                )

            else:

                restart_kubernetes_deployment()

                action = (
                    "pod recovery attempted"
                )

        else:

            action = "no remediation rule"

        last_action_time[alert_name] = now

        save_action(
            alert_name,
            action,
            action_status
        )

        return jsonify({
            "alert": alert_name,
            "action": action,
            "status": action_status
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
