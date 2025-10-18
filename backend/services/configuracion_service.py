import xml.etree.ElementTree as ET
from backend.utils.validators import validar_nit, extraer_fecha
from backend.models.categoria import Categoria
from backend.models.cliente import Cliente
from backend.models.configuracion import Configuracion, RecursoConfiguracion
from backend.models.instancia import Instancia
from backend.models.recurso import Recurso
import re


class ProcesadorConfiguracion:
    def __init__(self):
        self.resultados = {
            "recursos_creados": 0,
            "categorias_creadas": 0,
            "configuraciones_creadas": 0,
            "clientes_creados": 0,
            "instancias_creadas": 0,
            "errores": []
        }

    def procesar_xml(self,xml_data,db):
        """procesar el xml de la config completa"""
        try:
            root = ET.fromstring(xml_data)
            # 1. procesamos los recursox
            self._procesar_recursos(root,db)

            # 2. Procesar categorías y configuraciones
            self._procesar_categorias(root, db)

            # 3. Procesar clientes e instancias
            self._procesar_clientes(root, db)

            return self.resultados
        except ET.ParseError as e:
            self.resultados["errores"].append(f"Error en el parsing xml: {str(e)}")
            return self.resultados
        except Exception as e:
            self.resultados["errores"].append(f"Error general ice frio hielo {str(e)}")
            return self.resultados

    def _procesar_recursos(self, root, db):
        """Procesar la sección de recursos del XML"""
        lista_recursos = root.find('listaRecursos')
        if lista_recursos is None:
            return

        recursos_dict = {r.id: r for r in db['recursos']}

        for recurso_elem in lista_recursos.findall('recurso'):
            try:
                id_recurso = int(recurso_elem.get('id'))

                # Verificar si el recurso ya existe
                if id_recurso in recursos_dict:
                    continue

                nombre = recurso_elem.find('nombre').text.strip()
                abreviatura = recurso_elem.find('abreviatura').text.strip()
                metrica = recurso_elem.find('metrica').text.strip()
                tipo = recurso_elem.find('tipo').text.strip()
                valor_x_hora = float(recurso_elem.find('valorXhora').text)

                # validar el tipo de recutso
                if tipo not in ['Hardware', 'Software']:
                    self.resultados['errores'].append(f"Tipo de recurso inválido: {tipo}")
                    continue

                # Crear recursox
                recurso = Recurso(id_recurso, nombre, abreviatura, metrica, tipo, valor_x_hora)
                db['recursos'].append(recurso)
                self.resultados['recursos_creados'] += 1

            except (AttributeError, ValueError, TypeError) as e:
                self.resultados['errores'].append(f"Error procesando recurso {recurso_elem.get('id')}: {str(e)}")

    def _procesar_categorias(self, root, db):
        """Procesar la sección de categorías y configuraciones del XML"""
        lista_categorias = root.find('listaCategorias')
        if lista_categorias is None:
            return

        categorias_dict = {c.id: c for c in db['categorias']}
        configuraciones_dict = {c.id: c for c in db['configuraciones']}
        recursos_dict = {r.id: r for r in db['recursos']}

        for categoria_elem in lista_categorias.findall('categoria'):
            try:
                id_categoria = int(categoria_elem.get('id'))

                # Verificar si la categoría ya existe
                if id_categoria in categorias_dict:
                    categoria = categorias_dict[id_categoria]
                else:
                    # Crear nueva categoría
                    nombre = categoria_elem.find('nombre').text.strip()
                    descripcion = categoria_elem.find('descripcion').text.strip()
                    carga_trabajo = categoria_elem.find('cargaTrabajo').text.strip()

                    categoria = Categoria(id_categoria, nombre, descripcion, carga_trabajo)
                    db['categorias'].append(categoria)
                    self.resultados['categorias_creadas'] += 1

                # Procesar configuraciones de esta categoría
                self._procesar_configuraciones(categoria_elem, categoria, db, recursos_dict, configuraciones_dict)

            except (AttributeError, ValueError, TypeError) as e:
                self.resultados['errores'].append(f"Error procesando categoría {categoria_elem.get('id')}: {str(e)}")

    def _procesar_configuraciones(self, categoria_elem, categoria, db, recursos_dict, configuraciones_dict):
        """Procesamoh configuraciones dentro de una categoría"""
        lista_configuraciones = categoria_elem.find('listaConfiguraciones')
        if lista_configuraciones is None:
            return

        for config_elem in lista_configuraciones.findall('configuracion'):
            try:
                id_config = int(config_elem.get('id'))

                # Verificar si existe esta config.
                if id_config in configuraciones_dict:
                    continue

                nombre = config_elem.find('nombre').text.strip()
                descripcion = config_elem.find('descripcion').text.strip()

                # creamos la config
                configuracion = Configuracion(id_config, nombre, descripcion, categoria.id)

                # Procesar recursos de la configuración
                recursos_config = config_elem.find('recursosConfiguracion')
                if recursos_config is not None:
                    for recurso_elem in recursos_config.findall('recurso'):
                        id_recurso = int(recurso_elem.get('id'))
                        cantidad = float(recurso_elem.text)

                        # Verificar que el recurso exista
                        if id_recurso not in recursos_dict:
                            self.resultados['errores'].append(
                                f"Recurso {id_recurso} no existe en configuración {id_config}")
                            continue

                        recurso_config = RecursoConfiguracion(id_recurso, cantidad)
                        configuracion.agregar_recurso(recurso_config)

                # Agregar configuración a la categoría y a la base de datos
                categoria.agregar_configuracion(configuracion)
                db['configuraciones'].append(configuracion)
                self.resultados['configuraciones_creadas'] += 1

            except (AttributeError, ValueError, TypeError) as e:
                self.resultados['errores'].append(f"Error procesando configuración {config_elem.get('id')}: {str(e)}")

    def _procesar_clientes(self, root, db):
        """Procesar la sección de clientes e instancias del XML"""
        lista_clientes = root.find('listaClientes')
        if lista_clientes is None:
            return

        clientes_dict = {c.nit: c for c in db['clientes']}
        configuraciones_dict = {c.id: c for c in db['configuraciones']}
        instancias_dict = {i.id: i for i in db['instancias']}

        for cliente_elem in lista_clientes.findall('cliente'):
            try:
                nit = cliente_elem.get('nit')

                # Validar NIT
                if not validar_nit(nit):
                    self.resultados['errores'].append(f"NIT inválido: {nit}")
                    continue

                # Verificar si el cliente ya existe
                if nit in clientes_dict:
                    cliente = clientes_dict[nit]
                else:
                    # Crear nuevo cliente
                    nombre = cliente_elem.find('nombre').text.strip()
                    usuario = cliente_elem.find('usuario').text.strip()
                    clave = cliente_elem.find('clave').text.strip()
                    direccion = cliente_elem.find('direccion').text.strip()
                    correo = cliente_elem.find('correoElectronico').text.strip()

                    cliente = Cliente(nit, nombre, usuario, clave, direccion, correo)
                    db['clientes'].append(cliente)
                    self.resultados['clientes_creados'] += 1

                # Procesar instancias del cliente
                self._procesar_instancias(cliente_elem, cliente, db, configuraciones_dict, instancias_dict)

            except (AttributeError, ValueError, TypeError) as e:
                self.resultados['errores'].append(f"Error procesando cliente {cliente_elem.get('nit')}: {str(e)}")

    def _procesar_instancias(self, cliente_elem, cliente, db, configuraciones_dict, instancias_dict):
        """Procesar instancias dentro de un cliente"""
        lista_instancias = cliente_elem.find('listaInstancias')
        if lista_instancias is None:
            return

        for instancia_elem in lista_instancias.findall('instancia'):
            try:
                id_instancia = int(instancia_elem.get('id'))

                # Verificar si la instancia ya existe
                if id_instancia in instancias_dict:
                    continue

                id_configuracion = int(instancia_elem.find('idConfiguracion').text)
                nombre = instancia_elem.find('nombre').text.strip()
                fecha_inicio_text = instancia_elem.find('fechaInicio').text

                # Extraer fecha usando regex (según especificación del proyecto)
                fecha_inicio = extraer_fecha(fecha_inicio_text)
                if not fecha_inicio:
                    self.resultados['errores'].append(
                        f"Fecha inválida en instancia {id_instancia}: {fecha_inicio_text}")
                    continue

                # Verificar que la configuración exista
                if id_configuracion not in configuraciones_dict:
                    self.resultados['errores'].append(
                        f"Configuración {id_configuracion} no existe para instancia {id_instancia}")
                    continue

                # Crear instancia
                instancia = Instancia(id_instancia, id_configuracion, nombre, fecha_inicio, cliente.nit)

                # Procesar estado y fecha final si existen
                estado_elem = instancia_elem.find('estado')
                if estado_elem is not None:
                    estado = estado_elem.text.strip()
                    if estado == "Cancelada":
                        fecha_final_elem = instancia_elem.find('fechaFinal')
                        if fecha_final_elem is not None:
                            fecha_final = extraer_fecha(fecha_final_elem.text)
                            if fecha_final:
                                instancia.cancelar(fecha_final)

                # Agregar instancia al cliente y a la base de datos
                cliente.agregar_instancia(instancia)
                db['instancias'].append(instancia)
                self.resultados['instancias_creadas'] += 1

            except (AttributeError, ValueError, TypeError) as e:
                self.resultados['errores'].append(f"Error procesando instancia {instancia_elem.get('id')}: {str(e)}")