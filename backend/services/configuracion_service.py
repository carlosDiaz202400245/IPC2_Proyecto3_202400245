import sys
import os
import xml.etree.ElementTree as ET
import re

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from utils.validators import validar_nit, extraer_fecha
from models.recurso import Recurso
from models.categoria import Categoria
from models.configuracion import Configuracion, RecursoConfiguracion
from models.cliente import Cliente
from models.instancia import Instancia


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

    def procesar_xml(self, xml_data, db):
        """Procesar el XML de configuración completa"""
        try:
            print("🔍 DEBUG procesar_xml INICIO")
            root = ET.fromstring(xml_data)

            # 1. Procesar recursos
            self._procesar_recursos(root, db)

            # 2. Procesar categorías y configuraciones
            self._procesar_categorias(root, db)

            # 3. Procesar clientes e instancias
            self._procesar_clientes(root, db)

            print("🔍 DEBUG procesar_xml FIN - ÉXITO")
            return self.resultados

        except Exception as e:
            print(f"🔍 DEBUG procesar_xml ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            self.resultados["errores"].append(f"Error general: {str(e)}")
            return self.resultados

    def _procesar_recursos(self, root, db):
        """Procesar la sección de recursos del XML"""
        print("🔍 DEBUG _procesar_recursos INICIO")
        lista_recursos = root.find('listaRecursos')
        if lista_recursos is None:
            print("🔍 DEBUG: No hay listaRecursos")
            return

        for recurso_elem in lista_recursos.findall('recurso'):
            try:
                id_recurso = int(recurso_elem.get('id'))
                print(f"🔍 DEBUG: Procesando recurso {id_recurso}")

                # Verificar si el recurso ya existe
                recurso_existe = any(r.id == id_recurso for r in db['recursos'])
                if recurso_existe:
                    print(f"🔍 DEBUG: Recurso {id_recurso} ya existe, saltando")
                    continue

                nombre = recurso_elem.find('nombre').text.strip()
                abreviatura = recurso_elem.find('abreviatura').text.strip()
                metrica = recurso_elem.find('metrica').text.strip()
                tipo = recurso_elem.find('tipo').text.strip()
                valor_x_hora = float(recurso_elem.find('valorXhora').text)

                # Validar tipo de recurso
                if tipo not in ['Hardware', 'Software']:
                    self.resultados['errores'].append(f"Tipo de recurso inválido: {tipo}")
                    continue

                # Crear recurso
                recurso = Recurso(id_recurso, nombre, abreviatura, metrica, tipo, valor_x_hora)
                db['recursos'].append(recurso)
                self.resultados['recursos_creados'] += 1
                print(f"🔍 DEBUG: Recurso {id_recurso} creado exitosamente")

            except Exception as e:
                error_msg = f"Error procesando recurso {recurso_elem.get('id')}: {str(e)}"
                print(f"🔍 DEBUG: {error_msg}")
                self.resultados['errores'].append(error_msg)

    def _procesar_categorias(self, root, db):
        """Procesar la sección de categorías y configuraciones del XML"""
        print("🔍 DEBUG _procesar_categorias INICIO")
        lista_categorias = root.find('listaCategorias')
        if lista_categorias is None:
            print("🔍 DEBUG: No hay listaCategorias")
            return

        for categoria_elem in lista_categorias.findall('categoria'):
            try:
                id_categoria = int(categoria_elem.get('id'))
                print(f"🔍 DEBUG: Procesando categoría {id_categoria}")

                # Verificar si la categoría ya existe
                categoria_existente = next((c for c in db['categorias'] if c.id == id_categoria), None)
                if categoria_existente:
                    categoria = categoria_existente
                    print(f"🔍 DEBUG: Categoría {id_categoria} ya existe")
                else:
                    # Crear nueva categoría
                    nombre = categoria_elem.find('nombre').text.strip()
                    descripcion = categoria_elem.find('descripcion').text.strip()
                    carga_trabajo = categoria_elem.find('cargaTrabajo').text.strip()

                    categoria = Categoria(id_categoria, nombre, descripcion, carga_trabajo)
                    db['categorias'].append(categoria)
                    self.resultados['categorias_creadas'] += 1
                    print(f"🔍 DEBUG: Categoría {id_categoria} creada exitosamente")

                # Procesar configuraciones de esta categoría
                self._procesar_configuraciones(categoria_elem, categoria, db)

            except Exception as e:
                error_msg = f"Error procesando categoría {categoria_elem.get('id')}: {str(e)}"
                print(f"🔍 DEBUG: {error_msg}")
                self.resultados['errores'].append(error_msg)

    def _procesar_configuraciones(self, categoria_elem, categoria, db):
        """Procesar configuraciones dentro de una categoría"""
        print("🔍 DEBUG _procesar_configuraciones INICIO")
        lista_configuraciones = categoria_elem.find('listaConfiguraciones')
        if lista_configuraciones is None:
            print("🔍 DEBUG: No hay listaConfiguraciones")
            return

        for config_elem in lista_configuraciones.findall('configuracion'):
            try:
                id_config = int(config_elem.get('id'))
                print(f"🔍 DEBUG: Procesando configuración {id_config}")

                # Verificar si existe esta config.
                config_existente = any(c.id == id_config for c in db['configuraciones'])
                if config_existente:
                    print(f"🔍 DEBUG: Configuración {id_config} ya existe, saltando")
                    continue

                nombre = config_elem.find('nombre').text.strip()
                descripcion = config_elem.find('descripcion').text.strip()

                # Crear configuración
                configuracion = Configuracion(id_config, nombre, descripcion, categoria.id)

                # Procesar recursos de la configuración
                recursos_config = config_elem.find('recursosConfiguracion')
                if recursos_config is not None:
                    for recurso_elem in recursos_config.findall('recurso'):
                        id_recurso = int(recurso_elem.get('id'))
                        cantidad = float(recurso_elem.text)
                        print(f"🔍 DEBUG: Agregando recurso {id_recurso} a configuración {id_config}")

                        # Verificar que el recurso exista
                        recurso_existe = any(r.id == id_recurso for r in db['recursos'])
                        if not recurso_existe:
                            error_msg = f"Recurso {id_recurso} no existe en configuración {id_config}"
                            print(f"🔍 DEBUG: {error_msg}")
                            self.resultados['errores'].append(error_msg)
                            continue

                        recurso_config = RecursoConfiguracion(id_recurso, cantidad)
                        configuracion.agregar_recurso(recurso_config)

                # Agregar configuración
                categoria.agregar_configuracion(configuracion)
                db['configuraciones'].append(configuracion)
                self.resultados['configuraciones_creadas'] += 1
                print(f"🔍 DEBUG: Configuración {id_config} creada exitosamente")

            except Exception as e:
                error_msg = f"Error procesando configuración {config_elem.get('id')}: {str(e)}"
                print(f"🔍 DEBUG: {error_msg}")
                import traceback
                traceback.print_exc()
                self.resultados['errores'].append(error_msg)

    def _procesar_clientes(self, root, db):
        """Procesar la sección de clientes e instancias del XML"""
        print("🔍 DEBUG _procesar_clientes INICIO")
        lista_clientes = root.find('listaClientes')
        if lista_clientes is None:
            print("🔍 DEBUG: No hay listaClientes")
            return

        for cliente_elem in lista_clientes.findall('cliente'):
            try:
                nit = cliente_elem.get('nit')
                print(f"🔍 DEBUG: Procesando cliente {nit}")

                # Validar NIT
                if not validar_nit(nit):
                    error_msg = f"NIT inválido: {nit}"
                    print(f"🔍 DEBUG: {error_msg}")
                    self.resultados['errores'].append(error_msg)
                    continue

                # Verificar si el cliente ya existe
                cliente_existente = next((c for c in db['clientes'] if c.nit == nit), None)
                if cliente_existente:
                    cliente = cliente_existente
                    print(f"🔍 DEBUG: Cliente {nit} ya existe")
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
                    print(f"🔍 DEBUG: Cliente {nit} creado exitosamente")

                # Procesar instancias del cliente
                self._procesar_instancias(cliente_elem, cliente, db)

            except Exception as e:
                error_msg = f"Error procesando cliente {cliente_elem.get('nit')}: {str(e)}"
                print(f"🔍 DEBUG: {error_msg}")
                self.resultados['errores'].append(error_msg)

    def _procesar_instancias(self, cliente_elem, cliente, db):
        """Procesar instancias dentro de un cliente"""
        print("🔍 DEBUG _procesar_instancias INICIO")
        lista_instancias = cliente_elem.find('listaInstancias')
        if lista_instancias is None:
            print("🔍 DEBUG: No hay listaInstancias")
            return

        for instancia_elem in lista_instancias.findall('instancia'):
            try:
                id_instancia = int(instancia_elem.get('id'))
                print(f"🔍 DEBUG: Procesando instancia {id_instancia}")

                # Verificar si la instancia ya existe
                instancia_existente = any(i.id == id_instancia for i in db['instancias'])
                if instancia_existente:
                    print(f"🔍 DEBUG: Instancia {id_instancia} ya existe, saltando")
                    continue

                id_configuracion = int(instancia_elem.find('idConfiguracion').text)
                nombre = instancia_elem.find('nombre').text.strip()
                fecha_inicio_text = instancia_elem.find('fechaInicio').text

                # Extraer fecha
                fecha_inicio = extraer_fecha(fecha_inicio_text)
                if not fecha_inicio:
                    error_msg = f"Fecha inválida en instancia {id_instancia}: {fecha_inicio_text}"
                    print(f"🔍 DEBUG: {error_msg}")
                    self.resultados['errores'].append(error_msg)
                    continue

                # Verificar que la configuración exista
                config_existente = any(c.id == id_configuracion for c in db['configuraciones'])
                if not config_existente:
                    error_msg = f"Configuración {id_configuracion} no existe para instancia {id_instancia}"
                    print(f"🔍 DEBUG: {error_msg}")
                    self.resultados['errores'].append(error_msg)
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
                print(f"🔍 DEBUG: Instancia {id_instancia} creada exitosamente")

            except Exception as e:
                error_msg = f"Error procesando instancia {instancia_elem.get('id')}: {str(e)}"
                print(f"🔍 DEBUG: {error_msg}")
                self.resultados['errores'].append(error_msg)