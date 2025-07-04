from flask import Blueprint, render_template, jsonify, request
from monitoring_system.models.agent_data import (
    obtener_datos_historicos_por_host, 
    latest_agent_data,
    get_device_statistics,
    get_historical_data_from_firebase
)

dispositivo_bp = Blueprint('dispositivo', __name__)

@dispositivo_bp.route('/dispositivo/<hostname>')
def detalle_dispositivo(hostname):
    return render_template('dispositivo/detalle.html', hostname=hostname)

@dispositivo_bp.route('/get_device_data/<hostname>')
def get_device_data(hostname):
    # Obtener datos históricos (puede venir de Firebase si es necesario)
    historial = obtener_datos_historicos_por_host(hostname)

    riesgo = None
    if hostname in latest_agent_data:
        riesgo = latest_agent_data[hostname].get("calculated_risk_percent")

    ultimo = latest_agent_data.get(hostname, {})

    respuesta = {
        "timestamps": [d['timestamp'] for d in historial],
        "cpu": [d['cpu_percent'] for d in historial],
        "memory": [d['memory_percent'] for d in historial],
        "disk": [d['disk_percent'] for d in historial],
        "tx": [d['bytes_sent_mb'] for d in historial],
        "rx": [d['bytes_recv_mb'] for d in historial],
        "disks": ultimo.get("disks", {}),
        "disks_used_gb": ultimo.get("disks_used_gb", {}),
        "disks_total_gb": ultimo.get("disks_total_gb", {}),
        "riesgo": riesgo,
        "total_records": len(historial)
    }
    return jsonify(respuesta)

@dispositivo_bp.route('/get_extended_data/<hostname>')
def get_extended_data(hostname):
    """
    Obtiene datos históricos extendidos para análisis más profundo
    """
    try:
        # Obtener parámetros de consulta
        days = request.args.get('days', 7, type=int)
        limit = request.args.get('limit', 100, type=int)
        
        # Obtener datos históricos extendidos
        historical_data = get_historical_data_from_firebase(hostname, limit)
        
        # Obtener estadísticas del período
        stats = get_device_statistics(hostname, days)
        
        # Datos actuales
        current_data = latest_agent_data.get(hostname, {})
        
        response = {
            "hostname": hostname,
            "current_data": current_data,
            "historical_data": historical_data,
            "statistics": stats,
            "total_records": len(historical_data),
            "period_days": days
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({"error": f"Error al obtener datos extendidos: {str(e)}"}), 500

@dispositivo_bp.route('/device_health/<hostname>')
def device_health(hostname):
    """
    Endpoint para evaluar la salud del dispositivo
    """
    try:
        # Obtener estadísticas de la última semana
        stats = get_device_statistics(hostname, 7)
        
        if not stats:
            return jsonify({"error": "No hay datos suficientes"}), 404
        
        # Calcular indicadores de salud
        health_score = 100
        alerts = []
        
        # Evaluar CPU
        if stats['cpu_stats']['avg'] > 80:
            health_score -= 20
            alerts.append("CPU promedio alta")
        
        if stats['cpu_stats']['max'] > 95:
            health_score -= 15
            alerts.append("Picos de CPU críticos")
        
        # Evaluar Memoria
        if stats['memory_stats']['avg'] > 85:
            health_score -= 15
            alerts.append("Memoria promedio alta")
        
        if stats['memory_stats']['max'] > 95:
            health_score -= 10
            alerts.append("Memoria crítica detectada")
        
        # Evaluar Disco
        if stats['disk_stats']['avg'] > 80:
            health_score -= 10
            alerts.append("Espacio en disco bajo")
        
        if stats['disk_stats']['max'] > 90:
            health_score -= 15
            alerts.append("Disco casi lleno")
        
        # Determinar estado
        if health_score >= 80:
            status = "Saludable"
            color = "green"
        elif health_score >= 60:
            status = "Atención"
            color = "orange"
        else:
            status = "Crítico"
            color = "red"
        
        health_report = {
            "hostname": hostname,
            "health_score": max(0, health_score),
            "status": status,
            "color": color,
            "alerts": alerts,
            "statistics": stats,
            "evaluation_period": "7 días"
        }
        
        return jsonify(health_report)
        
    except Exception as e:
        return jsonify({"error": f"Error al evaluar salud: {str(e)}"}), 500