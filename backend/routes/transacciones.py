from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.app import db
from backend.models.transaccion import Transaccion
from backend.models.producto import Producto
from datetime import datetime

transacciones_bp = Blueprint('transacciones', __name__)

@transacciones_bp.route('', methods=['GET'])
@jwt_required()
def obtener_transacciones():
    """Obtener todas las transacciones"""
    tipo = request.args.get('tipo')
    producto_id = request.args.get('producto_id')
    pagina = request.args.get('pagina', 1, type=int)
    por_pagina = request.args.get('por_pagina', 50, type=int)
    
    query = Transaccion.query
    
    if tipo:
        query = query.filter_by(tipo=tipo)
    
    if producto_id:
        query = query.filter_by(producto_id=producto_id)
    
    transacciones = query.order_by(Transaccion.fecha_transaccion.desc()).paginate(
        page=pagina, per_page=por_pagina
    )
    
    return jsonify({
        'transacciones': [t.to_dict() for t in transacciones.items],
        'total': transacciones.total,
        'paginas': transacciones.pages,
        'pagina_actual': pagina
    }), 200

@transacciones_bp.route('/entrada', methods=['POST'])
@jwt_required()
def registrar_entrada():
    """Registrar entrada de stock"""
    usuario_id = get_jwt_identity()
    datos = request.get_json()
    
    if not datos or not all(k in datos for k in ['producto_id', 'cantidad']):
        return jsonify({'error': 'Datos incompletos'}), 400
    
    producto = Producto.query.get(datos['producto_id'])
    if not producto:
        return jsonify({'error': 'Producto no encontrado'}), 404
    
    cantidad = int(datos['cantidad'])
    if cantidad <= 0:
        return jsonify({'error': 'La cantidad debe ser mayor a 0'}), 400
    
    # Actualizar cantidad
    producto.cantidad += cantidad
    producto.ultima_actualizacion = datetime.utcnow()
    
    # Registrar transacción
    transaccion = Transaccion(
        producto_id=datos['producto_id'],
        tipo='entrada',
        cantidad=cantidad,
        usuario_id=usuario_id,
        motivo=datos.get('motivo', 'Entrada de stock'),
        referencia=datos.get('referencia'),
        observaciones=datos.get('observaciones')
    )
    
    db.session.add(transaccion)
    db.session.commit()
    
    return jsonify({
        'message': 'Entrada registrada exitosamente',
        'transaccion': transaccion.to_dict(),
        'producto': producto.to_dict()
    }), 201

@transacciones_bp.route('/salida', methods=['POST'])
@jwt_required()
def registrar_salida():
    """Registrar salida de stock"""
    usuario_id = get_jwt_identity()
    datos = request.get_json()
    
    if not datos or not all(k in datos for k in ['producto_id', 'cantidad']):
        return jsonify({'error': 'Datos incompletos'}), 400
    
    producto = Producto.query.get(datos['producto_id'])
    if not producto:
        return jsonify({'error': 'Producto no encontrado'}), 404
    
    cantidad = int(datos['cantidad'])
    if cantidad <= 0:
        return jsonify({'error': 'La cantidad debe ser mayor a 0'}), 400
    
    if producto.cantidad < cantidad:
        return jsonify({
            'error': 'Stock insuficiente',
            'disponible': producto.cantidad,
            'solicitado': cantidad
        }), 400
    
    # Actualizar cantidad
    producto.cantidad -= cantidad
    producto.ultima_actualizacion = datetime.utcnow()
    
    # Registrar transacción
    transaccion = Transaccion(
        producto_id=datos['producto_id'],
        tipo='salida',
        cantidad=cantidad,
        usuario_id=usuario_id,
        motivo=datos.get('motivo', 'Salida de stock'),
        referencia=datos.get('referencia'),
        observaciones=datos.get('observaciones')
    )
    
    db.session.add(transaccion)
    db.session.commit()
    
    return jsonify({
        'message': 'Salida registrada exitosamente',
        'transaccion': transaccion.to_dict(),
        'producto': producto.to_dict()
    }), 201

@transacciones_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def obtener_transaccion(id):
    """Obtener una transacción específica"""
    transaccion = Transaccion.query.get(id)
    
    if not transaccion:
        return jsonify({'error': 'Transacción no encontrada'}), 404
    
    return jsonify(transaccion.to_dict()), 200

@transacciones_bp.route('/producto/<int:producto_id>', methods=['GET'])
@jwt_required()
def obtener_transacciones_producto(producto_id):
    """Obtener transacciones de un producto"""
    producto = Producto.query.get(producto_id)
    if not producto:
        return jsonify({'error': 'Producto no encontrado'}), 404
    
    transacciones = Transaccion.query.filter_by(producto_id=producto_id).order_by(
        Transaccion.fecha_transaccion.desc()
    ).all()
    
    return jsonify([t.to_dict() for t in transacciones]), 200