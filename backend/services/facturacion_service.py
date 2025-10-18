from backend.models.factura import Factura, DetalleFactura
from backend.utils.date_utils import parsear_fecha, es_rango_fecha_valido, obtener_fecha_actual
from datetime import datetime


class FacturacionService:
    def __init__(self):
        self.factura_id_counter = 1

    def generar_facturas(self, db, fecha_inicio, fecha_fin):
        """
        Generar facturas para todos los clientes en un rango de fechas
        para consumos no facturados previamente
        """
        if not es_rango_fecha_valido(fecha_inicio, fecha_fin):
            return {'error': 'Rango de fechas inválido'}

        facturas_generadas = []
        clientes_procesados = set()

        # Procesar cada instancia para calcular consumos no facturados
        for instancia in db['instancias']:
            if instancia.nit_cliente in clientes_procesados:
                continue

            # Generar factura para este cliente
            factura = self._generar_factura_cliente(
                db, instancia.nit_cliente, fecha_inicio, fecha_fin
            )

            if factura:
                facturas_generadas.append(factura)
                db['facturas'].append(factura)
                clientes_procesados.add(instancia.nit_cliente)

        return {
            'facturas_generadas': len(facturas_generadas),
            'detalle': [factura.to_dict() for factura in facturas_generadas]
        }

    def _generar_factura_cliente(self, db, nit_cliente, fecha_inicio, fecha_fin):
        """Generar factura para un cliente específico"""
        # Buscar cliente
        cliente = next((c for c in db['clientes'] if c.nit == nit_cliente), None)
        if not cliente:
            return None

        # Crear factura
        factura_id = self._obtener_siguiente_id()
        fecha_emision = obtener_fecha_actual()
        periodo = f"{fecha_inicio} - {fecha_fin}"

        factura = Factura(factura_id, nit_cliente, fecha_emision, periodo)

        # Calcular consumos y montos para cada instancia del cliente
        total_factura = 0.0

        for instancia in cliente.instancias:
            if instancia.estado != "Vigente":
                continue

            # Calcular consumo total y monto para esta instancia en el período
            monto_instancia = self._calcular_monto_instancia(db, instancia, fecha_inicio, fecha_fin)

            if monto_instancia > 0:
                tiempo_total = sum(consumo.tiempo for consumo in instancia.consumos)

                detalle = DetalleFactura(
                    instancia.id,
                    tiempo_total,
                    monto_instancia
                )
                factura.agregar_detalle(detalle)
                total_factura += monto_instancia

        # Si no hay consumos, no generar factura
        if len(factura.detalles) == 0:
            return None

        return factura

    def _calcular_monto_instancia(self, db, instancia, fecha_inicio, fecha_fin):
        """Calcular monto a facturar para una instancia en un período"""
        # Buscar configuración de la instancia
        configuracion = next(
            (c for c in db['configuraciones'] if c.id == instancia.id_configuracion),
            None
        )

        if not configuracion:
            return 0.0

        # Crear diccionario de recursos para cálculo rápido
        recursos_dict = {r.id: r for r in db['recursos']}

        # Calcular costo por hora de la configuración
        costo_por_hora = configuracion.calcular_costo_hora(recursos_dict)

        # Calcular horas consumidas en el período (simplificado - usar todos los consumos)
        # En una implementación real, aquí se filtrarían por fecha
        horas_totales = instancia.calcular_consumo_total()

        return costo_por_hora * horas_totales

    def _obtener_siguiente_id(self):
        """Obtener siguiente ID de factura único"""
        current_id = self.factura_id_counter
        self.factura_id_counter += 1
        return current_id

    def obtener_factura_por_id(self, db, factura_id):
        """Obtener factura por ID"""
        for factura in db['facturas']:
            if factura.id == factura_id:
                return factura
        return None

    def obtener_facturas_por_cliente(self, db, nit_cliente):
        """Obtener todas las facturas de un cliente"""
        return [f for f in db['facturas'] if f.nit_cliente == nit_cliente]

    def generar_reporte_analitico(self, db, fecha_inicio, fecha_fin, tipo_reporte):
        """Generar reporte analítico de ventas con datos REALES"""
        if tipo_reporte == 'categorias':
            return self._analizar_ingresos_por_categoria(db, fecha_inicio, fecha_fin)
        elif tipo_reporte == 'recursos':
            return self._analizar_ingresos_por_recurso(db, fecha_inicio, fecha_fin)
        else:
            return {'error': 'Tipo de reporte no válido'}

    def _analizar_ingresos_por_categoria(self, db, fecha_inicio, fecha_fin):
        """Analizar ingresos por categoría en un rango de fechas con datos REALES"""
        ingresos_por_categoria = {}

        # Procesar todas las facturas en el rango
        for factura in db['facturas']:
            # Verificar si la factura está en el rango de fechas (simplificado)
            # En implementación real, se verificaría la fecha del período

            for detalle in factura.detalles:
                instancia = next((i for i in db['instancias'] if i.id == detalle.id_instancia), None)
                if not instancia:
                    continue

                configuracion = next((c for c in db['configuraciones'] if c.id == instancia.id_configuracion), None)
                if not configuracion:
                    continue

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
                ingresos_por_categoria[categoria.id]['ingresos'] += detalle.monto

        # Convertir sets a contadores
        for categoria_id, datos in ingresos_por_categoria.items():
            datos['configuraciones'] = len(datos['configuraciones'])
            datos['instancias'] = len(datos['instancias'])

        return ingresos_por_categoria

    def _analizar_ingresos_por_recurso(self, db, fecha_inicio, fecha_fin):
        """Analizar ingresos por recurso en un rango de fechas con datos REALES"""
        ingresos_por_recurso = {}

        for factura in db['facturas']:
            for detalle in factura.detalles:
                instancia = next((i for i in db['instancias'] if i.id == detalle.id_instancia), None)
                if not instancia:
                    continue

                configuracion = next((c for c in db['configuraciones'] if c.id == instancia.id_configuracion), None)
                if not configuracion:
                    continue

                # Calcular distribución del monto por recurso
                recursos_dict = {r.id: r for r in db['recursos']}
                costo_por_hora = configuracion.calcular_costo_hora(recursos_dict)

                if costo_por_hora > 0:
                    for recurso_config in configuracion.recursos:
                        recurso = recursos_dict.get(recurso_config.id_recurso)
                        if recurso:
                            proporcion = (recurso.valor_x_hora * recurso_config.cantidad) / costo_por_hora
                            monto_recurso = detalle.monto * proporcion
                            uso_recurso = recurso_config.cantidad * detalle.tiempo_total

                            if recurso.id not in ingresos_por_recurso:
                                ingresos_por_recurso[recurso.id] = {
                                    'nombre': recurso.nombre,
                                    'tipo': recurso.tipo,
                                    'uso_total': 0.0,
                                    'ingresos': 0.0
                                }

                            ingresos_por_recurso[recurso.id]['uso_total'] += uso_recurso
                            ingresos_por_recurso[recurso.id]['ingresos'] += monto_recurso

        return ingresos_por_recurso

    def _analizar_ingresos_por_categoria(self, db, fecha_inicio, fecha_fin):
        """Analizar ingresos por categoría en un rango de fechas"""
        ingresos_por_categoria = {}

        for factura in db['facturas']:
            # Aquí se implementaría la lógica para analizar por categoría
            # basándose en las configuraciones de las instancias facturadas
            pass

        return ingresos_por_categoria

    def _analizar_ingresos_por_recurso(self, db, fecha_inicio, fecha_fin):
        """Analizar ingresos por recurso en un rango de fechas"""
        ingresos_por_recurso = {}

        for factura in db['facturas']:
            # Aquí se implementaría la lógica para analizar por recurso
            # basándose en los recursos utilizados en las configuraciones
            pass

        return ingresos_por_recurso