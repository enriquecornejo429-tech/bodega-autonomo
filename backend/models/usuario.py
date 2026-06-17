from backend.app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from datetime import timedelta, datetime

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(120), unique=True, nullable=False)
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    contraseña = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), default='operador')  # admin, supervisor, operador
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    transacciones = db.relationship('Transaccion', backref='usuario_registrador', lazy=True)
    
    def set_contraseña(self, contraseña):
        """Hashear y guardar contraseña"""
        self.contraseña = generate_password_hash(contraseña)
    
    def verificar_contraseña(self, contraseña):
        """Verificar contraseña"""
        return check_password_hash(self.contraseña, contraseña)
    
    def generar_token(self):
        """Generar token JWT"""
        token = create_access_token(
            identity=self.id,
            additional_claims={'usuario': self.usuario, 'rol': self.rol},
            expires_delta=timedelta(hours=24)
        )
        return token
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'correo': self.correo,
            'usuario': self.usuario,
            'rol': self.rol,
            'activo': self.activo,
            'fecha_creacion': self.fecha_creacion.isoformat()
        }
    
    def __repr__(self):
        return f'<Usuario {self.usuario}>'