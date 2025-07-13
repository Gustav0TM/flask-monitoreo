from functools import wraps
from flask import Blueprint, render_template, jsonify, session, redirect, url_for
import time

# Importamos las funciones necesarias de agent_data.py
from monitoring_system.models.agent_data import (
    obtener_datos_historicos_por_host,
    latest_agent_data,
    get_detailed_hardware_info,
    get_risk_status
)

dispositivo_bp = Blueprint('dispositivo', __name__)

# Función de verificación de sesión
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# Ruta para la vista general del detalle del dispositivo (detalle.html)
@dispositivo_bp.route('/dispositivo/<hostname>')
@login_required
def detalle_dispositivo(hostname):
    # Obtener los datos históricos del agente para los gráficos
    historial = obtener_datos_historicos_por_host(hostname)

    # Obtener el riesgo y otros datos del 'latest_agent_data'
    riesgo = None
    if hostname in latest_agent_data:
        riesgo = latest_agent_data[hostname].get("calculated_risk_percent")

    # Formatear timestamps para ser legibles en el frontend (esto es para la primera carga si detalle.html los usara directamente)
    # Sin embargo, get_device_data se encarga de los timestamps para Chart.js.
    # Esta línea se mantiene para consistencia si el template los usara sin JS.
    formatted_timestamps = [time.strftime('%H:%M:%S', time.localtime(d['timestamp'])) for d in historial]

    # Renderizar la plantilla detalle.html y pasar los datos
    return render_template(
        'dispositivo/detalle.html',
        hostname=hostname,
        # Estos datos se usan para la carga inicial de los gráficos si no se usa AJAX de inmediato
        timestamps=formatted_timestamps, # Mantener por si se usa en el HTML directamente
        cpu=[d['cpu_percent'] for d in historial],
        memory=[d['memory_percent'] for d in historial],
        disks=[d['disk_percent'] for d in historial],
        tx=[d['bytes_sent_mb'] for d in historial],
        rx=[d['bytes_recv_mb'] for d in historial],
        disks_total_gb=latest_agent_data.get(hostname, {}).get("disks_total_gb", {}),
        disks_used_gb=latest_agent_data.get(hostname, {}).get("disks_used_gb", {}),
        cpu_temperature=latest_agent_data.get(hostname, {}).get("cpu_temperature", "N/A"),
        riesgo=riesgo
    )

# Ruta para obtener los datos JSON del dispositivo (para actualización de gráficos vía AJAX)
@dispositivo_bp.route('/get_device_data/<hostname>')
@login_required
def get_device_data(hostname):
    historial = obtener_datos_historicos_por_host(hostname)

    riesgo = None
    if hostname in latest_agent_data:
        riesgo = latest_agent_data[hostname].get("calculated_risk_percent")

    ultimo = latest_agent_data.get(hostname, {})
    
    # *** ESTE ES EL CAMBIO CLAVE PARA LOS TIMESTAMPS DE CHART.JS ***
    # Convertir timestamps a milisegundos para Chart.js con tipo 'time'
    timestamps_ms = [int(d['timestamp'] * 1000) for d in historial]

    respuesta = {
        "timestamps": timestamps_ms, # Usar milisegundos para Chart.js
        "cpu": [d.get('cpu_percent', 0) for d in historial],
        "memory": [d.get('memory_percent', 0) for d in historial],
        "disk": [d.get('disk_percent', 0) for d in historial],
        "tx": [d.get('bytes_sent_mb', 0) for d in historial],
        "rx": [d.get('bytes_recv_mb', 0) for d in historial],
        "disks": ultimo.get("disks", {}),
        "disks_used_gb": ultimo.get("disks_used_gb", {}),
        "disks_total_gb": ultimo.get("disks_total_gb", {}),
        "cpu_temperature": ultimo.get("cpu_temperature", "N/A"),
        "riesgo": riesgo
    }
    return jsonify(respuesta)

# --- RUTA ÚNICA Y GENERAL PARA EL DETALLE AVANZADO DE HARDWARE ---
# Esta ruta cargará toda la información de hardware y la pasará a la plantilla.
# La plantilla decidirá qué mostrar basándose en la información recibida.
@dispositivo_bp.route('/dispositivo/<hostname>/detalle_hardware') # Cambiado a una ruta más genérica
@login_required 
def detalle_hardware_completo(hostname): # Nombre de función más descriptivo
    hardware_info = get_detailed_hardware_info(hostname)
    latest_data = latest_agent_data.get(hostname) # Para mostrar hostname y riesgo actual

    if not hardware_info or ("error" in hardware_info and hardware_info["error"]):
        # Si no hay información de hardware, muestra un mensaje de error
        return render_template(
            'dispositivo/detalle_cpu_hardware.html', # Usamos la misma plantilla
            hostname=hostname,
            hardware_info={"error": hardware_info.get("error", "Información detallada de hardware no disponible. Asegúrate de que el agente esté ejecutándose como administrador y haya enviado los datos.")},
            latest_data=latest_data,
            get_risk_status=get_risk_status,
            section_title="HARDWARE COMPLETO" # Título genérico para el error
        )

    return render_template(
        'dispositivo/detalle_cpu_hardware.html',
        hostname=hostname,
        hardware_info=hardware_info, # PASAMOS TODA LA INFO DE HARDWARE
        latest_data=latest_data, 
        get_risk_status=get_risk_status,
        section_title="HARDWARE COMPLETO" # Título genérico para la vista
    )