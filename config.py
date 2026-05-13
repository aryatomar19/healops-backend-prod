import os


# =============================
# FLASK / JWT
# =============================
JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "healops-secret-key"
)


# =============================
# DATABASE
# =============================
DB_HOST = "database-1.c5ecywggqf0l.ap-south-1.rds.amazonaws.com"

DB_NAME = "healops"

DB_USER = "postgres"

DB_PASSWORD = "arya007varth"

# =============================
# PROMETHEUS
# =============================
PROMETHEUS_URL = os.getenv(
    "PROMETHEUS_URL",
    "http://localhost:9090"
)


# =============================
# HEALING
# =============================
COOLDOWN = 60
