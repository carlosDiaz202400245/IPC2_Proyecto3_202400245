# app/views.py COMPLETO Y CORREGIDO
import requests
import json
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.conf import settings
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from io import BytesIO
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
import xml.etree.ElementTree as ET

# Configuración del backend
BACKEND_URL = getattr(settings, 'BACKEND_URL', 'http://localhost:5000')

def dashboard(request):
    """Página principal del dashboard"""
    # Intentar cargar estadísticas del backend
    estadisticas = {
        'recursos': 0,
        'clientes': 0,
        'instancias': 0,
        'facturas': 0,
        'consumos': 0
    }

    try:
        response = requests.get(f"{BACKEND_URL}/consultar", params={'tipo': 'all'})
        if response.status_code == 200:
            data = response.json()
            estadisticas['recursos'] = len(data.get('recursos', []))
            estadisticas['clientes'] = len(data.get('clientes', []))
            estadisticas['instancias'] = len(data.get('instancias', []))
            estadisticas['facturas'] = len(data.get('facturas', []))
            estadisticas['consumos'] = len(data.get('consumos', []))
    except:
        # Si el backend no está disponible, usar valores por defecto
        pass

    return render(request, 'dashboard.html', {'estadisticas': estadisticas})


def enviar_configuracion(request):
    """Procesar mensaje XML de configuración - CON MANEJO DE ARCHIVOS GRANDES"""
    print("=" * 60)
    print(" DEBUG: VISTA enviar_configuracion INICIADA")
    print(f" Método: {request.method}")
    print(f" FILES: {dict(request.FILES)}")
    print("=" * 60)

    if request.method == 'POST':
        print(" POST RECIBIDO EN LA VISTA ")

        try:
            xml_file = request.FILES.get('xml_file')
            print(f" Archivo recibido: {xml_file}")

            if xml_file:
                print(f" Nombre: {xml_file.name}")
                print(f" Tamaño: {xml_file.size} bytes")

                # Validar que sea XML
                if not xml_file.name.endswith('.xml'):
                    print(" Archivo no es XML")
                    messages.error(request, "El archivo debe ser XML")
                    return redirect('configuracion')


                xml_bytes = b""
                chunk_size = 8192  # 8KB chunks

                for chunk in xml_file.chunks(chunk_size):
                    xml_bytes += chunk

                # Decodificar UNA SOLA VEZ al final
                xml_content = xml_bytes.decode('utf-8')

                print("=" * 60)
                print(" VERIFICACIÓN FINAL DEL ARCHIVO EN FRONTEND")
                print("=" * 60)
                print(f" Tamaño en BYTES: {len(xml_bytes)}")
                print(f" Tamaño en CARACTERES: {len(xml_content)}")
                print(f" PRIMEROS 50 chars: {repr(xml_content[:50])}")
                print(f" ÚLTIMOS 50 chars: {repr(xml_content[-50:])}")
                print(f" ¿Termina correctamente?: {xml_content.strip().endswith('</archivoConfiguraciones>')}")
                print("=" * 60)
                # **VALIDAR INTEGRIDAD DEL XML**
                if not xml_content.strip().endswith('</archivoConfiguraciones>'):
                    print(" ERROR: XML truncado o incompleto")
                    print(f" Final del archivo: {xml_content[-50:]}")
                    messages.error(request, "El archivo XML está incompleto o corrupto")
                    return render(request, 'configuracion/enviar_configuracion.html', {
                        'error': 'El archivo XML está incompleto. Verifique que no se haya cortado durante la subida.'
                    })

                # Intentar parsear para validar estructura
                try:
                    ET.fromstring(xml_content)
                    print(" XML válido - estructura correcta")
                except ET.ParseError as e:
                    print(f" ERROR DE PARSEO XML: {e}")
                    messages.error(request, f"Error en la estructura XML: {str(e)}")
                    return render(request, 'configuracion/enviar_configuracion.html', {
                        'error': f'Error en la estructura XML: {str(e)}'
                    })

                # ENVIAR AL BACKEND
                headers = {
                    'Content-Type': 'application/xml',
                    'Accept': 'application/json'
                }

                backend_url = f"{BACKEND_URL}/configuracion"
                print(f"🔗 Enviando a: {backend_url}")

                try:
                    print(" Iniciando request al backend para archivo grande...")

                    # Crear sesión con configuración optimizada
                    session = requests.Session()

                    # Configurar adapter con buffers más grandes
                    from requests.adapters import HTTPAdapter

                    adapter = HTTPAdapter(
                        pool_connections=100,
                        pool_maxsize=100,
                        max_retries=3,
                        pool_block=True
                    )

                    session.mount("http://", adapter)
                    session.mount("https://", adapter)

                    #  HEADERS ESPECÍFICOS para xmls grandes como los de prueba
                    headers = {
                        'Content-Type': 'application/xml; charset=utf-8',
                        'Accept': 'application/json',
                        'Content-Length': str(len(xml_content.encode('utf-8'))),
                        'Connection': 'keep-alive'
                    }

                    print(f" Enviando {len(xml_content)} caracteres ({len(xml_content.encode('utf-8'))} bytes)")

                    #  ENVÍO CON CONFIGURACIÓN MEJORADA
                    response = session.post(
                        backend_url,
                        data=xml_content.encode('utf-8'),
                        headers=headers,
                        timeout=120,
                        verify=False,
                        stream=True  #  Usar streaming para archivos grandes
                    )

                    print(f" Request completado. Status: {response.status_code}")
                    print("=" * 50)
                    print(" RESPUESTA DEL BACKEND:")
                    print(f" Status Code: {response.status_code}")
                    print(f" Response Text: {response.text}")
                    print("=" * 50)

                    if response.status_code == 201:
                        data = response.json()
                        print(f" Procesamiento exitoso: {data}")

                        resultado = data.get('resultado', {})
                        detalles = []

                        if 'recursos_procesados' in resultado:
                            detalles.append(f"{resultado['recursos_procesados']} recursos")
                        if 'categorias_procesadas' in resultado:
                            detalles.append(f"{resultado['categorias_procesadas']} categorías")
                        if 'configuraciones_procesadas' in resultado:
                            detalles.append(f"{resultado['configuraciones_procesadas']} configuraciones")
                        if 'clientes_procesados' in resultado:
                            detalles.append(f"{resultado['clientes_procesados']} clientes")
                        if 'instancias_procesadas' in resultado:
                            detalles.append(f"{resultado['instancias_procesadas']} instancias")

                        if detalles:
                            mensaje = f" Configuración procesada: {', '.join(detalles)}"
                        else:
                            mensaje = data.get('mensaje', ' Configuración procesada exitosamente')

                        messages.success(request, mensaje)
                        print(f" Mensaje de éxito: {mensaje}")

                        return render(request, 'configuracion/enviar_configuracion.html', {
                            'data': data,
                            'success': mensaje
                        })

                    else:
                        print(f" Error del backend - Status: {response.status_code}")
                        try:
                            error_data = response.json()
                            error_msg = error_data.get('error', f'Error {response.status_code} del backend')
                        except:
                            error_msg = f'Error {response.status_code}: {response.text}'

                        messages.error(request, error_msg)
                        print(f" Error message: {error_msg}")

                        return render(request, 'configuracion/enviar_configuracion.html', {
                            'error': error_msg
                        })

                except requests.exceptions.ConnectionError as e:
                    error_msg = f" No se puede conectar al backend en {BACKEND_URL}"
                    print(f" ConnectionError: {e}")
                    messages.error(request, error_msg)
                    return render(request, 'configuracion/enviar_configuracion.html', {
                        'error': error_msg
                    })

                except requests.exceptions.Timeout as e:
                    error_msg = " Timeout: El backend tardó más de 60 segundos en responder"
                    print(f" Timeout: {e}")
                    messages.error(request, error_msg)
                    return render(request, 'configuracion/enviar_configuracion.html', {
                        'error': error_msg
                    })

                except requests.exceptions.RequestException as e:
                    error_msg = f"🔌 Error de conexión: {str(e)}"
                    print(f" RequestException: {e}")
                    messages.error(request, error_msg)
                    return render(request, 'configuracion/enviar_configuracion.html', {
                        'error': error_msg
                    })

            else:
                print(" No se recibió archivo")
                messages.error(request, " No se seleccionó ningún archivo")

        except UnicodeDecodeError as e:
            error_msg = " Error de codificación: El archivo no está en UTF-8 válido"
            print(f" UnicodeDecodeError: {e}")
            messages.error(request, error_msg)
            return render(request, 'configuracion/enviar_configuracion.html', {
                'error': error_msg
            })

        except MemoryError as e:
            error_msg = "Error de memoria: El archivo es demasiado grande"
            print(f" MemoryError: {e}")
            messages.error(request, error_msg)
            return render(request, 'configuracion/enviar_configuracion.html', {
                'error': error_msg
            })

        except Exception as e:
            error_msg = f" Error procesando archivo: {str(e)}"
            print(f" General Exception: {e}")
            messages.error(request, error_msg)
            return render(request, 'configuracion/enviar_configuracion.html', {
                'error': error_msg
            })

    else:
        print(" Método GET - Mostrando formulario")

    return render(request, 'configuracion/enviar_configuracion.html')


def enviar_consumo(request):
    """Procesar mensaje XML de consumo"""
    if request.method == 'POST':
        try:
            xml_file = request.FILES.get('xml_file')

            if not xml_file:
                return JsonResponse({
                    'mensaje': 'No se proporcionó archivo XML',
                    'resultado': {}
                }, status=400)

            # Leer y procesar el XML
            xml_content = xml_file.read().decode('utf-8')

            # Enviar al backend
            headers = {
                'Content-Type': 'application/xml',
                'Accept': 'application/json'
            }

            response = requests.post(
                f"{BACKEND_URL}/consumo",
                data=xml_content,
                headers=headers,
                timeout=30
            )

            if response.status_code in [200, 201]:
                data = response.json()
                return JsonResponse({
                    'mensaje': 'Consumo procesado exitosamente',
                    'resultado': data.get('resultado', {})
                })
            else:
                error_data = response.json()
                return JsonResponse({
                    'mensaje': 'Error al procesar consumo',
                    'resultado': {
                        'errores': [error_data.get('error', 'Error desconocido')]
                    }
                }, status=400)

        except Exception as e:
            return JsonResponse({
                'mensaje': 'Error al procesar el consumo',
                'resultado': {
                    'errores': [f'Error: {str(e)}']
                }
            }, status=500)

    # GET request - mostrar el formulario
    return render(request, 'consumo/enviar_consumo.html')


def inicializar_sistema(request):
    """Inicializar sistema - eliminar todos los datos"""
    if request.method == 'POST':
        try:
            response = requests.post(f"{BACKEND_URL}/reset")
            if response.status_code == 200:
                messages.success(request, "Sistema inicializado correctamente. Todos los datos han sido eliminados.")
            else:
                messages.error(request, "Error al inicializar el sistema")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

    return redirect('consultar')


def consultar_datos(request):
    """Consultar datos del sistema según tipo"""
    tipo = request.GET.get('tipo', 'all')

    try:
        # USAR ENDPOINT CORRECTO
        response = requests.get(f"{BACKEND_URL}/consultarDatos", params={'tipo': tipo})

        if response.status_code == 200:
            data = response.json()
            return render(request, 'operaciones/consultar_datos.html', {
                'data': data,
                'tipo': tipo,
                'timestamp': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            })
        else:
            messages.error(request, f"Error {response.status_code} al consultar datos")
    except requests.exceptions.ConnectionError:
        messages.error(request, " No se puede conectar al backend")
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")

    return render(request, 'operaciones/consultar_datos.html', {'data': None, 'tipo': tipo})


def crear_datos(request):
    """Crear nuevos datos manualmente - CORREGIDO"""
    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        datos = {}
        endpoint = None  # INICIALIZAR endpoint

        try:
            # Procesar datos según el tipo
            if tipo == 'recurso':
                datos = {
                    'id': int(request.POST.get('id')),
                    'nombre': request.POST.get('nombre'),
                    'abreviatura': request.POST.get('abreviatura'),
                    'metrica': request.POST.get('metrica'),
                    'tipo': request.POST.get('tipo'),
                    'valorXhora': float(request.POST.get('valorXhora'))
                }
                endpoint = '/crearRecurso'

            elif tipo == 'categoria':
                datos = {
                    'id': int(request.POST.get('id')),
                    'nombre': request.POST.get('nombre'),
                    'descripcion': request.POST.get('descripcion', ''),
                    'cargaTrabajo': request.POST.get('cargaTrabajo')
                }
                endpoint = '/crearCategoria'

            elif tipo == 'configuracion':
                recursos = request.POST.getlist('recursos[]')
                cantidades = request.POST.getlist('cantidades[]')
                recursos_config = []

                for i in range(len(recursos)):
                    if recursos[i] and cantidades[i]:
                        recursos_config.append({
                            'idRecurso': int(recursos[i]),
                            'cantidad': int(cantidades[i])
                        })

                datos = {
                    'id': int(request.POST.get('id')),
                    'idCategoria': int(request.POST.get('idCategoria')),
                    'nombre': request.POST.get('nombre'),
                    'descripcion': request.POST.get('descripcion', ''),
                    'recursos': recursos_config
                }
                endpoint = '/crearConfiguracion'

            elif tipo == 'cliente':
                datos = {
                    'nit': request.POST.get('nit'),
                    'nombre': request.POST.get('nombre'),
                    'usuario': request.POST.get('usuario'),
                    'clave': request.POST.get('clave'),
                    'direccion': request.POST.get('direccion', ''),
                    'correoElectronico': request.POST.get('correoElectronico')
                }
                endpoint = '/crearCliente'

            elif tipo == 'instancia':
                datos = {
                    'id': int(request.POST.get('id')),
                    'nitCliente': request.POST.get('nitCliente'),
                    'idConfiguracion': int(request.POST.get('idConfiguracion')),
                    'nombre': request.POST.get('nombre'),
                    'fechaInicio': request.POST.get('fechaInicio'),
                    'estado': request.POST.get('estado')
                }

                if datos['estado'] == 'Cancelada' and request.POST.get('fechaFinal'):
                    datos['fechaFinal'] = request.POST.get('fechaFinal')

                endpoint = '/crearInstancia'

            else:
                # TIPO NO VÁLIDO
                messages.error(request, f"Tipo de dato no válido: {tipo}")
                return redirect('crear')

            # VERIFICAR QUE ENDPOINT ESTÉ DEFINIDO
            if endpoint is None:
                messages.error(request, "Error: Endpoint no definido para el tipo de dato")
                return redirect('crear')

            # Enviar al backend
            print(f"Enviando datos a {endpoint}: {datos}")
            response = requests.post(f"{BACKEND_URL}{endpoint}", json=datos)

            if response.status_code == 200:
                messages.success(request, f"{tipo.capitalize()} creado exitosamente")
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', 'Error desconocido')
                except:
                    error_msg = f"Error {response.status_code}"
                messages.error(request, f"Error al crear {tipo}: {error_msg}")

        except ValueError as e:
            messages.error(request, f"Error en los datos: {str(e)}")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

        return redirect('crear')

    return render(request, 'operaciones/crear_datos.html')


def proceso_facturacion(request):
    """Generar facturas en un rango de fechas - CORREGIDO"""
    if request.method == 'POST':
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')

        print(f" DEBUG - Fechas recibidas del formulario:")
        print(f"  Fecha inicio: {fecha_inicio}")
        print(f"  Fecha fin: {fecha_fin}")

        # Validar que las fechas no estén vacías
        if not fecha_inicio or not fecha_fin:
            messages.error(request, "Ambas fechas son requeridas")
            return render(request, 'operaciones/facturacion.html')

        try:
            # Convertir fechas al formato dd/mm/yyyy que espera el backend
            fecha_inicio_obj = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            fecha_fin_obj = datetime.strptime(fecha_fin, '%Y-%m-%d')

            fecha_inicio_formatted = fecha_inicio_obj.strftime('%d/%m/%Y')
            fecha_fin_formatted = fecha_fin_obj.strftime('%d/%m/%Y')

            print(f" DEBUG - Fechas formateadas para backend:")
            print(f"  Fecha inicio formateada: {fecha_inicio_formatted}")
            print(f"  Fecha fin formateada: {fecha_fin_formatted}")

            # Preparar datos para el backend
            datos_facturacion = {
                'fechaInicio': fecha_inicio_formatted,
                'fechaFin': fecha_fin_formatted
            }

            print(f" DEBUG - Enviando al backend: {datos_facturacion}")

            endpoint = f"{BACKEND_URL}/generarFactura"

            try:
                print(f" Conectando a: {endpoint}")
                response = requests.post(
                    endpoint,
                    json=datos_facturacion,
                    timeout=30
                )

                print(f" Respuesta recibida - Status: {response.status_code}")
                print(f" Response text: {response.text}")

                if response.status_code == 200:
                    data = response.json()
                    print(f" DEBUG - Respuesta JSON completa del backend: {data}")


                    facturas_backend = data.get('facturas', [])
                    print(f" DEBUG - Facturas encontradas: {len(facturas_backend)}")

                    if facturas_backend:
                        # Convertir las facturas al formato que espera el template
                        facturas_formateadas = []
                        for factura in facturas_backend:
                            print(f" DEBUG - Procesando factura: {factura}")
                            factura_formateada = {
                                'id': factura.get('id'),
                                'numero_factura': f"FACT-{factura.get('id', '')}",
                                'nit_cliente': factura.get('nitCliente'),  #
                                'fecha_factura': factura.get('fechaEmision'),  #
                                'monto': factura.get('montoTotal', 0),  #
                                'periodo': factura.get('periodo'),
                                # Datos adicionales para el detalle
                                'detalles': factura.get('detalles', [])
                            }
                            facturas_formateadas.append(factura_formateada)

                        print(f" DEBUG - Facturas formateadas: {facturas_formateadas}")
                        messages.success(request, f" {len(facturas_formateadas)} facturas generadas exitosamente")

                        return render(request, 'operaciones/facturacion.html', {
                            'facturas': facturas_formateadas,
                            'fecha_inicio': fecha_inicio,
                            'fecha_fin': fecha_fin
                        })
                    else:
                        print(" DEBUG - No se encontraron facturas en la respuesta")
                        messages.info(request, "ℹ No se generaron facturas para el período seleccionado")
                        return render(request, 'operaciones/facturacion.html', {
                            'facturas': [],
                            'fecha_inicio': fecha_inicio,
                            'fecha_fin': fecha_fin
                        })
                else:
                    print(f" Error del backend - Status: {response.status_code}")
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('error', f'Error {response.status_code} del backend')
                        print(f" DEBUG - Error detallado: {error_data}")
                    except:
                        error_msg = f"Error {response.status_code}: {response.text}"
                        print(f" DEBUG - Error text: {response.text}")

                    messages.error(request, f" {error_msg}")

            except requests.exceptions.ConnectionError:
                error_msg = f"No se puede conectar al backend en {BACKEND_URL}"
                print(f" ConnectionError: {error_msg}")
                messages.error(request, error_msg)
            except requests.exceptions.Timeout:
                error_msg = "El backend tardó demasiado en responder"
                print(f" Timeout")
                messages.error(request, error_msg)
            except Exception as e:
                error_msg = f"Error de conexión: {str(e)}"
                print(f" Exception: {e}")
                messages.error(request, error_msg)

        except ValueError as e:
            error_msg = "Formato de fecha inválido. Use YYYY-MM-DD"
            print(f" ValueError: {e}")
            messages.error(request, error_msg)
        except Exception as e:
            error_msg = f"Error inesperado: {str(e)}"
            print(f" Exception: {e}")
            messages.error(request, error_msg)

    # GET request o después de POST
    return render(request, 'operaciones/facturacion.html')

def cancelar_instancia(request, instancia_id):
    """Cancelar una instancia específica"""
    if request.method == 'POST':
        try:
            response = requests.post(f"{BACKEND_URL}/cancelarInstancia/{instancia_id}")
            if response.status_code == 200:
                messages.success(request, f"Instancia {instancia_id} cancelada exitosamente")
            else:
                error_msg = response.json().get('error', 'Error al cancelar instancia')
                messages.error(request, error_msg)
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

    return redirect('consultar')


def reporte_detalle_factura(request, factura_id):
    """Generar reporte detallado de factura"""
    try:
        response = requests.get(f"{BACKEND_URL}/facturas/{factura_id}")
        if response.status_code == 200:
            factura = response.json()

            # Generar PDF si se solicita
            if request.GET.get('format') == 'pdf':
                return generar_pdf_detalle_factura(factura)

            return render(request, 'reportes/detalle_factura.html', {'factura': factura})
        else:
            messages.error(request, "Factura no encontrada")
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")

    return redirect('facturacion')


def reporte_analisis_ventas(request):
    """Generar análisis de ventas - CORREGIDO"""
    if request.method == 'POST':
        tipo_analisis = request.POST.get('tipo_analisis')
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')

        print(f" DEBUG - Análisis de ventas:")
        print(f"  Tipo: {tipo_analisis}")
        print(f"  Fecha inicio: {fecha_inicio}")
        print(f"  Fecha fin: {fecha_fin}")

        # Validar que las fechas no estén vacías
        if not fecha_inicio or not fecha_fin:
            messages.error(request, "Ambas fechas son requeridas")
            return render(request, 'reportes/analisis_ventas.html')
        if not tipo_analisis:
            messages.error(request, "El tipo de análisis es requerido")
            return render(request, 'reportes/analisis_ventas.html')

        try:
            # Convertir fechas
            fecha_inicio_obj = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            fecha_fin_obj = datetime.strptime(fecha_fin, '%Y-%m-%d')

            fecha_inicio_formatted = fecha_inicio_obj.strftime('%d/%m/%Y')
            fecha_fin_formatted = fecha_fin_obj.strftime('%d/%m/%Y')

            print(f" DEBUG - Fechas formateadas para backend:")
            print(f"  Fecha inicio: {fecha_inicio_formatted}")
            print(f"  Fecha fin: {fecha_fin_formatted}")

            datos_analisis = {
                'tipo': tipo_analisis,
                'fechaInicio': fecha_inicio_formatted,
                'fechaFin': fecha_fin_formatted
            }

            print(f" DEBUG - Enviando al backend: {datos_analisis}")

            endpoint = f"{BACKEND_URL}/reporte/analitico"

            response = requests.post(
                endpoint,
                json=datos_analisis,
                timeout=30
            )

            print(f" DEBUG - Respuesta del backend - Status: {response.status_code}")
            print(f" DEBUG - Response text: {response.text}")

            if response.status_code == 200:
                data = response.json()
                print(f" DEBUG - Datos recibidos: {data}")

                # Verificar si hay error en la respuesta
                reporte_data = data.get('reporte', {})

                if isinstance(reporte_data, dict) and 'error' in reporte_data:
                    error_msg = reporte_data['error']
                    print(f" Error del backend: {error_msg}")
                    messages.error(request, f"Error: {error_msg}")
                    return render(request, 'reportes/analisis_ventas.html')

                if isinstance(reporte_data, dict) and 'mensaje' in reporte_data:
                    info_msg = reporte_data['mensaje']
                    print(f" Mensaje del backend: {info_msg}")
                    messages.info(request, info_msg)
                    return render(request, 'reportes/analisis_ventas.html', {
                        'datos': [],
                        'tipo_analisis': tipo_analisis,
                        'fecha_inicio': fecha_inicio,
                        'fecha_fin': fecha_fin
                    })

                # Procesar datos normales
                datos_formateados = []
                total_ingresos = 0

                if tipo_analisis == 'categorias':
                    for categoria_id, info in reporte_data.items():
                        if isinstance(info, dict):
                            ingresos = info.get('ingresos', 0)
                            datos_formateados.append({
                                'categoria': info.get('nombre', f'Categoría {categoria_id}'),
                                'configuracion': f"{info.get('configuraciones', 0)} configs",
                                'ingresos': ingresos,
                                'porcentaje': 0
                            })
                            total_ingresos += ingresos
                else:
                    for recurso_id, info in reporte_data.items():
                        if isinstance(info, dict):
                            ingresos = info.get('ingresos', 0)
                            datos_formateados.append({
                                'recurso': info.get('nombre', f'Recurso {recurso_id}'),
                                'tipo': info.get('tipo', 'N/A'),
                                'ingresos': ingresos,
                                'porcentaje': 0
                            })
                            total_ingresos += ingresos

                # Calcular porcentajes
                if total_ingresos > 0:
                    for item in datos_formateados:
                        item['porcentaje'] = (item['ingresos'] / total_ingresos) * 100

                print(f" DEBUG - Datos formateados: {len(datos_formateados)} items")

                # Generar PDF si se solicita
                if request.POST.get('generar_pdf'):
                    return generar_pdf_analisis_ventas(datos_formateados, tipo_analisis, fecha_inicio_formatted,
                                                       fecha_fin_formatted)

                return render(request, 'reportes/analisis_ventas.html', {
                    'datos': datos_formateados,
                    'tipo_analisis': tipo_analisis,
                    'fecha_inicio': fecha_inicio,
                    'fecha_fin': fecha_fin,
                    'fecha_inicio_formatted': fecha_inicio_formatted,
                    'fecha_fin_formatted': fecha_fin_formatted
                })
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', 'Error al generar análisis')
                except:
                    error_msg = f"Error {response.status_code}: {response.text}"

                print(f" Error: {error_msg}")
                messages.error(request, error_msg)

        except ValueError as e:
            error_msg = "Formato de fecha inválido"
            print(f"ValueError: {e}")
            messages.error(request, error_msg)
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(f" Exception: {e}")
            messages.error(request, error_msg)

    return render(request, 'reportes/analisis_ventas.html')

def info_estudiante(request):
    """Mostrar información del estudiante"""
    info = {
        'nombre': 'Tu Nombre Completo',
        'carnet': 'Tu Carnet',
        'curso': 'Introducción a la Programación y Computación 2',
        'semestre': '2S2025',
        'proyecto': 'Proyecto 3 - Sistema de Gestión Cloud',
        'empresa': 'Tecnologías Chapinas, S.A.',
        'fecha_entrega': '24 de Octubre 2024'
    }
    return render(request, 'ayuda/info_estudiante.html', {'info': info})


# ===== FUNCIONES PARA GENERACIÓN DE PDFs  =====

def generar_pdf_detalle_factura(factura):
    """Generar PDF detallado de factura"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=1 * inch)
    elements = []
    styles = getSampleStyleSheet()

    # Estilos personalizados
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1  # Centrado
    )

    # Título
    title = Paragraph(f"DETALLE DE FACTURA #{factura.get('numero_factura', '')}", title_style)
    elements.append(title)

    # Información de la factura
    info_data = [
        ['NÚMERO DE FACTURA:', factura.get('numero_factura', '')],
        ['FECHA DE FACTURA:', factura.get('fecha_factura', '')],
        ['NIT CLIENTE:', factura.get('nit_cliente', '')],
        ['NOMBRE CLIENTE:', factura.get('nombre_cliente', '')],
        ['DIRECCIÓN:', factura.get('direccion_cliente', '')],
        ['EMAIL:', factura.get('email_cliente', '')]
    ]

    info_table = Table(info_data, colWidths=[200, 300])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
        ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#ecf0f1')),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 20))

    # Detalle por instancias
    instancias = factura.get('instancias', [])
    for idx, instancia in enumerate(instancias, 1):
        # Encabezado de instancia
        instancia_title = Paragraph(f"INSTANCIA {idx}: {instancia.get('nombre', '')}", styles['Heading2'])
        elements.append(instancia_title)

        # Información de la instancia
        instancia_info = [
            ['Configuración:', instancia.get('configuracion', '')],
            ['Tiempo Total:', f"{instancia.get('tiempo_total', 0)} horas"],
            ['Costo Total:', f"Q{instancia.get('costo_total', 0):.2f}"]
        ]

        instancia_table = Table(instancia_info, colWidths=[150, 350])
        instancia_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ]))
        elements.append(instancia_table)

        # Detalle de recursos
        recursos = instancia.get('recursos', [])
        if recursos:
            recurso_headers = ['Recurso', 'Tipo', 'Cantidad', 'Valor/Hora', 'Horas', 'Subtotal']
            recurso_data = [recurso_headers]

            for recurso in recursos:
                recurso_data.append([
                    recurso.get('nombre', ''),
                    recurso.get('tipo', ''),
                    str(recurso.get('cantidad', 0)),
                    f"Q{recurso.get('valor_hora', 0):.2f}",
                    f"{recurso.get('horas_usadas', 0):.2f}",
                    f"Q{recurso.get('subtotal', 0):.2f}"
                ])

            # Agregar total de la instancia
            recurso_data.append(['', '', '', '', 'TOTAL:', f"Q{instancia.get('costo_total', 0):.2f}"])

            recursos_table = Table(recurso_data, colWidths=[120, 80, 60, 70, 60, 70])
            recursos_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BACKGROUND', (0, 1), (-1, -2), colors.HexColor('#f8f9fa')),
                ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -2), 8),
                ('BACKGROUND', (-2, -1), (-1, -1), colors.HexColor('#e74c3c')),
                ('TEXTCOLOR', (-2, -1), (-1, -1), colors.whitesmoke),
                ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(recursos_table)

        elements.append(Spacer(1, 15))

    # Resumen final
    elements.append(Spacer(1, 20))
    resumen_data = [
        ['SUBTOTAL:', f"Q{factura.get('subtotal', 0):.2f}"],
        ['IVA (12%):', f"Q{factura.get('iva', 0):.2f}"],
        ['TOTAL A PAGAR:', f"Q{factura.get('monto', 0):.2f}"]
    ]

    resumen_table = Table(resumen_data, colWidths=[400, 100])
    resumen_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
        ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#27ae60')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('PADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(resumen_table)

    # Pie de página
    elements.append(Spacer(1, 30))
    footer = Paragraph(
        f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} - Tecnologías Chapinas, S.A.",
        styles['Normal']
    )
    elements.append(footer)

    doc.build(elements)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="factura_{factura.get("numero_factura", "")}_detalle.pdf"'
    return response


def generar_pdf_analisis_ventas(datos, tipo_analisis, fecha_inicio, fecha_fin):
    """Generar PDF de análisis de ventas - ACTUALIZADO"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # Título
    titulo = "ANÁLISIS DE VENTAS"
    if tipo_analisis == 'categorias':
        titulo += " - CATEGORÍAS Y CONFIGURACIONES"
    else:
        titulo += " - RECURSOS"

    title = Paragraph(titulo, styles['Heading1'])
    elements.append(title)

    # Período
    periodo = Paragraph(f"Período: {fecha_inicio} al {fecha_fin}", styles['Heading3'])
    elements.append(periodo)
    elements.append(Spacer(1, 20))

    # Tabla de datos
    if tipo_analisis == 'categorias':
        headers = ['Categoría', 'Configuraciones', 'Ingresos (Q)', 'Porcentaje']
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

    if len(data) > 1:  # Si hay datos además de los headers
        table = Table(data, colWidths=[180, 180, 80, 60])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecf0f1')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("No hay datos para mostrar", styles['Normal']))

    # Resumen
    elements.append(Spacer(1, 20))
    total_ingresos = sum(item.get('ingresos', 0) for item in datos)
    resumen = Paragraph(f"<b>Total de Ingresos en el Período: Q{total_ingresos:.2f}</b>", styles['Heading3'])
    elements.append(resumen)

    doc.build(elements)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    filename = f"analisis_ventas_{tipo_analisis}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def crear_datos(request):
    """Crear nuevos datos manualmente - CORREGIDO"""
    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        datos = {}
        endpoint = None

        try:
            # Procesar datos según el tipo
            if tipo == 'recurso':
                datos = {
                    'id': int(request.POST.get('id')),
                    'nombre': request.POST.get('nombre'),
                    'abreviatura': request.POST.get('abreviatura'),
                    'metrica': request.POST.get('metrica'),
                    'tipo': request.POST.get('tipo_recurso'),
                    'valorXhora': float(request.POST.get('valorXhora'))
                }
                endpoint = '/crearRecurso'

            elif tipo == 'categoria':
                datos = {
                    'id': int(request.POST.get('id')),
                    'nombre': request.POST.get('nombre'),
                    'descripcion': request.POST.get('descripcion', ''),
                    'cargaTrabajo': request.POST.get('cargaTrabajo')
                }
                endpoint = '/crearCategoria'

            elif tipo == 'configuracion':
                recursos = request.POST.getlist('recursos[]')
                cantidades = request.POST.getlist('cantidades[]')
                recursos_config = []

                for i in range(len(recursos)):
                    if recursos[i] and cantidades[i]:
                        recursos_config.append({
                            'idRecurso': int(recursos[i]),
                            'cantidad': int(cantidades[i])
                        })

                datos = {
                    'id': int(request.POST.get('id')),
                    'idCategoria': int(request.POST.get('idCategoria')),
                    'nombre': request.POST.get('nombre'),
                    'descripcion': request.POST.get('descripcion', ''),
                    'recursos': recursos_config
                }
                endpoint = '/crearConfiguracion'

            elif tipo == 'cliente':
                datos = {
                    'nit': request.POST.get('nit'),
                    'nombre': request.POST.get('nombre'),
                    'usuario': request.POST.get('usuario'),
                    'clave': request.POST.get('clave'),
                    'direccion': request.POST.get('direccion', ''),
                    'correoElectronico': request.POST.get('correoElectronico')
                }
                endpoint = '/crearCliente'

            elif tipo == 'instancia':
                datos = {
                    'id': int(request.POST.get('id')),
                    'nitCliente': request.POST.get('nitCliente'),
                    'idConfiguracion': int(request.POST.get('idConfiguracion')),
                    'nombre': request.POST.get('nombre'),
                    'fechaInicio': request.POST.get('fechaInicio'),
                    'estado': request.POST.get('estado')
                }

                if datos['estado'] == 'Cancelada' and request.POST.get('fechaFinal'):
                    datos['fechaFinal'] = request.POST.get('fechaFinal')

                endpoint = '/crearInstancia'

            else:
                messages.error(request, f"Tipo de dato no válido: {tipo}")
                return redirect('crear')

            if endpoint is None:
                messages.error(request, "Error: Endpoint no definido para el tipo de dato")
                return redirect('crear')

            # Enviar al backend
            print(f"Enviando datos a {endpoint}: {datos}")
            response = requests.post(f"{BACKEND_URL}{endpoint}", json=datos)

            # CORRECCIÓN: Verificar tanto 200 como 201 como exitosos
            if response.status_code in [200, 201]:  # ¡CAMBIÉ ESTA LÍNEA!
                messages.success(request, f"{tipo.capitalize()} creado exitosamente")
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', 'Error desconocido')
                except:
                    error_msg = f"Error {response.status_code}: {response.text}"
                messages.error(request, f"Error al crear {tipo}: {error_msg}")

        except ValueError as e:
            messages.error(request, f"Error en los datos: {str(e)}")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

        return redirect('crear')

    return render(request, 'operaciones/crear_datos.html')