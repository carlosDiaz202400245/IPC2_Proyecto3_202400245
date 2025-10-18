import xml.etree.ElementTree as ET
from xml.dom import minidom

def parsear_xml(xml_string):
    """Parsear string XML y retornar elemento raíz"""
    try:
        return ET.fromstring(xml_string)
    except ET.ParseError as e:
        raise ValueError(f"Error parseando XML: {str(e)}")

def crear_xml_desde_dict(data_dict, root_tag):
    """Crear XML desde un diccionario (útil para respuestas)"""
    root = ET.Element(root_tag)
    _agregar_elementos_desde_dict(root, data_dict)
    return _prettify_xml(root)

def _agregar_elementos_desde_dict(parent, data_dict):
    """Función auxiliar recursiva para agregar elementos desde dict"""
    for key, value in data_dict.items():
        if isinstance(value, dict):
            child = ET.SubElement(parent, key)
            _agregar_elementos_desde_dict(child, value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    child = ET.SubElement(parent, key)
                    _agregar_elementos_desde_dict(child, item)
                else:
                    ET.SubElement(parent, key).text = str(item)
        else:
            ET.SubElement(parent, key).text = str(value)

def _prettify_xml(elem):
    """Convertir elemento XML a string formateado"""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def validar_xml_contra_esquema(xml_string, esquema_path):
    """
    Validar XML contra un esquema XSD
    """
    
    return True, "Validación XSD no implementada aún"

def encontrar_elemento_texto(elemento, tag, default=None):
    """Encontrar texto de un elemento de forma segura"""
    elem = elemento.find(tag)
    return elem.text if elem is not None else default

def encontrar_elemento_attr(elemento, attr, default=None):
    """Encontrar atributo de un elemento de forma segura"""
    return elemento.get(attr, default)