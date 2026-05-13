from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from config import JWT_SECRET_KEY

from auth.auth_routes import auth_bp
from routes.project_routes import project_bp
from routes.metrics_routes import metrics_bp
from routes.webhook_routes import webhook_bp


app = Flask(__name__)

CORS(app)

app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY

jwt = JWTManager(app)


# =============================
# REGISTER BLUEPRINTS
# =============================
app.register_blueprint(auth_bp)
app.register_blueprint(project_bp)
app.register_blueprint(metrics_bp)
app.register_blueprint(webhook_bp)


# =============================
# HEALTH CHECK
# =============================
@app.route('/')
def home():

    return "HealOps Backend Running"


# =============================
# START APP
# =============================
if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
 )
