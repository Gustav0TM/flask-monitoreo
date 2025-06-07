import datetime
import time

latest_agent_data = {}

def save_agent_data(data):
    hostname = data.get("hostname")
    if hostname:
        data["timestamp"] = int(datetime.datetime.now().timestamp())
                
        latest_agent_data[hostname] = data

def limpiar_dispositivos_inactivos():
    ahora = time.time()
    limite = ahora - 300  # 5 minutos = 300 segundos
    # Filtra y deja solo los dispositivos con timestamp reciente
    activos = {k: v for k, v in latest_agent_data.items() if v.get("timestamp", 0) > limite}
    # Actualiza el dict global
    latest_agent_data.clear()
    latest_agent_data.update(activos)

def get_all_agent_data():
    return latest_agent_data

def format_datetime(timestamp):
    if timestamp is None:
        return "N/A"
    return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
