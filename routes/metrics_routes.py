from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from services.prometheus_service import (
    get_cpu_usage,
    get_memory_usage,
    get_disk_usage,
    get_restart_count
)

from utils.helpers import run_command


metrics_bp = Blueprint(
    "metrics",
    __name__
)


# =============================
# METRICS
# =============================
@metrics_bp.route('/metrics', methods=['GET'])
@jwt_required()
def metrics():

    try:

        cpu = get_cpu_usage()
        memory = get_memory_usage()
        disk = get_disk_usage()
        restarts = get_restart_count()

        return jsonify({
            "cpu": cpu,
            "memory": memory,
            "disk": disk,
            "restarts": restarts
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# =============================
# MANUAL TEST
# =============================
@metrics_bp.route('/simulate', methods=['GET'])
@jwt_required()
def simulate():

    run_command(
        "/usr/bin/docker restart myapp"
    )

    return jsonify({
        "status": "simulated"
    })
