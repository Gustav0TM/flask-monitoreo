import datetime
import time
from firebase_config import firebase_manager
from firebase_admin import firestore

# Mantener datos en memoria para acceso rápido
latest_agent_data = {}
historial_agent_data = {}

def save_agent_data(data):
    """
    Guarda los datos del agente tanto en memoria como en Firebase
    """
    hostname = data.get("hostname")
    if not hostname:
        return

    timestamp = int(datetime.datetime.now().timestamp())
    data["timestamp"] = timestamp
    data["datetime"] = datetime.datetime.now().isoformat()

    # Guardar en memoria (para acceso rápido)
    latest_agent_data[hostname] = data
    
    # Inicializar historial si no existe
    if hostname not in historial_agent_data:
        historial_agent_data[hostname] = []
    
    # Guardar copia en historial en memoria
    historial_agent_data[hostname].append(data.copy())
    
    # Limitar historial en memoria a 10 registros
    if len(historial_agent_data[hostname]) > 10:
        historial_agent_data[hostname].pop(0)

    # Guardar en Firebase
    save_to_firebase(data)

def save_to_firebase(data):
    """
    Guarda los datos en Firebase Firestore
    """
    try:
        db = firebase_manager.get_db()
        if not db:
            print("Firebase no está conectado")
            return
        
        hostname = data.get("hostname")
        
        # Colección: dispositivos/{hostname}/historico/{timestamp}
        doc_ref = db.collection('dispositivos').document(hostname).collection('historico').document(str(data["timestamp"]))
        doc_ref.set(data)
        
        # Actualizar último registro
        latest_ref = db.collection('dispositivos').document(hostname)
        latest_ref.set({
            'hostname': hostname,
            'ultimo_registro': data,
            'ultima_actualizacion': datetime.datetime.now()
        })
        
        print(f"✓ Datos guardados en Firebase para {hostname}")
        
    except Exception as e:
        print(f"✗ Error al guardar en Firebase: {str(e)}")

def get_historical_data_from_firebase(hostname, limit=100):
    """
    Obtiene datos históricos desde Firebase
    """
    try:
        db = firebase_manager.get_db()
        if not db:
            return []
        
        # Obtener últimos registros ordenados por timestamp
        docs = db.collection('dispositivos').document(hostname).collection('historico').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit).stream()
        
        historical_data = []
        for doc in docs:
            historical_data.append(doc.to_dict())
        
        # Revertir orden para mostrar cronológicamente
        historical_data.reverse()
        return historical_data
        
    except Exception as e:
        print(f"✗ Error al obtener datos históricos: {str(e)}")
        return []

def get_all_devices_from_firebase():
    """
    Obtiene todos los dispositivos desde Firebase
    """
    try:
        db = firebase_manager.get_db()
        if not db:
            return {}
        
        devices = {}
        docs = db.collection('dispositivos').stream()
        
        for doc in docs:
            data = doc.to_dict()
            if 'ultimo_registro' in data:
                devices[doc.id] = data['ultimo_registro']
        
        return devices
        
    except Exception as e:
        print(f"✗ Error al obtener dispositivos: {str(e)}")
        return {}

def sync_with_firebase():
    """
    Sincroniza los datos en memoria con Firebase al iniciar la aplicación
    """
    try:
        global latest_agent_data, historial_agent_data
        
        # Obtener últimos datos de todos los dispositivos
        firebase_devices = get_all_devices_from_firebase()
        
        if firebase_devices:
            latest_agent_data.update(firebase_devices)
            print(f"✓ Sincronizados {len(firebase_devices)} dispositivos desde Firebase")
        
        # Obtener historial reciente para cada dispositivo
        for hostname in latest_agent_data.keys():
            recent_history = get_historical_data_from_firebase(hostname, 10)
            if recent_history:
                historial_agent_data[hostname] = recent_history[-10:]  # Últimos 10
        
    except Exception as e:
        print(f"✗ Error en sincronización: {str(e)}")

# Funciones existentes mantenidas para compatibilidad
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
    Primero intenta desde memoria, si no hay suficientes datos, consulta Firebase.
    """
    # Datos en memoria
    memory_data = historial_agent_data.get(hostname, [])
    
    # Si tenemos pocos datos en memoria, consultamos Firebase
    if len(memory_data) < 10:
        firebase_data = get_historical_data_from_firebase(hostname, 50)
        if firebase_data:
            # Actualizar memoria con datos más completos
            historial_agent_data[hostname] = firebase_data[-10:]
            return firebase_data
    
    return memory_data

def obtener_ultimo_dato(hostname):
    """
    Devuelve el último dato registrado de un dispositivo.
    """
    return latest_agent_data.get(hostname)

def get_device_statistics(hostname, days=7):
    """
    Obtiene estadísticas del dispositivo de los últimos N días desde Firebase
    """
    try:
        db = firebase_manager.get_db()
        if not db:
            return None
        
        # Calcular timestamp de hace N días
        end_time = datetime.datetime.now()
        start_time = end_time - datetime.timedelta(days=days)
        start_timestamp = int(start_time.timestamp())
        
        # Consultar datos del período
        docs = db.collection('dispositivos').document(hostname).collection('historico').where('timestamp', '>=', start_timestamp).order_by('timestamp').stream()
        
        data_points = []
        for doc in docs:
            data_points.append(doc.to_dict())
        
        if not data_points:
            return None
        
        # Calcular estadísticas
        cpu_values = [d.get('cpu_percent', 0) for d in data_points]
        memory_values = [d.get('memory_percent', 0) for d in data_points]
        disk_values = [d.get('disk_percent', 0) for d in data_points]
        
        stats = {
            'total_records': len(data_points),
            'period_days': days,
            'cpu_stats': {
                'avg': sum(cpu_values) / len(cpu_values),
                'max': max(cpu_values),
                'min': min(cpu_values)
            },
            'memory_stats': {
                'avg': sum(memory_values) / len(memory_values),
                'max': max(memory_values),
                'min': min(memory_values)
            },
            'disk_stats': {
                'avg': sum(disk_values) / len(disk_values),
                'max': max(disk_values),
                'min': min(disk_values)
            }
        }
        
        return stats
        
    except Exception as e:
        print(f"✗ Error al obtener estadísticas: {str(e)}")
        return None