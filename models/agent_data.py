import datetime
import time

latest_agent_data = {}

def save_agent_data(data):
    hostname = data.get("hostname")
    if hostname:
        data["timestamp"] = int(datetime.datetime.now().timestamp())
        latest_agent_data[hostname] = data

def get_all_agent_data_sorted():
    # Retorna los datos ordenados por timestamp descendente (más recientes primero)
    return dict(
        sorted(
            latest_agent_data.items(),
            key=lambda item: item[1].get("timestamp", 0),
            reverse=True
        )
    )

def get_all_agent_data():
    # Retorna sin ordenar (por si acaso necesitas la versión original)
    return latest_agent_data

def format_datetime(timestamp):
    if timestamp is None:
        return "N/A"
    return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
