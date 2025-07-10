import datetime
import time

# Últimos datos de cada dispositivo
latest_agent_data = {}

# Historial real de los últimos 10 registros por dispositivo
historial_agent_data = {}

# Nueva variable para almacenar la información de hardware estática por agente
hardware_info_by_agent = {} # Nuevo: Almacena info detallada del hardware

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

    # --- Nuevo: Manejar la información detallada de hardware ---
    if 'hardware_info' in data:
        hardware_info_by_agent[hostname] = data['hardware_info']
        # Es buena práctica eliminar 'hardware_info' de los datos que se guardan repetidamente
        # en latest_agent_data y historial_agent_data para evitar redundancia y reducir memoria.
        data_to_save = data.copy() # Copia para modificar sin alterar el 'data' original
        del data_to_save['hardware_info']
    else:
        # Si no hay hardware_info en este envío, usa los datos tal cual
        data_to_save = data
    # --- Fin de la nueva parte ---

    # Guardar último dato actualizado
    latest_agent_data[hostname] = data_to_save # Usamos data_to_save aquí

    # Inicializar historial si no existe
    if hostname not in historial_agent_data:
        historial_agent_data[hostname] = []

    # Guardar copia en historial
    historial_agent_data[hostname].append(data_to_save.copy()) # Usamos data_to_save aquí también

    # Limitar historial a 10 registros
    if len(historial_agent_data[hostname]) > 10: # Tu límite es 10, no 20 como propuse. Lo mantengo.
        historial_agent_data[hostname].pop(0)

def get_all_agent_data_sorted():
    """
    Devuelve los dispositivos ordenados por último timestamp descendente.
    """
    # Se obtienen los datos directamente de latest_agent_data, que ya tiene la info sin 'hardware_info'
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

# --- Nuevo: Función para obtener la información de hardware detallada ---
def get_detailed_hardware_info(hostname):
    """
    Devuelve la información de hardware estática para un hostname específico.
    """
    return hardware_info_by_agent.get(hostname)

# --- Puedes añadir esta función si la usas en el dashboard o detalle para el riesgo ---
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