from flask import Flask, request, jsonify
from flask_cors import CORS
from services.configuracion_service import ProcesadorConfiguracion
from services.consumo_service import ProcesadorConsumo
from services.facturacion_service import FacturacionService
from database.xml_manager import XMLManager
from utils.validators import validar_nit, extraer_fecha
import re
from services.reportes_service import ReportePDFService
import base64

app = Flask(__name__)
CORS(app)

# Inicializar servicios
xml_manager = XMLManager()
procesador_config = ProcesadorConfiguracion()
procesador_consumo = ProcesadorConsumo()
facturacion_service = FacturacionService()
reporte_service = ReportePDFService()

# Cargar datos existentes al iniciar
db = xml_manager.cargar_todo()


def guardar_db():
    """Función helper para guardar la base de datos"""
    xml_manager.guardar_todo(db)


# ==================== ENDPOINTS PRINCIPALES ====================

@app.route('/configuracion', methods=['POST'])
def recibir_configuracion():
    """Procesar mensaje XML de configuración """
    try:
        xml_data = request.data.decode('utf-8')
        resultado = procesador_config.procesar_xml(xml_data, db)
        guardar_db()  # Persistir cambios

        return jsonify({
            'mensaje': 'Configuración procesada exitosamente',
            'resultado': resultado
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/consumo', methods=['POST'])
def recibir_consumo():
    """Procesar mensaje XML de consumo """
    try:
        xml_data = request.data.decode('utf-8')
        resultado = procesador_consumo.procesar_xml(xml_data, db)
        guardar_db()  # Persistir cambios

        return jsonify({
            'mensaje': 'Consumo procesado exitosamente',
            'resultado': resultado
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/consultarDatos', methods=['GET'])
def consultar_datos():
    """Consultar todos los datos del sistema"""
    try:
        tipo = request.args.get('tipo', 'all')

        # Convertir objetos a dict para JSON
        if tipo == 'recursos':
            datos = [r.to_dict() for r in db['recursos']]
            return jsonify({'recursos': datos})
        elif tipo == 'categorias':
            datos = [c.to_dict() for c in db['categorias']]
            return jsonify({'categorias': datos})
        elif tipo == 'configuraciones':
            datos = [c.to_dict() for c in db['configuraciones']]
            return jsonify({'configuraciones': datos})
        elif tipo == 'clientes':
            datos = [c.to_dict() for c in db['clientes']]
            return jsonify({'clientes': datos})
        elif tipo == 'instancias':
            datos = [i.to_dict() for i in db['instancias']]
            return jsonify({'instancias': datos})
        elif tipo == 'facturas':
            datos = [f.to_dict() for f in db['facturas']]
            return jsonify({'facturas': datos})
        else:
            return jsonify({
                'recursos': [r.to_dict() for r in db['recursos']],
                'categorias': [c.to_dict() for c in db['categorias']],
                'configuraciones': [c.to_dict() for c in db['configuraciones']],
                'clientes': [c.to_dict() for c in db['clientes']],
                'instancias': [i.to_dict() for i in db['instancias']],
                'facturas': [f.to_dict() for f in db['facturas']]
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/crearRecurso', methods=['POST'])
def crear_recurso():
    """Crear un nuevo recurso """
    try:
        data = request.get_json()

        if not all(key in data for key in ['id', 'nombre', 'abreviatura', 'metrica', 'tipo', 'valorXhora']):
            return jsonify({'error': 'Faltan campos requeridos'}), 400

        # Verificar si el ID ya existe
        if any(r.id == data['id'] for r in db['recursos']):
            return jsonify({'error': 'El ID del recurso ya existe'}), 400

        # Validar tipo de recurso
        if data['tipo'] not in ['Hardware', 'Software']:
            return jsonify({'error': 'Tipo de recurso debe ser Hardware o Software'}), 400

        # Crear objeto Recurso
        nuevo_recurso = Recurso(
            data['id'], data['nombre'], data['abreviatura'],
            data['metrica'], data['tipo'], data['valorXhora']
        )

        db['recursos'].append(nuevo_recurso)
        guardar_db()

        return jsonify({
            'mensaje': 'Recurso creado exitosamente',
            'recurso': nuevo_recurso.to_dict()
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/crearCategoria', methods=['POST'])
def crear_categoria():
    """Crear una nueva categoría """
    try:
        data = request.get_json()

        if not all(key in data for key in ['id', 'nombre', 'descripcion', 'cargaTrabajo']):
            return jsonify({'error': 'Faltan campos requeridos'}), 400

        if any(c.id == data['id'] for c in db['categorias']):
            return jsonify({'error': 'El ID de la categoría ya existe'}), 400

        nueva_categoria = Categoria(
            data['id'], data['nombre'], data['descripcion'], data['cargaTrabajo']
        )

        db['categorias'].append(nueva_categoria)
        guardar_db()

        return jsonify({
            'mensaje': 'Categoría creada exitosamente',
            'categoria': nueva_categoria.to_dict()
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/crearConfiguracion', methods=['POST'])
def crear_configuracion():
    """Crear una nueva configuración """
    try:
        data = request.get_json()

        if not all(key in data for key in ['id', 'nombre', 'descripcion', 'idCategoria', 'recursos']):
            return jsonify({'error': 'Faltan campos requeridos'}), 400

        # Verificar que la categoría exista
        categoria = next((c for c in db['categorias'] if c.id == data['idCategoria']), None)
        if not categoria:
            return jsonify({'error': 'La categoría especificada no existe'}), 400

        # Crear configuración
        configuracion = Configuracion(
            data['id'], data['nombre'], data['descripcion'], data['idCategoria']
        )

        # Agregar recursos a la configuración
        for recurso_data in data['recursos']:
            if not any(r.id == recurso_data['idRecurso'] for r in db['recursos']):
                return jsonify({'error': f'Recurso {recurso_data["idRecurso"]} no existe'}), 400

            recurso_config = RecursoConfiguracion(
                recurso_data['idRecurso'], recurso_data['cantidad']
            )
            configuracion.agregar_recurso(recurso_config)

        # Agregar a BD y categoría
        db['configuraciones'].append(configuracion)
        categoria.agregar_configuracion(configuracion)
        guardar_db()

        return jsonify({
            'mensaje': 'Configuración creada exitosamente',
            'configuracion': configuracion.to_dict()
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/crearCliente', methods=['POST'])
def crear_cliente():
    """Crear un nuevo cliente """
    try:
        data = request.get_json()

        if not all(key in data for key in ['nit', 'nombre', 'usuario', 'clave', 'direccion', 'correoElectronico']):
            return jsonify({'error': 'Faltan campos requeridos'}), 400

        # Validar NIT
        if not validar_nit(data['nit']):
            return jsonify({'error': 'Formato de NIT inválido'}), 400

        if any(c.nit == data['nit'] for c in db['clientes']):
            return jsonify({'error': 'El NIT del cliente ya existe'}), 400

        nuevo_cliente = Cliente(
            data['nit'], data['nombre'], data['usuario'], data['clave'],
            data['direccion'], data['correoElectronico']
        )

        db['clientes'].append(nuevo_cliente)
        guardar_db()

        return jsonify({
            'mensaje': 'Cliente creado exitosamente',
            'cliente': nuevo_cliente.to_dict()
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/crearInstancia', methods=['POST'])
def crear_instancia():
    """Crear una nueva instancia """
    try:
        data = request.get_json()

        if not all(key in data for key in ['id', 'idConfiguracion', 'nombre', 'fechaInicio', 'nitCliente']):
            return jsonify({'error': 'Faltan campos requeridos'}), 400

        # Verificar configuración
        configuracion = next((c for c in db['configuraciones'] if c.id == data['idConfiguracion']), None)
        if not configuracion:
            return jsonify({'error': 'Configuración no existe'}), 400

        # Verificar cliente
        cliente = next((c for c in db['clientes'] if c.nit == data['nitCliente']), None)
        if not cliente:
            return jsonify({'error': 'Cliente no existe'}), 400

        # Extraer fecha
        fecha_inicio = extraer_fecha(data['fechaInicio'])
        if not fecha_inicio:
            return jsonify({'error': 'Fecha inválida'}), 400

        # Crear instancia
        instancia = Instancia(
            data['id'], data['idConfiguracion'], data['nombre'],
            fecha_inicio, data['nitCliente']
        )

        db['instancias'].append(instancia)
        cliente.agregar_instancia(instancia)
        guardar_db()

        return jsonify({
            'mensaje': 'Instancia creada exitosamente',
            'instancia': instancia.to_dict()
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/cancelarInstancia', methods=['POST'])
def cancelar_instancia():
    """Cancelar una instancia """
    try:
        data = request.get_json()

        if not all(key in data for key in ['idInstancia', 'fechaFinal']):
            return jsonify({'error': 'Faltan campos requeridos'}), 400

        # Buscar instancia
        instancia = next((i for i in db['instancias'] if i.id == data['idInstancia']), None)
        if not instancia:
            return jsonify({'error': 'Instancia no encontrada'}), 404

        # Extraer fecha final
        fecha_final = extraer_fecha(data['fechaFinal'])
        if not fecha_final:
            return jsonify({'error': 'Fecha final inválida'}), 400

        # Cancelar instancia
        instancia.cancelar(fecha_final)
        guardar_db()

        return jsonify({
            'mensaje': 'Instancia cancelada exitosamente',
            'instancia': instancia.to_dict()
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/generarFactura', methods=['POST'])
def generar_factura():
    """Generar factura para un rango de fechas """
    try:
        data = request.get_json()

        if not all(key in data for key in ['fechaInicio', 'fechaFin']):
            return jsonify({'error': 'Faltan campos requeridos'}), 400

        # Usar el servicio de facturación
        resultado = facturacion_service.generar_facturas(db, data['fechaInicio'], data['fechaFin'])

        if 'error' in resultado:
            return jsonify({'error': resultado['error']}), 400

        guardar_db()

        return jsonify({
            'mensaje': f"{resultado['facturas_generadas']} facturas generadas exitosamente",
            'facturas': resultado['detalle']
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/reporte/pdf/detalle-factura', methods=['POST'])
def generar_pdf_detalle_factura():
    """Generar PDF con detalle de factura"""
    try:
        data = request.get_json()

        if 'idFactura' not in data:
            return jsonify({'error': 'ID de factura requerido'}), 400

        # Buscar factura
        factura = next((f for f in db['facturas'] if f.id == data['idFactura']), None)
        if not factura:
            return jsonify({'error': 'Factura no encontrada'}), 404

        # Generar PDF
        pdf_path = reporte_service.generar_detalle_factura(factura, db)

        # Leer PDF y convertirlo a base64 para enviar
        with open(pdf_path, 'rb') as pdf_file:
            pdf_base64 = base64.b64encode(pdf_file.read()).decode('utf-8')

        return jsonify({
            'mensaje': 'PDF generado exitosamente',
            'pdf_base64': pdf_base64,
            'filename': os.path.basename(pdf_path)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/reporte/pdf/analisis-ventas', methods=['POST'])
def generar_pdf_analisis_ventas():
    """Generar PDF de análisis de ventas"""
    try:
        data = request.get_json()

        if not all(key in data for key in ['fechaInicio', 'fechaFin', 'tipo']):
            return jsonify({'error': 'Faltan campos requeridos'}), 400

        # Obtener datos del reporte (usando el servicio de facturación)
        reporte_data = facturacion_service.generar_reporte_analitico(
            db, data['fechaInicio'], data['fechaFin'], data['tipo']
        )

        # Generar PDF
        pdf_path = reporte_service.generar_analisis_ventas(
            reporte_data, data['tipo'], data['fechaInicio'], data['fechaFin']
        )

        # Leer y enviar PDF
        with open(pdf_path, 'rb') as pdf_file:
            pdf_base64 = base64.b64encode(pdf_file.read()).decode('utf-8')

        return jsonify({
            'mensaje': 'PDF de análisis generado exitosamente',
            'pdf_base64': pdf_base64,
            'filename': os.path.basename(pdf_path)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/reporte/analitico', methods=['POST'])
def generar_reporte_analitico():
    """Generar reporte analítico de ventas """
    try:
        data = request.get_json()

        if not all(key in data for key in ['fechaInicio', 'fechaFin', 'tipo']):
            return jsonify({'error': 'Faltan campos requeridos'}), 400

        resultado = facturacion_service.generar_reporte_analitico(
            db, data['fechaInicio'], data['fechaFin'], data['tipo']
        )

        return jsonify({
            'reporte': resultado
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/reset', methods=['POST'])
def reset_sistema():
    """Resetear todos los datos del sistema"""
    try:
        for key in db:
            db[key] = []
        guardar_db()
        return jsonify({'mensaje': 'Sistema reseteado exitosamente'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500



from models.recurso import Recurso
from models.categoria import Categoria
from models.configuracion import Configuracion, RecursoConfiguracion
from models.cliente import Cliente
from models.instancia import Instancia

if __name__ == '__main__':
    app.run(debug=True, port=5000)

import os