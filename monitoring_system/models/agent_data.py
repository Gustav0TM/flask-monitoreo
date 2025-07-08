import datetime
import time
from monitoring_system.firebase_config import db_ref

# Últimos datos de cada dispositivo
latest_agent_data = {}

# Historial real de los últimos 10 registros por dispositivo
historial_agent_data = {}

def save_agent_data(data):
    """
    Guarda los datos recibidos del agente en Firebase.
    """
    hostname = data.get("hostname")
    if not hostname:
        return

    timestamp = int(datetime.datetime.now().timestamp())
    data["timestamp"] = timestamp

    # Guardar el último dato en la ruta /latest/{hostname}
    db_ref.child('latest').child(hostname).set(data)

    # Guardar en el historial en la ruta /history/{hostname}
    historial_ref = db_ref.child('history').child(hostname).push(data)
    data['firebase_key'] = historial_ref.key


def get_all_agent_data_sorted():
    """
    Devuelve los dispositivos ordenados por último timestamp descendente desde Firebase.
    """
    latest_data = db_ref.child('latest').get()
    if latest_data:
        return dict(sorted(
            latest_data.items(),
            key=lambda item: item[1].get("timestamp", 0),
            reverse=True
        ))
    return {}

def get_all_agent_data():
    """
    Devuelve todos los dispositivos sin ordenar desde Firebase.
    """
    return db_ref.child('latest').get() or {}

def format_datetime(timestamp):
    """
    Formatea un timestamp a formato legible.
    """
    if timestamp is None:
        return "N/A"
    return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def obtener_datos_historicos_por_host(hostname):
    """
    Devuelve la lista de historial de un dispositivo específico desde Firebase.
    """
    historial = db_ref.child('history').child(hostname).get()
    return list(historial.values()) if historial else []

def obtener_ultimo_dato(hostname):
    """
    Devuelve el último dato registrado de un dispositivo desde Firebase.
    """
    latest = db_ref.child('latest').child(hostname).get()
    return latest if latest else {}