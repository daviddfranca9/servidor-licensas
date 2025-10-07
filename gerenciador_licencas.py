# gerenciador_licencas.py
import json
import os
import hashlib
import uuid

DATA_DIR = '/etc/secrets'
DB_FILE = os.path.join(DATA_DIR, 'licenses.json')

def carregar_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

def salvar_db(db):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=4)

def adicionar_chave():
    db = carregar_db()
    nova_chave = str(uuid.uuid4()).upper()
    db[nova_chave] = {"status": "active", "machine_id": None}
    salvar_db(db)
    print(f"\n[SUCESSO] Chave gerada e ativada: {nova_chave}\n")

def listar_chaves():
    db = carregar_db()
    print("\n--- LISTA DE LICENÇAS ---")
    for key, info in db.items():
        if key == "_master_config": continue
        status = info.get('status', 'N/A').upper()
        machine_id = info.get('machine_id') or "NÃO ATIVADA"
        print(f"Chave: {key} | Status: {status} | Máquina: {machine_id}")
    print("-------------------------\n")

def mudar_status(status_alvo):
    chave = input(f"Digite a chave que deseja {status_alvo}: ").strip().upper()
    db = carregar_db()
    if chave in db and chave != "_master_config":
        db[chave]['status'] = status_alvo
        salvar_db(db)
        print(f"\n[SUCESSO] A chave {chave} foi definida como '{status_alvo}'.\n")
    else:
        print("\n[ERRO] Chave não encontrada.\n")

def definir_senha_mestra():
    nova_senha = input("Digite a nova senha mestra de fallback: ").strip()
    if not nova_senha:
        print("\nA senha não pode ser vazia.\n")
        return
        
    hash_senha = hashlib.sha256(nova_senha.encode('utf-8')).hexdigest()
    
    db = carregar_db()
    db["_master_config"] = {"master_password_hash": hash_senha}
    salvar_db(db)
    print("\n[SUCESSO] Senha mestra atualizada no servidor.\n")

def main():
    while True:
        print("Gerenciador de Licenças:")
        print("1. Gerar nova chave de licença")
        print("2. Listar todas as licenças")
        print("3. Bloquear uma licença")
        print("4. Desbloquear uma licença")
        print("5. DEFINIR/ALTERAR SENHA MESTRA")
        print("6. Sair")
        
        escolha = input("Escolha uma opção: ")

        if escolha == '1': adicionar_chave()
        elif escolha == '2': listar_chaves()
        elif escolha == '3': mudar_status('blocked')
        elif escolha == '4': mudar_status('active')
        elif escolha == '5': definir_senha_mestra()
        elif escolha == '6': break
        else: print("\nOpção inválida. Tente novamente.\n")

if __name__ == '__main__':
    main()
