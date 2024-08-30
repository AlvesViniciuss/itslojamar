from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '12345'  # Substitua por uma chave secreta segura

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Modelos
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
    modelo = db.Column(db.String(80), nullable=False)
    tamanho = db.Column(db.String(20), nullable=False)
    cor = db.Column(db.String(20), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    valor_unitario = db.Column(db.Float, nullable=False)
    preco_medio = db.Column(db.Float, nullable=False)
    valor_total = db.Column(db.Float, nullable=False)
    data = db.Column(db.DateTime, nullable=False)

# Filtro personalizado para formatação de moeda
def format_currency(value):
    try:
        return "R$ {:.2f}".format(value)
    except (TypeError, ValueError):
        return "R$ 0.00"

app.jinja_env.filters['currency'] = format_currency

# Decorador para proteger as rotas
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Rotas
@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/compra', methods=['GET', 'POST'])
@login_required
def compra():
    if request.method == 'POST':
        modelo = request.form['modelo'].upper()
        tamanho = request.form['tamanho'].upper()
        cor = request.form['cor'].upper()
        quantidade = int(request.form['quantidade'])
        valor = float(request.form['valor'])
        data = datetime.strptime(request.form['data'], '%Y-%m-%d').date()

        total = quantidade * valor

        nova_compra = Compra(
            modelo=modelo,
            tamanho=tamanho,
            cor=cor,
            quantidade=quantidade,
            valor=valor,
            total=total,
            data=data
        )

        db.session.add(nova_compra)
        db.session.commit()

        # Atualizar estoque com base na compra
        estoque_item = Estoque.query.filter_by(nome=modelo, tamanho=tamanho, cor=cor).first()
        if estoque_item:
            estoque_item.quantidade += quantidade
            estoque_item.valor_unitario = (estoque_item.valor_unitario * estoque_item.quantidade + valor * quantidade) / (estoque_item.quantidade + quantidade)
        else:
            novo_estoque = Estoque(
                nome=modelo,
                tamanho=tamanho,
                cor=cor,
                quantidade=quantidade,
                valor_unitario=valor
            )
            db.session.add(novo_estoque)
        db.session.commit()

        return redirect(url_for('compra'))

    compras = Compra.query.all()

    # Calculando o preço médio
    modelos = db.session.query(
        Compra.modelo,
        db.func.avg(Compra.valor).label('preco_medio')
    ).group_by(Compra.modelo).all()

    return render_template('compra.html', compras=compras, modelos=modelos)

@app.route('/compra/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_compra(id):
    compra = Compra.query.get_or_404(id)
    if request.method == 'POST':
        compra.modelo = request.form['modelo']
        compra.tamanho = request.form['tamanho']
        compra.cor = request.form['cor']
        compra.quantidade = int(request.form['quantidade'])
        compra.valor = float(request.form['valor'])
        compra.total = compra.quantidade * compra.valor
        compra.data = datetime.strptime(request.form['data'], '%Y-%m-%d').date()

        db.session.commit()
        return redirect(url_for('compra'))

    return render_template('editar_compra.html', compra=compra)

@app.route('/compra/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_compra(id):
    compra = Compra.query.get_or_404(id)
    db.session.delete(compra)
    db.session.commit()
    return redirect(url_for('compra'))

@app.route('/estoque', methods=['GET', 'POST'])
@login_required
def estoque():
    if request.method == 'POST':
        item_id = request.form.get('item_id')
        quantidade = int(request.form.get('quantidade'))
        valor_unitario = float(request.form.get('valor_unitario'))

        estoque_item = Estoque.query.get(item_id)
        if estoque_item and estoque_item.quantidade >= quantidade:
            estoque_item.quantidade -= quantidade
            db.session.commit()

            # Registrar venda com o preco_medio do estoque
            nova_venda = Venda(
                modelo=estoque_item.nome,
                tamanho=estoque_item.tamanho,
                cor=estoque_item.cor,
                quantidade=quantidade,
                valor_unitario=valor_unitario,
                preco_medio=estoque_item.valor_unitario,
                valor_total=quantidade * valor_unitario,
                data=datetime.today()
            )
            db.session.add(nova_venda)
            db.session.commit()

        return redirect(url_for('estoque'))

    filtro_modelo = request.args.get('modelo')
    filtro_tamanho = request.args.get('tamanho')
    filtro_cor = request.args.get('cor')

    query = Estoque.query

    if filtro_modelo:
        query = query.filter(Estoque.nome.ilike(f"%{filtro_modelo}%"))
    if filtro_tamanho:
        query = query.filter(Estoque.tamanho.ilike(f"%{filtro_tamanho}%"))
    if filtro_cor:
        query = query.filter(Estoque.cor.ilike(f"%{filtro_cor}%"))

    itens_estoque = query.all()

    return render_template('estoque.html', itens=itens_estoque)

@app.route('/estoque/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_estoque(id):
    item = Estoque.query.get_or_404(id)
    if request.method == 'POST':
        item.nome = request.form['nome'].upper()
        item.tamanho = request.form['tamanho'].upper()
        item.cor = request.form['cor'].upper()
        item.quantidade = int(request.form['quantidade'])
        item.valor_unitario = float(request.form['valor_unitario'])

        db.session.commit()
        return redirect(url_for('estoque'))

    return render_template('editar_estoque.html', item=item)

@app.route('/estoque/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_estoque(id):
    item = Estoque.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('estoque'))

@app.route('/vendas', methods=['GET'])
@login_required
def vendas():
    vendas = Venda.query.all()
    return render_template('vendas.html', vendas=vendas)

@app.route('/estoque/item/<int:item_id>', methods=['GET'])
@login_required
def get_estoque_item(item_id):
    item = Estoque.query.get(item_id)
    if item:
        return jsonify({
            'nome': item.nome,
            'tamanho': item.tamanho,
            'cor': item.cor,
            'quantidade': item.quantidade,
            'valor_unitario': item.valor_unitario
        })
    return jsonify({'error': 'Item não encontrado'}), 404

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Validar credenciais (aqui é uma validação simples, substitua por sua lógica de autenticação)
        if username == 'admin' and password == 'admin':
            session['logged_in'] = True
            return redirect(url_for('index'))
        return 'Credenciais inválidas'
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=8080)
