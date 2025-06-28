import os
import sys
import time
import psutil
import platform
import requests
import json
import subprocess

# URL del servidor Flask donde se envían los datos
FLASK_APP_URL = "https://mi-monitor-red.onrender.com/receive_data"  # Cambiar por IP real si es necesario

# Detectar la ruta base
if getattr(sys, 'frozen', False):
    RUTA_BASE = os.path.dirname(sys.executable)
else:
    RUTA_BASE = os.path.dirname(os.path.abspath(__file__))

# Ruta de OpenHardwareMonitor dentro de ohm_files
RUTA_OHM = os.path.join(RUTA_BASE, "OpenHardwareMonitor", "OpenHardwareMonitor.exe")

def lanzar_ohm():
    """ Inicia OpenHardwareMonitor de forma oculta """
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        subprocess.Popen([RUTA_OHM], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, startupinfo=startupinfo)
        print("✅ OpenHardwareMonitor iniciado.")
    except Exception as e:
        print(f"❌ Error al iniciar OpenHardwareMonitor: {e}")

def get_cpu_temperature():
    """ Obtiene la temperatura usando OpenHardwareMonitor (WMI) """
    try:
        import wmi
        c = wmi.WMI(namespace="root\\OpenHardwareMonitor")
        for sensor in c.Sensor():
            if sensor.SensorType == u'Temperature' and 'CPU' in sensor.Name:
                return round(sensor.Value, 1)
    except:
        pass
    return None

def get_system_metrics():
    """ Recolecta métricas del sistema """
    cpu_percent = psutil.cpu_percent(interval=1)
    mem_info = psutil.virtual_memory()
    mem_percent = mem_info.percent
    mem_total_gb = round(mem_info.total / (1024**3), 2)
    mem_used_gb = round(mem_info.used / (1024**3), 2)

    disks, disks_used_gb, disks_total_gb = {}, {}, {}
    for partition in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            disks[partition.device] = round(usage.percent, 1)
            disks_used_gb[partition.device] = round(usage.used / (1024**3), 2)
            disks_total_gb[partition.device] = round(usage.total / (1024**3), 2)
        except PermissionError:
            continue

    disk_percent = round(sum(disks.values()) / len(disks), 2) if disks else 0
    net_io = psutil.net_io_counters()
    hostname = platform.node()
    cpu_temp = get_cpu_temperature()

    metrics = {
        "hostname": hostname,
        "timestamp": time.time(),
        "cpu_percent": cpu_percent,
        "memory_percent": mem_percent,
        "memory_total_gb": mem_total_gb,
        "memory_used_gb": mem_used_gb,
        "disk_percent": disk_percent,
        "disks": disks,
        "disks_used_gb": disks_used_gb,
        "disks_total_gb": disks_total_gb,
        "bytes_sent_mb": round(net_io.bytes_sent / (1024**2), 2),
        "bytes_recv_mb": round(net_io.bytes_recv / (1024**2), 2),
        "cpu_temperature": cpu_temp
    }

    calculated_risk_percent = round((cpu_percent + mem_percent + disk_percent) / 3, 2)
    metrics["calculated_risk_percent"] = calculated_risk_percent
    return metrics

def send_data_to_server(data):
    """ Envía los datos al servidor """
    try:
        response = requests.post(FLASK_APP_URL, json=data, timeout=5)
        if response.status_code == 200:
            print(f"✅ Datos enviados exitosamente: {data['hostname']}")
        else:
            print(f"❌ Error al enviar datos. Código: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")

if __name__ == "__main__":
    lanzar_ohm()
    print("🔄 Iniciando monitoreo...")

    while True:
        datos = get_system_metrics()
        send_data_to_server(datos)
        time.sleep(5)
