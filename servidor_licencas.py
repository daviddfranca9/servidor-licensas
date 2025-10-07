# servidor_licencas.py (VERSÃO FINAL COM SUPABASE POSTGRESQL - 100% GRÁTIS)
import os
import uuid
import hashlib
from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
from sqlalchemy import create_engine, Column, String, Text
from sqlalchemy.orm import sessionmaker, declarative_base

# --- CONFIGURAÇÃO DO FLASK E BANCO DE DADOS ---
app = Flask(__name__)
# A Secret Key é para a segurança da sessão de login do admin
app.secret_key = os.environ.get('SECRET_KEY', 'fallback_secret_key_super_segura_123')

# Pega a URL de conexão do Supabase das variáveis de ambiente da Render
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("A variável de ambiente DATABASE_URL não foi definida!")

# O Supabase usa 'postgres://', mas o SQLAlchemy moderno prefere 'postgresql://'
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Pega a senha do painel de admin das variáveis de ambiente
SENHA_ADMIN = os.environ.get('ADMIN_PASSWORD', 'admin123')


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- MODELOS DAS TABELAS DO BANCO DE DADOS (Exatamente como antes) ---
class License(Base):
    __tablename__ = "licenses"
    key = Column(String, primary_key=True, index=True)
    status = Column(String, default="active")
    machine_id = Column(String, nullable=True)

class Config(Base):
    __tablename__ = "config"
    key = Column(String, primary_key=True)
    value = Column(Text)

# Cria as tabelas no banco de dados do Supabase se elas não existirem
Base.metadata.create_all(bind=engine)

# --- FUNÇÃO DE ACESSO AO BANCO DE DADOS ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- ROTAS PÚBLICAS (PARA A APLICAÇÃO TKINTER) - NENHUMA MUDANÇA AQUI ---

@app.route('/master_password', methods=['GET'])
def get_master_password():
    db = next(get_db())
    master_config = db.query(Config).filter(Config.key == "master_password_hash").first()
    if not master_config:
        return jsonify({"error": "Senha mestra não configurada."}), 404
    return jsonify({"master_password_hash": master_config.value})

@app.route('/activate', methods=['POST'])
def activate():
    data = request.json
    key, machine_id = data.get('license_key'), data.get('machine_id')
    if not key or not machine_id:
        return jsonify({"status": "error", "message": "Chave ou ID da máquina ausente."}), 400
    
    db = next(get_db())
    license_info = db.query(License).filter(License.key == key).first()

    if not license_info:
        return jsonify({"status": "error", "message": "Chave de licença não encontrada."}), 404
    if license_info.status == 'blocked':
        return jsonify({"status": "error", "message": "Esta licença foi bloqueada pelo administrador."}), 403
    if license_info.machine_id is not None and license_info.machine_id != machine_id:
        return jsonify({"status": "error", "message": "Esta licença já está em uso em outro computador."}), 409
    
    license_info.machine_id = machine_id
    db.commit()
    return jsonify({"status": "success", "message": "Licença ativada com sucesso."})

@app.route('/validate', methods=['POST'])
def validate():
    data = request.json
    key, machine_id = data.get('license_key'), data.get('machine_id')
    if not key or not machine_id:
        return jsonify({"status": "error", "message": "Dados de validação ausentes."}), 400
    
    db = next(get_db())
    license_info = db.query(License).filter(License.key == key).first()

    if not license_info:
        return jsonify({"status": "invalid", "message": "Chave não existe."}), 404
    if license_info.status != 'active':
        return jsonify({"status": "invalid", "message": "Licença não está ativa ou foi bloqueada."}), 403
    if license_info.machine_id != machine_id:
        return jsonify({"status": "invalid", "message": "ID da máquina não corresponde."}), 403
    return jsonify({"status": "valid", "message": "Licença válida."})

# --- ROTAS DE ADMINISTRAÇÃO (PAINEL WEB) - NENHUMA MUDANÇA AQUI ---
# O HTML e a lógica são os mesmos, pois eles usam as funções de banco de dados que adaptamos.

ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-br"><head><meta charset="UTF-8"><title>Painel de Administração</title><style>body{font-family:sans-serif;margin:2em;background-color:#f4f4f9;color:#333}.container{max-width:900px;margin:auto;background:white;padding:2em;border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,.1)}h1,h2{color:#5a5a5a}table{width:100%;border-collapse:collapse;margin-top:1em}th,td{padding:.75em;text-align:left;border-bottom:1px solid #ddd}th{background-color:#f2f2f2}.btn{padding:.5em 1em;color:white;border:none;border-radius:4px;cursor:pointer;text-decoration:none;display:inline-block}.btn-green{background-color:#28a745}.btn-red{background-color:#dc3545}.btn-blue{background-color:#007bff}.actions{margin-top:1.5em;display:flex;gap:1em}.form-group{margin-top:1em}input[type=text],input[type=password]{padding:.5em;width:300px}.message{padding:1em;margin-bottom:1em;border-radius:4px}.message-success{background-color:#d4edda;color:#155724}</style></head><body><div class="container"><h1>Painel de Administração</h1>{% if message %}<div class="message message-success">{{ message }}</div>{% endif %}<div class="actions"><form action="{{ url_for('admin_add_key') }}" method="post" style="margin:0;"><button type="submit" class="btn btn-green">Gerar Nova Chave</button></form></div><h2>Licenças Atuais</h2><table><tr><th>Chave</th><th>Status</th><th>ID da Máquina</th><th>Ação</th></tr>{% for license in licenses %}<tr><td>{{ license.key }}</td><td>{{ license.status | upper }}</td><td>{{ license.machine_id or 'NÃO ATIVADA' }}</td><td>{% if license.status == 'active' %}<a href="{{ url_for('admin_toggle_status', key=license.key) }}" class="btn btn-red">Bloquear</a>{% else %}<a href="{{ url_for('admin_toggle_status', key=license.key) }}" class="btn btn-blue">Desbloquear</a>{% endif %}</td></tr>{% endfor %}</table><h2>Senha Mestra (Fallback)</h2><form action="{{ url_for('admin_set_master') }}" method="post" class="form-group"><label for="master_pass">Definir/Alterar Senha de Fallback:</label><br><input type="password" name="master_pass" id="master_pass" required><button type="submit" class="btn btn-blue">Salvar Senha Mestra</button></form><p>Hash Atual: {{ master_hash or 'Não definida' }}</p></div></body></html>
"""
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html><head><title>Login Admin</title></head><body style="font-family: sans-serif; text-align: center; padding-top: 5em;"><h2>Acesso ao Painel de Administração</h2>{% if error %}<p style="color: red;">{{ error }}</p>{% endif %}<form method="post"><label for="password">Senha:</label><input type="password" name="password" id="password" required><button type="submit">Entrar</button></form></body></html>
"""
@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if request.method == 'POST':
        if request.form.get('password') == SENHA_ADMIN:
            session['logged_in'] = True
            return redirect(url_for('admin_panel'))
        else:
            return render_template_string(LOGIN_TEMPLATE, error="Senha incorreta.")
    if not session.get('logged_in'):
        return render_template_string(LOGIN_TEMPLATE)
    
    db = next(get_db())
    licenses = db.query(License).all()
    master_config = db.query(Config).filter(Config.key == "master_password_hash").first()
    message = session.pop('message', None)
    return render_template_string(ADMIN_TEMPLATE, licenses=licenses, master_hash=master_config.value if master_config else None, message=message)

@app.route('/admin/add', methods=['POST'])
def admin_add_key():
    if not session.get('logged_in'): return redirect(url_for('admin_panel'))
    
    db = next(get_db())
    nova_chave = str(uuid.uuid4()).upper()
    new_license = License(key=nova_chave, status="active")
    db.add(new_license)
    db.commit()
    
    session['message'] = f"Chave gerada com sucesso: {nova_chave}"
    return redirect(url_for('admin_panel'))

@app.route('/admin/toggle/<key>')
def admin_toggle_status(key):
    if not session.get('logged_in'): return redirect(url_for('admin_panel'))
    
    db = next(get_db())
    license_to_toggle = db.query(License).filter(License.key == key).first()
    if license_to_toggle:
        license_to_toggle.status = 'blocked' if license_to_toggle.status == 'active' else 'active'
        db.commit()
        session['message'] = f"Status da chave {key} alterado."
    return redirect(url_for('admin_panel'))

@app.route('/admin/set_master', methods=['POST'])
def admin_set_master():
    if not session.get('logged_in'): return redirect(url_for('admin_panel'))
    
    nova_senha = request.form.get('master_pass')
    if nova_senha:
        hash_senha = hashlib.sha256(nova_senha.encode('utf-8')).hexdigest()
        
        db = next(get_db())
        master_config = db.query(Config).filter(Config.key == "master_password_hash").first()
        if master_config:
            master_config.value = hash_senha
        else:
            new_master_config = Config(key="master_password_hash", value=hash_senha)
            db.add(new_master_config)
        db.commit()
        session['message'] = "Senha mestra atualizada com sucesso."
    return redirect(url_for('admin_panel'))
