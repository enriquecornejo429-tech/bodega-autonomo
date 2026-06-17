from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.app import db
from backend.models.usuario import Usuario

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """Endpoint de login"""
    datos = request.get_json()
    
    if not datos or not datos.get('usuario') or not datos.get('contraseña'):
        return jsonify({'error': 'Usuario y contraseña requeridos'}), 400
    
    usuario = Usuario.query.filter_by(usuario=datos['usuario']).first()
    
    if usuario and usuario.verificar_contraseña(datos['contraseña']) and usuario.activo:
        token = usuario.generar_token()
        return jsonify({
            'token': token,
            'usuario': usuario.usuario,
            'nombre': usuario.nombre,
            'rol': usuario.rol,
            'id': usuario.id
        }), 200
    
    return jsonify({'error': 'Credenciales inválidas'}), 401

@auth_bp.route('/registro', methods=['POST'])
@jwt_required()
def registro():
    """Endpoint de registro (solo admin puede registrar usuarios)"""
    usuario_actual_id = get_jwt_identity()
    usuario_actual = Usuario.query.get(usuario_actual_id)
    
    if usuario_actual.rol != 'admin':
        return jsonify({'error': 'Solo administradores pueden registrar usuarios'}), 403
    
    datos = request.get_json()
    
    if not datos or not all(k in datos for k in ['usuario', 'correo', 'contraseña', 'nombre']):
        return jsonify({'error': 'Datos incompletos'}), 400
    
    if Usuario.query.filter_by(usuario=datos['usuario']).first():
        return jsonify({'error': 'Usuario ya existe'}), 409
    
    if Usuario.query.filter_by(correo=datos['correo']).first():
        return jsonify({'error': 'Correo ya existe'}), 409
    
    nuevo_usuario = Usuario(
        nombre=datos['nombre'],
        correo=datos['correo'],
        usuario=datos['usuario'],
        rol=datos.get('rol', 'operador')
    )
    nuevo_usuario.set_contraseña(datos['contraseña'])
    
    db.session.add(nuevo_usuario)
    db.session.commit()
    
    return jsonify({
        'message': 'Usuario registrado exitosamente',
        'usuario': nuevo_usuario.to_dict()
    }), 201

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    """Obtener datos del usuario actual"""
    usuario_id = get_jwt_identity()
    usuario = Usuario.query.get(usuario_id)
    
    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    
    return jsonify(usuario.to_dict()), 200

@auth_bp.route('/usuarios', methods=['GET'])
@jwt_required()
def obtener_usuarios():
    """Obtener lista de usuarios (solo admin)"""
    usuario_id = get_jwt_identity()
    usuario = Usuario.query.get(usuario_id)
    
    if usuario.rol != 'admin':
        return jsonify({'error': 'Acceso denegado'}), 403
    
    usuarios = Usuario.query.all()
    return jsonify([u.to_dict() for u in usuarios]), 200

@auth_bp.route('/usuarios/<int:id>', methods=['PUT'])
@jwt_required()
def actualizar_usuario(id):
    """Actualizar usuario"""
    usuario_id = get_jwt_identity()
    usuario_actual = Usuario.query.get(usuario_id)
    
    # Solo admin o el mismo usuario pueden actualizar
    if usuario_actual.rol != 'admin' and usuario_id != id:
        return jsonify({'error': 'Acceso denegado'}), 403
    
    usuario = Usuario.query.get(id)
    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    
    datos = request.get_json()
    
    if 'nombre' in datos:
        usuario.nombre = datos['nombre']
    if 'correo' in datos:
        usuario.correo = datos['correo']
    if 'rol' in datos and usuario_actual.rol == 'admin':
        usuario.rol = datos['rol']
    if 'activo' in datos and usuario_actual.rol == 'admin':
        usuario.activo = datos['activo']
    
    db.session.commit()
    return jsonify(usuario.to_dict()), 200

@auth_bp.route('/usuarios/<int:id>/contraseña', methods=['PUT'])
@jwt_required()
def cambiar_contraseña(id):
    """Cambiar contraseña"""
    usuario_id = get_jwt_identity()
    
    # Solo el mismo usuario o admin pueden cambiar contraseña
    if usuario_id != id:
        usuario_actual = Usuario.query.get(usuario_id)
        if usuario_actual.rol != 'admin':
            return jsonify({'error': 'Acceso denegado'}), 403
    
    usuario = Usuario.query.get(id)
    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    
    datos = request.get_json()
    
    if not datos.get('contraseña_nueva'):
        return jsonify({'error': 'Contraseña nueva requerida'}), 400
    
    usuario.set_contraseña(datos['contraseña_nueva'])
    db.session.commit()
    
    return jsonify({'message': 'Contraseña actualizada exitosamente'}), 200