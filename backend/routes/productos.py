from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.app import db
from backend.models.producto import Producto
from werkzeug.utils import secure_filename
import os
from datetime import datetime

productos_bp = Blueprint('productos', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@productos_bp.route('', methods=['GET'])
@jwt_required()
def obtener_productos():
    """Obtener todos los productos activos"""
    estado = request.args.get('estado', 'activo')
    categoria = request.args.get('categoria')
    
    query = Producto.query
    
    if estado:
        query = query.filter_by(estado=estado)
    
    if categoria:
        query = query.filter_by(categoria=categoria)
    
    productos = query.all()
    return jsonify([p.to_dict() for p in productos]), 200

@productos_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def obtener_producto(id):
    """Obtener un producto específico"""
    producto = Producto.query.get(id)
    
    if not producto:
        return jsonify({'error': 'Producto no encontrado'}), 404
    
    return jsonify(producto.to_dict()), 200

@productos_bp.route('', methods=['POST'])
@jwt_required()
def crear_producto():
    """Crear un nuevo producto"""
    datos = request.get_json()
    
    if not datos or not all(k in datos for k in ['codigo', 'nombre', 'precio_unitario']):
        return jsonify({'error': 'Datos incompletos'}), 400
    
    if Producto.query.filter_by(codigo=datos['codigo']).first():
        return jsonify({'error': 'Código de producto ya existe'}), 409
    
    nuevo_producto = Producto(
        codigo=datos['codigo'],
        nombre=datos['nombre'],
        descripcion=datos.get('descripcion'),
        cantidad=datos.get('cantidad', 0),
        cantidad_minima=datos.get('cantidad_minima', 5),
        precio_unitario=float(datos['precio_unitario']),
        categoria=datos.get('categoria'),
        proveedor=datos.get('proveedor')
    )
    
    db.session.add(nuevo_producto)
    db.session.commit()
    
    return jsonify(nuevo_producto.to_dict()), 201

@productos_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def actualizar_producto(id):
    """Actualizar un producto"""
    producto = Producto.query.get(id)
    
    if not producto:
        return jsonify({'error': 'Producto no encontrado'}), 404
    
    datos = request.get_json()
    
    campos_permitidos = ['nombre', 'descripcion', 'cantidad', 'cantidad_minima', 
                        'precio_unitario', 'categoria', 'proveedor', 'estado']
    
    for campo in campos_permitidos:
        if campo in datos:
            if campo == 'precio_unitario':
                setattr(producto, campo, float(datos[campo]))
            elif campo in ['cantidad', 'cantidad_minima']:
                setattr(producto, campo, int(datos[campo]))
            else:
                setattr(producto, campo, datos[campo])
    
    producto.ultima_actualizacion = datetime.utcnow()
    db.session.commit()
    
    return jsonify(producto.to_dict()), 200

@productos_bp.route('/<int:id>/imagen', methods=['POST'])
@jwt_required()
def subir_imagen_producto(id):
    """Subir imagen para un producto"""
    producto = Producto.query.get(id)
    
    if not producto:
        return jsonify({'error': 'Producto no encontrado'}), 404
    
    if 'archivo' not in request.files:
        return jsonify({'error': 'No se proporcionó archivo'}), 400
    
    archivo = request.files['archivo']
    
    if archivo.filename == '':
        return jsonify({'error': 'No se seleccionó archivo'}), 400
    
    if not allowed_file(archivo.filename):
        return jsonify({'error': 'Tipo de archivo no permitido'}), 400
    
    from backend.app import app
    filename = secure_filename(f"{producto.codigo}_{datetime.utcnow().timestamp()}.{archivo.filename.rsplit('.', 1)[1].lower()}")
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    archivo.save(filepath)
    producto.imagen = f"/uploads/{filename}"
    db.session.commit()
    
    return jsonify({
        'message': 'Imagen subida exitosamente',
        'producto': producto.to_dict()
    }), 200

@productos_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def eliminar_producto(id):
    """Eliminar un producto (marcar como inactivo)"""
    producto = Producto.query.get(id)
    
    if not producto:
        return jsonify({'error': 'Producto no encontrado'}), 404
    
    producto.estado = 'inactivo'
    db.session.commit()
    
    return jsonify({'message': 'Producto eliminado exitosamente'}), 200

@productos_bp.route('/bajo-stock', methods=['GET'])
@jwt_required()
def productos_bajo_stock():
    """Obtener productos con stock bajo"""
    productos = Producto.query.filter(
        Producto.cantidad < Producto.cantidad_minima,
        Producto.estado == 'activo'
    ).all()
    
    return jsonify([p.to_dict() for p in productos]), 200

@productos_bp.route('/categorias', methods=['GET'])
@jwt_required()
def obtener_categorias():
    """Obtener lista de categorías únicas"""
    categorias = db.session.query(Producto.categoria).distinct().filter(
        Producto.estado == 'activo'
    ).all()
    
    return jsonify([c[0] for c in categorias if c[0]]), 200