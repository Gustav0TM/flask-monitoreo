import datetime
from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for
from monitoring_system.models.agent_data import (
    save_agent_data, 
    get_all_agent_data_sorted,
    get_device_statistics,
    get_historical_data_from_firebase
)

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    return render_template('dashboard/dashboard.html')

@dashboard_bp.route('/get_agent_data')
def get_agent_data():
    if 'usuario' not in session:
        return jsonify({"error": "No autorizado"}), 401

    datos_ordenados = get_all_agent_data_sorted()
    return jsonify(datos_ordenados)

@dashboard_bp.route('/submit_agent_data', methods=['POST'])
def submit_agent_data():
    data = request.json
    save_agent_data(data)
    return jsonify({"status": "success"}), 200

@dashboard_bp.route('/receive_data', methods=['POST'])
def receive_data():
    data = request.get_json()
    save_agent_data(data)
    return jsonify({"mensaje": "Datos recibidos correctamente"}), 200

@dashboard_bp.route('/datos', methods=['POST'])
def recibir_datos_android():
    return receive_data()

@dashboard_bp.route('/device_stats/<hostname>')
def device_stats(hostname):
    """
    Endpoint para obtener estadísticas del dispositivo
    """
    if 'usuario' not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    days = request.args.get('days', 7, type=int)
    stats = get_device_statistics(hostname, days)
    
    if stats:
        return jsonify(stats)
    else:
        return jsonify({"error": "No se pudieron obtener las estadísticas"}), 404

@dashboard_bp.route('/historical_data/<hostname>')
def historical_data(hostname):
    """
    Endpoint para obtener datos históricos extendidos
    """
    if 'usuario' not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    limit = request.args.get('limit', 100, type=int)
    historical_data = get_historical_data_from_firebase(hostname, limit)
    
    return jsonify({
        "hostname": hostname,
        "data": historical_data,
        "total_records": len(historical_data)
    })

@dashboard_bp.route('/export_data/<hostname>')
def export_data(hostname):
    """
    Endpoint para exportar datos históricos
    """
    if 'usuario' not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    try:
        # Obtener todos los datos históricos
        historical_data = get_historical_data_from_firebase(hostname, 1000)
        
        if not historical_data:
            return jsonify({"error": "No hay datos para exportar"}), 404
        
        # Preparar datos para exportación
        export_data = {
            "hostname": hostname,
            "export_timestamp": int(datetime.datetime.now().timestamp()),
            "total_records": len(historical_data),
            "data": historical_data
        }
        
        return jsonify(export_data)
        
    except Exception as e:
        return jsonify({"error": f"Error al exportar datos: {str(e)}"}), 500