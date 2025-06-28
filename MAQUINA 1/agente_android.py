import platform
import socket
import uuid
import psutil
import requests
import time
import random
import os

URL_SERVIDOR = "http://127.0.0.1:5000/datos"
ID_ARCHIVO = "device_id.txt"

def generar_o_cargar_id(): # Genera un ID único o lo carga desde un archivo
    if os.path.exists(ID_ARCHIVO):
        with open(ID_ARCHIVO, "r") as f:
            return f.read().strip() #🔁 Si ya existe, lo reutiliza
    else:
        nuevo_id = str(uuid.uuid4())    # Genera un nuevo ID único aleatorio
        with open(ID_ARCHIVO, "w") as f:
            f.write(nuevo_id)       # Guarda el nuevo ID en un archivo
        return nuevo_id

def es_android():
    return (
        os.path.exists("/system/build.prop") or
        os.path.exists("/system/app") or
        os.path.exists("/system/priv-app")
    )

def obtener_marca():
    # Intentar leer la marca desde build.prop
    try:
        if os.path.exists("/system/build.prop"):
            with open("/system/build.prop", "r") as f:
                for line in f:
                    if "ro.product.brand" in line:
                        return line.strip().split("=")[-1].upper()
    except:
        pass

    # Si no se pudo leer la marca pero el sistema es Android
    if es_android():
        return "ANDROID"

    # Fallback: usar sistema operativo (Linux, Windows, etc.)
    return platform.system().upper()

def obtener_mac():
    mac_num = hex(uuid.getnode()).replace('0x', '').upper()
    return ':'.join(mac_num[i:i+2] for i in range(0, 11, 2))

def obtener_datos():
    device_id = generar_o_cargar_id()
    marca = obtener_marca()

    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    memory_percent = mem.percent
    memory_total_gb = round(mem.total / (1024 ** 3), 2)
    memory_used_gb = round(mem.used / (1024 ** 3), 2)

    disk_percent = disk.percent
    disk_total_gb = round(disk.total / (1024 ** 3), 2)
    disk_used_gb = round(disk.used / (1024 ** 3), 2)

    cpu_percent = round(random.uniform(5, 90), 2)
    bytes_sent_mb = round(random.uniform(100, 2000), 2)
    bytes_recv_mb = round(random.uniform(100, 2000), 2)
    cpu_temp_celsius = round(random.uniform(35, 85), 2)

    calculated_risk_percent = round((cpu_percent + memory_percent + disk_percent) / 3, 2)

    return {
        "hostname": f"{marca}_{device_id[:8]}",
        "timestamp": time.time(),
        "cpu_percent": cpu_percent,
        "memory_percent": memory_percent,
        "memory_total_gb": memory_total_gb,
        "memory_used_gb": memory_used_gb,
        "disk_percent": disk_percent,
        "disk_total_gb": disk_total_gb,
        "disk_used_gb": disk_used_gb,
        "bytes_sent_mb": bytes_sent_mb,
        "bytes_recv_mb": bytes_recv_mb,
        "calculated_risk_percent": calculated_risk_percent,
        "cpu_temp_celsius": cpu_temp_celsius,
        "origen": marca
    }

def enviar_datos():
    while True:
        datos = obtener_datos()
        try:
            print(f"📡 Enviando desde: {datos['hostname']}...")
            response = requests.post(URL_SERVIDOR, json=datos)
            print("✅ Enviado:", response.status_code)
        except Exception as e:
            print("❌ Error al enviar datos:", e)
        time.sleep(5) # Espera 5 segundos antes de enviar nuevamente

if __name__ == "__main__":
    print("🚀 Iniciando agente de monitoreo...")
    enviar_datos()
