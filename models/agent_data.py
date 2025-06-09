import datetime
import time

latest_agent_data = {}

def save_agent_data(data):
    hostname = data.get("hostname")
    if hostname:
        data["timestamp"] = int(datetime.datetime.now().timestamp())
        latest_agent_data[hostname] = data

def ordenar_dispositivos_por_estado():
    ahora = time.time()
    limite = ahora - 300  # 5 minutos = 300 segundos

    # Ordena primero activos (timestamp > limite), luego inactivos
    ordenados = dict(sorted(
        latest_agent_data.items(),
        key=lambda item: 0 if item[1].get("timestamp", 0) > limite else 1
    ))

    latest_agent_data.clear()
    latest_agent_data.update(ordenados)

def get_all_agent_data():
    return latest_agent_data

def format_datetime(timestamp):
    if timestamp is None:
        return "N/A"
    return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
