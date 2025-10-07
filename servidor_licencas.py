# servidor_licencas.py (VERSÃO PARA RENDER)
from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

# O Render vai "montar" nosso disco persistente neste caminho.
# Todas as leituras e escritas devem apontar para este diretório.
DATA_DIR = '/etc/secrets'
DB_FILE = os.path.join(DATA_DIR, 'licenses.json')

def carregar_db():
    # Garante que o diretório de dados exista
    os.makedirs(DATA_DIR, exist_ok=True)
    
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def salvar_db(db):
    # Garante que o diretório de dados exista antes de salvar
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=4)

@app.route('/master_password', methods=['GET'])
def get_master_password():
    db = carregar_db()
    master_config = db.get("_master_config", {})
    master_hash = master_config.get("master_password_hash")
    
    if not master_hash:
        return jsonify({"error": "Senha mestra não configurada."}), 404
        
    return jsonify({"master_password_hash": master_hash})
    
@app.route('/activate', methods=['POST'])
def activate():
    data = request.json
    key = data.get('license_key')
    machine_id = data.get('machine_id')
    
    if not key or not machine_id:
        return jsonify({"status": "error", "message": "Chave ou ID da máquina ausente."}), 400

    db = carregar_db()
    
    if key not in db or key == "_master_config":
        return jsonify({"status": "error", "message": "Chave de licença não encontrada."}), 404

    license_info = db[key]

    if license_info['status'] == 'blocked':
        return jsonify({"status": "error", "message": "Esta licença foi bloqueada pelo administrador."}), 403

    if license_info['machine_id'] is not None and license_info['machine_id'] != machine_id:
        return jsonify({"status": "error", "message": "Esta licença já está em uso em outro computador."}), 409
    
    license_info['machine_id'] = machine_id
    salvar_db(db)
    
    return jsonify({"status": "success", "message": "Licença ativada com sucesso."})

@app.route('/validate', methods=['POST'])
def validate():
    data = request.json
    key = data.get('license_key')
    machine_id = data.get('machine_id')

    if not key or not machine_id:
        return jsonify({"status": "error", "message": "Dados de validação ausentes."}), 400

    db = carregar_db()

    if key not in db or key == "_master_config":
        return jsonify({"status": "invalid", "message": "Chave não existe."}), 404

    license_info = db[key]

    # ATENÇÃO: A lógica original não validava o status 'active'. Adicionei essa verificação.
    if license_info['status'] != 'active':
        return jsonify({"status": "invalid", "message": "Licença não está ativa ou foi bloqueada."}), 403

    if license_info['machine_id'] != machine_id:
        return jsonify({"status": "invalid", "message": "ID da máquina não corresponde."}), 403

    return jsonify({"status": "valid", "message": "Licença válida."})

# A linha __main__ é removida, pois a Render usará um servidor WSGI (Gunicorn) para iniciar o app.
# if __name__ == '__main__':
#     app.run(...)
