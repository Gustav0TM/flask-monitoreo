import datetime
import time

# Últimos datos de cada dispositivo
latest_agent_data = {}

# Historial real de los últimos 10 registros por dispositivo
historial_agent_data = {}

def save_agent_data(data):
    """
    Guarda los datos recibidos del agente, incluyendo:
    - Uso de CPU, memoria, disco
    - Particiones
    - Red
    - Temperatura de CPU (si se envía)
    """
    hostname = data.get("hostname")
    if not hostname:
        return

    timestamp = int(datetime.datetime.now().timestamp())
    data["timestamp"] = timestamp

    # Guardar último dato actualizado
    latest_agent_data[hostname] = data

    # Inicializar historial si no existe
    if hostname not in historial_agent_data:
        historial_agent_data[hostname] = []

    # Guardar copia en historial
    historial_agent_data[hostname].append(data.copy())

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
