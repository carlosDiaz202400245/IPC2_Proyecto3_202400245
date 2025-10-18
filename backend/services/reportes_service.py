from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from datetime import datetime
import os


class ReportePDFService:
    def __init__(self, output_path="reportes"):
        self.output_path = output_path
        self.ensure_directory()

    def ensure_directory(self):
        """Asegurar que el directorio de reportes existe"""
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

    def generar_detalle_factura(self, factura, db):
        """Generar reporte PDF con detalle de factura"""
        filename = f"factura_{factura.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.output_path, filename)

        doc = SimpleDocTemplate(filepath, pagesize=A4)
        elements = []

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Centrado
        )

        # Título
        elements.append(Paragraph("DETALLE DE FACTURA", title_style))
        elements.append(Spacer(1, 20))

        # Información de la factura
        factura_data = [
            ['Número de Factura:', str(factura.id)],
            ['NIT:', factura.nit_cliente],
            ['Fecha de Emisión:', factura.fecha_emision],
            ['Período Facturado:', factura.periodo],
            ['Monto Total:', f"Q{factura.monto_total:.2f}"]
        ]

        factura_table = Table(factura_data, colWidths=[2 * inch, 3 * inch])
        factura_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(factura_table)
        elements.append(Spacer(1, 30))

        # Detalle por instancia
        elements.append(Paragraph("DETALLE POR INSTANCIA", styles['Heading2']))
        elements.append(Spacer(1, 15))

        # Obtener información del cliente
        cliente = self._obtener_cliente(db, factura.nit_cliente)
        if cliente:
            cliente_info = [
                ['Nombre:', cliente.nombre],
                ['Dirección:', cliente.direccion],
                ['Email:', cliente.correo_electronico]
            ]

            cliente_table = Table(cliente_info, colWidths=[1.5 * inch, 4 * inch])
            cliente_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))

            elements.append(cliente_table)
            elements.append(Spacer(1, 20))

        # Tabla de detalles
        detalle_headers = ['Instancia', 'Configuración', 'Tiempo (hrs)', 'Monto (Q)']
        detalle_data = [detalle_headers]

        for detalle in factura.detalles:
            instancia = self._obtener_instancia(db, detalle.id_instancia)
            if instancia:
                configuracion = self._obtener_configuracion(db, instancia.id_configuracion)
                config_nombre = configuracion.nombre if configuracion else "N/A"

                detalle_data.append([
                    instancia.nombre,
                    config_nombre,
                    f"{detalle.tiempo_total:.2f}",
                    f"{detalle.monto:.2f}"
                ])

        if len(detalle_data) > 1:
            detalle_table = Table(detalle_data, colWidths=[1.5 * inch, 2 * inch, 1.5 * inch, 1.5 * inch])
            detalle_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))

            elements.append(detalle_table)
            elements.append(Spacer(1, 20))


        elements.append(Paragraph("DESGLOSE DE RECURSOS", styles['Heading3']))
        elements.append(Spacer(1, 10))

        recursos_data = self._generar_desglose_recursos(factura, db)
        if recursos_data:
            recursos_table = Table(recursos_data, colWidths=[2 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch])
            recursos_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))

            elements.append(recursos_table)

        # Generar PDF
        doc.build(elements)
        return filepath

    def generar_analisis_ventas(self, reporte_data, tipo_reporte, fecha_inicio, fecha_fin):
        """Generar reporte PDF de análisis de ventas"""
        filename = f"analisis_ventas_{tipo_reporte}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.output_path, filename)

        doc = SimpleDocTemplate(filepath, pagesize=A4)
        elements = []

        styles = getSampleStyleSheet()

        # Título
        titulo = f"ANÁLISIS DE VENTAS - {tipo_reporte.upper()}"
        elements.append(Paragraph(titulo, styles['Heading1']))
        elements.append(Spacer(1, 10))

        # Período
        periodo_text = f"Período: {fecha_inicio} a {fecha_fin}"
        elements.append(Paragraph(periodo_text, styles['Normal']))
        elements.append(Spacer(1, 30))

        if tipo_reporte == 'categorias':
            self._generar_reporte_categorias(elements, reporte_data, styles)
        elif tipo_reporte == 'recursos':
            self._generar_reporte_recursos(elements, reporte_data, styles)

        # Generar PDF
        doc.build(elements)
        return filepath

    def _generar_reporte_categorias(self, elements, reporte_data, styles):
        """Generar sección de reporte por categorías con datos REALES"""
        elements.append(Paragraph("INGRESOS POR CATEGORÍA", styles['Heading2']))
        elements.append(Spacer(1, 15))

        if not reporte_data:
            elements.append(Paragraph("No hay datos disponibles para el período seleccionado", styles['Normal']))
            return

        # Preparar datos para tabla
        tabla_data = [['Categoría', 'Configuraciones', 'Instancias', 'Ingresos (Q)']]

        total_ingresos = 0
        total_configuraciones = 0
        total_instancias = 0

        for categoria_id, datos in reporte_data.items():
            ingresos = datos.get('ingresos', 0)
            configuraciones = datos.get('configuraciones', 0)
            instancias = datos.get('instancias', 0)

            tabla_data.append([
                datos.get('nombre', 'N/A'),
                str(configuraciones),
                str(instancias),
                f"{ingresos:.2f}"
            ])

            total_ingresos += ingresos
            total_configuraciones += configuraciones
            total_instancias += instancias

        # Agregar fila de totales
        tabla_data.append([
            'TOTAL',
            str(total_configuraciones),
            str(total_instancias),
            f"{total_ingresos:.2f}"
        ])

        tabla = Table(tabla_data, colWidths=[2.5 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -2), colors.white),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(tabla)

    def _generar_reporte_recursos(self, elements, reporte_data, styles):
        """Generar sección de reporte por recursos con datos REALES"""
        elements.append(Paragraph("INGRESOS POR RECURSO", styles['Heading2']))
        elements.append(Spacer(1, 15))

        if not reporte_data:
            elements.append(Paragraph("No hay datos disponibles para el período seleccionado", styles['Normal']))
            return

        tabla_data = [['Recurso', 'Tipo', 'Uso Total', 'Ingresos (Q)']]

        total_ingresos = 0
        total_uso = 0

        for recurso_id, datos in reporte_data.items():
            ingresos = datos.get('ingresos', 0)
            uso_total = datos.get('uso_total', 0)

            tabla_data.append([
                datos.get('nombre', 'N/A'),
                datos.get('tipo', 'N/A'),
                f"{uso_total:.2f}",
                f"{ingresos:.2f}"
            ])

            total_ingresos += ingresos
            total_uso += uso_total

        # Agregar fila de totales
        tabla_data.append([
            'TOTAL',
            '',
            f"{total_uso:.2f}",
            f"{total_ingresos:.2f}"
        ])

        tabla = Table(tabla_data, colWidths=[2.5 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -2), colors.white),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(tabla)

    def _obtener_cliente(self, db, nit_cliente):
        """Obtener cliente por NIT"""
        return next((c for c in db['clientes'] if c.nit == nit_cliente), None)

    def _obtener_instancia(self, db, id_instancia):
        """Obtener instancia por ID"""
        return next((i for i in db['instancias'] if i.id == id_instancia), None)

    def _obtener_configuracion(self, db, id_configuracion):
        """Obtener configuración por ID"""
        return next((c for c in db['configuraciones'] if c.id == id_configuracion), None)

    def _generar_desglose_recursos(self, factura, db):
        """Generar desglose REAL de recursos utilizados en la factura"""
        # Diccionario para acumular el uso y costo por recurso
        recursos_acumulados = {}

        # Procesar cada detalle de la factura
        for detalle in factura.detalles:
            instancia = self._obtener_instancia(db, detalle.id_instancia)
            if not instancia:
                continue

            configuracion = self._obtener_configuracion(db, instancia.id_configuracion)
            if not configuracion:
                continue

            # Calcular el tiempo total de esta instancia en el período facturado
            tiempo_instancia = detalle.tiempo_total

            # Procesar cada recurso de la configuración
            for recurso_config in configuracion.recursos:
                recurso = self._obtener_recurso(db, recurso_config.id_recurso)
                if not recurso:
                    continue

                # Calcular cantidad y costo para este recurso
                cantidad = recurso_config.cantidad
                costo_por_hora = recurso.valor_x_hora * cantidad
                costo_total = costo_por_hora * tiempo_instancia

                # Acumular en el diccionario
                if recurso.id not in recursos_acumulados:
                    recursos_acumulados[recurso.id] = {
                        'nombre': recurso.nombre,
                        'metrica': recurso.metrica,
                        'cantidad_total': 0.0,
                        'costo_total': 0.0,
                        'tipo': recurso.tipo
                    }

                recursos_acumulados[recurso.id]['cantidad_total'] += cantidad * tiempo_instancia
                recursos_acumulados[recurso.id]['costo_total'] += costo_total

        # Convertir a formato de tabla
        tabla_data = [['Recurso', 'Tipo', 'Métrica', 'Uso Total', 'Costo Total (Q)']]

        for recurso_id, datos in recursos_acumulados.items():
            tabla_data.append([
                datos['nombre'],
                datos['tipo'],
                datos['metrica'],
                f"{datos['cantidad_total']:.2f}",
                f"{datos['costo_total']:.2f}"
            ])

        # Ordenar por costo total (mayor a menor)
        if len(tabla_data) > 1:
            tabla_data[1:] = sorted(tabla_data[1:], key=lambda x: float(x[4].replace('Q', '').strip()), reverse=True)

        return tabla_data

    def _obtener_recurso(self, db, id_recurso):
        """Obtener recurso por ID"""
        return next((r for r in db['recursos'] if r.id == id_recurso), None)