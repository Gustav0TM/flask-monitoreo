from flask import Blueprint, render_template, jsonify
from monitoring_system.models.agent_data import obtener_datos_historicos_por_host, latest_agent_data

dispositivo_bp = Blueprint('dispositivo', __name__)

@dispositivo_bp.route('/dispositivo/<hostname>')
def detalle_dispositivo(hostname):
    return render_template('dispositivo/detalle.html', hostname=hostname)

@dispositivo_bp.route('/get_device_data/<hostname>')
def get_device_data(hostname):
    historial = obtener_datos_historicos_por_host(hostname)

    riesgo = None
    if hostname in latest_agent_data:
        riesgo = latest_agent_data[hostname].get("calculated_risk_percent")

    ultimo = latest_agent_data.get(hostname, {})

    respuesta = {
        "timestamps": [d['timestamp'] for d in historial],
        "cpu": [d['cpu_percent'] for d in historial],
        "memory": [d['memory_percent'] for d in historial],
        "disk": [d['disk_percent'] for d in historial],
        "tx": [d['bytes_sent_mb'] for d in historial],
        "rx": [d['bytes_recv_mb'] for d in historial],
        "disks": ultimo.get("disks", {}),
        "disks_used_gb": ultimo.get("disks_used_gb", {}),
        "disks_total_gb": ultimo.get("disks_total_gb", {}),
        "riesgo": riesgo
    }
    return jsonify(respuesta)
