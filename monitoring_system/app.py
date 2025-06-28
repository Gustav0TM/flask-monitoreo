from flask import Flask
from monitoring_system.controllers.dashboard_controller import dashboard_bp
from monitoring_system.controllers.auth_controller import auth_bp
from monitoring_system.controllers.dispositivo_controller import dispositivo_bp



app = Flask(__name__, template_folder='views', static_folder='views/layout')
app.secret_key = "clave_supersecreta"

# 🔽 ESTE PRINT ES PARA VERIFICAR EN RENDER
print("🔥 Versión desplegada el 28/06/2025 - ACTIVA")

app.register_blueprint(dashboard_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(dispositivo_bp) #este
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
