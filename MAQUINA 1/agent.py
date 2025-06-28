import psutil
import platform
import time
import requests
import json

# URL de tu aplicación Flask donde el agente enviará los datos
# Asegúrate de que esta URL sea accesible desde la máquina donde corre el agente.
# Si tu app Flask corre en localhost, necesitarás la IP de tu servidor si el agente está en otra máquina.
FLASK_APP_URL = "http://127.0.0.1:5000/receive_data" # Cambia esto a la IP/dominio real de tu servidor Flask


def get_system_metrics():
    # Obtener uso de CPU
    cpu_percent = psutil.cpu_percent(interval=1) # Porcentaje de uso de CPU en el último segundo

    # Obtener uso de memoria (RAM)
    mem_info = psutil.virtual_memory()
    mem_percent = mem_info.percent
    mem_total_gb = round(mem_info.total / (1024**3), 2)
    mem_used_gb = round(mem_info.used / (1024**3), 2)

    # Obtener uso de disco
    disk_info = psutil.disk_usage('/') # Para la raíz del sistema de archivos, ajusta según sea necesario para Windows (e.g., 'C:')
    disk_percent = disk_info.percent
    disk_total_gb = round(disk_info.total / (1024**3), 2)
    disk_used_gb = round(disk_info.used / (1024**3), 2)

    # Información de la red
    net_io = psutil.net_io_counters()
    bytes_sent_mb = round(net_io.bytes_sent / (1024**2), 2)
    bytes_recv_mb = round(net_io.bytes_recv / (1024**2), 2)

    # Nombre del host para identificar la máquina
    hostname = platform.node()

    # Puedes añadir la temperatura si tienes sensores que psutil pueda leer (más complejo, depende del OS y hardware)
    # Ejemplo básico si estuviera disponible:
    # try:
    #     temps = psutil.sensors_temperatures()
    #     cpu_temp = temps['coretemp'][0].current # Esto es un ejemplo, el nombre puede variar
    # except AttributeError:
    #     cpu_temp = None # No disponible
    # except KeyError:
    #     cpu_temp = None # No disponible

    metrics = {
        "hostname": hostname,
        "timestamp": time.time(),
        "cpu_percent": cpu_percent,
        "memory_percent": mem_percent,
        "memory_total_gb": mem_total_gb,
        "memory_used_gb": mem_used_gb,
        "disk_percent": disk_percent,
        "disk_total_gb": disk_total_gb,
        "disk_used_gb": disk_used_gb,
        "bytes_sent_mb": bytes_sent_mb,
        "bytes_recv_mb": bytes_recv_mb,
    }

    # Agregar el riesgo calculado (promedio simple de CPU, RAM y Disco)
    calculated_risk_percent = round((cpu_percent + mem_percent + disk_percent) / 3, 2)
    metrics["calculated_risk_percent"] = calculated_risk_percent

    return metrics

def send_data_to_server(data):
    try:
        response = requests.post(FLASK_APP_URL, json=data, timeout=5)
        if response.status_code == 200:
            print(f"Datos enviados exitosamente: {data['hostname']}")
        else:
            print(f"Error al enviar datos. Código de estado: {response.status_code}, Respuesta: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión al enviar datos: {e}")

if __name__ == "__main__":
    print("Iniciando agente de monitoreo...")
    while True:
        system_data = get_system_metrics()
        print(f"Recopilando datos de {system_data['hostname']}...")
        send_data_to_server(system_data)
        time.sleep(5) # python  recibe en segundos, espera 5 segundos antes de la próxima recopilación