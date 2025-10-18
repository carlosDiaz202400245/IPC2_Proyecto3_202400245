from datetime import datetime, timedelta
import re


def parsear_fecha(fecha_str):
    """Convertir string dd/mm/yyyy a objeto datetime"""
    try:
        return datetime.strptime(fecha_str, '%d/%m/%Y')
    except ValueError:
        return None


def formatear_fecha(fecha_dt):
    """Convertir objeto datetime a string dd/mm/yyyy"""
    return fecha_dt.strftime('%d/%m/%Y')


def calcular_diferencia_horas(fecha_inicio_str, fecha_fin_str):
    """
    segun el doc:
    Calcular diferencia en horas entre dos fechas
    Asume formato dd/mm/yyyy o dd/mm/yyyy hh:mi
    """
    try:
        # Intentar parsear con hora primero
        try:
            inicio = datetime.strptime(fecha_inicio_str, '%d/%m/%Y %H:%M')
            fin = datetime.strptime(fecha_fin_str, '%d/%m/%Y %H:%M')
        except ValueError:
            # Si falla, intentar solo con fecha
            inicio = datetime.strptime(fecha_inicio_str, '%d/%m/%Y')
            fin = datetime.strptime(fecha_fin_str, '%d/%m/%Y')

        diferencia = fin - inicio
        return diferencia.total_seconds() / 3600.0  # Convertir a horas

    except ValueError:
        return 0.0


def es_rango_fecha_valido(fecha_inicio_str, fecha_fin_str):
    """Validar que el rango de fechas sea válido (fecha_inicio <= fecha_fin)"""
    fecha_inicio = parsear_fecha(fecha_inicio_str)
    fecha_fin = parsear_fecha(fecha_fin_str)

    if not fecha_inicio or not fecha_fin:
        return False

    return fecha_inicio <= fecha_fin


def obtener_fecha_actual():
    """Obtener fecha actual en formato dd/mm/yyyy"""
    return datetime.now().strftime('%d/%m/%Y')


def obtener_mes_anio_desde_fecha(fecha_str):
    """Extraer mes y año desde una fecha string"""
    fecha = parsear_fecha(fecha_str)
    if fecha:
        return fecha.strftime('%m/%Y')
    return None