from backend.app import db
from datetime import datetime

class Producto(db.Model):
    __tablename__ = 'productos'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False, index=True)
    nombre = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)
    cantidad = db.Column(db.Integer, default=0)
    cantidad_minima = db.Column(db.Integer, default=5)
    precio_unitario = db.Column(db.Float, nullable=False)
    imagen = db.Column(db.String(255))  # Ruta de la imagen
    categoria = db.Column(db.String(100))
    proveedor = db.Column(db.String(150))
    fecha_ingreso = db.Column(db.DateTime, default=datetime.utcnow)
    ultima_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    estado = db.Column(db.String(20), default='activo')
    
    transacciones = db.relationship('Transaccion', backref='producto', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'codigo': self.codigo,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'cantidad': self.cantidad,
            'cantidad_minima': self.cantidad_minima,
            'precio_unitario': self.precio_unitario,
            'imagen': self.imagen,
            'categoria': self.categoria,
            'proveedor': self.proveedor,
            'fecha_ingreso': self.fecha_ingreso.isoformat(),
            'ultima_actualizacion': self.ultima_actualizacion.isoformat(),
            'estado': self.estado,
            'valor_total': self.cantidad * self.precio_unitario,
            'alerta_stock': self.cantidad < self.cantidad_minima
        }
    
    def __repr__(self):
        return f'<Producto {self.codigo}>'