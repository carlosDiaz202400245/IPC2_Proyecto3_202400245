
import requests
from django.shortcuts import render
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from io import BytesIO
from datetime import datetime


def generar_pdf_factura(factura):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    # Título
    title = Paragraph(f"FACTURA #{factura.get('numero_factura', '')}", styles['Heading1'])
    elements.append(title)

    # Información de la factura
    data = [
        ['NIT Cliente:', factura.get('nit_cliente', '')],
        ['Fecha Factura:', factura.get('fecha_factura', '')],
        ['Monto Total:', f"Q{factura.get('monto', 0):.2f}"]
    ]

    table = Table(data, colWidths=[200, 200])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="factura_{factura.get("numero_factura", "")}.pdf"'
    return response


def generar_pdf_analisis(datos, tipo, fecha_inicio, fecha_fin):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    # Título
    title_text = f"Análisis de Ventas - {tipo.capitalize()}"
    title = Paragraph(title_text, styles['Heading1'])
    elements.append(title)

    # Período
    periodo = Paragraph(f"Período: {fecha_inicio} al {fecha_fin}", styles['Normal'])
    elements.append(periodo)

    # Tabla de datos
    if tipo == 'categorias':
        headers = ['Categoría', 'Configuración', 'Ingresos (Q)', 'Porcentaje']
        data = [headers]
        for item in datos:
            data.append([
                item.get('categoria', ''),
                item.get('configuracion', ''),
                f"{item.get('ingresos', 0):.2f}",
                f"{item.get('porcentaje', 0):.1f}%"
            ])
    else:
        headers = ['Recurso', 'Tipo', 'Ingresos (Q)', 'Porcentaje']
        data = [headers]
        for item in datos:
            data.append([
                item.get('recurso', ''),
                item.get('tipo', ''),
                f"{item.get('ingresos', 0):.2f}",
                f"{item.get('porcentaje', 0):.1f}%"
            ])

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    filename = f"analisis_ventas_{tipo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response