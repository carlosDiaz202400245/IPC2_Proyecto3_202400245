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
            #Acceder a atributos del objeto
            recurso_elem.set("id", str(recurso.id))  # ← recurso.id, NO recurso['id']

            ET.SubElement(recurso_elem, "nombre").text = recurso.nombre
            ET.SubElement(recurso_elem, "abreviatura").text = recurso.abreviatura
            ET.SubElement(recurso_elem, "metrica").text = recurso.metrica
            ET.SubElement(recurso_elem, "tipo").text = recurso.tipo
            ET.SubElement(recurso_elem, "valorXhora").text = str(recurso.valor_x_hora)

        self._guardar_xml(root, "recursos.xml")

    def cargar_recursos(self):  # <-- AGREGA ESTE MÉTODO AQUÍ
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
            # Acceder a atributos del objeto
            categoria_elem.set("id", str(categoria.id))

            ET.SubElement(categoria_elem, "nombre").text = categoria.nombre
            ET.SubElement(categoria_elem, "descripcion").text = categoria.descripcion
            ET.SubElement(categoria_elem, "cargaTrabajo").text = categoria.carga_trabajo

            lista_configs = ET.SubElement(categoria_elem, "listaConfiguraciones")
            for config in categoria.configuraciones:  # ← categoria.configuraciones, NO categoria.get('configuraciones')
                config_elem = ET.SubElement(lista_configs, "configuracion")
                config_elem.set("id", str(config.id))

                ET.SubElement(config_elem, "nombre").text = config.nombre
                ET.SubElement(config_elem, "descripcion").text = config.descripcion

                recursos_config = ET.SubElement(config_elem, "recursosConfiguracion")
                for recurso_config in config.recursos:  # ← config.recursos, NO config.get('recursos')
                    recurso_elem = ET.SubElement(recursos_config, "recurso")
                    recurso_elem.set("id", str(recurso_config.id_recurso))
                    recurso_elem.text = str(recurso_config.cantidad)

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
            #  Acceder a atributos del objeto
            cliente_elem.set("nit", cliente.nit)

            ET.SubElement(cliente_elem, "nombre").text = cliente.nombre
            ET.SubElement(cliente_elem, "usuario").text = cliente.usuario
            ET.SubElement(cliente_elem, "clave").text = cliente.clave
            ET.SubElement(cliente_elem, "direccion").text = cliente.direccion
            ET.SubElement(cliente_elem, "correoElectronico").text = cliente.correo_electronico

            lista_instancias = ET.SubElement(cliente_elem, "listaInstancias")
            for instancia in cliente.instancias:  # ← cliente.instancias, NO cliente.get('instancias')
                instancia_elem = ET.SubElement(lista_instancias, "instancia")
                instancia_elem.set("id", str(instancia.id))

                ET.SubElement(instancia_elem, "idConfiguracion").text = str(instancia.id_configuracion)
                ET.SubElement(instancia_elem, "nombre").text = instancia.nombre
                ET.SubElement(instancia_elem, "fechaInicio").text = instancia.fecha_inicio
                ET.SubElement(instancia_elem, "estado").text = instancia.estado

                if instancia.fecha_final:  # ← instancia.fecha_final, NO instancia['fechaFinal']
                    ET.SubElement(instancia_elem, "fechaFinal").text = instancia.fecha_final

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
            factura_elem.set("id", str(factura.id))

            ET.SubElement(factura_elem, "nitCliente").text = factura.nit_cliente
            ET.SubElement(factura_elem, "fechaEmision").text = factura.fecha_emision
            ET.SubElement(factura_elem, "periodo").text = factura.periodo
            ET.SubElement(factura_elem, "montoTotal").text = str(factura.monto_total)

            detalles_elem = ET.SubElement(factura_elem, "detalles")
            for detalle in factura.detalles:  # ← factura.detalles, NO factura.get('detalles')
                detalle_elem = ET.SubElement(detalles_elem, "detalle")
                ET.SubElement(detalle_elem, "idInstancia").text = str(detalle.id_instancia)
                ET.SubElement(detalle_elem, "tiempoTotal").text = str(detalle.tiempo_total)
                ET.SubElement(detalle_elem, "monto").text = str(detalle.monto)

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
        """Cargar toda la base de datos - versión funcional"""
        try:
            # Cargar como diccionarios primero
            recursos_dict = self.cargar_recursos()
            categorias_dict = self.cargar_categorias()
            clientes_dict = self.cargar_clientes()
            facturas_dict = self.cargar_facturas()

            # Convertir a objetos
            from models.recurso import Recurso
            from models.categoria import Categoria
            from models.configuracion import Configuracion, RecursoConfiguracion
            from models.cliente import Cliente
            from models.instancia import Instancia, Consumo
            from models.factura import Factura, DetalleFactura

            # Convertir recursos
            recursos = []
            for recurso_data in recursos_dict:
                recursos.append(Recurso.from_dict(recurso_data))

            # Convertir categorías
            categorias = []
            configuraciones = []
            for categoria_data in categorias_dict:
                # Crear categoría sin configuraciones primero
                categoria = Categoria(
                    categoria_data['id'],
                    categoria_data['nombre'],
                    categoria_data['descripcion'],
                    categoria_data['cargaTrabajo']
                )
                categorias.append(categoria)

                # Convertir configuraciones de esta categoría
                for config_data in categoria_data.get('configuraciones', []):
                    configuracion = Configuracion(
                        config_data['id'],
                        config_data['nombre'],
                        config_data['descripcion'],
                        categoria_data['id']  # id de la categoría padre
                    )

                    # Agregar recursos a la configuración
                    for recurso_config_data in config_data.get('recursos', []):
                        recurso_config = RecursoConfiguracion(
                            recurso_config_data['idRecurso'],
                            recurso_config_data['cantidad']
                        )
                        configuracion.agregar_recurso(recurso_config)

                    configuraciones.append(configuracion)
                    categoria.agregar_configuracion(configuracion)

            # Convertir clientes
            clientes = []
            instancias = []
            for cliente_data in clientes_dict:
                cliente = Cliente(
                    cliente_data['nit'],
                    cliente_data['nombre'],
                    cliente_data['usuario'],
                    cliente_data['clave'],
                    cliente_data['direccion'],
                    cliente_data['correoElectronico']
                )
                clientes.append(cliente)

                # Convertir instancias de este cliente
                for instancia_data in cliente_data.get('instancias', []):
                    instancia = Instancia(
                        instancia_data['id'],
                        instancia_data['idConfiguracion'],
                        instancia_data['nombre'],
                        instancia_data['fechaInicio'],
                        cliente_data['nit']
                    )
                    instancia.estado = instancia_data.get('estado', 'Vigente')
                    instancia.fecha_final = instancia_data.get('fechaFinal')

                    instancias.append(instancia)
                    cliente.agregar_instancia(instancia)

            # Convertir facturas
            facturas = []
            for factura_data in facturas_dict:
                factura = Factura(
                    factura_data['id'],
                    factura_data['nitCliente'],
                    factura_data['fechaEmision'],
                    factura_data['periodo']
                )
                factura.monto_total = factura_data.get('montoTotal', 0.0)

                for detalle_data in factura_data.get('detalles', []):
                    detalle = DetalleFactura(
                        detalle_data['idInstancia'],
                        detalle_data['tiempoTotal'],
                        detalle_data['monto']
                    )
                    factura.agregar_detalle(detalle)

                facturas.append(factura)

            return {
                'recursos': recursos,
                'categorias': categorias,
                'clientes': clientes,
                'configuraciones': configuraciones,
                'instancias': instancias,
                'consumos': [],  # Por ahora vacío
                'facturas': facturas
            }

        except Exception as e:
            print(f" Error cargando datos: {e}")

            return {
                'recursos': [],
                'categorias': [],
                'clientes': [],
                'configuraciones': [],
                'instancias': [],
                'consumos': [],
                'facturas': []
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