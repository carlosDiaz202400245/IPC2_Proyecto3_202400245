
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)


import xml.etree.ElementTree as ET
from models.instancia import Consumo
from utils.validators import extraer_fecha_hora, validar_nit


class ProcesadorConsumo:
    def __init__(self):
        self.resultados = {
            'consumos_procesados': 0,
            'errores': []
        }

    def procesar_xml(self, xml_data, db):
        """Procesar el XML de consumo de recursos"""
        try:
            root = ET.fromstring(xml_data)

            # Procesar cada consumo en el listado
            for consumo_elem in root.findall('consumo'):
                self._procesar_consumo(consumo_elem, db)

            return self.resultados

        except ET.ParseError as e:
            self.resultados['errores'].append(f"Error parsing XML: {str(e)}")
            return self.resultados
        except Exception as e:
            self.resultados['errores'].append(f"Error general: {str(e)}")
            return self.resultados

    def _procesar_consumo(self, consumo_elem, db):
        """Procesar un elemento de consumo individual"""
        try:
            nit_cliente = consumo_elem.get('nitCliente')
            id_instancia = int(consumo_elem.get('idInstancia'))

            print(f"DEBUG: Procesando consumo - NIT: {nit_cliente}, Instancia: {id_instancia}")

            # Validar NIT
            if not validar_nit(nit_cliente):
                error_msg = f"NIT inválido: {nit_cliente}"
                print(f"DEBUG: {error_msg}")
                self.resultados['errores'].append(error_msg)
                return

            # Buscar la instancia
            instancia = self._buscar_instancia(id_instancia, nit_cliente, db)
            if not instancia:
                error_msg = f"Instancia {id_instancia} no encontrada para cliente {nit_cliente}"
                print(f"DEBUG: {error_msg}")
                self.resultados['errores'].append(error_msg)
                return

            # Verificar que la instancia esté vigente
            if instancia.estado != "Vigente":
                error_msg = f"Instancia {id_instancia} no está vigente"
                print(f"DEBUG: {error_msg}")
                self.resultados['errores'].append(error_msg)
                return

            # Extraer tiempo de consumo
            tiempo_elem = consumo_elem.find('tiempo')
            if tiempo_elem is None or not tiempo_elem.text:
                error_msg = f"Tiempo de consumo no especificado para instancia {id_instancia}"
                print(f"DEBUG: {error_msg}")
                self.resultados['errores'].append(error_msg)
                return

            try:
                tiempo_consumo = float(tiempo_elem.text)
                if tiempo_consumo <= 0:
                    error_msg = f"Tiempo de consumo debe ser positivo: {tiempo_consumo}"
                    print(f"DEBUG: {error_msg}")
                    self.resultados['errores'].append(error_msg)
                    return
            except ValueError:
                error_msg = f"Tiempo de consumo inválido: {tiempo_elem.text}"
                print(f"DEBUG: {error_msg}")
                self.resultados['errores'].append(error_msg)
                return

            # Extraer fecha y hora
            fecha_hora_elem = consumo_elem.find('fechahora')
            if fecha_hora_elem is None or not fecha_hora_elem.text:
                error_msg = f"Fecha/hora no especificada para instancia {id_instancia}"
                print(f"DEBUG: {error_msg}")
                self.resultados['errores'].append(error_msg)
                return

            fecha_hora = extraer_fecha_hora(fecha_hora_elem.text)
            print(f"DEBUG: Texto fecha/hora: '{fecha_hora_elem.text}' -> Objeto: {fecha_hora}")

            if not fecha_hora:
                error_msg = f"Fecha/hora inválida: {fecha_hora_elem.text}"
                print(f"DEBUG: {error_msg}")
                self.resultados['errores'].append(error_msg)
                return

            # Crear y registrar el consumo
            consumo = Consumo(tiempo_consumo, fecha_hora)
            instancia.agregar_consumo(consumo)

            self.resultados['consumos_procesados'] += 1
            print(f"DEBUG: Consumo registrado exitosamente para instancia {id_instancia}")

        except (AttributeError, ValueError, TypeError) as e:
            error_msg = f"Error procesando consumo: {str(e)}"
            print(f"DEBUG: EXCEPCIÓN - {error_msg}")
            import traceback
            traceback.print_exc()
            self.resultados['errores'].append(error_msg)

    def _buscar_instancia(self, id_instancia, nit_cliente, db):
        """Buscar una instancia por ID y NIT de cliente"""
        for instancia in db['instancias']:
            if instancia.id == id_instancia and instancia.nit_cliente == nit_cliente:
                return instancia
        return None

    def obtener_consumos_por_cliente(self, nit_cliente, db, fecha_inicio=None, fecha_fin=None):
        """Obtener todos los consumos de un cliente en un rango de fechas"""
        consumos_cliente = []

        for instancia in db['instancias']:
            if instancia.nit_cliente == nit_cliente:
                for consumo in instancia.consumos:
                    # Si se especifica rango de fechas, filtrar
                    if fecha_inicio and fecha_fin:
                        # Aquí se podría implementar filtro por fecha si es necesario
                        pass
                    consumos_cliente.append({
                        'id_instancia': instancia.id,
                        'nombre_instancia': instancia.nombre,
                        'consumo': consumo.to_dict()
                    })

        return consumos_cliente