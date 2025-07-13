from functools import wraps
from flask import Blueprint, render_template, jsonify, session, redirect, url_for
import time # Para formatear timestamps si es necesario

# Importamos las funciones necesarias de agent_data.py
from monitoring_system.models.agent_data import (
    obtener_datos_historicos_por_host,
    latest_agent_data,
    get_detailed_hardware_info,
    get_risk_status
)

dispositivo_bp = Blueprint('dispositivo', __name__)

# Función de verificación de sesión (la misma que ya tienes)
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# Tu ruta existente para el detalle general del dispositivo (detalle.html)
@dispositivo_bp.route('/dispositivo/<hostname>')
@login_required # <-- Es buena práctica proteger esta ruta
def detalle_dispositivo(hostname):
    # Obtener los datos históricos del agente para los gráficos
    historial = obtener_datos_historicos_por_host(hostname)

    # Obtener la última información de hardware detallada
    # Esta es la información COMPLETA que necesitarás para el PDF en el futuro.
    full_hardware_info = get_detailed_hardware_info(hostname)

    # Preparar la información de hardware para MOSTRAR en detalle.html
    # Solo incluimos las secciones que se pidieron para ser mostradas
    # Las secciones como 'Mainboard' y 'OS' se excluyen aquí intencionalmente.
    hardware_info_display = {
        "Processor": full_hardware_info.get("Processor", {}),
        "Memory": full_hardware_info.get("Memory", {}),
        "Disks": full_hardware_info.get("Disks", []),
        "Graphics": full_hardware_info.get("Graphics", [])
        # No incluimos 'Mainboard' ni 'OS' aquí para que no se muestren en detalle.html
    }
    
    # Manejo de si no hay información de hardware
    if not full_hardware_info:
        # Puedes decidir cómo manejar esto. Por ahora, pasamos un objeto vacío
        # o un indicador de error para que la plantilla lo maneje.
        # En detalle.html, los bucles for y .get() manejarán la ausencia de datos.
        hardware_info_display = {
            "Processor": {"error": "No data"},
            "Memory": {"error": "No data"},
            "Disks": [],
            "Graphics": []
        }

    # Obtener el riesgo y otros datos del 'latest_agent_data' para los gráficos
    riesgo = None
    if hostname in latest_agent_data:
        riesgo = latest_agent_data[hostname].get("calculated_risk_percent")

    # Formatear timestamps para ser legibles en el frontend (para gráficos)
    formatted_timestamps = [time.strftime('%H:%M:%S', time.localtime(d['timestamp'])) for d in historial]

    # Renderizar la plantilla detalle.html y pasar todos los datos necesarios
    return render_template(
        'dispositivo/detalle.html',
        hostname=hostname,
        timestamps=formatted_timestamps,
        cpu=[d['cpu_percent'] for d in historial],
        memory=[d['memory_percent'] for d in historial],
        disks=[d['disk_percent'] for d in historial], # Esto es una lista de porcentajes de disco por partición si viene así
        tx=[d['bytes_sent_mb'] for d in historial],
        rx=[d['bytes_recv_mb'] for d in historial],
        # Los siguientes son para el gráfico de disco si los usas para labels o datalabels
        disks_total_gb=latest_agent_data.get(hostname, {}).get("disks_total_gb", {}),
        disks_used_gb=latest_agent_data.get(hostname, {}).get("disks_used_gb", {}),
        cpu_temperature=latest_agent_data.get(hostname, {}).get("cpu_temperature", "N/A"),
        riesgo=riesgo,
        hardware_info_display=hardware_info_display # Pasamos SOLO lo que queremos mostrar en detalle.html
        # No se pasa 'full_hardware_info' directamente a detalle.html si no se necesita ahí para la interfaz.
        # Se asume que 'get_detailed_hardware_info' ya está guardando los datos completos en algún lugar
        # para una futura recuperación (como para el PDF).
    )

# Tu ruta existente para obtener los datos JSON del dispositivo (para actualización de gráficos)
# Esta ruta no necesita cambios significativos si ya funciona para los gráficos.
@dispositivo_bp.route('/get_device_data/<hostname>')
def get_device_data(hostname):
    # @login_required # <-- Descomentar si quieres proteger esta API
    historial = obtener_datos_historicos_por_host(hostname)

    riesgo = None
    if hostname in latest_agent_data:
        riesgo = latest_agent_data[hostname].get("calculated_risk_percent")

    ultimo = latest_agent_data.get(hostname, {})
    
    # Formatear timestamps para ser legibles en el frontend
    formatted_timestamps = [time.strftime('%H:%M:%S', time.localtime(ts)) for ts in [d['timestamp'] for d in historial]]

    respuesta = {
        "timestamps": formatted_timestamps,
        "cpu": [d['cpu_percent'] for d in historial],
        "memory": [d['memory_percent'] for d in historial],
        "disk": [d['disk_percent'] for d in historial], # Asegúrate de que esto sea una lista de porcentajes
        "tx": [d['bytes_sent_mb'] for d in historial],
        "rx": [d['bytes_recv_mb'] for d in historial],
        "disks": ultimo.get("disks", {}), # Diccionario de {particion: porcentaje}
        "disks_used_gb": ultimo.get("disks_used_gb", {}), # Diccionario de {particion: GB_usado}
        "disks_total_gb": ultimo.get("disks_total_gb", {}), # Diccionario de {particion: GB_total}
        "cpu_temperature": ultimo.get("cpu_temperature", "N/A"),
        "riesgo": riesgo
    }
    return jsonify(respuesta)

# --- RUTA Y FUNCIÓN PARA EL DETALLE AVANZADO DE CPU/HARDWARE (detalle_cpu_hardware.html) ---
# Esta ruta permanece igual, ya que obtiene TODA la información de hardware para su propia vista.
@dispositivo_bp.route('/dispositivo/<hostname>/detalle_hardware_cpu')
# @login_required # <-- Puedes añadir el decorador de autenticación si quieres protegerla
def detalle_hardware_cpu(hostname):
    hardware_info = get_detailed_hardware_info(hostname) # Aquí sí se obtiene toda la info
    latest_data = latest_agent_data.get(hostname) # Para mostrar hostname y riesgo actual

    if not hardware_info:
        return render_template(
            'dispositivo/detalle_cpu_hardware.html',
            hostname=hostname,
            hardware_info={"error": "Información detallada de hardware no disponible. Asegúrate de que el agente esté ejecutándose como administrador y haya enviado los datos."}
        )

    return render_template(
        'dispositivo/detalle_cpu_hardware.html',
        hostname=hostname,
        hardware_info=hardware_info, # Se pasa la información completa aquí
        latest_data=latest_data,
        get_risk_status=get_risk_status
    )