from backend.app import db
from datetime import datetime

class Transaccion(db.Model):
    __tablename__ = 'transacciones'
    
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # entrada, salida
    cantidad = db.Column(db.Integer, nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    motivo = db.Column(db.String(255))
    referencia = db.Column(db.String(100))
    fecha_transaccion = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    observaciones = db.Column(db.Text)
    
    def to_dict(self):
        usuario = self.usuario_registrador
        
        return {
            'id': self.id,
            'producto_id': self.producto_id,
            'producto': self.producto.nombre if self.producto else None,
            'codigo': self.producto.codigo if self.producto else None,
            'tipo': self.tipo,
            'cantidad': self.cantidad,
            'usuario_id': self.usuario_id,
            'usuario': usuario.usuario if usuario else None,
            'motivo': self.motivo,
            'referencia': self.referencia,
            'fecha': self.fecha_transaccion.isoformat(),
            'observaciones': self.observaciones
        }
    
    def __repr__(self):
        return f'<Transaccion {self.id}>'