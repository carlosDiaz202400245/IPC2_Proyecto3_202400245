import xml.etree.ElementTree as ET
from xml.dom import minidom
import os
from datetime import datetime


class XMLManager:
    def __init__(self, base_path="data"):
        self.base_path = base_path
        self.ensure_directory()

    def ensure_directory(self):
        """Asegurar que el directorio de datos existe"""
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)

    def guardar_recursos(self, recursos):
        """Guardar lista de recursos en XML"""
        root = ET.Element("listaRecursos")

        for recurso in recursos:
            recurso_elem = ET.SubElement(root, "recurso")
            recurso_elem.set("id", str(recurso['id']))

            ET.SubElement(recurso_elem, "nombre").text = recurso['nombre']
            ET.SubElement(recurso_elem, "abreviatura").text = recurso['abreviatura']
            ET.SubElement(recurso_elem, "metrica").text = recurso['metrica']
            ET.SubElement(recurso_elem, "tipo").text = recurso['tipo']
            ET.SubElement(recurso_elem, "valorXhora").text = str(recurso['valorXhora'])

        self._guardar_xml(root, "recursos.xml")

    def cargar_recursos(self):
        """Cargar recursos desde XML"""
        try:
            tree = ET.parse(os.path.join(self.base_path, "recursos.xml"))
            root = tree.getroot()

            recursos = []
            for recurso_elem in root.findall('recurso'):
                recurso = {
                    'id': int(recurso_elem.get('id')),
                    'nombre': recurso_elem.find('nombre').text,
                    'abreviatura': recurso_elem.find('abreviatura').text,
                    'metrica': recurso_elem.find('metrica').text,
                    'tipo': recurso_elem.find('tipo').text,
                    'valorXhora': float(recurso_elem.find('valorXhora').text)
                }
                recursos.append(recurso)

            return recursos
        except FileNotFoundError:
            return []

    def guardar_categorias(self, categorias):
        """Guardar categorías en XML"""
        root = ET.Element("listaCategorias")

        for categoria in categorias:
            categoria_elem = ET.SubElement(root, "categoria")
            categoria_elem.set("id", str(categoria['id']))

            ET.SubElement(categoria_elem, "nombre").text = categoria['nombre']
            ET.SubElement(categoria_elem, "descripcion").text = categoria['descripcion']
            ET.SubElement(categoria_elem, "cargaTrabajo").text = categoria['cargaTrabajo']

            lista_configs = ET.SubElement(categoria_elem, "listaConfiguraciones")
            for config in categoria.get('configuraciones', []):
                config_elem = ET.SubElement(lista_configs, "configuracion")
                config_elem.set("id", str(config['id']))

                ET.SubElement(config_elem, "nombre").text = config['nombre']
                ET.SubElement(config_elem, "descripcion").text = config['descripcion']

                recursos_config = ET.SubElement(config_elem, "recursosConfiguracion")
                for recurso in config.get('recursos', []):
                    recurso_elem = ET.SubElement(recursos_config, "recurso")
                    recurso_elem.set("id", str(recurso['idRecurso']))
                    recurso_elem.text = str(recurso['cantidad'])

        self._guardar_xml(root, "categorias.xml")

    def cargar_categorias(self):
        """Cargar categorías desde XML"""
        try:
            tree = ET.parse(os.path.join(self.base_path, "categorias.xml"))
            root = tree.getroot()

            categorias = []
            for categoria_elem in root.findall('categoria'):
                categoria = {
                    'id': int(categoria_elem.get('id')),
                    'nombre': categoria_elem.find('nombre').text,
                    'descripcion': categoria_elem.find('descripcion').text,
                    'cargaTrabajo': categoria_elem.find('cargaTrabajo').text,
                    'configuraciones': []
                }

                lista_configs = categoria_elem.find('listaConfiguraciones')
                if lista_configs is not None:
                    for config_elem in lista_configs.findall('configuracion'):
                        config = {
                            'id': int(config_elem.get('id')),
                            'nombre': config_elem.find('nombre').text,
                            'descripcion': config_elem.find('descripcion').text,
                            'recursos': []
                        }

                        recursos_config = config_elem.find('recursosConfiguracion')
                        if recursos_config is not None:
                            for recurso_elem in recursos_config.findall('recurso'):
                                recurso_config = {
                                    'idRecurso': int(recurso_elem.get('id')),
                                    'cantidad': float(recurso_elem.text)
                                }
                                config['recursos'].append(recurso_config)

                        categoria['configuraciones'].append(config)

                categorias.append(categoria)

            return categorias
        except FileNotFoundError:
            return []

    def guardar_clientes(self, clientes):
        """Guardar clientes en XML"""
        root = ET.Element("listaClientes")

        for cliente in clientes:
            cliente_elem = ET.SubElement(root, "cliente")
            cliente_elem.set("nit", cliente['nit'])

            ET.SubElement(cliente_elem, "nombre").text = cliente['nombre']
            ET.SubElement(cliente_elem, "usuario").text = cliente['usuario']
            ET.SubElement(cliente_elem, "clave").text = cliente['clave']
            ET.SubElement(cliente_elem, "direccion").text = cliente['direccion']
            ET.SubElement(cliente_elem, "correoElectronico").text = cliente['correoElectronico']

            lista_instancias = ET.SubElement(cliente_elem, "listaInstancias")
            for instancia in cliente.get('instancias', []):
                instancia_elem = ET.SubElement(lista_instancias, "instancia")
                instancia_elem.set("id", str(instancia['id']))

                ET.SubElement(instancia_elem, "idConfiguracion").text = str(instancia['idConfiguracion'])
                ET.SubElement(instancia_elem, "nombre").text = instancia['nombre']
                ET.SubElement(instancia_elem, "fechaInicio").text = instancia['fechaInicio']
                ET.SubElement(instancia_elem, "estado").text = instancia['estado']

                if instancia['fechaFinal']:
                    ET.SubElement(instancia_elem, "fechaFinal").text = instancia['fechaFinal']

        self._guardar_xml(root, "clientes.xml")

    def cargar_clientes(self):
        """Cargar clientes desde XML"""
        try:
            tree = ET.parse(os.path.join(self.base_path, "clientes.xml"))
            root = tree.getroot()

            clientes = []
            for cliente_elem in root.findall('cliente'):
                cliente = {
                    'nit': cliente_elem.get('nit'),
                    'nombre': cliente_elem.find('nombre').text,
                    'usuario': cliente_elem.find('usuario').text,
                    'clave': cliente_elem.find('clave').text,
                    'direccion': cliente_elem.find('direccion').text,
                    'correoElectronico': cliente_elem.find('correoElectronico').text,
                    'instancias': []
                }

                lista_instancias = cliente_elem.find('listaInstancias')
                if lista_instancias is not None:
                    for instancia_elem in lista_instancias.findall('instancia'):
                        instancia = {
                            'id': int(instancia_elem.get('id')),
                            'idConfiguracion': int(instancia_elem.find('idConfiguracion').text),
                            'nombre': instancia_elem.find('nombre').text,
                            'fechaInicio': instancia_elem.find('fechaInicio').text,
                            'estado': instancia_elem.find('estado').text,
                            'fechaFinal': instancia_elem.find('fechaFinal').text if instancia_elem.find(
                                'fechaFinal') is not None else None,
                            'nitCliente': cliente['nit'],
                            'consumos': []
                        }
                        cliente['instancias'].append(instancia)

                clientes.append(cliente)

            return clientes
        except FileNotFoundError:
            return []

    def guardar_consumos(self, consumos):
        """Guardar consumos en XML"""
        root = ET.Element("listadoConsumos")

        for consumo in consumos:
            consumo_elem = ET.SubElement(root, "consumo")
            consumo_elem.set("nitCliente", consumo['nitCliente'])
            consumo_elem.set("idInstancia", str(consumo['idInstancia']))

            ET.SubElement(consumo_elem, "tiempo").text = str(consumo['tiempo'])
            ET.SubElement(consumo_elem, "fechahora").text = consumo['fechahora']

        self._guardar_xml(root, "consumos.xml")

    def cargar_consumos(self):
        """Cargar consumos desde XML"""
        try:
            tree = ET.parse(os.path.join(self.base_path, "consumos.xml"))
            root = tree.getroot()

            consumos = []
            for consumo_elem in root.findall('consumo'):
                consumo = {
                    'nitCliente': consumo_elem.get('nitCliente'),
                    'idInstancia': int(consumo_elem.get('idInstancia')),
                    'tiempo': float(consumo_elem.find('tiempo').text),
                    'fechahora': consumo_elem.find('fechahora').text
                }
                consumos.append(consumo)

            return consumos
        except FileNotFoundError:
            return []

    def guardar_facturas(self, facturas):
        """Guardar facturas en XML"""
        root = ET.Element("listaFacturas")

        for factura in facturas:
            factura_elem = ET.SubElement(root, "factura")
            factura_elem.set("id", str(factura['id']))

            ET.SubElement(factura_elem, "nitCliente").text = factura['nitCliente']
            ET.SubElement(factura_elem, "fechaEmision").text = factura['fechaEmision']
            ET.SubElement(factura_elem, "periodo").text = factura['periodo']
            ET.SubElement(factura_elem, "montoTotal").text = str(factura['montoTotal'])

            detalles_elem = ET.SubElement(factura_elem, "detalles")
            for detalle in factura.get('detalles', []):
                detalle_elem = ET.SubElement(detalles_elem, "detalle")
                ET.SubElement(detalle_elem, "idInstancia").text = str(detalle['idInstancia'])
                ET.SubElement(detalle_elem, "tiempoTotal").text = str(detalle['tiempoTotal'])
                ET.SubElement(detalle_elem, "monto").text = str(detalle['monto'])

        self._guardar_xml(root, "facturas.xml")

    def cargar_facturas(self):
        """Cargar facturas desde XML"""
        try:
            tree = ET.parse(os.path.join(self.base_path, "facturas.xml"))
            root = tree.getroot()

            facturas = []
            for factura_elem in root.findall('factura'):
                factura = {
                    'id': int(factura_elem.get('id')),
                    'nitCliente': factura_elem.find('nitCliente').text,
                    'fechaEmision': factura_elem.find('fechaEmision').text,
                    'periodo': factura_elem.find('periodo').text,
                    'montoTotal': float(factura_elem.find('montoTotal').text),
                    'detalles': []
                }

                detalles_elem = factura_elem.find('detalles')
                if detalles_elem is not None:
                    for detalle_elem in detalles_elem.findall('detalle'):
                        detalle = {
                            'idInstancia': int(detalle_elem.find('idInstancia').text),
                            'tiempoTotal': float(detalle_elem.find('tiempoTotal').text),
                            'monto': float(detalle_elem.find('monto').text)
                        }
                        factura['detalles'].append(detalle)

                facturas.append(factura)

            return facturas
        except FileNotFoundError:
            return []

    def _guardar_xml(self, root, filename):
        """Guardar XML con formato legible"""
        rough_string = ET.tostring(root, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="  ")

        with open(os.path.join(self.base_path, filename), 'w', encoding='utf-8') as f:
            f.write(pretty_xml)

    def guardar_todo(self, db):
        """Guardar toda la base de datos"""
        self.guardar_recursos(db['recursos'])
        self.guardar_categorias(db['categorias'])
        self.guardar_clientes(db['clientes'])
        self.guardar_consumos(db['consumos'])
        self.guardar_facturas(db['facturas'])

    def cargar_todo(self):
        """Cargar toda la base de datos"""
        return {
            'recursos': self.cargar_recursos(),
            'categorias': self.cargar_categorias(),
            'clientes': self.cargar_clientes(),
            'configuraciones': self._extraer_configuraciones(),
            'instancias': self._extraer_instancias(),
            'consumos': self.cargar_consumos(),
            'facturas': self.cargar_facturas()
        }

    def _extraer_configuraciones(self):
        """Extraer todas las configuraciones de las categorías"""
        configuraciones = []
        categorias = self.cargar_categorias()

        for categoria in categorias:
            configuraciones.extend(categoria['configuraciones'])

        return configuraciones

    def _extraer_instancias(self):
        """Extraer todas las instancias de los clientes"""
        instancias = []
        clientes = self.cargar_clientes()

        for cliente in clientes:
            instancias.extend(cliente['instancias'])

        return instancias