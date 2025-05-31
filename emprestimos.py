from db import inserir_dado, supabase
from usuario import consultar_usuario_por_cpf
from datetime import date, timedelta

def verificar_disponibilidade_item(item_id):
    """
    Verifica se o item está disponível para empréstimo.
    Retorna True se disponível, False caso contrário.
    """
    try:
        resposta = supabase.table("itens").select("status").eq("id", item_id).execute()
        if resposta.data and resposta.data[0]["status"] == "disponivel":
            return True
    except Exception as e:
        print("Erro ao verificar disponibilidade do item:", e)
    return False


def calcular_data_devolucao_prevista(categoria):
    """
    Calcula a data prevista para devolução do empréstimo,
    baseado no limite de dias definido para a categoria do usuário.
    Retorna um objeto date.
    """
    try:
        resposta = supabase.table("limites_emprestimo").select("dias_emprestimo").eq("categoria", categoria).execute()
        if resposta.data:
            dias = resposta.data[0]["dias_emprestimo"]
        else:
            dias = 7  # padrão
        return date.today() + timedelta(days=dias)
    except Exception as e:
        print("Erro ao calcular data de devolução:", e)
        return date.today() + timedelta(days=7)


def registrar_emprestimo(cpf_usuario, item_id, id_usuario_sistema):
    """
    Registra um empréstimo de item para o usuário identificado pelo CPF.
    Verifica se o usuário está ativo e se o item está disponível.
    Atualiza status do item para 'emprestado' após registro.
    Retorna True em caso de sucesso, False caso contrário.
    """
    usuario = consultar_usuario_por_cpf(cpf_usuario)
    if not usuario:
        print("Usuário não encontrado.")
        return False

    if usuario["status"] != "ativo":
        print("Usuário está inativo e não pode realizar empréstimos.")
        return False

    if not verificar_disponibilidade_item(item_id):
        print("Item não disponível para empréstimo.")
        return False

    categoria = usuario["categoria"]
    data_devolucao = calcular_data_devolucao_prevista(categoria)

    emprestimo = {
        "usuario_id": usuario["id"],
        "item_id": item_id,
        "data_devolucao_prevista": data_devolucao.isoformat(),
        "registrado_por": id_usuario_sistema
    }

    try:
        resultado = inserir_dado("emprestimos", emprestimo)
        if not resultado:
            print("Erro ao registrar empréstimo.")
            return False

        # Atualiza status do item para 'emprestado'
        resposta = supabase.table("itens").update({"status": "emprestado"}).eq("id", item_id).execute()
        if not resposta.data:
            print("Erro ao atualizar status do item.")
            return False

        return True
    except Exception as e:
        print("Erro ao registrar empréstimo:", e)
        return False
