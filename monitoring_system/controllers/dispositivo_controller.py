# monitoring_system/controllers/dispositivo_controller.py

from flask import Blueprint, render_template, jsonify, session, redirect, url_for
from monitoring_system.models.agent_data import (
    obtener_datos_historicos_por_host,
    latest_agent_data,
    get_detailed_hardware_info,
    get_risk_status # Asegúrate de que esta función está importada
)
import time # Para formatear timestamps en la respuesta JSON
from functools import wraps # Necesario si usas login_required

dispositivo_bp = Blueprint('dispositivo', __name__)

# Decorador de autenticación
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# Tu ruta existente para el detalle general del dispositivo
@dispositivo_bp.route('/dispositivo/<hostname>')
@login_required # <-- Aplicar el decorador aquí si quieres proteger esta ruta
def detalle_dispositivo(hostname):
    return render_template('dispositivo/detalle.html', hostname=hostname)

@dispositivo_bp.route('/get_device_data/<hostname>')
@login_required # <-- Aplicar el decorador aquí si quieres proteger esta ruta
def get_device_data(hostname):
    historial = obtener_datos_historicos_por_host(hostname)

    riesgo = None
    if hostname in latest_agent_data:
        riesgo = latest_agent_data[hostname].get("calculated_risk_percent")

    ultimo = latest_agent_data.get(hostname, {})
    
    # --- CORRECCIÓN "Invalid Date": Formatear timestamps a milisegundos para Chart.js ---
    # Chart.js con tipo 'time' prefiere milisegundos desde la época
    # O, si usas 'category' en el eje X, puedes enviar cadenas de fecha
    # Usaremos milisegundos para ser más robustos con 'time' scale.
    timestamps_ms = [int(d['timestamp'] * 1000) for d in historial]

    respuesta = {
        "timestamps": timestamps_ms, # Corregido: Enviar milisegundos
        "cpu": [d.get('cpu_percent', 0) for d in historial], # Usar .get para evitar KeyError si falta
        "memory": [d.get('memory_percent', 0) for d in historial],
        "disk": [d.get('disk_percent', 0) for d in historial],
        "tx": [d.get('bytes_sent_mb', 0) for d in historial],
        "rx": [d.get('bytes_recv_mb', 0) for d in historial],
        # --- CORRECCIÓN Temperatura CPU: Incluir temperatura aquí ---
        "cpu_temperature": ultimo.get("cpu_temperature", "N/A"), # Asegúrate de pasar la temperatura
        "disks": ultimo.get("disks", {}),
        "disks_used_gb": ultimo.get("disks_used_gb", {}),
        "disks_total_gb": ultimo.get("disks_total_gb", {}),
        "riesgo": riesgo
    }
    return jsonify(respuesta)

# NUEVA RUTA Y FUNCIÓN PARA EL DETALLE AVANZADO DE CPU/HARDWARE
@dispositivo_bp.route('/dispositivo/<hostname>/detalle_hardware_cpu')
@login_required # <-- Aplicar el decorador aquí si quieres proteger esta ruta
def detalle_hardware_cpu(hostname):
    hardware_info = get_detailed_hardware_info(hostname)
    latest_data = latest_agent_data.get(hostname) # Para mostrar hostname y riesgo actual

    # La función get_detailed_hardware_info ya devuelve un diccionario con "error"
    # si no encuentra la info, así que solo pasamos el resultado a la plantilla.

    return render_template(
        'dispositivo/detalle_cpu_hardware.html',
        hostname=hostname,
        hardware_info=hardware_info,
        latest_data=latest_data, # Pasa los datos actuales para mostrar riesgo/estado
        get_risk_status=get_risk_status # Para usar en la plantilla
    )