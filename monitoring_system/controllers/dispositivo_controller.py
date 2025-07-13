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

    # Formatear timestamps para ser legibles en el frontend (para la carga inicial si detalle.html los usara directamente)
    # Sin embargo, get_device_data se encarga de los timestamps para Chart.js.
    formatted_timestamps = [time.strftime('%H:%M:%S', time.localtime(d['timestamp'])) for d in historial]

    # Renderizar la plantilla detalle.html y pasar los datos
    return render_template(
        'dispositivo/detalle.html',
        hostname=hostname,
        timestamps=formatted_timestamps,
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

# --- RUTAS ESPECÍFICAS PARA EL DETALLE AVANZADO DE HARDWARE ---

def _render_hardware_detail(hostname, section_key, section_title):
    full_hardware_info = get_detailed_hardware_info(hostname)
    latest_data = latest_agent_data.get(hostname)

    # Si hay un error general en la obtención de info de hardware
    if not full_hardware_info or ("error" in full_hardware_info and full_hardware_info["error"]):
        return render_template(
            'dispositivo/detalle_cpu_hardware.html',
            hostname=hostname,
            hardware_info={"error": full_hardware_info.get("error", "Información detallada de hardware no disponible. Asegúrate de que el agente esté ejecutándose como administrador y haya enviado los datos.")},
            latest_data=latest_data,
            get_risk_status=get_risk_status,
            section_title=section_title
        )

    # Prepara solo la información de la sección solicitada
    hardware_to_display = {}
    if section_key: # Si se pide una sección específica
        if section_key == "Graphics" or section_key == "Disks" or section_key == "Network": # Estas son listas
            if section_key in full_hardware_info:
                hardware_to_display[section_key] = full_hardware_info[section_key]
            else:
                hardware_to_display["error_section"] = f"No se encontró información para {section_title}."
        elif section_key in full_hardware_info: # Las demás son diccionarios
            hardware_to_display[section_key] = full_hardware_info[section_key]
        else:
            hardware_to_display["error_section"] = f"No se encontró información para {section_title}."
    else: # Si se pide el hardware completo (para un botón "Detalle Hardware" general)
        hardware_to_display = full_hardware_info

    return render_template(
        'dispositivo/detalle_cpu_hardware.html',
        hostname=hostname,
        hardware_info=hardware_to_display, 
        latest_data=latest_data, 
        get_risk_status=get_risk_status,
        section_title=section_title # Título específico para cada sección
    )

# Ruta para el detalle de CPU
@dispositivo_bp.route('/dispositivo/<hostname>/detalle_hardware_cpu')
@login_required
def detalle_hardware_cpu(hostname):
    return _render_hardware_detail(hostname, "Processor", "PROCESADOR (CPU)")

# Ruta para el detalle de Memoria
@dispositivo_bp.route('/dispositivo/<hostname>/detalle_hardware_memory')
@login_required
def detalle_hardware_memory(hostname):
    return _render_hardware_detail(hostname, "Memory", "MEMORIA")

# Ruta para el detalle de Disco
@dispositivo_bp.route('/dispositivo/<hostname>/detalle_hardware_disk')
@login_required
def detalle_hardware_disk(hostname):
    return _render_hardware_detail(hostname, "Disks", "ALMACENAMIENTO (DISCOS)")

# Ruta para el detalle de Gráficos (GPU)
@dispositivo_bp.route('/dispositivo/<hostname>/detalle_hardware_gpu')
@login_required
def detalle_hardware_gpu(hostname):
    return _render_hardware_detail(hostname, "Graphics", "GRÁFICOS (GPU)")

# Puedes mantener una ruta general de hardware completo si lo deseas
@dispositivo_bp.route('/dispositivo/<hostname>/detalle_hardware_completo')
@login_required
def detalle_hardware_completo(hostname):
    return _render_hardware_detail(hostname, None, "HARDWARE COMPLETO") # 'None' para indicar que no filtre y pase todo