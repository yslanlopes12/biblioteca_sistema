from usuario import (
    cadastrar_usuario,
    consultar_usuario_por_cpf,
    consultar_usuario_por_nome,
    atualizar_usuario,
    inativar_usuario,
    ativar_usuario
)

def menu_bibliotecario():
    print("\n=== Menu Bibliotecário ===")
    print("1 - Consultar Usuário")
    print("2 - Atualizar Dados do Usuário")
    print("3 - Inativar Usuário")
    print("4 - Ativar Usuário")
    print("5 - Sair")

def menu_comum():
    print("\n=== Menu Usuário ===")
    print("1 - Sair")

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

            sucesso = cadastrar_usuario(nome, data_nascimento, cpf, telefone, endereco,
                                        categoria, email, matricula, departamento)
            if sucesso:
                print("Usuário cadastrado com sucesso!")
                return consultar_usuario_por_cpf(cpf)
            else:
                print("Erro ao cadastrar. Tente novamente.")
        else:
            usuario = consultar_usuario_por_cpf(cpf)
            if usuario:
                print(f"Bem-vindo(a), {usuario['nome_completo']} ({usuario['categoria']})")
                return usuario
            else:
                print("Usuário não encontrado. Deseja cadastrar? (s/n)")
                if input().strip().lower() == 's':
                    cpf = ''  # volta ao fluxo de cadastro
                else:
                    continue

def main():
    usuario_logado = login_ou_cadastro()

    if usuario_logado['categoria'] == 'bibliotecario':
        while True:
            menu_bibliotecario()
            opcao = input("Escolha uma opção: ").strip()

            if opcao == '1':
                filtro = input("Buscar por (1) CPF ou (2) Nome? ").strip()
                if filtro == '1':
                    cpf = input("Digite o CPF: ").strip()
                    usuario = consultar_usuario_por_cpf(cpf)
                    print(usuario if usuario else "Usuário não encontrado.")
                elif filtro == '2':
                    nome = input("Digite o nome: ").strip()
                    usuarios = consultar_usuario_por_nome(nome)
                    if usuarios:
                        for u in usuarios:
                            print(u)
                    else:
                        print("Nenhum usuário encontrado.")
                else:
                    print("Opção inválida.")

            elif opcao == '2':
                cpf = input("Digite o CPF do usuário para atualizar: ").strip()
                usuario = consultar_usuario_por_cpf(cpf)
                if not usuario:
                    print("Usuário não encontrado.")
                    continue

                print("Deixe em branco para manter o valor atual.")
                nome = input(f"Nome completo [{usuario['nome_completo']}]: ").strip() or usuario['nome_completo']
                data_nascimento = input(f"Data nascimento [{usuario['data_nascimento']}]: ").strip() or usuario['data_nascimento']
                telefone = input(f"Telefone [{usuario['telefone']}]: ").strip() or usuario['telefone']
                endereco = input(f"Endereço [{usuario['endereco']}]: ").strip() or usuario['endereco']
                categoria = input(f"Categoria [{usuario['categoria']}]: ").strip() or usuario['categoria']
                email = input(f"Email [{usuario.get('email', '')}]: ").strip() or usuario.get('email', '')
                matricula = input(f"Matrícula [{usuario.get('matricula', '')}]: ").strip() or usuario.get('matricula', '')
                departamento = input(f"Departamento/Curso [{usuario.get('departamento_curso', '')}]: ").strip() or usuario.get('departamento_curso', '')

                sucesso = atualizar_usuario(usuario['id'], nome, data_nascimento, telefone, endereco,
                                            categoria, email, matricula, departamento)
                print("Usuário atualizado com sucesso!" if sucesso else "Erro ao atualizar usuário.")

            elif opcao == '3':
                cpf = input("Digite o CPF do usuário para inativar: ").strip()
                usuario = consultar_usuario_por_cpf(cpf)
                if not usuario:
                    print("Usuário não encontrado.")
                    continue
                if usuario['status'] == 'inativo':
                    print("Usuário já está inativo.")
                    continue
                motivo = input("Motivo da inativação: ").strip()
                sucesso = inativar_usuario(usuario['id'], motivo, realizado_por=usuario_logado['id'])
                print("Usuário inativado com sucesso!" if sucesso else "Erro ao inativar usuário.")

            elif opcao == '4':
                cpf = input("Digite o CPF do usuário para ativar: ").strip()
                usuario = consultar_usuario_por_cpf(cpf)
                if not usuario:
                    print("Usuário não encontrado.")
                    continue
                if usuario['status'] == 'ativo':
                    print("Usuário já está ativo.")
                    continue
                sucesso = ativar_usuario(usuario['id'])
                print("Usuário ativado com sucesso!" if sucesso else "Erro ao ativar usuário.")

            elif opcao == '5':
                print("Saindo...")
                break
            else:
                print("Opção inválida.")

    else:
        # Menu para usuários comuns
        while True:
            menu_comum()
            opcao = input("Escolha uma opção: ").strip()
            if opcao == '1':
                print("Saindo...")
                break
            else:
                print("Opção inválida.")

if __name__ == "__main__":
    main()
