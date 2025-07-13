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

    # Obtener el riesgo y otros datos del 'latest_agent_data' para los gráficos
    riesgo = None
    if hostname in latest_agent_data:
        riesgo = latest_agent_data[hostname].get("calculated_risk_percent")

    ultimo = latest_agent_data.get(hostname, {})

     # Formatear timestamps a milisegundos para Chart.js con tipo 'time'
    timestamps_ms = [int(d['timestamp'] * 1000) for d in historial]

    respuesta = {
        "timestamps": timestamps_ms, # Usar milisegundos
        "cpu": [d.get('cpu_percent', 0) for d in historial], # Añadido .get con default 0 para seguridad
        "memory": [d.get('memory_percent', 0) for d in historial], # Añadido .get con default 0 para seguridad
        # El resto de tus listas de datos de gráficos
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

# Ruta para obtener los datos JSON del dispositivo (para actualización de gráficos vía AJAX)
@dispositivo_bp.route('/get_device_data/<hostname>')
@login_required # Proteger esta API también
def get_device_data(hostname):
    historial = obtener_datos_historicos_por_host(hostname)

    riesgo = None
    if hostname in latest_agent_data:
        riesgo = latest_agent_data[hostname].get("calculated_risk_percent")

    ultimo = latest_agent_data.get(hostname, {})
    
    # CAMBIO AQUÍ: Convertir timestamps a milisegundos para Chart.js con tipo 'time'
    timestamps_ms = [int(d['timestamp'] * 1000) for d in historial]


    respuesta = {
        "timestamps": timestamps_ms, # Usar los timestamps en milisegundos
        "cpu": [d.get('cpu_percent', 0) for d in historial], # Usar .get con valor por defecto es buena práctica
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

# --- RUTAS ESPECÍFICAS PARA EL DETALLE AVANZADO DE HARDWARE (usando detalle_cpu_hardware.html) ---

# Ruta para el detalle de CPU
@dispositivo_bp.route('/dispositivo/<hostname>/detalle_hardware_cpu')
@login_required
def detalle_hardware_cpu(hostname):
    full_hardware_info = get_detailed_hardware_info(hostname)
    
    # Prepara solo la información del procesador y caché para esta vista
    hardware_to_display = {
        "Processor": full_hardware_info.get("Processor", {}),
    }

    return render_template(
        'dispositivo/detalle_cpu_hardware.html',
        hostname=hostname,
        hardware_info=hardware_to_display, 
        latest_data=latest_agent_data.get(hostname), 
        get_risk_status=get_risk_status,
        section_title="PROCESADOR (CPU)" # Título específico para esta sección
    )

# Ruta para el detalle de Memoria
@dispositivo_bp.route('/dispositivo/<hostname>/detalle_hardware_memory')
@login_required
def detalle_hardware_memory(hostname):
    full_hardware_info = get_detailed_hardware_info(hostname)
    
    # Prepara solo la información de la memoria para esta vista
    hardware_to_display = {
        "Memory": full_hardware_info.get("Memory", {}),
    }

    return render_template(
        'dispositivo/detalle_cpu_hardware.html', # Reutilizamos la plantilla
        hostname=hostname,
        hardware_info=hardware_to_display, # Pasamos solo la sección de Memoria
        latest_data=latest_agent_data.get(hostname),
        get_risk_status=get_risk_status,
        section_title="MEMORIA" # Título específico para esta sección
    )

# Ruta para el detalle de Disco
@dispositivo_bp.route('/dispositivo/<hostname>/detalle_hardware_disk')
@login_required
def detalle_hardware_disk(hostname):
    full_hardware_info = get_detailed_hardware_info(hostname)
    
    # Prepara solo la información de los discos para esta vista
    hardware_to_display = {
        "Disks": full_hardware_info.get("Disks", []),
    }

    return render_template(
        'dispositivo/detalle_cpu_hardware.html', # Reutilizamos la plantilla
        hostname=hostname,
        hardware_info=hardware_to_display, # Pasamos solo la sección de Discos
        latest_data=latest_agent_data.get(hostname),
        get_risk_status=get_risk_status,
        section_title="ALMACENAMIENTO (DISCOS)" # Título específico para esta sección
    )

# Ruta para el detalle de Gráficos (GPU)
@dispositivo_bp.route('/dispositivo/<hostname>/detalle_hardware_gpu')
@login_required
def detalle_hardware_gpu(hostname):
    full_hardware_info = get_detailed_hardware_info(hostname)
    
    # Prepara solo la información de las tarjetas gráficas para esta vista
    hardware_to_display = {
        "Graphics": full_hardware_info.get("Graphics", []),
    }

    return render_template(
        'dispositivo/detalle_cpu_hardware.html', # Reutilizamos la plantilla
        hostname=hostname,
        hardware_info=hardware_to_display, # Pasamos solo la sección de Gráficos
        latest_data=latest_agent_data.get(hostname),
        get_risk_status=get_risk_status,
        section_title="GRÁFICOS (GPU)" # Título específico para esta sección
    )