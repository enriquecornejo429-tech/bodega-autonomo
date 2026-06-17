from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.app import db
from backend.models.transaccion import Transaccion
from backend.models.producto import Producto
from datetime import datetime, timedelta

reportes_bp = Blueprint('reportes', __name__)

@reportes_bp.route('/resumen', methods=['GET'])
@jwt_required()
def resumen():
    """Obtener resumen general del sistema"""
    total_productos = Producto.query.filter_by(estado='activo').count()
    total_valor = db.session.query(db.func.sum(Producto.cantidad * Producto.precio_unitario)).filter(
        Producto.estado == 'activo'
    ).scalar() or 0
    
    productos_bajo_stock = Producto.query.filter(
        Producto.cantidad < Producto.cantidad_minima,
        Producto.estado == 'activo'
    ).count()
    
    transacciones_hoy = Transaccion.query.filter(
        Transaccion.fecha_transaccion >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    ).count()
    
    return jsonify({
        'total_productos': total_productos,
        'valor_inventario': float(total_valor),
        'productos_bajo_stock': productos_bajo_stock,
        'transacciones_hoy': transacciones_hoy
    }), 200

@reportes_bp.route('/transacciones', methods=['GET'])
@jwt_required()
def reporte_transacciones():
    """Reporte de transacciones por rango de fechas"""
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')
    tipo = request.args.get('tipo')
    
    query = Transaccion.query
    
    if fecha_inicio:
        fecha_inicio = datetime.fromisoformat(fecha_inicio)
        query = query.filter(Transaccion.fecha_transaccion >= fecha_inicio)
    
    if fecha_fin:
        fecha_fin = datetime.fromisoformat(fecha_fin)
        query = query.filter(Transaccion.fecha_transaccion <= fecha_fin)
    
    if tipo:
        query = query.filter_by(tipo=tipo)
    
    transacciones = query.order_by(Transaccion.fecha_transaccion.desc()).all()
    
    return jsonify([t.to_dict() for t in transacciones]), 200

@reportes_bp.route('/inventario', methods=['GET'])
@jwt_required()
def reporte_inventario():
    """Reporte completo de inventario"""
    productos = Producto.query.filter_by(estado='activo').all()
    
    data = []
    for p in productos:
        data.append({
            'codigo': p.codigo,
            'nombre': p.nombre,
            'categoria': p.categoria,
            'cantidad': p.cantidad,
            'cantidad_minima': p.cantidad_minima,
            'precio_unitario': p.precio_unitario,
            'valor_total': p.cantidad * p.precio_unitario,
            'bajo_stock': p.cantidad < p.cantidad_minima,
            'proveedor': p.proveedor,
            'fecha_ingreso': p.fecha_ingreso.isoformat()
        })
    
    total_valor = sum([p['valor_total'] for p in data])
    
    return jsonify({
        'productos': data,
        'total_valor': total_valor,
        'cantidad_total': len(data)
    }), 200

@reportes_bp.route('/movimientos/<int:producto_id>', methods=['GET'])
@jwt_required()
def reporte_movimientos_producto(producto_id):
    """Reporte de movimientos de un producto específico"""
    producto = Producto.query.get(producto_id)
    
    if not producto:
        return jsonify({'error': 'Producto no encontrado'}), 404
    
    transacciones = Transaccion.query.filter_by(producto_id=producto_id).order_by(
        Transaccion.fecha_transaccion.desc()
    ).all()
    
    entradas = sum([t.cantidad for t in transacciones if t.tipo == 'entrada'])
    salidas = sum([t.cantidad for t in transacciones if t.tipo == 'salida'])
    
    return jsonify({
        'producto': producto.to_dict(),
        'total_entradas': entradas,
        'total_salidas': salidas,
        'saldo': entradas - salidas,
        'movimientos': [t.to_dict() for t in transacciones]
    }), 200

@reportes_bp.route('/bajo-stock', methods=['GET'])
@jwt_required()
def reporte_bajo_stock():
    """Reporte de productos con stock bajo"""
    productos = Producto.query.filter(
        Producto.cantidad < Producto.cantidad_minima,
        Producto.estado == 'activo'
    ).all()
    
    data = []
    for p in productos:
        data.append({
            'codigo': p.codigo,
            'nombre': p.nombre,
            'cantidad_actual': p.cantidad,
            'cantidad_minima': p.cantidad_minima,
            'faltante': p.cantidad_minima - p.cantidad,
            'proveedor': p.proveedor
        })
    
    return jsonify({
        'productos_bajo_stock': data,
        'cantidad_total': len(data)
    }), 200