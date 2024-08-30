from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Compra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    modelo = db.Column(db.String(100), nullable=False)
    tamanho = db.Column(db.String(10), nullable=False)
    cor = db.Column(db.String(50), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    valor = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)
    data = db.Column(db.Date, nullable=False)

class Estoque(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    tamanho = db.Column(db.String(10), nullable=False)
    cor = db.Column(db.String(50), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    valor_unitario = db.Column(db.Float, nullable=False)

class Venda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    modelo = db.Column(db.String(50))
    tamanho = db.Column(db.String(10))
    cor = db.Column(db.String(20))
    quantidade = db.Column(db.Integer)
    valor_unitario = db.Column(db.Float)
    preco_medio = db.Column(db.Float)  # Ensure this line exists
    valor_total = db.Column(db.Float)
    data = db.Column(db.DateTime)

