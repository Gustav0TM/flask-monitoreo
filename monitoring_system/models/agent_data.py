# monitoring_system/models/agent_data.py

import datetime
import time

# Últimos datos de cada dispositivo
latest_agent_data = {}

# Historial real de los últimos 10 registros por dispositivo
historial_agent_data = {}

# Nueva variable para almacenar la información de hardware estática por agente
hardware_info_by_agent = {}

def save_agent_data(data):
    """
    Guarda los datos recibidos del agente, incluyendo:
    - Uso de CPU, memoria, disco
    - Particiones
    - Red
    - Temperatura de CPU (si se envía)
    - Información detallada de hardware (si se envía por primera vez)
    """
    hostname = data.get("hostname")
    if not hostname:
        return

    timestamp = int(datetime.datetime.now().timestamp())
    data["timestamp"] = timestamp

    # --- Manejar la información detallada de hardware ---
    data_to_save = data.copy() # Copia para modificar sin alterar el 'data' original
    if 'hardware_info' in data_to_save:
        # Almacenar la hardware_info por separado
        hardware_info_by_agent[hostname] = data_to_save['hardware_info']
        del data_to_save['hardware_info'] # Eliminarla de los datos que se guardan repetidamente
    # --- Fin de la nueva parte ---

    # Guardar último dato actualizado (sin la info de hardware estática)
    latest_agent_data[hostname] = data_to_save

    # Inicializar historial si no existe
    if hostname not in historial_agent_data:
        historial_agent_data[hostname] = []

    # Guardar copia en historial (también sin la info de hardware estática)
    historial_agent_data[hostname].append(data_to_save.copy())

    # Limitar historial a 10 registros
    if len(historial_agent_data[hostname]) > 10:
        historial_agent_data[hostname].pop(0)

def get_all_agent_data_sorted():
    """
    Devuelve los dispositivos ordenados por último timestamp descendente.
    """
    return dict(
        sorted(
            latest_agent_data.items(),
            key=lambda item: item[1].get("timestamp", 0),
            reverse=True
        )
    )

def get_all_agent_data():
    """
    Devuelve todos los dispositivos sin ordenar.
    """
    return latest_agent_data

def format_datetime(timestamp):
    """
    Formatea un timestamp a formato legible.
    """
    if timestamp is None:
        return "N/A"
    return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def obtener_datos_historicos_por_host(hostname):
    """
    Devuelve la lista de historial de un dispositivo específico.
    """
    return historial_agent_data.get(hostname, [])

def obtener_ultimo_dato(hostname):
    """
    Devuelve el último dato registrado de un dispositivo.
    """
    return latest_agent_data.get(hostname)

def get_detailed_hardware_info(hostname):
    """
    Devuelve la información de hardware estática para un hostname específico.
    Si no existe, devuelve un diccionario con un mensaje de error.
    """
    info = hardware_info_by_agent.get(hostname)
    if info is None:
        return {"error": "Información detallada de hardware no disponible para este host. Asegúrate de que el agente esté ejecutándose como administrador y haya enviado los datos."}
    return info

def get_risk_status(risk_percent):
    """Determina el estado de riesgo basado en un porcentaje."""
    if risk_percent is None:
        return "N/A"
    elif risk_percent >= 80:
        return "Alto"
    elif risk_percent >= 50:
        return "Medio"
    else:
        return "Bajo"