from flask import Flask, render_template, url_for, flash, redirect, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from datetime import datetime
from flask_babel import Babel, format_datetime # Importar Babel e format_datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui' # Mude para uma chave segura e complexa!
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuração do Flask-Babel
app.config['BABEL_DEFAULT_LOCALE'] = 'pt_BR'
app.config['BABEL_DEFAULT_TIMEZONE'] = 'America/Sao_Paulo' # Ajuste para seu fuso horário se for diferente
babel = Babel(app)

# ADICIONE ESTA LINHA ABAIXO PARA TORNAR format_datetime DISPONÍVEL NO JINJA2
app.jinja_env.globals.update(format_datetime=format_datetime)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Modelos do Banco de Dados
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    producoes = db.relationship('Producao', backref='autor', lazy=True)

    def __repr__(self):
        return f"User('{self.username}')"

class Producao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_registro = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    bairro = db.Column(db.String(100), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    residencia = db.Column(db.Integer, nullable=False, default=0)
    comercio = db.Column(db.Integer, nullable=False, default=0)
    terreno_baldio = db.Column(db.Integer, nullable=False, default=0)
    ponto_estrategico = db.Column(db.Integer, nullable=False, default=0)
    outros = db.Column(db.Integer, nullable=False, default=0)
    ciclo_ano = db.Column(db.String(20), nullable=False)
    numero = db.Column(db.String(20), nullable=False) # Considerando que pode ter letras/formatos específicos
    total = db.Column(db.Integer, nullable=False, default=0)
    eliminados = db.Column(db.Integer, nullable=False, default=0)
    recusas = db.Column(db.Integer, nullable=False, default=0)
    fechados = db.Column(db.Integer, nullable=False, default=0)
    recuperados = db.Column(db.Integer, nullable=False, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Producao('{self.bairro}', '{self.data_registro}')"

# Formulários WTForms
class RegistrationForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Senha', validators=[DataRequired()])
    confirm_password = PasswordField('Confirmar Senha',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrar')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Este nome de usuário já está em uso. Por favor, escolha outro.')

class LoginForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired()])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember_me = BooleanField('Lembrar-me')
    submit = SubmitField('Entrar')

class ProducaoForm(FlaskForm):
    bairro = StringField('Bairro', validators=[DataRequired()])
    nome = StringField('Nome do Agente', validators=[DataRequired()])
    residencia = IntegerField('Residência', default=0)
    comercio = IntegerField('Comércio', default=0)
    terreno_baldio = IntegerField('Terreno Baldio', default=0)
    ponto_estrategico = IntegerField('Ponto Estratégico', default=0)
    outros = IntegerField('Outros', default=0)
    ciclo_ano = StringField('Ciclo/Ano', validators=[DataRequired(), Length(max=20)])
    numero = StringField('Número (Ex: A01)', validators=[DataRequired(), Length(max=20)])
    eliminados = IntegerField('Eliminados', default=0)
    recusas = IntegerField('Recusas', default=0)
    fechados = IntegerField('Fechados', default=0)
    recuperados = IntegerField('Recuperados', default=0)
    submit = SubmitField('Salvar Produção')

# Formulário de Pesquisa (NOVO)
class SearchForm(FlaskForm):
    ciclo_ano = StringField('Ciclo/Ano')
    bairro = StringField('Bairro')
    submit = SubmitField('Pesquisar')

# Rotas
@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html', title='Home')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        from werkzeug.security import generate_password_hash
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        user = User(username=form.username.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Sua conta foi criada com sucesso! Agora você pode fazer login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Registrar', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        from werkzeug.security import check_password_hash
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            flash('Login bem-sucedido!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login sem sucesso. Verifique seu usuário e senha.', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('login'))

@app.route('/nova_producao', methods=['GET', 'POST'])
@login_required
def nova_producao():
    form = ProducaoForm()
    if form.validate_on_submit():
        total_calculado = (form.residencia.data + form.comercio.data + form.terreno_baldio.data +
                           form.ponto_estrategico.data + form.outros.data)
        
        producao = Producao(
            bairro=form.bairro.data,
            nome=form.nome.data,
            residencia=form.residencia.data,
            comercio=form.comercio.data,
            terreno_baldio=form.terreno_baldio.data,
            ponto_estrategico=form.ponto_estrategico.data,
            outros=form.outros.data,
            ciclo_ano=form.ciclo_ano.data,
            numero=form.numero.data,
            total=total_calculado, # O total é calculado aqui!
            eliminados=form.eliminados.data,
            recusas=form.recusas.data,
            fechados=form.fechados.data,
            recuperados=form.recuperados.data,
            autor=current_user
        )
        db.session.add(producao)
        db.session.commit()
        flash('Produção registrada com sucesso!', 'success')
        return redirect(url_for('meus_dados_producao')) # Redirecionar para a página de dados
    return render_template('nova_producao.html', title='Nova Produção', form=form)


@app.route('/meus_dados_producao')
@login_required
def meus_dados_producao():
    # Obtém apenas as produções do usuário logado, ordenadas por data
    producoes = Producao.query.filter_by(user_id=current_user.id).order_by(Producao.data_registro.desc()).all()
    return render_template('meus_dados_producao.html', title='Meus Dados de Produção', producoes=producoes)

# Rota para pesquisa de produção (AGORA COM FUNCIONALIDADE DE FILTRO)
@app.route('/pesquisar_producao', methods=['GET']) # Definindo métodos GET para a pesquisa via URL
@login_required
def pesquisar_producao():
    form = SearchForm()
    producoes_filtradas = []
    
    # Inicia a query com todos os dados do usuário atual
    query = Producao.query.filter_by(user_id=current_user.id)

    # Aplica os filtros se os campos foram preenchidos
    if form.validate_on_submit() or (request.args.get('ciclo_ano') or request.args.get('bairro')):
        ciclo_ano_pesquisa = form.ciclo_ano.data if form.validate_on_submit() else request.args.get('ciclo_ano')
        bairro_pesquisa = form.bairro.data if form.validate_on_submit() else request.args.get('bairro')
        
        if ciclo_ano_pesquisa:
    # Use ilike para pesquisa case-insensitive e parcial
            query = query.filter(Producao.ciclo_ano.ilike(f'%{ciclo_ano_pesquisa}%'))
        if bairro_pesquisa:
            # Use ilike para pesquisa case-insensitive e parcial
            query = query.filter(Producao.bairro.ilike(f'%{bairro_pesquisa}%'))
        
        producoes_filtradas = query.order_by(Producao.data_registro.desc()).all()
        if not producoes_filtradas:
            flash('Nenhum registro encontrado com os filtros aplicados.', 'info')
    
    # Se a página é acessada sem filtros, mostra todos os dados do usuário (opcional, ou pode mostrar vazio)
    # Por padrão, vamos mostrar todos os dados do usuário logado se nenhum filtro for aplicado inicialmente.
    if not producoes_filtradas and not (request.args.get('ciclo_ano') or request.args.get('bairro')):
        producoes_filtradas = Producao.query.filter_by(user_id=current_user.id).order_by(Producao.data_registro.desc()).all()


    return render_template('pesquisar_producao.html', 
                           title='Pesquisar Produção', 
                           form=form, 
                           producoes=producoes_filtradas,
                           ciclo_ano_previo=request.args.get('ciclo_ano', ''), # Para manter o valor no campo
                           bairro_previo=request.args.get('bairro', '')) # Para manter o valor no campo


@app.route('/excluir_producao/<int:producao_id>', methods=['POST'])
@login_required
def excluir_producao(producao_id):
    producao = Producao.query.get_or_404(producao_id)
    if producao.user_id != current_user.id:
        flash('Você não tem permissão para excluir este registro.', 'danger')
        return redirect(url_for('meus_dados_producao'))
    
    db.session.delete(producao)
    db.session.commit()
    flash('Registro de produção excluído com sucesso!', 'success')
    return redirect(url_for('meus_dados_producao'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)