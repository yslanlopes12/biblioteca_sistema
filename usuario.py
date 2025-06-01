import bcrypt
from db import selecionar_todos, inserir_dado, supabase
from datetime import datetime

# --- Funções de Segurança ---

def gerar_hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verificar_senha(senha: str, hash_senha: str) -> bool:
    return bcrypt.checkpw(senha.encode('utf-8'), hash_senha.encode('utf-8'))

# --- Simulação do usuário logado ---
def obter_usuario_logado():
    return {
        "id": 1,
        "nome": "Admin Teste",
        "perfil": "admin"
    }

# --- Consultas ---

def consultar_usuario_por_cpf(cpf: str):
    try:
        resposta = supabase.table("usuarios").select("*").eq("cpf", cpf).execute()
        return resposta.data[0] if resposta.data else None
    except Exception as e:
        print(f"Erro ao consultar usuário por CPF: {e}")
        return None

def consultar_usuario_por_id(user_id: int):
    try:
        resposta = supabase.table("usuarios").select("*").eq("id", user_id).execute()
        return resposta.data[0] if resposta.data else None
    except Exception as e:
        print(f"Erro ao buscar usuário por ID: {e}")
        return None

def consultar_usuario_por_nome(nome: str):
    try:
        resposta = supabase.table("usuarios").select("*").ilike("nome_completo", f"%{nome}%").execute()
        return resposta.data if resposta.data else []
    except Exception as e:
        print(f"Erro ao consultar usuário por nome: {e}")
        return []

def consultar_usuario_por_matricula(matricula: str):
    try:
        resposta = supabase.table("usuarios").select("*").eq("matricula", matricula).execute()
        return resposta.data[0] if resposta.data else None
    except Exception as e:
        print(f"Erro ao consultar usuário por matrícula: {e}")
        return None

# --- Cadastro ---

def cadastrar_usuario(
    nome_completo, data_nascimento, cpf, telefone, endereco, categoria,
    email=None, matricula=None, departamento_curso=None, senha=None
):
    if not senha:
        print("❌ Senha obrigatória.")
        return False

    if consultar_usuario_por_cpf(cpf):
        print("❌ CPF já cadastrado.")
        return False

    if not (cpf.isdigit() and len(cpf) == 11):
        print("❌ CPF inválido. Deve conter 11 dígitos numéricos.")
        return False

    if email and ("@" not in email or "." not in email):
        print("❌ Email inválido.")
        return False

    senha_hash = gerar_hash_senha(senha)

    dados = {
        "nome_completo": nome_completo,
        "data_nascimento": data_nascimento,
        "cpf": cpf,
        "telefone": telefone,
        "endereco": endereco,
        "categoria": categoria.lower(),
        "email": email,
        "matricula": matricula,
        "departamento_curso": departamento_curso,
        "senha_hash": senha_hash,
        "status": "ativo"
    }

    sucesso = inserir_dado("usuarios", dados)
    if sucesso:
        print("✅ Usuário cadastrado com sucesso.")
    else:
        print("❌ Erro ao cadastrar usuário.")
    return sucesso

# --- Login ---

def login_usuario(cpf, senha):
    try:
        resposta = supabase.table("usuarios").select("*").eq("cpf", cpf).eq("status", "ativo").execute()
        if resposta.data:
            usuario = resposta.data[0]
            if 'senha_hash' in usuario and verificar_senha(senha, usuario['senha_hash']):
                return usuario
        print("❌ CPF ou senha incorretos.")
        return None
    except Exception as e:
        print(f"Erro ao fazer login: {e}")
        return None

# --- Atualização ---

def atualizar_usuario(
        usuario_id: object, nome_completo: object, data_nascimento: object, telefone: object, endereco: object,
        categoria: object, email: object, matricula: object, departamento_curso: object,
        senha_hash: object = None, alterado_por: object = None
) -> bool:
    try:
        usuario_atual = consultar_usuario_por_id(usuario_id)
        if not usuario_atual:
            print("❌ Usuário não encontrado.")
            return False

        if not alterado_por:
            usuario_logado = obter_usuario_logado()
            alterado_por = usuario_logado["id"]

        novos_dados = {
            "nome_completo": nome_completo,
            "data_nascimento": data_nascimento,
            "telefone": telefone,
            "endereco": endereco,
            "categoria": categoria.lower(),
            "email": email,
            "matricula": matricula,
            "departamento_curso": departamento_curso,
        }

        if senha_hash:
            novos_dados["senha_hash"] = senha_hash

        alteracoes_historico = []

        for campo, novo_valor in novos_dados.items():
            valor_anterior = usuario_atual.get(campo)
            if str(novo_valor) != str(valor_anterior):
                alteracoes_historico.append({
                    "usuario_id": usuario_id,
                    "alterado_por": alterado_por,
                    "campo_alterado": campo,
                    "valor_anterior": str(valor_anterior) if valor_anterior is not None else None,
                    "valor_novo": str(novo_valor) if novo_valor is not None else None,
                    "data_alteracao": datetime.now().isoformat()
                })

        if not alteracoes_historico and not senha_hash:
            print("⚠️ Nenhuma alteração detectada.")
            return False

        supabase.table("usuarios").update(novos_dados).eq("id", usuario_id).execute()

        if alteracoes_historico:
            supabase.table("historico_alteracoes_usuario").insert(alteracoes_historico).execute()

        print("✅ Usuário atualizado com sucesso.")
        return True

    except Exception as e:
        print(f"❌ Erro ao atualizar usuário: {e}")
        return False

# --- Exibir dados do usuário ---

def print_usuario(usuario):
    print("\n--- Dados do Usuário ---")
    for chave, valor in usuario.items():
        print(f"{chave}: {valor}")
    print("-----------------------")

# --- Inativar usuário ---

def inativar_usuario():
    print("\n=== Inativar Cadastro de Usuário ===")

    cpf = input("Digite o CPF do usuário: ").strip()
    usuario = consultar_usuario_por_cpf(cpf)

    if not usuario:
        print("❌ Usuário não encontrado.")
        return

    print_usuario(usuario)

    if usuario.get('status') == 'inativo':
        print("⚠️ O usuário já está inativo.")
        return

    usuario_logado = obter_usuario_logado()
    if not usuario_logado or usuario_logado.get('perfil') != 'admin':
        print("❌ Você não tem permissão para inativar usuários.")
        return

    emprestimos = supabase.table("emprestimos") \
        .select("*") \
        .eq("usuario_id", usuario["id"]) \
        .eq("status", "ativo") \
        .execute().data

    if emprestimos:
        print("❌ O usuário possui empréstimos ativos. Regularize antes de inativar.")
        return

    confirmar = input("Tem certeza que deseja inativar este usuário? (s/n): ").strip().lower()
    if confirmar != 's':
        print("❌ Operação cancelada.")
        return

    motivo = input("Digite o motivo da inativação: ").strip()
    if not motivo:
        print("❌ Motivo é obrigatório.")
        return

    try:
        supabase.table("usuarios").update({"status": "inativo"}).eq("id", usuario["id"]).execute()

        supabase.table("inativacoes").insert({
            "usuario_id": usuario["id"],
            "realizado_por": usuario_logado["id"],
            "motivo": motivo,
            "data_inativacao": datetime.now().isoformat()
        }).execute()

        print("✅ Usuário inativado com sucesso.")
    except Exception as e:
        print(f"❌ Erro ao inativar usuário: {e}")

# --- Ativar usuário ---

def ativar_usuario(usuario_id):
    try:
        resposta = supabase.table("usuarios").update({"status": "ativo"}).eq("id", usuario_id).execute()
        if resposta.data:
            print("✅ Usuário ativado com sucesso.")
            return True
        else:
            print("❌ Usuário não encontrado ou erro ao ativar.")
            return False
    except Exception as e:
        print(f"Erro ao ativar usuário: {e}")
        return False
