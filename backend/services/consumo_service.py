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
            print("=" * 60)
            print(" DEBUG CONSUMO_SERVICE - INICIO")
            print("=" * 60)
            print(f" XML recibido: {len(xml_data)} caracteres")
            print(f" Primeros 200 chars: {repr(xml_data[:200])}")

            root = ET.fromstring(xml_data)
            print(f" XML parseado. Root tag: {root.tag}")
            print(f" Número de consumos: {len(root.findall('consumo'))}")

            # Procesar cada consumo en el listado
            for i, consumo_elem in enumerate(root.findall('consumo')):
                print(f"\n Procesando consumo {i + 1}...")
                self._procesar_consumo(consumo_elem, db)

            print("=" * 60)
            print(f" DEBUG CONSUMO_SERVICE - FIN")
            print(f" Consumos procesados: {self.resultados['consumos_procesados']}")
            print(f" Errores: {len(self.resultados['errores'])}")
            print("=" * 60)

            return self.resultados

        except ET.ParseError as e:
            error_msg = f"Error parsing XML: {str(e)}"
            print(f" {error_msg}")
            self.resultados['errores'].append(error_msg)
            return self.resultados
        except Exception as e:
            error_msg = f"Error general: {str(e)}"
            print(f" {error_msg}")
            import traceback
            traceback.print_exc()
            self.resultados['errores'].append(error_msg)
            return self.resultados

    def _procesar_consumo(self, consumo_elem, db):
        """Procesar un elemento de consumo individual"""
        try:
            nit_cliente = consumo_elem.get('nitCliente')
            id_instancia = int(consumo_elem.get('idInstancia'))

            print(f" DEBUG: Procesando consumo - NIT: {nit_cliente}, Instancia: {id_instancia}")

            # Validar NIT
            if not validar_nit(nit_cliente):
                error_msg = f"NIT inválido: {nit_cliente}"
                print(f" {error_msg}")
                self.resultados['errores'].append(error_msg)
                return

            # Buscar la instancia
            instancia = self._buscar_instancia(id_instancia, nit_cliente, db)
            if not instancia:
                error_msg = f"Instancia {id_instancia} no encontrada para cliente {nit_cliente}"
                print(f" {error_msg}")
                self.resultados['errores'].append(error_msg)
                return

            print(f" Instancia encontrada: {instancia.nombre} (Estado: {instancia.estado})")

            # Verificar que la instancia esté vigente
            if instancia.estado != "Vigente":
                error_msg = f"Instancia {id_instancia} no está vigente (estado: {instancia.estado})"
                print(f" {error_msg}")
                self.resultados['errores'].append(error_msg)
                return

            # Extraer tiempo de consumo
            tiempo_elem = consumo_elem.find('tiempo')
            if tiempo_elem is None or not tiempo_elem.text:
                error_msg = f"Tiempo de consumo no especificado para instancia {id_instancia}"
                print(f" {error_msg}")
                self.resultados['errores'].append(error_msg)
                return

            try:
                tiempo_consumo = float(tiempo_elem.text)
                if tiempo_consumo <= 0:
                    error_msg = f"Tiempo de consumo debe ser positivo: {tiempo_consumo}"
                    print(f" {error_msg}")
                    self.resultados['errores'].append(error_msg)
                    return
                print(f" Tiempo de consumo: {tiempo_consumo} horas")
            except ValueError:
                error_msg = f"Tiempo de consumo inválido: {tiempo_elem.text}"
                print(f" {error_msg}")
                self.resultados['errores'].append(error_msg)
                return

            # Extraer fecha y hora
            fecha_hora_elem = consumo_elem.find('fechahora')
            if fecha_hora_elem is None or not fecha_hora_elem.text:
                error_msg = f"Fecha/hora no especificada para instancia {id_instancia}"
                print(f" {error_msg}")
                self.resultados['errores'].append(error_msg)
                return

            fecha_hora_texto = fecha_hora_elem.text
            print(f" Texto fecha/hora original: '{fecha_hora_texto}'")

            fecha_hora = extraer_fecha_hora(fecha_hora_texto)
            print(f" Fecha/hora extraída: {fecha_hora}")

            if not fecha_hora:
                error_msg = f"Fecha/hora inválida: {fecha_hora_texto}"
                print(f" {error_msg}")
                self.resultados['errores'].append(error_msg)
                return

            # Crear y registrar el consumo
            consumo = Consumo(tiempo_consumo, fecha_hora)
            instancia.agregar_consumo(consumo)

            self.resultados['consumos_procesados'] += 1
            print(f" Consumo registrado exitosamente para instancia {id_instancia}")

        except (AttributeError, ValueError, TypeError) as e:
            error_msg = f"Error procesando consumo: {str(e)}"
            print(f" EXCEPCIÓN - {error_msg}")
            import traceback
            traceback.print_exc()
            self.resultados['errores'].append(error_msg)

    def _buscar_instancia(self, id_instancia, nit_cliente, db):
        """Buscar una instancia por ID y NIT de cliente"""
        print(f" Buscando instancia {id_instancia} para cliente {nit_cliente}")
        print(f" Total de instancias en DB: {len(db['instancias'])}")

        for instancia in db['instancias']:
            print(f" Comparando: Instancia {instancia.id} - Cliente {instancia.nit_cliente}")
            if instancia.id == id_instancia and instancia.nit_cliente == nit_cliente:
                print(f" Instancia encontrada: {instancia.nombre}")
                return instancia
        print(f" Instancia NO encontrada")
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