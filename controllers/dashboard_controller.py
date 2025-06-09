from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for
from models.agent_data import save_agent_data, get_all_agent_data_sorted

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    return render_template('dashboard.html')

@dashboard_bp.route('/get_agent_data')
def get_agent_data():
    if 'usuario' not in session:
        return jsonify({"error": "No autorizado"}), 401

    # Obtenemos los datos ordenados por timestamp descendente
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
    print(f"Datos recibidos: {data}")
    save_agent_data(data)
    return jsonify({"mensaje": "Datos recibidos correctamente"}), 200

@dashboard_bp.route('/datos', methods=['POST'])
def recibir_datos_android():
    return receive_data()  # Reutiliza la misma lógica
