from db import selecionar_todos, inserir_dado, supabase
from datetime import datetime

def cadastrar_usuario(nome_completo, data_nascimento, cpf, telefone, endereco, categoria,
                      email=None, matricula=None, departamento_curso=None):
    """
    Cadastra um novo usuário na tabela 'usuarios' com status ativo.
    """
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
        "status": "ativo"
    }
    return inserir_dado("usuarios", dados)


def login_usuario(cpf):
    """
    Realiza login com base no CPF. Retorna o usuário se existir e estiver ativo.
    """
    try:
        resposta = supabase.table("usuarios").select("*").eq("cpf", cpf).eq("status", "ativo").execute()
        return resposta.data[0] if resposta.data else None
    except Exception as e:
        print("Erro ao fazer login:", e)
        return None


def consultar_usuario_por_cpf(cpf):
    """
    Retorna o usuário com o CPF especificado.
    """
    try:
        resposta = supabase.table("usuarios").select("*").eq("cpf", cpf).execute()
        return resposta.data[0] if resposta.data else None
    except Exception as e:
        print("Erro ao consultar usuário por CPF:", e)
        return None


def consultar_usuario_por_nome(nome):
    """
    Retorna lista de usuários cujo nome contenha o termo (case insensitive).
    """
    try:
        resposta = supabase.table("usuarios").select("*").ilike("nome_completo", f"%{nome}%").execute()
        return resposta.data
    except Exception as e:
        print("Erro ao consultar usuário por nome:", e)
        return []


def consultar_usuario_por_id(usuario_id):
    """
    Retorna o usuário com o ID especificado.
    """
    try:
        resposta = supabase.table("usuarios").select("*").eq("id", usuario_id).execute()
        return resposta.data[0] if resposta.data else None
    except Exception as e:
        print("Erro ao consultar usuário por ID:", e)
        return None


def atualizar_usuario(usuario_id, nome_completo, data_nascimento, telefone, endereco,
                      categoria, email, matricula, departamento_curso):
    """
    Atualiza os dados do usuário com o ID fornecido.
    """
    try:
        dados = {
            "nome_completo": nome_completo,
            "data_nascimento": data_nascimento,
            "telefone": telefone,
            "endereco": endereco,
            "categoria": categoria,
            "email": email,
            "matricula": matricula,
            "departamento_curso": departamento_curso
        }
        resposta = supabase.table("usuarios").update(dados).eq("id", usuario_id).execute()
        return len(resposta.data) > 0
    except Exception as e:
        print("Erro ao atualizar usuário:", e)
        return False


def inativar_usuario(usuario_id, motivo, realizado_por=1):
    """
    Inativa o usuário e registra o motivo da inativação.
    """
    try:
        resposta_status = supabase.table("usuarios").update({"status": "inativo"}).eq("id", usuario_id).execute()
        if not resposta_status.data:
            return False

        inativacao = {
            "usuario_id": usuario_id,
            "realizado_por": realizado_por,
            "motivo": motivo,
            "data": datetime.now().isoformat()
        }
        inserir_dado("inativacoes", inativacao)
        return True
    except Exception as e:
        print("Erro ao inativar usuário:", e)
        return False


def ativar_usuario(usuario_id):
    """
    Ativa o usuário atualizando o status para 'ativo'.
    """
    try:
        resposta = supabase.table("usuarios").update({"status": "ativo"}).eq("id", usuario_id).execute()
        return len(resposta.data) > 0
    except Exception as e:
        print("Erro ao ativar usuário:", e)
        return False
