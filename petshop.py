# ============================================
# PET SHOP - BANHO E TOSA (back end)
# ============================================

# ---------- DADOS ----------

# Tabela de preços: dicionário aninhado -> PRECOS[servico][porte]
PRECOS = {
    "banho":      {"pequeno": 40.0, "medio": 60.0, "grande": 80.0},
    "tosa":       {"pequeno": 50.0, "medio": 70.0, "grande": 90.0},
    "hidratacao": {"pequeno": 30.0, "medio": 45.0, "grande": 60.0},
}

DESCONTO_COMBO = 0.15      # 15% no combo banho + tosa
BANHOS_PARA_GRATIS = 10    # a cada 10 banhos pagos, o próximo é grátis

pets = []        # lista de dicionários (um por pet)
historico = []   # lista de atendimentos realizados


# ---------- FUNÇÕES AUXILIARES ----------

def pedir_opcao(mensagem, opcoes):
    """Repete a pergunta até o usuário digitar uma opção válida."""
    while True:
        valor = input(mensagem).strip().lower()
        if valor in opcoes:
            return valor
        print("Opção inválida. Escolha entre:", ", ".join(opcoes))


def buscar_pet(nome, tutor):
    """Procura um pet pelo nome E pelo tutor. Retorna o dicionário ou None."""
    for pet in pets:
        if (pet["nome"].lower() == nome.lower()
                and pet["tutor"].lower() == tutor.lower()):
            return pet
    return None


# ---------- CADASTRO ----------

def cadastrar_pet():
    nome = input("Nome do pet: ").strip()
    tutor = input("Nome do tutor: ").strip()
    if buscar_pet(nome, tutor) is not None:
        print("Esse tutor já tem um pet com esse nome.")
        return

    especie = pedir_opcao("Espécie (cachorro/gato): ", ["cachorro", "gato"])
    porte = pedir_opcao("Porte (pequeno/medio/grande): ",
                        ["pequeno", "medio", "grande"])

    pet = {
        "nome": nome,
        "especie": especie,
        "porte": porte,
        "tutor": tutor,
        "banhos_pagos": 0,   # contador de fidelidade (por pet)
    }
    pets.append(pet)
    print("Pet cadastrado com sucesso!")


def listar_pets():
    if len(pets) == 0:
        print("Nenhum pet cadastrado.")
        return
    for pet in pets:
        faltam = BANHOS_PARA_GRATIS - pet["banhos_pagos"]
        print(f"- {pet['nome']} ({pet['especie']}, {pet['porte']}) "
              f"| Tutor: {pet['tutor']} | Banhos p/ o grátis: {faltam}")


def mostrar_tabela_precos():
    print("\n--- TABELA DE PREÇOS ---")
    for servico in PRECOS:
        print(servico.upper())
        for porte in PRECOS[servico]:
            print(f"   {porte}: R$ {PRECOS[servico][porte]:.2f}")


# ---------- REGRAS DE NEGÓCIO ----------

def calcular_atendimento(pet, servicos):
    """
    Recebe o pet e a lista de serviços (ex: ["banho", "tosa"]).
    Retorna: total, desconto_combo, banho_gratis
    """
    porte = pet["porte"]
    total = 0.0
    for servico in servicos:
        total += PRECOS[servico][porte]

    # Regra 1: banho grátis (fidelidade)
    banho_gratis = False
    if "banho" in servicos and pet["banhos_pagos"] >= BANHOS_PARA_GRATIS:
        banho_gratis = True
        total -= PRECOS["banho"][porte]

    # Regra 2: combo banho + tosa tem 15% de desconto
    # (só se o banho não for grátis, para não descontar duas vezes)
    desconto = 0.0
    if "banho" in servicos and "tosa" in servicos and not banho_gratis:
        valor_combo = PRECOS["banho"][porte] + PRECOS["tosa"][porte]
        desconto = valor_combo * DESCONTO_COMBO
        total -= desconto

    return total, desconto, banho_gratis


def registrar_atendimento():
    nome = input("Nome do pet: ").strip()
    tutor = input("Nome do tutor: ").strip()
    pet = buscar_pet(nome, tutor)
    if pet is None:
        print("Pet não encontrado. Cadastre primeiro.")
        return

    # Escolha dos serviços
    servicos = []
    for servico in PRECOS:
        resposta = pedir_opcao(f"Incluir {servico}? (s/n): ", ["s", "n"])
        if resposta == "s":
            servicos.append(servico)

    if len(servicos) == 0:
        print("Nenhum serviço selecionado.")
        return

    total, desconto, banho_gratis = calcular_atendimento(pet, servicos)

    # Atualiza o contador de fidelidade
    if "banho" in servicos:
        if banho_gratis:
            pet["banhos_pagos"] = 0       # zera depois do grátis
        else:
            pet["banhos_pagos"] += 1      # conta mais um banho pago

    historico.append({"pet": pet["nome"], "servicos": servicos, "total": total})

    # Recibo
    print("\n--- RECIBO ---")
    print(f"Pet: {pet['nome']} ({pet['porte']}) | Tutor: {pet['tutor']}")
    print("Serviços:", ", ".join(servicos))
    if banho_gratis:
        print("🎉 Banho GRÁTIS (fidelidade)!")
    if desconto > 0:
        print(f"Desconto combo (15%): -R$ {desconto:.2f}")
    print(f"TOTAL: R$ {total:.2f}")


def mostrar_historico():
    if len(historico) == 0:
        print("Nenhum atendimento registrado.")
        return
    faturamento = 0.0
    for item in historico:
        print(f"- {item['pet']}: {', '.join(item['servicos'])} "
              f"= R$ {item['total']:.2f}")
        faturamento += item["total"]
    print(f"Faturamento total: R$ {faturamento:.2f}")


# ---------- MENU PRINCIPAL ----------

def menu():
    while True:
        print("\n===== PET SHOP =====")
        print("1 - Cadastrar pet")
        print("2 - Listar pets")
        print("3 - Ver tabela de preços")
        print("4 - Registrar atendimento")
        print("5 - Histórico")
        print("0 - Sair")
        opcao = input("Escolha: ").strip()

        if opcao == "1":
            cadastrar_pet()
        elif opcao == "2":
            listar_pets()
        elif opcao == "3":
            mostrar_tabela_precos()
        elif opcao == "4":
            registrar_atendimento()
        elif opcao == "5":
            mostrar_historico()
        elif opcao == "0":
            print("Até logo!")
            break
        else:
            print("Opção inválida.")


menu()
