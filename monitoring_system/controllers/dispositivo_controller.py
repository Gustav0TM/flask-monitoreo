# monitoring_system/controllers/dispositivo_controller.py

from flask import Blueprint, render_template, jsonify, session, redirect, url_for
from monitoring_system.models.agent_data import (
    obtener_datos_historicos_por_host,
    latest_agent_data,
    get_detailed_hardware_info,
    get_risk_status
)
import time
from functools import wraps

dispositivo_bp = Blueprint('dispositivo', __name__)

# Decorador de autenticación
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@dispositivo_bp.route('/dispositivo/<hostname>')
@login_required
def detalle_dispositivo(hostname):
    return render_template('dispositivo/detalle.html', hostname=hostname)

@dispositivo_bp.route('/get_device_data/<hostname>')
@login_required
def get_device_data(hostname):
    historial = obtener_datos_historicos_por_host(hostname)
    riesgo = None
    if hostname in latest_agent_data:
        riesgo = latest_agent_data[hostname].get("calculated_risk_percent")

    ultimo = latest_agent_data.get(hostname, {})
    
    timestamps_ms = [int(d['timestamp'] * 1000) for d in historial]

    respuesta = {
        "timestamps": timestamps_ms,
        "cpu": [d.get('cpu_percent', 0) for d in historial],
        "memory": [d.get('memory_percent', 0) for d in historial],
        "disk": [d.get('disk_percent', 0) for d in historial],
        "tx": [d.get('bytes_sent_mb', 0) for d in historial],
        "rx": [d.get('bytes_recv_mb', 0) for d in historial],
        "cpu_temperature": ultimo.get("cpu_temperature", "N/A"),
        "disks": ultimo.get("disks", {}),
        "disks_used_gb": ultimo.get("disks_used_gb", {}),
        "disks_total_gb": ultimo.get("disks_total_gb", {}),
        "riesgo": riesgo
    }
    return jsonify(respuesta)

# --- CORRECCIÓN AQUÍ: Nueva lógica para detalle_hardware_cpu ---
@dispositivo_bp.route('/dispositivo/<hostname>/detalle_hardware_cpu')
@login_required
def detalle_hardware_cpu(hostname):
    # Intentamos obtener la información de hardware.
    # get_detailed_hardware_info ya devuelve un diccionario con "error" si no hay info.
    hardware_info = get_detailed_hardware_info(hostname)
    latest_data = latest_agent_data.get(hostname) # Para mostrar hostname y riesgo actual

    # Si hardware_info tiene un error (es decir, el agente no lo envió o la recolección falló),
    # lo pasamos tal cual para que la plantilla lo muestre como un error.
    # Si no, se pasa la información normal.

    return render_template(
        'dispositivo/detalle_cpu_hardware.html',
        hostname=hostname,
        hardware_info=hardware_info, # Pasamos hardware_info tal cual, con o sin 'error'
        latest_data=latest_data,
        get_risk_status=get_risk_status
    )