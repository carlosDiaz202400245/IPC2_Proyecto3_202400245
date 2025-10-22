# services/facturacion_service.py - CORREGIDO
from models.factura import Factura, DetalleFactura
from utils.date_utils import parsear_fecha, es_rango_fecha_valido, obtener_fecha_actual
from datetime import datetime


class FacturacionService:
    def __init__(self):
        pass

    def generar_facturas(self, db, fecha_inicio, fecha_fin):
        """
        Generar facturas para todos los clientes en un rango de fechas
        """
        if not es_rango_fecha_valido(fecha_inicio, fecha_fin):
            return {'error': 'Rango de fechas inválido'}

        facturas_generadas = []
        clientes_procesados = set()

        factura_id = self._obtener_siguiente_id(db)

        for instancia in db['instancias']:
            if instancia.nit_cliente in clientes_procesados:
                continue

            # Generar factura para este cliente
            factura = self._generar_factura_cliente(
                db, instancia.nit_cliente, fecha_inicio, fecha_fin, factura_id
            )

            if factura:
                facturas_generadas.append(factura)
                db['facturas'].append(factura)
                clientes_procesados.add(instancia.nit_cliente)
                factura_id += 1

        return {
            'facturas_generadas': len(facturas_generadas),
            'detalle': [factura.to_dict() for factura in facturas_generadas]
        }

    def _generar_factura_cliente(self, db, nit_cliente, fecha_inicio, fecha_fin, factura_id):
        """Generar factura para un cliente específico"""
        cliente = next((c for c in db['clientes'] if c.nit == nit_cliente), None)
        if not cliente:
            return None

        fecha_emision = obtener_fecha_actual()
        periodo = f"{fecha_inicio} - {fecha_fin}"

        factura = Factura(factura_id, nit_cliente, fecha_emision, periodo)
        total_factura = 0.0

        for instancia in cliente.instancias:
            if instancia.estado != "Vigente":
                continue

            configuracion = next((c for c in db['configuraciones'] if c.id == instancia.id_configuracion), None)
            if not configuracion:
                continue

            costo_por_hora = configuracion.calcular_costo_hora(db['recursos'])

            #  FILTRAR CONSUMOS POR FECHA
            consumos_periodo = []
            for consumo in instancia.consumos:
                try:
                    fecha_consumo = consumo.fecha_hora.split(' ')[0]  # Extraer fecha
                    if fecha_inicio <= fecha_consumo <= fecha_fin:
                        consumos_periodo.append(consumo)
                except:
                    continue

            tiempo_total = sum(consumo.tiempo for consumo in consumos_periodo)
            monto_instancia = costo_por_hora * tiempo_total

            if monto_instancia > 0:
                detalle = DetalleFactura(instancia.id, tiempo_total, monto_instancia)
                factura.agregar_detalle(detalle)
                total_factura += monto_instancia

        return factura if len(factura.detalles) > 0 else None

    def _obtener_siguiente_id(self, db):
        """Obtener siguiente ID basado en facturas existentes"""
        if db['facturas']:
            return max(f.id for f in db['facturas']) + 1
        return 1

    def generar_reporte_analitico(self, db, fecha_inicio, fecha_fin, tipo_reporte):
        """Generar reporte analítico de ventas con datos REALES"""
        print(f" DEBUG - Generando reporte: {tipo_reporte}, {fecha_inicio} a {fecha_fin}")

        if tipo_reporte == 'categorias':
            return self._analizar_ingresos_por_categoria(db, fecha_inicio, fecha_fin)
        elif tipo_reporte == 'recursos':
            return self._analizar_ingresos_por_recurso(db, fecha_inicio, fecha_fin)
        else:
            return {'error': 'Tipo de reporte no válido. Use: categorias o recursos'}

    def _analizar_ingresos_por_categoria(self, db, fecha_inicio, fecha_fin):
        """Analizar ingresos por categoría en un rango de fechas con datos REALES - CORREGIDO"""
        ingresos_por_categoria = {}
        print(f" DEBUG - Analizando categorías para período: {fecha_inicio} a {fecha_fin}")

        # Primero, generar facturas para el período solicitado
        resultado_facturacion = self.generar_facturas(db, fecha_inicio, fecha_fin)

        if 'error' in resultado_facturacion:
            return {'error': resultado_facturacion['error']}

        facturas_periodo = resultado_facturacion['detalle']
        print(f" DEBUG - Facturas en período: {len(facturas_periodo)}")

        if not facturas_periodo:
            return {'mensaje': 'No hay facturas en el período seleccionado'}

        # Procesar las facturas generadas en el período
        for factura_data in facturas_periodo:
            for detalle_data in factura_data.get('detalles', []):
                instancia_id = detalle_data.get('idInstancia')
                monto = detalle_data.get('monto', 0)

                # Buscar la instancia
                instancia = next((i for i in db['instancias'] if i.id == instancia_id), None)
                if not instancia:
                    continue

                # Buscar configuración
                configuracion = next((c for c in db['configuraciones'] if c.id == instancia.id_configuracion), None)
                if not configuracion:
                    continue

                # Buscar categoría
                categoria = next((cat for cat in db['categorias'] if cat.id == configuracion.id_categoria), None)
                if not categoria:
                    continue

                # Acumular datos por categoría
                if categoria.id not in ingresos_por_categoria:
                    ingresos_por_categoria[categoria.id] = {
                        'nombre': categoria.nombre,
                        'configuraciones': set(),
                        'instancias': set(),
                        'ingresos': 0.0
                    }

                ingresos_por_categoria[categoria.id]['configuraciones'].add(configuracion.id)
                ingresos_por_categoria[categoria.id]['instancias'].add(instancia.id)
                ingresos_por_categoria[categoria.id]['ingresos'] += monto

        # Convertir sets a contadores
        for categoria_id, datos in ingresos_por_categoria.items():
            datos['configuraciones'] = len(datos['configuraciones'])
            datos['instancias'] = len(datos['instancias'])

        print(f" DEBUG - Categorías encontradas: {len(ingresos_por_categoria)}")
        return ingresos_por_categoria

    def _analizar_ingresos_por_recurso(self, db, fecha_inicio, fecha_fin):
        """Analizar ingresos por recurso en un rango de fechas con datos REALES - CORREGIDO"""
        ingresos_por_recurso = {}
        print(f" DEBUG - Analizando recursos para período: {fecha_inicio} a {fecha_fin}")

        # Primero, generar facturas para el período solicitado
        resultado_facturacion = self.generar_facturas(db, fecha_inicio, fecha_fin)

        if 'error' in resultado_facturacion:
            return {'error': resultado_facturacion['error']}

        facturas_periodo = resultado_facturacion['detalle']
        print(f" DEBUG - Facturas en período: {len(facturas_periodo)}")

        if not facturas_periodo:
            return {'mensaje': 'No hay facturas en el período seleccionado'}

        # Procesar las facturas generadas en el período
        for factura_data in facturas_periodo:
            for detalle_data in factura_data.get('detalles', []):
                instancia_id = detalle_data.get('idInstancia')
                monto_total = detalle_data.get('monto', 0)
                tiempo_total = detalle_data.get('tiempoTotal', 0)

                # Buscar la instancia
                instancia = next((i for i in db['instancias'] if i.id == instancia_id), None)
                if not instancia:
                    continue

                # Buscar configuración
                configuracion = next((c for c in db['configuraciones'] if c.id == instancia.id_configuracion), None)
                if not configuracion:
                    continue

                # Calcular costo por hora de la configuración
                costo_por_hora = configuracion.calcular_costo_hora(db['recursos'])

                if costo_por_hora > 0 and tiempo_total > 0:
                    # Distribuir el monto entre los recursos
                    for recurso_config in configuracion.recursos:
                        recurso = next((r for r in db['recursos'] if r.id == recurso_config.id_recurso), None)
                        if recurso:
                            # Calcular proporción del costo que corresponde a este recurso
                            costo_recurso_por_hora = recurso.valor_x_hora * recurso_config.cantidad
                            proporcion = costo_recurso_por_hora / costo_por_hora
                            monto_recurso = monto_total * proporcion
                            uso_recurso = recurso_config.cantidad * tiempo_total

                            if recurso.id not in ingresos_por_recurso:
                                ingresos_por_recurso[recurso.id] = {
                                    'nombre': recurso.nombre,
                                    'tipo': recurso.tipo,
                                    'uso_total': 0.0,
                                    'ingresos': 0.0
                                }

                            ingresos_por_recurso[recurso.id]['uso_total'] += uso_recurso
                            ingresos_por_recurso[recurso.id]['ingresos'] += monto_recurso
        print(f" DEBUG - Recursos encontrados: {len(ingresos_por_recurso)}")
        return ingresos_por_recurso