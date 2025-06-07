from flask import Flask, session
from controllers.dashboard_controller import dashboard_bp
from controllers.auth_controller import auth_bp

app = Flask(__name__)
app.secret_key = "clave_supersecreta"  # Necesario para sesiones

app.register_blueprint(dashboard_bp)
app.register_blueprint(auth_bp)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)