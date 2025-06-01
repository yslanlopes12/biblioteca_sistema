from db import inserir_dado, supabase
from usuario import consultar_usuario_por_cpf, consultar_usuario_por_nome, consultar_usuario_por_matricula
from datetime import date, timedelta


def verificar_disponibilidade_item(item_id):
    try:
        resposta = supabase.table("itens").select("status, data_devolucao_prevista").eq("id", item_id).execute()
        if not resposta.data:
            return (False, "Item não encontrado")

        item = resposta.data[0]
        if item["status"] == "disponivel":
            return (True, "Disponível")
        elif item["status"] == "emprestado":
            return (False, f"Item emprestado. Devolução prevista para {item['data_devolucao_prevista']}")
        else:
            return (False, f"Item com status: {item['status']}")
    except Exception as e:
        print("Erro ao verificar disponibilidade do item:", e)
        return (False, "Erro ao verificar disponibilidade")


def calcular_data_devolucao_prevista(categoria, tipo_material):
    try:
        # Verifica se há regra específica para o tipo de material
        resposta = supabase.table("limites_emprestimo").select("dias_emprestimo").match({
            "categoria": categoria,
            "tipo_material": tipo_material
        }).execute()

        if not resposta.data:
            # Usa regra padrão para a categoria
            resposta = supabase.table("limites_emprestimo").select("dias_emprestimo").eq("categoria",
                                                                                         categoria).execute()

        dias = resposta.data[0]["dias_emprestimo"] if resposta.data else 7
        return date.today() + timedelta(days=dias)
    except Exception as e:
        print("Erro ao calcular data de devolução:", e)
        return date.today() + timedelta(days=7)


def verificar_multas_pendentes(usuario_id):
    try:
        resposta = supabase.table("multas").select("valor").eq("usuario_id", usuario_id).eq("paga", False).execute()
        if resposta.data:
            total_multas = sum(multa["valor"] for multa in resposta.data)
            return (True, f"Usuário possui R${total_multas:.2f} em multas pendentes")
        return (False, "")
    except Exception as e:
        print("Erro ao verificar multas pendentes:", e)
        return (True, "Erro ao verificar multas")


def verificar_limite_emprestimos(usuario_id, categoria):
    try:
        emprestimos = supabase.table("emprestimos").select("id").eq("usuario_id", usuario_id).eq("status",
                                                                                                 "ativo").execute()
        total = len(emprestimos.data)

        limite_resp = supabase.table("limites_emprestimo").select("max_emprestimos").eq("categoria",
                                                                                        categoria).execute()
        max_emprestimos = limite_resp.data[0]["max_emprestimos"] if limite_resp.data else 3

        if total >= max_emprestimos:
            return (False, f"Limite de {max_emprestimos} empréstimos atingido")
        return (True, "")
    except Exception as e:
        print("Erro ao verificar limite de empréstimos:", e)
        return (False, "Erro ao verificar limite de empréstimos")


def verificar_material_restrito(item_id, usuario_categoria):
    try:
        resposta = supabase.table("itens").select("circulacao_restrita").eq("id", item_id).execute()
        if resposta.data and resposta.data[0]["circulacao_restrita"]:
            # Verifica se a categoria do usuário permite empréstimo de materiais restritos
            permissoes = supabase.table("categorias_usuarios").select("permite_restrito").eq("categoria",
                                                                                             usuario_categoria).execute()
            if not permissoes.data or not permissoes.data[0]["permite_restrito"]:
                return (False, "Usuário não tem permissão para materiais de circulação restrita")
        return (True, "")
    except Exception as e:
        print("Erro ao verificar material restrito:", e)
        return (False, "Erro ao verificar permissões")


def buscar_usuario_emprestimo():
    print("\n=== Buscar Usuário ===")
    print("1 - Por CPF")
    print("2 - Por Nome")
    print("3 - Por Matrícula")
    opcao = input("Escolha o método de busca: ").strip()

    if opcao == '1':
        cpf = input("Digite o CPF (apenas números): ").strip()
        usuario = consultar_usuario_por_cpf(cpf)
    elif opcao == '2':
        nome = input("Digite o nome: ").strip()
        usuarios = consultar_usuario_por_nome(nome)
        if len(usuarios) == 1:
            usuario = usuarios[0]
        elif len(usuarios) > 1:
            print("\nVários usuários encontrados:")
            for i, usuario in enumerate(usuarios, 1):
                print(f"{i} - {usuario['nome_completo']} (CPF: {usuario['cpf']}, Matrícula: {usuario['matricula']})")
            selecao = input("Digite o número do usuário correto: ").strip()
            try:
                usuario = usuarios[int(selecao) - 1]
            except (ValueError, IndexError):
                usuario = None
        else:
            usuario = None
    elif opcao == '3':
        matricula = input("Digite a matrícula: ").strip()
        usuario = consultar_usuario_por_matricula(matricula)
    else:
        print("Opção inválida.")
        return None

    if usuario:
        print("\nDados do usuário:")
        print(f"Nome: {usuario['nome_completo']}")
        print(f"CPF: {usuario['cpf']}")
        print(f"Matrícula: {usuario['matricula']}")
        print(f"Categoria: {usuario['categoria']}")
        print(f"Status: {usuario['status']}")
        return usuario
    else:
        print("Usuário não encontrado.")
        return None


def _selecionar_item_multiplos_resultados(itens):
    if not itens:
        return None
    if len(itens) == 1:
        return itens[0]

    print("\nVários itens encontrados:")
    for i, item in enumerate(itens, 1):
        print(f"{i} - {item['titulo']} (ID: {item['id']}, ISBN: {item['isbn']}, Status: {item['status']})")
    selecao = input("Digite o número do item correto: ").strip()
    try:
        return itens[int(selecao) - 1]
    except (ValueError, IndexError):
        return None


def buscar_item_emprestimo():
    print("\n=== Buscar Item ===")
    print("1 - Por ID")
    print("2 - Por Título")
    print("3 - Por ISBN")
    opcao = input("Escolha o método de busca: ").strip()

    try:
        if opcao == '1':
            item_id = input("Digite o ID do item: ").strip()
            resposta = supabase.table("itens").select("*").eq("id", int(item_id)).execute()
            item = resposta.data[0] if resposta.data else None
        elif opcao == '2':
            titulo = input("Digite parte do título: ").strip()
            resposta = supabase.table("itens").select("*").ilike("titulo", f"%{titulo}%").execute()
            item = _selecionar_item_multiplos_resultados(resposta.data)
        elif opcao == '3':
            isbn = input("Digite o ISBN: ").strip()
            resposta = supabase.table("itens").select("*").eq("isbn", isbn).execute()
            item = _selecionar_item_multiplos_resultados(resposta.data)
        else:
            print("Opção inválida.")
            return None

        if item:
            print("\nDados do item:")
            print(f"ID: {item['id']}")
            print(f"Título: {item['titulo']}")
            print(f"Autor: {item['autor']}")
            print(f"ISBN: {item['isbn']}")
            print(f"Tipo: {item['tipo_material']}")
            print(f"Status: {item['status']}")
            if item['status'] == 'emprestado':
                print(f"Devolução prevista: {item.get('data_devolucao_prevista', 'Não informada')}")
            print(f"Circulação restrita: {'Sim' if item['circulacao_restrita'] else 'Não'}")
            return item
        else:
            print("Item não encontrado.")
            return None
    except Exception as e:
        print("Erro ao buscar item:", e)
        return None


def adicionar_lista_espera(usuario_id, item_id):
    try:
        lista_espera = {
            "usuario_id": usuario_id,
            "item_id": item_id,
            "data_solicitacao": date.today().isoformat(),
            "status": "pendente"
        }
        resultado = inserir_dado("lista_espera", lista_espera)
        if resultado:
            print("✅ Usuário adicionado à lista de espera para este item.")
            return True
        return False
    except Exception as e:
        print("Erro ao adicionar à lista de espera:", e)
        return False


def registrar_emprestimo(usuario, item, id_usuario_sistema):
    print("\nResumo do empréstimo:")
    print(f"Usuário: {usuario['nome_completo']} (ID: {usuario['id']})")
    print(f"Item: {item['titulo']} (ID: {item['id']})")

    # Verificações
    if usuario["status"] != "ativo":
        print("❌ Usuário está inativo e não pode realizar empréstimos.")
        return False

    multa_pendente, msg_multa = verificar_multas_pendentes(usuario["id"])
    if multa_pendente:
        print(f"❌ {msg_multa}")
        return False

    limite_ok, msg_limite = verificar_limite_emprestimos(usuario["id"], usuario["categoria"])
    if not limite_ok:
        print(f"❌ {msg_limite}")
        return False

    disponivel, msg_disponibilidade = verificar_disponibilidade_item(item["id"])
    if not disponivel:
        print(f"❌ {msg_disponibilidade}")
        if "emprestado" in msg_disponibilidade:
            deseja_lista_espera = input("Deseja adicionar o usuário à lista de espera? (S/N): ").strip().lower()
            if deseja_lista_espera == 's':
                adicionar_lista_espera(usuario["id"], item["id"])
        return False

    restrito_ok, msg_restrito = verificar_material_restrito(item["id"], usuario["categoria"])
    if not restrito_ok:
        print(f"❌ {msg_restrito}")
        return False

    data_devolucao = calcular_data_devolucao_prevista(usuario["categoria"], item["tipo_material"])
    print(f"Data de devolução prevista: {data_devolucao.isoformat()}")

    confirmacao = input("\nConfirmar empréstimo? (S/N): ").strip().lower()
    if confirmacao != 's':
        print("Operação cancelada.")
        return False

    emprestimo = {
        "usuario_id": usuario["id"],
        "item_id": item["id"],
        "data_emprestimo": date.today().isoformat(),
        "data_devolucao_prevista": data_devolucao.isoformat(),
        "registrado_por": id_usuario_sistema,
        "status": "ativo"
    }

    try:
        # Inicia transação
        supabase.postgrest.schema("public")  # Garante que estamos no schema correto

        # Registra empréstimo
        resultado = inserir_dado("emprestimos", emprestimo)
        if not resultado:
            print("❌ Erro ao registrar empréstimo.")
            return False

        # Atualiza status do item
        atualizar_status = supabase.table("itens").update({
            "status": "emprestado",
            "ultimo_emprestimo": date.today().isoformat()
        }).eq("id", item["id"]).execute()

        if not atualizar_status.data:
            print("❌ Erro ao atualizar status do item.")
            return False

        # Atualiza histórico do usuário
        historico = {
            "usuario_id": usuario["id"],
            "item_id": item["id"],
            "data_acao": date.today().isoformat(),
            "tipo_acao": "emprestimo",
            "responsavel_id": id_usuario_sistema
        }
        inserir_dado("historico", historico)

        print(f"\n✅ Empréstimo registrado com sucesso!")
        print(f"Usuário: {usuario['nome_completo']}")
        print(f"Item: {item['titulo']}")
        print(f"Data de devolução: {data_devolucao.isoformat()}")
        return True

    except Exception as e:
        print("❌ Erro ao registrar empréstimo:", e)
        return False


def menu_emprestimo(id_usuario_sistema):
    while True:
        print("\n=== MENU EMPRÉSTIMO ===")
        print("1 - Registrar novo empréstimo")
        print("2 - Voltar ao menu principal")
        opcao = input("Escolha uma opção: ").strip()

        if opcao == '1':
            usuario = buscar_usuario_emprestimo()
            if not usuario:
                continue

            item = buscar_item_emprestimo()
            if not item:
                continue

            registrar_emprestimo(usuario, item, id_usuario_sistema)
        elif opcao == '2':
            break
        else:
            print("Opção inválida. Tente novamente.")