from functools import wraps
from flask import Blueprint, render_template, jsonify, session, redirect, url_for
# Importamos la nueva función get_detailed_hardware_info y otras que necesitarás
from monitoring_system.models.agent_data import (
    obtener_datos_historicos_por_host,
    latest_agent_data,
    get_detailed_hardware_info, # Nuevo
    get_risk_status # Nuevo, si lo usas para mostrar riesgo en la página de detalle
)
import time # Para formatear timestamps si es necesario

dispositivo_bp = Blueprint('dispositivo', __name__)

# Función de verificación de sesión (la misma que ya tienes)
def login_required(f):
    @wraps(f) # Importa functools.wraps si no lo has hecho
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# Tu ruta existente para el detalle general del dispositivo
@dispositivo_bp.route('/dispositivo/<hostname>')
def detalle_dispositivo(hostname):
    # Asegúrate de que esta ruta use el decorador de login_required si quieres protegerla
    # @login_required # <-- Descomentar si aplica
    return render_template('dispositivo/detalle.html', hostname=hostname)

# Tu ruta existente para obtener los datos JSON del dispositivo
@dispositivo_bp.route('/get_device_data/<hostname>')
def get_device_data(hostname):
    # Asegúrate de que esta ruta use el decorador de login_required si quieres protegerla
    # @login_required # <-- Descomentar si aplica
    historial = obtener_datos_historicos_por_host(hostname)

    riesgo = None
    if hostname in latest_agent_data:
        riesgo = latest_agent_data[hostname].get("calculated_risk_percent")

    ultimo = latest_agent_data.get(hostname, {})
    
    # Formatear timestamps para ser legibles en el frontend
    formatted_timestamps = [time.strftime('%H:%M:%S', time.localtime(ts)) for ts in [d['timestamp'] for d in historial]]


    respuesta = {
        "timestamps": formatted_timestamps, # Usar los formateados
        "cpu": [d['cpu_percent'] for d in historial],
        "memory": [d['memory_percent'] for d in historial],
        "disk": [d['disk_percent'] for d in historial],
        "tx": [d['bytes_sent_mb'] for d in historial],
        "rx": [d['bytes_recv_mb'] for d in historial],
        "disks": ultimo.get("disks", {}),
        "disks_used_gb": ultimo.get("disks_used_gb", {}),
        "disks_total_gb": ultimo.get("disks_total_gb", {}),
        "cpu_temperature": ultimo.get("cpu_temperature", "N/A"), # Asegúrate de pasar la temperatura
        "riesgo": riesgo
    }
    return jsonify(respuesta)

# --- NUEVA RUTA Y FUNCIÓN PARA EL DETALLE AVANZADO DE CPU/HARDWARE ---
@dispositivo_bp.route('/dispositivo/<hostname>/detalle_hardware_cpu')
# Puedes añadir el decorador de autenticación si quieres que solo usuarios logueados accedan
# @login_required 
def detalle_hardware_cpu(hostname):
    hardware_info = get_detailed_hardware_info(hostname)
    latest_data = latest_agent_data.get(hostname) # Para mostrar hostname y riesgo actual

    if not hardware_info:
        # Si no hay información de hardware, muestra un mensaje de error
        # o redirige a la página principal de detalle con un flash message.
        # Aquí, simplemente retornamos un template de error o un mensaje.
        return render_template(
            'dispositivo/detalle_cpu_hardware.html', # Usamos la misma plantilla
            hostname=hostname,
            hardware_info={"error": "Información detallada de hardware no disponible. Asegúrate de que el agente esté ejecutándose como administrador y haya enviado los datos."}
        )

    return render_template(
        'dispositivo/detalle_cpu_hardware.html',
        hostname=hostname,
        hardware_info=hardware_info,
        latest_data=latest_data, # Pasa los datos actuales para mostrar riesgo/estado
        get_risk_status=get_risk_status # Para usar en la plantilla
    )