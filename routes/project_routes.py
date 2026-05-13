from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity
)

from db import db, get_cursor


project_bp = Blueprint(
    "projects",
    __name__
)


# =============================
# ADD PROJECT
# =============================
@project_bp.route('/add-project', methods=['POST'])
@jwt_required()
def add_project():

    try:

        data = request.json

        current_user = get_jwt_identity()

        project_name = data.get("project_name")
        environment = data.get("environment")
        infra_type = data.get("infra_type")
        cloud_provider = data.get("cloud_provider")
        namespace = data.get("namespace")

        cursor = get_cursor()

        cursor.execute(
            """
            INSERT INTO projects
            (
                user_email,
                project_name,
                environment,
                infra_type,
                cloud_provider,
                namespace
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                current_user,
                project_name,
                environment,
                infra_type,
                cloud_provider,
                namespace
            )
        )

        db.commit()

        return jsonify({
            "message": "Project added successfully"
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# =============================
# GET PROJECTS
# =============================
@project_bp.route('/projects', methods=['GET'])
@jwt_required()
def get_projects():

    try:

        current_user = get_jwt_identity()

        cursor = get_cursor(dict_cursor=True)

        cursor.execute(
            """
            SELECT *
            FROM projects
            WHERE user_email=%s
            ORDER BY id DESC
            """,
            (current_user,)
        )

        projects = cursor.fetchall()

        return jsonify(projects)

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500
