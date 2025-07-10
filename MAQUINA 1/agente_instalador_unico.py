import os
import sys
import time
import psutil
import platform
import requests
import json
import subprocess
import wmi # Necesario para la recolección de información detallada de hardware

# URL del servidor Flask donde se envían los datos
FLASK_APP_URL = "https://mi-monitor-red.onrender.com/receive_data"  # Cambiar por IP real si es necesario

# Detectar la ruta base
if getattr(sys, 'frozen', False):
    RUTA_BASE = os.path.dirname(sys.executable)
else:
    RUTA_BASE = os.path.dirname(os.path.abspath(__file__))
#RUTA_BASE = r"C:\Program Files (x86)\AgenteMonitoreo"

# Ruta de LibreHardwareMonitor dentro de LibreHardwareMonitor-net472
RUTA_LHM = os.path.join(RUTA_BASE, "LibreHardwareMonitor-net472", "LibreHardwareMonitor.exe")

# Variable global para almacenar la información de hardware estática
GLOBAL_HARDWARE_INFO = None

def lanzar_lhm():
    """ Inicia LibreHardwareMonitor de forma oculta """
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        # Utiliza shell=True solo si el comando es un archivo de script o necesita PATH
        # Para un .exe directo, no suele ser necesario y puede introducir riesgos de seguridad
        subprocess.Popen([RUTA_LHM], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, startupinfo=startupinfo)
        print("✅ LibreHardwareMonitor iniciado.")
    except Exception as e:
        # Aquí es donde se captura el WinError 740 si no se ejecuta como administrador
        print(f"❌ Error al iniciar LibreHardwareMonitor: {e}")

def get_cpu_temperature():
    """ Obtiene la temperatura usando LibreHardwareMonitor (WMI) """
    try:
        # Importar wmi aquí si solo se usa en esta función, o globalmente si es para todo el archivo
        # Ya está globalmente, así que no es necesario aquí, pero lo dejo como recordatorio
        # import wmi 
        c = wmi.WMI(namespace="root\\LibreHardwareMonitor")
        for sensor in c.Sensor():
            if sensor.SensorType == u'Temperature' and 'CPU' in sensor.Name:
                return round(sensor.Value, 1)
    except Exception:
        pass
    return None

def safe_get_attribute(obj, attr_name, default_value="N/A"):
    """
    Intenta obtener un atributo de un objeto y devuelve un valor por defecto
    si el atributo no existe o es None.
    """
    try:
        value = getattr(obj, attr_name, None)
        return value.strip() if isinstance(value, str) else value if value is not None else default_value
    except Exception:
        return default_value

def get_cpu_cache_info():
    """
    Intenta obtener información detallada de la caché de la CPU
    usando WMI (puede variar la disponibilidad y el detalle).
    """
    cache_info = []
    try:
        c = wmi.WMI()
        caches = c.Win32_CacheMemory()
        for cache in caches:
            cache_level = safe_get_attribute(cache, 'Level')
            cache_installed_size = safe_get_attribute(cache, 'InstalledSize')
            cache_size_kb = round(cache_installed_size / 1024, 0) if isinstance(cache_installed_size, (int, float)) else 'N/A'
            cache_type = safe_get_attribute(cache, 'CacheType')
            cache_associativity = safe_get_attribute(cache, 'Associativity')
            cache_info.append(f"Nivel {cache_level}: {cache_size_kb} KB ({cache_type}, {cache_associativity})")
    except Exception as e:
        # print(f"Error al obtener info de caché: {e}")
        pass # No es crítico si no se puede obtener
    return cache_info

def get_detailed_system_hardware_info():
    """
    Recolecta información técnica detallada del hardware del sistema Windows
    simulando la información de CPU-Z.
    """
    info = {}
    try:
        c = wmi.WMI()

        # --- Procesador (CPU Tab) ---
        cpu = c.Win32_Processor()[0]
        info["Processor"] = {
            "Name": safe_get_attribute(cpu, 'Name'),
            "Manufacturer": safe_get_attribute(cpu, 'Manufacturer'),
            "Description": safe_get_attribute(cpu, 'Description'),
            "NumberOfCores": safe_get_attribute(cpu, 'NumberOfCores', 0),
            "NumberOfLogicalProcessors": safe_get_attribute(cpu, 'NumberOfLogicalProcessors', 0), # Threads
            "Architecture": platform.machine(), # 'AMD64' para 64-bit
            "Family": safe_get_attribute(cpu, 'Family'),
            "Model": safe_get_attribute(cpu, 'Model'), # Este era el que fallaba, ahora con safe_get_attribute
            "Stepping": safe_get_attribute(cpu, 'Stepping'),
            "ProcessorId": safe_get_attribute(cpu, 'ProcessorId'), # Para "Brand ID"
            "CurrentClockSpeed_MHz": safe_get_attribute(cpu, 'CurrentClockSpeed'),
            "MaxClockSpeed_MHz": safe_get_attribute(cpu, 'MaxClockSpeed'),
            "L2CacheSize_KB": round(safe_get_attribute(cpu, 'L2CacheSize', 0) / 1024, 0) if safe_get_attribute(cpu, 'L2CacheSize', 0) else 'N/A',
            "L3CacheSize_KB": round(safe_get_attribute(cpu, 'L3CacheSize', 0) / 1024, 0) if safe_get_attribute(cpu, 'L3CacheSize', 0) else 'N/A',
            "Instructions": "N/A" # No directamente accesible via WMI de forma detallada
        }
        # Intentar obtener info de caché más detallada (aunque WMI puede ser limitado aquí)
        info["Processor"]["CacheDetails"] = get_cpu_cache_info()


        # --- Placa Madre (Mainboard Tab) ---
        board = c.Win32_BaseBoard()[0]
        bios = c.Win32_BIOS()[0]
        info["Mainboard"] = {
            "Manufacturer": safe_get_attribute(board, 'Manufacturer'),
            "Model": safe_get_attribute(board, 'Product'),
            "SerialNumber": safe_get_attribute(board, 'SerialNumber'),
            "Chipset": "N/A", # Difícil de obtener directamente via WMI genérico
            "BIOS_Vendor": safe_get_attribute(bios, 'Manufacturer'),
            "BIOS_Version": safe_get_attribute(bios, 'SMBIOSBIOSVersion'),
            "BIOS_Date": safe_get_attribute(bios, 'ReleaseDate')[:4] + '-' + safe_get_attribute(bios, 'ReleaseDate')[4:6] + '-' + safe_get_attribute(bios, 'ReleaseDate')[6:8] if safe_get_attribute(bios, 'ReleaseDate') else "N/A"
        }

        # --- Memoria (Memory Tab) ---
        mem_info = psutil.virtual_memory()
        total_memory_gb = round(mem_info.total / (1024**3), 2)
        ram_modules = c.Win32_PhysicalMemory()
        
        memory_details = []
        for i, module in enumerate(ram_modules):
            try:
                capacity_gb = round(int(safe_get_attribute(module, 'Capacity', 0)) / (1024**3), 2) if safe_get_attribute(module, 'Capacity', 0) else "N/A"
                speed_mhz = safe_get_attribute(module, 'Speed')
                manufacturer = safe_get_attribute(module, 'Manufacturer')
                part_number = safe_get_attribute(module, 'PartNumber')
                serial_number = safe_get_attribute(module, 'SerialNumber')
                device_locator = safe_get_attribute(module, 'DeviceLocator') # Slot info

                memory_details.append({
                    "Slot": device_locator,
                    "Capacity_GB": capacity_gb,
                    "Speed_MHz": speed_mhz,
                    "Manufacturer": manufacturer,
                    "Part_Number": part_number,
                    "Serial_Number": serial_number
                })
            except Exception:
                continue # Continuar con los demás módulos

        info["Memory"] = {
            "Total_Installed_GB": total_memory_gb,
            "Number_of_Memory_Modules": len(ram_modules),
            "Details": memory_details,
            "Type": "N/A" # Tipo general (DDR4, DDR5) es difícil de inferir sin SPD/DIMM
        }

        # --- Gráficos (Graphics Tab) ---
        gpus = c.Win32_VideoController()
        graphics_details = []
        for gpu in gpus:
            graphics_details.append({
                "Name": safe_get_attribute(gpu, 'Name'),
                "Manufacturer": safe_get_attribute(gpu, 'AdapterDACType'), # Esto es más un tipo DAC
                "Driver_Version": safe_get_attribute(gpu, 'DriverVersion'),
                "VRAM_MB": round(int(safe_get_attribute(gpu, 'AdapterRAM', 0)) / (1024**2), 1) if safe_get_attribute(gpu, 'AdapterRAM', 0) else "N/A",
                "Resolution": f"{safe_get_attribute(gpu, 'CurrentHorizontalResolution', 'N/A')}x{safe_get_attribute(gpu, 'CurrentVerticalResolution', 'N/A')}"
            })
        info["Graphics"] = graphics_details

        # --- Discos (Aunque CPU-Z no tiene una pestaña de discos, es útil para monitoreo) ---
        disks_info = []
        for disk in c.Win32_DiskDrive():
            disks_info.append({
                "Model": safe_get_attribute(disk, 'Model'),
                "SerialNumber": safe_get_attribute(disk, 'SerialNumber'),
                "Size_GB": round(int(safe_get_attribute(disk, 'Size', 0)) / (1024**3), 2) if safe_get_attribute(disk, 'Size', 0) else "N/A",
                "InterfaceType": safe_get_attribute(disk, 'InterfaceType')
            })
        info["Disks"] = disks_info

        # --- Sistema Operativo (OS) ---
        os_info = c.Win32_OperatingSystem()[0]
        info["OS"] = {
            "Name": safe_get_attribute(os_info, 'Caption'),
            "Architecture": safe_get_attribute(os_info, 'OSArchitecture'),
            "Version": safe_get_attribute(os_info, 'Version'),
            "BuildNumber": safe_get_attribute(os_info, 'BuildNumber'),
            "InstallDate": safe_get_attribute(os_info, 'InstallDate')[:8] if safe_get_attribute(os_info, 'InstallDate') else "N/A", # YYYYMMDD
            "RegisteredUser": safe_get_attribute(os_info, 'RegisteredUser')
        }

    except wmi.x_wmi as e: # Captura específica para errores de WMI si la librería los expone así
        print(f"❌ Error WMI al recolectar info detallada: {e}. Asegúrate de ejecutar con permisos de administrador.")
        return {"error": f"Error WMI: {e}. Puede requerir permisos de administrador o WMI no disponible."}
    except Exception as e: # Captura general para cualquier otro error
        print(f"❌ Error general al recolectar información detallada del sistema: {e}")
        return {"error": f"Error general al recolectar información: {e}"}

    return info

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

    # Calcular disk_percent solo si hay discos
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
    
    # Si la información de hardware estática no ha sido recolectada, hazlo ahora y envíala.
    global GLOBAL_HARDWARE_INFO
    if GLOBAL_HARDWARE_INFO is None:
        print("⚙️ Recolectando información detallada de hardware por primera vez...")
        GLOBAL_HARDWARE_INFO = get_detailed_system_hardware_info()
        if "error" in GLOBAL_HARDWARE_INFO:
            print(f"⚠️ Atención: No se pudo recolectar toda la información de hardware: {GLOBAL_HARDWARE_INFO['error']}")
        else:
            print("✅ Información detallada de hardware recolectada.")
            
    # Adjuntar la información de hardware al diccionario de métricas
    # Siempre se envía la info de hardware una vez que se ha recolectado.
    metrics["hardware_info"] = GLOBAL_HARDWARE_INFO

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
    lanzar_lhm()
    print("🔄 Iniciando monitoreo...")

    while True:
        datos = get_system_metrics()
        send_data_to_server(datos)
        time.sleep(5)