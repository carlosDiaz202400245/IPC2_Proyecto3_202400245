import re
from datetime import datetime


def validar_nit(nit):
    """
    segun doc:
    Validar formato de NIT según especificaciones del proyecto.
    Formato: sucesión de números seguidos por guion y dígito de validación (0-9 o K)
    Ejemplos válidos: "34300-4", "110339001-K", "1234567-8"
    """
    if not nit:
        return False

    # expresion regular
    patron = r'^\d+-\d|[Kk]$'
    return re.match(patron, nit) is not None


def extraer_fecha(texto_fecha):
    """
    segun el doc:
    Extraer fecha del formato dd/mm/yyyy de un texto según especificaciones.
    - Puede contener cualquier hilera mientras tenga una secuencia dd/mm/yyyy válida
    - Si hay múltiples fechas, usar la primera válida
    - Retorna la fecha en formato string dd/mm/yyyy o None si no se encuentra
    """
    if not texto_fecha:
        return None

    # Buscar patrones de fecha dd/mm/yyyy
    patron = r'(\d{2}/\d{2}/\d{4})'
    coincidencias = re.findall(patron, texto_fecha)

    for fecha_str in coincidencias:
        try:
            # Validar que sea una fecha real
            dia, mes, anio = map(int, fecha_str.split('/'))
            datetime(anio, mes, dia)  # Esto lanzará ValueError si la fecha es inválida
            return fecha_str
        except ValueError:
            continue  # Fecha inválida, probar con la siguiente

    return None


def extraer_fecha_hora(texto_fecha_hora):
    """
    segun el enunciado:
    Extraer fecha y hora del formato dd/mm/yyyy hh24:mi
    - Aplica las mismas reglas que extraer_fecha pero incluye hora
    - Retorna string en formato "dd/mm/yyyy hh:mi" o None si no se encuentra
    """
    if not texto_fecha_hora:
        return None

    # Buscar patrones de fecha y hora dd/mm/yyyy hh:mi
    patron = r'(\d{2}/\d{2}/\d{4} \d{2}:\d{2})'
    coincidencias = re.findall(patron, texto_fecha_hora)

    for fecha_hora_str in coincidencias:
        try:
            # Separar fecha y hora
            fecha_str, hora_str = fecha_hora_str.split(' ')
            dia, mes, anio = map(int, fecha_str.split('/'))
            hora, minuto = map(int, hora_str.split(':'))

            # Validar rangos
            if 1 <= dia <= 31 and 1 <= mes <= 12 and hora < 24 and minuto < 60:
                datetime(anio, mes, dia, hora, minuto)
                return fecha_hora_str
        except ValueError:
            continue

    return None


def validar_estado_instancia(estado):
    """Validar que el estado de instancia sea 'Vigente' o 'Cancelada'"""
    return estado in ['Vigente', 'Cancelada']


def validar_tipo_recurso(tipo):
    """Validar que el tipo de recurso sea 'Hardware' o 'Software'"""
    return tipo in ['Hardware', 'Software']


def validar_valor_positivo(valor, nombre_campo=""):
    """Validar que un valor numérico sea positivo"""
    try:
        valor_float = float(valor)
        if valor_float >= 0:
            return True, valor_float
        else:
            return False, f"{nombre_campo} debe ser positivo"
    except (ValueError, TypeError):
        return False, f"{nombre_campo} debe ser un número válido"


def validar_id(id_valor, nombre_entidad=""):
    """Validar que un ID sea un entero positivo"""
    try:
        id_int = int(id_valor)
        if id_int > 0:
            return True, id_int
        else:
            return False, f"ID de {nombre_entidad} debe ser positivo"
    except (ValueError, TypeError):
        return False, f"ID de {nombre_entidad} debe ser un número entero"