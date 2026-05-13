from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity
)

from db import db, get_cursor


auth_bp = Blueprint(
    "auth",
    __name__
)


# =============================
# REGISTER
# =============================
@auth_bp.route('/register', methods=['POST'])
def register():

    try:

        data = request.json

        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        cursor = get_cursor()

        cursor.execute(
            """
            INSERT INTO users
            (
                username,
                email,
                password
            )
            VALUES (%s, %s, %s)
            """,
            (
                username,
                email,
                password
            )
        )

        db.commit()

        return jsonify({
            "message": "User registered"
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# =============================
# LOGIN
# =============================
@auth_bp.route('/login', methods=['POST'])
def login():

    try:

        data = request.json

        email = data.get("email")
        password = data.get("password")

        cursor = get_cursor(dict_cursor=True)

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE email=%s
            AND password=%s
            """,
            (
                email,
                password
            )
        )

        user = cursor.fetchone()

        if not user:

            return jsonify({
                "error": "Invalid credentials"
            }), 401

        token = create_access_token(
            identity=user["email"]
        )

        return jsonify({
            "token": token
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# =============================
# CURRENT USER
# =============================
@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():

    current_user = get_jwt_identity()

    return jsonify({
        "email": current_user
    })
