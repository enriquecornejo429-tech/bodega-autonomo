from flask import Flask, jsonify, render_template, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv

load_dotenv()

# Inicializar extensiones
db = SQLAlchemy()
jwt = JWTManager()

def create_app(config_name='development'):
    """Factory para crear la aplicación Flask"""
    app = Flask(__name__, 
                static_folder='../frontend',
                static_url_path='',
                template_folder='../frontend')
    
    # Configuración
    from backend.config import config
    app.config.from_object(config[config_name])
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-secret-key')
    
    # Inicializar extensiones
    db.init_app(app)
    jwt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Crear carpeta de uploads
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    # Importar modelos
    from backend.models.usuario import Usuario
    from backend.models.producto import Producto
    from backend.models.transaccion import Transaccion
    
    # Importar blueprints
    from backend.routes.auth import auth_bp
    from backend.routes.productos import productos_bp
    from backend.routes.transacciones import transacciones_bp
    from backend.routes.reportes import reportes_bp
    from backend.routes.excel import excel_bp
    
    # Registrar blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(productos_bp, url_prefix='/api/productos')
    app.register_blueprint(transacciones_bp, url_prefix='/api/transacciones')
    app.register_blueprint(reportes_bp, url_prefix='/api/reportes')
    app.register_blueprint(excel_bp, url_prefix='/api/excel')
    
    # Rutas públicas
    @app.route('/')
    def index():
        return send_from_directory('../frontend', 'index.html')
    
    @app.route('/api/health', methods=['GET'])
    def health():
        return jsonify({'status': 'ok', 'message': 'Sistema de Bodega Activo'}), 200
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint no encontrado', 'status': 404}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor', 'status': 500}), 500
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({'error': 'Acceso denegado', 'status': 403}), 403
    
    # Crear tablas
    with app.app_context():
        db.create_all()
        crear_usuario_admin()
    
    return app

def crear_usuario_admin():
    """Crear usuario administrador por defecto"""
    from backend.models.usuario import Usuario
    
    admin_existente = Usuario.query.filter_by(usuario='admin').first()
    if not admin_existente:
        admin = Usuario(
            nombre='Administrador',
            correo='admin@bodega.local',
            usuario='admin',
            rol='admin',
            activo=True
        )
        admin.set_contraseña('admin123')
        db.session.add(admin)
        db.session.commit()
        print('✅ Usuario administrador creado: admin / admin123')

if __name__ == '__main__':
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    app.run(debug=True, host='0.0.0.0', port=5000)