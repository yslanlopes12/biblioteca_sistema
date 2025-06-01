import re
import bcrypt
from datetime import datetime
from supabase import create_client, Client
from usuario import (
    cadastrar_usuario,
    consultar_usuario_por_cpf,
    consultar_usuario_por_nome,
    atualizar_usuario,
    inativar_usuario,
    ativar_usuario,
    consultar_usuario_por_matricula,
    consultar_usuario_por_id,
)
from emprestimos import (
    registrar_emprestimo,
    buscar_usuario_emprestimo,
    buscar_item_emprestimo,
    menu_emprestimo
)


def validar_cpf(cpf: str) -> bool:
    """Valida CPF pelo formato e dígitos verificadores."""
    if not re.fullmatch(r"\d{11}", cpf):
        return False

    def calcular_dv(cpf_parcial: str, pesos: range) -> str:
        soma = sum(int(d) * p for d, p in zip(cpf_parcial, pesos))
        resto = soma % 11
        return '0' if resto < 2 else str(11 - resto)

    cpf_base = cpf[:9]
    dv1 = calcular_dv(cpf_base, range(10, 1, -1))
    dv2 = calcular_dv(cpf_base + dv1, range(11, 1, -1))
    return cpf[-2:] == dv1 + dv2


def validar_email(email: str) -> bool:
    """Valida email simples, retorna True se vazio (opcional)."""
    return bool(re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email)) if email else True


def validar_data(data: str) -> bool:
    """Valida formato de data AAAA-MM-DD."""
    try:
        datetime.strptime(data, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def print_usuario(usuario):
    print("\n--- Dados do Usuário ---")
    print(f"ID: {usuario.get('id')}")
    print(f"Nome: {usuario.get('nome_completo')}")
    print(f"Data de Nascimento: {usuario.get('data_nascimento')}")
    print(f"CPF: {usuario.get('cpf')}")
    print(f"Telefone: {usuario.get('telefone')}")
    print(f"Endereço: {usuario.get('endereco')}")
    print(f"Categoria: {usuario.get('categoria')}")
    print(f"Email: {usuario.get('email')}")
    print(f"Matrícula: {usuario.get('matricula')}")
    print(f"Departamento/Curso: {usuario.get('departamento_curso')}")
    print(f"Status: {usuario.get('status')}")
    print("---------------------------")


def menu_bibliotecario():
    print(
        """
=== Menu Bibliotecário ===
1 - Gerenciar Usuários
2 - Gerenciar Empréstimos
3 - Sair
"""
    )


def menu_gerenciar_usuarios():
    print(
        """
=== Gerenciar Usuários ===
1 - Consultar Usuário
2 - Cadastrar Novo Usuário
3 - Atualizar Dados do Usuário
4 - Inativar Usuário
5 - Ativar Usuário
6 - Redefinir Senha de Usuário
7 - Voltar
"""
    )


def menu_gerenciar_emprestimos():
    print(
        """
=== Gerenciar Empréstimos ===
1 - Registrar Empréstimo
2 - Registrar Devolução
3 - Consultar Empréstimos Ativos
4 - Voltar
"""
    )


def menu_comum():
    print(
        """
=== Menu Usuário ===
1 - Consultar Meus Empréstimos
2 - Sair
"""
    )


def cadastrar_usuario_bibliotecario():
    print("\n=== Cadastro de Novo Usuário ===")
    nome = input("Nome completo: ").strip()
    data_nascimento = input("Data nascimento (AAAA-MM-DD): ").strip()
    cpf = input("CPF (11 dígitos): ").strip()
    telefone = input("Telefone: ").strip()
    endereco = input("Endereço: ").strip()
    categoria = input("Categoria (estudante, professor, visitante, bibliotecario): ").strip().lower()

    email = input("Email (opcional): ").strip()
    matricula = input("Matrícula institucional (opcional): ").strip()
    departamento = input("Departamento/Curso (opcional): ").strip()
    senha = input("Crie uma senha para o usuário: ").strip()

    campos_faltando = [
        campo for campo, valor in {
            "Nome": nome,
            "Data de nascimento": data_nascimento,
            "CPF": cpf,
            "Telefone": telefone,
            "Endereço": endereco,
            "Categoria": categoria,
            "Senha": senha,
        }.items() if not valor
    ]

    if campos_faltando:
        print(f"⚠️ Preencha todos os campos obrigatórios: {', '.join(campos_faltando)}")
        return

    if not validar_data(data_nascimento):
        print("⚠️ Data inválida. Use o formato AAAA-MM-DD.")
        return

    if not validar_cpf(cpf):
        print("⚠️ CPF inválido. Verifique o formato e os dígitos verificadores.")
        return

    if consultar_usuario_por_cpf(cpf):
        print("⚠️ CPF já cadastrado. Tente novamente.")
        return

    if email and not validar_email(email):
        print("⚠️ Email inválido.")
        return

    senha_hash = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()

    sucesso = cadastrar_usuario(
        nome,
        data_nascimento,
        cpf,
        telefone,
        endereco,
        categoria,
        email or None,
        matricula or None,
        departamento or None,
        senha_hash,
    )

    print("✅ Usuário cadastrado com sucesso!" if sucesso else "❌ Erro ao cadastrar. Tente novamente.")


def redefinir_senha(usuario_logado):
    print("\n=== Redefinir Senha de Usuário ===")
    cpf = input("Digite o CPF do usuário: ").strip()

    usuario = consultar_usuario_por_cpf(cpf)
    if not usuario:
        print("❌ Usuário não encontrado.")
        return

    nova_senha = input("Digite a nova senha: ").strip()
    confirmar = input("Confirme a nova senha: ").strip()

    if nova_senha != confirmar:
        print("❌ As senhas não coincidem.")
        return

    senha_hash = bcrypt.hashpw(nova_senha.encode(), bcrypt.gensalt()).decode()

    sucesso = atualizar_usuario(
        usuario['id'],
        usuario['nome_completo'],
        usuario['data_nascimento'],
        usuario['telefone'],
        usuario['endereco'],
        usuario['categoria'],
        usuario.get('email'),
        usuario.get('matricula'),
        usuario.get('departamento_curso'),
        senha_hash=senha_hash,
        alterado_por=usuario_logado['id']
    )

    print("✅ Senha redefinida com sucesso!" if sucesso else "❌ Erro ao redefinir senha.")


def consultar_emprestimos_ativos(usuario_id=None):
    try:
        query = supabase.table("emprestimos").select("*, itens(*), usuarios(*)").eq("status", "ativo")

        if usuario_id:
            query = query.eq("usuario_id", usuario_id)

        resposta = query.execute()

        if not resposta.data:
            print("Nenhum empréstimo ativo encontrado.")
            return

        print("\n=== Empréstimos Ativos ===")
        for emprestimo in resposta.data:
            print(f"\nID Empréstimo: {emprestimo['id']}")
            print(f"Item: {emprestimo['itens']['titulo']} (ID: {emprestimo['item_id']})")
            print(f"Usuário: {emprestimo['usuarios']['nome_completo']} (ID: {emprestimo['usuario_id']})")
            print(f"Data Empréstimo: {emprestimo['data_emprestimo']}")
            print(f"Data Devolução Prevista: {emprestimo['data_devolucao_prevista']}")
            print("---------------------------")

    except Exception as e:
        print(f"Erro ao consultar empréstimos: {e}")


def registrar_devolucao(usuario_logado):
    print("\n=== Registrar Devolução ===")
    emprestimo_id = input("Digite o ID do empréstimo: ").strip()

    try:
        emprestimo_id = int(emprestimo_id)
    except ValueError:
        print("ID do empréstimo deve ser um número.")
        return

    try:
        # Verifica se o empréstimo existe e está ativo
        resposta = supabase.table("emprestimos").select("*").eq("id", emprestimo_id).eq("status", "ativo").execute()

        if not resposta.data:
            print("Empréstimo não encontrado ou já devolvido.")
            return

        emprestimo = resposta.data[0]

        # Atualiza status do empréstimo
        atualizacao = supabase.table("emprestimos").update({
            "status": "devolvido",
            "data_devolucao_real": datetime.now().isoformat(),
            "devolvido_por": usuario_logado['id']
        }).eq("id", emprestimo_id).execute()

        if not atualizacao.data:
            print("Erro ao atualizar empréstimo.")
            return

        # Atualiza status do item
        supabase.table("itens").update({
            "status": "disponivel"
        }).eq("id", emprestimo['item_id']).execute()

        # Registra no histórico
        supabase.table("historico").insert({
            "usuario_id": emprestimo['usuario_id'],
            "item_id": emprestimo['item_id'],
            "data_acao": datetime.now().isoformat(),
            "tipo_acao": "devolucao",
            "responsavel_id": usuario_logado['id']
        }).execute()

        print("✅ Devolução registrada com sucesso!")

    except Exception as e:
        print(f"Erro ao registrar devolução: {e}")


def login_ou_cadastro():
    print("=== Bem-vindo ao Sistema da Biblioteca ===")
    while True:
        cpf = input("Digite seu CPF (ou deixe em branco para cadastrar): ").strip()
        if not cpf:
            print("Vamos realizar seu cadastro.")
            nome = input("Nome completo: ").strip()
            data_nascimento = input("Data nascimento (AAAA-MM-DD): ").strip()
            cpf = input("CPF (11 dígitos): ").strip()
            telefone = input("Telefone: ").strip()
            endereco = input("Endereço: ").strip()
            categoria = input("Categoria (bibliotecario, estudante, professor, visitante): ").strip().lower()
            email = input("Email (opcional): ").strip()
            matricula = input("Matrícula institucional (opcional): ").strip()
            departamento = input("Departamento/Curso (opcional): ").strip()
            senha = input("Crie uma senha: ").strip()

            if not nome or not data_nascimento or not cpf or not telefone or not endereco or not categoria or not senha:
                print("⚠️ Preencha todos os campos obrigatórios.")
                continue
            if not validar_data(data_nascimento):
                print("⚠️ Data inválida. Use o formato AAAA-MM-DD.")
                continue
            if not validar_cpf(cpf):
                print("⚠️ CPF inválido.")
                continue
            if email and not validar_email(email):
                print("⚠️ Email inválido.")
                continue
            if consultar_usuario_por_cpf(cpf):
                print("⚠️ CPF já cadastrado.")
                continue

            senha_hash = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()

            sucesso = cadastrar_usuario(
                nome,
                data_nascimento,
                cpf,
                telefone,
                endereco,
                categoria,
                email or None,
                matricula or None,
                departamento or None,
                senha_hash,
            )
            if sucesso:
                print("Usuário cadastrado com sucesso!")
                return consultar_usuario_por_cpf(cpf)
            else:
                print("Erro ao cadastrar. Tente novamente.")
        else:
            usuario = consultar_usuario_por_cpf(cpf)
            if usuario:
                senha = input("Digite sua senha: ").strip()
                if 'senha_hash' not in usuario:
                    print("Este usuário não possui senha cadastrada. Contate o administrador.")
                    continue
                if bcrypt.checkpw(senha.encode(), usuario['senha_hash'].encode()):
                    print(f"Bem-vindo(a), {usuario['nome_completo']} ({usuario['categoria']})")
                    return usuario
                else:
                    print("Senha incorreta. Tente novamente.")
            else:
                print("Usuário não encontrado. Deseja cadastrar? (s/n)")
                if input().strip().lower() == 's':
                    cpf = ''
                else:
                    continue


def main():
    usuario_logado = login_ou_cadastro()
    if not usuario_logado:
        return

    if usuario_logado['categoria'] == 'bibliotecario':
        while True:
            menu_bibliotecario()
            opcao = input("Escolha uma opção: ").strip()

            if opcao == '1':  # Gerenciar Usuários
                while True:
                    menu_gerenciar_usuarios()
                    sub_opcao = input("Escolha uma opção: ").strip()

                    if sub_opcao == '1':  # Consultar Usuário
                        print("\n=== Consultar Usuário ===")
                        print("Buscar por:")
                        print("1 - CPF")
                        print("2 - Nome")
                        print("3 - ID")
                        print("4 - Matrícula")
                        print("5 - Voltar")

                        filtro = input("Escolha uma opção de busca: ").strip()

                        if filtro == '1':
                            cpf = input("Digite o CPF: ").strip()
                            usuario = consultar_usuario_por_cpf(cpf)
                            if usuario:
                                print_usuario(usuario)
                            else:
                                print("⚠️ Nenhum usuário encontrado com esse CPF.")

                        elif filtro == '2':
                            nome = input("Digite o nome: ").strip()
                            usuarios = consultar_usuario_por_nome(nome)
                            if usuarios:
                                print(f"{len(usuarios)} usuário(s) encontrado(s):")
                                for u in usuarios:
                                    print_usuario(u)
                            else:
                                print("⚠️ Nenhum usuário encontrado com esse nome.")

                        elif filtro == '3':
                            try:
                                user_id = int(input("Digite o ID do usuário: ").strip())
                                usuario = consultar_usuario_por_id(user_id)
                                if usuario:
                                    print_usuario(usuario)
                                else:
                                    print("⚠️ Nenhum usuário encontrado com esse ID.")
                            except ValueError:
                                print("ID inválido.")

                        elif filtro == '4':
                            matricula = input("Digite a matrícula: ").strip()
                            usuario = consultar_usuario_por_matricula(matricula)
                            if usuario:
                                print_usuario(usuario)
                            else:
                                print("⚠️ Nenhum usuário encontrado com essa matrícula.")
                        elif filtro == '5':
                            break
                        else:
                            print("Opção inválida.")

                    elif sub_opcao == '2':  # Cadastrar Novo Usuário
                        cadastrar_usuario_bibliotecario()

                    elif sub_opcao == '3':  # Atualizar Dados do Usuário
                        print("\n=== Atualizar Dados do Usuário ===")
                        cpf = input("Digite o CPF do usuário: ").strip()
                        usuario = consultar_usuario_por_cpf(cpf)
                        if not usuario:
                            print("Usuário não encontrado.")
                            continue

                        print("Deixe em branco para manter o valor atual.")
                        nome = input(f"Nome [{usuario.get('nome_completo')}]: ").strip() or usuario.get('nome_completo')
                        data_nascimento = input(
                            f"Data nascimento [{usuario.get('data_nascimento')}]: ").strip() or usuario.get(
                            'data_nascimento')
                        telefone = input(f"Telefone [{usuario.get('telefone')}]: ").strip() or usuario.get('telefone')
                        endereco = input(f"Endereço [{usuario.get('endereco')}]: ").strip() or usuario.get('endereco')
                        categoria = input(f"Categoria [{usuario.get('categoria')}]: ").strip().lower() or usuario.get(
                            'categoria')
                        email = input(f"Email [{usuario.get('email') or 'vazio'}]: ").strip() or usuario.get('email')
                        matricula = input(
                            f"Matrícula [{usuario.get('matricula') or 'vazio'}]: ").strip() or usuario.get('matricula')
                        departamento = input(
                            f"Departamento/Curso [{usuario.get('departamento_curso') or 'vazio'}]: ").strip() or usuario.get(
                            'departamento_curso')

                        if not validar_data(data_nascimento):
                            print("Data inválida.")
                            continue

                        if email and not validar_email(email):
                            print("Email inválido.")
                            continue

                        sucesso = atualizar_usuario(
                            usuario['id'],
                            nome,
                            data_nascimento,
                            telefone,
                            endereco,
                            categoria,
                            email,
                            matricula,
                            departamento,
                            senha_hash=usuario.get('senha_hash'),
                            alterado_por=usuario_logado['id']
                        )
                        print("Usuário atualizado com sucesso!" if sucesso else "Erro ao atualizar.")

                    elif sub_opcao == '4':  # Inativar Usuário
                        print("\n=== Inativar Usuário ===")
                        cpf = input("Digite o CPF do usuário a inativar: ").strip()
                        usuario = consultar_usuario_por_cpf(cpf)
                        if usuario:
                            if usuario.get('status') == 'inativo':
                                print("Usuário já está inativo.")
                            else:
                                if inativar_usuario(usuario['id']):
                                    print("Usuário inativado com sucesso.")
                                else:
                                    print("Erro ao inativar usuário.")
                        else:
                            print("Usuário não encontrado.")

                    elif sub_opcao == '5':  # Ativar Usuário
                        print("\n=== Ativar Usuário ===")
                        cpf = input("Digite o CPF do usuário a ativar: ").strip()
                        usuario = consultar_usuario_por_cpf(cpf)
                        if usuario:
                            if usuario.get('status') == 'ativo':
                                print("Usuário já está ativo.")
                            else:
                                if ativar_usuario(usuario['id']):
                                    print("Usuário ativado com sucesso.")
                                else:
                                    print("Erro ao ativar usuário.")
                        else:
                            print("Usuário não encontrado.")

                    elif sub_opcao == '6':  # Redefinir Senha
                        redefinir_senha(usuario_logado)

                    elif sub_opcao == '7':  # Voltar
                        break

                    else:
                        print("Opção inválida.")

            elif opcao == '2':  # Gerenciar Empréstimos
                while True:
                    menu_gerenciar_emprestimos()
                    sub_opcao = input("Escolha uma opção: ").strip()

                    if sub_opcao == '1':  # Registrar Empréstimo
                        menu_emprestimo(usuario_logado['id'])

                    elif sub_opcao == '2':  # Registrar Devolução
                        registrar_devolucao(usuario_logado)

                    elif sub_opcao == '3':  # Consultar Empréstimos Ativos
                        consultar_emprestimos_ativos()

                    elif sub_opcao == '4':  # Voltar
                        break

                    else:
                        print("Opção inválida.")

            elif opcao == '3':  # Sair
                print("Saindo do sistema. Até logo!")
                break

            else:
                print("Opção inválida, tente novamente.")

    else:  # Usuário comum
        while True:
            menu_comum()
            opcao = input("Escolha uma opção: ").strip()

            if opcao == '1':  # Consultar Meus Empréstimos
                consultar_emprestimos_ativos(usuario_logado['id'])

            elif opcao == '2':  # Sair
                print("Saindo do sistema. Até logo!")
                break

            else:
                print("Opção inválida, tente novamente.")


if __name__ == "__main__":
    main()