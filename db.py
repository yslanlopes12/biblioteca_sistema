from supabase import create_client, Client
from dotenv import load_dotenv
import os

# Carrega as variáveis do .env
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def selecionar_todos(nome_tabela):
    try:
        resposta = supabase.table(nome_tabela).select("*").execute()
        return resposta.data
    except Exception as e:
        print("Erro ao buscar dados:", e)
        return []

def inserir_dado(nome_tabela, dados: dict):
    try:
        resposta = supabase.table(nome_tabela).insert(dados).execute()
        return resposta.data
    except Exception as e:
        print("Erro ao inserir dados:", e)
        return []

def deletar_dado(nome_tabela, condicao: dict):
    try:
        resposta = supabase.table(nome_tabela).delete().match(condicao).execute()
        return resposta.data
    except Exception as e:
        print("Erro ao deletar dados:", e)
        return []
