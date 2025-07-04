from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import datetime
from decouple import config

# Importar controladores
from monitoring_system.controllers.auth_controller import auth_bp
from monitoring_system.controllers.dashboard_controller import dashboard_bp
from monitoring_system.controllers.dispositivo_controller import dispositivo_bp

# Importar configuración de Firebase
from monitoring_system.models.firebase_config import firebase_manager
from monitoring_system.models.agent_data import sync_with_firebase

def create_app():
    app = Flask(__name__)
    
    # Configuración
    app.secret_key = config('SECRET_KEY', default='tu-clave-secreta-aqui')
    
    # Registrar blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(dispositivo_bp)
    
    # Ruta principal
    @app.route('/')
    def index():
        if 'usuario' not in session:
            return redirect(url_for('auth.login'))
        return redirect(url_for('dashboard.index'))
    
    # Endpoint para verificar estado de Firebase
    @app.route('/firebase-status')
    def firebase_status():
        if 'usuario' not in session:
            return jsonify({"error": "No autorizado"}), 401
        
        status = {
            "connected": firebase_manager.is_connected(),
            "timestamp": int(datetime.datetime.now().timestamp())
        }
        return jsonify(status)
    
    # Inicializar Firebase al crear la app
    with app.app_context():
        try:
            # Sincronizar datos existentes de Firebase
            sync_with_firebase()
            print("✓ Aplicación iniciada con Firebase")
        except Exception as e:
            print(f"✗ Error al inicializar Firebase: {str(e)}")
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    # Configuración para desarrollo/producción
    debug_mode = config('DEBUG', default=False, cast=bool)
    port = config('PORT', default=5000, cast=int)
    
    app.run(debug=debug_mode, host='0.0.0.0', port=port)