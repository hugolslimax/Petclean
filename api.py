# ============================================
# PET SHOP - API (Flask)
# Instalar:  pip install flask flask-cors
# Rodar:     python api.py   ->  http://localhost:5000
# ============================================

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # libera o front (outra porta/origem) para chamar a API

# ---------- DADOS ----------

PRECOS = {
    "banho":      {"pequeno": 40.0, "medio": 60.0, "grande": 80.0},
    "tosa":       {"pequeno": 50.0, "medio": 70.0, "grande": 90.0},
    "hidratacao": {"pequeno": 30.0, "medio": 45.0, "grande": 60.0},
}

DESCONTO_COMBO = 0.15
BANHOS_PARA_GRATIS = 10
ESPECIES = ["cachorro", "gato"]
PORTES = ["pequeno", "medio", "grande"]

pets = []
historico = []
proximo_id = 1   # cada pet novo recebe um id único


# ---------- FUNÇÕES DE REGRA DE NEGÓCIO ----------

def buscar_pet_por_id(pet_id):
    for pet in pets:
        if pet["id"] == pet_id:
            return pet
    return None


def buscar_duplicado(nome, tutor):
    """Mesmo nome + mesmo tutor = pet repetido."""
    for pet in pets:
        if (pet["nome"].lower() == nome.lower()
                and pet["tutor"].lower() == tutor.lower()):
            return pet
    return None


def calcular_atendimento(pet, servicos):
    """Retorna total, desconto_combo e banho_gratis (sem alterar o pet)."""
    porte = pet["porte"]
    total = 0.0
    for servico in servicos:
        total += PRECOS[servico][porte]

    banho_gratis = False
    if "banho" in servicos and pet["banhos_pagos"] >= BANHOS_PARA_GRATIS:
        banho_gratis = True
        total -= PRECOS["banho"][porte]

    desconto = 0.0
    if "banho" in servicos and "tosa" in servicos and not banho_gratis:
        valor_combo = PRECOS["banho"][porte] + PRECOS["tosa"][porte]
        desconto = valor_combo * DESCONTO_COMBO
        total -= desconto

    return round(total, 2), round(desconto, 2), banho_gratis


def validar_servicos(servicos):
    """Retorna mensagem de erro ou None se estiver tudo certo."""
    if not isinstance(servicos, list) or len(servicos) == 0:
        return "Envie 'servicos' como uma lista, ex: [\"banho\", \"tosa\"]"
    for s in servicos:
        if not isinstance(s, str) or s not in PRECOS:
            return f"Serviço inválido: {s}. Use: {', '.join(PRECOS.keys())}"
    if len(set(servicos)) != len(servicos):
        return "Não repita o mesmo serviço na lista"
    return None


# ---------- ENDPOINTS ----------

# GET /precos -> tabela de preços
@app.route("/precos", methods=["GET"])
def get_precos():
    return jsonify({
        "precos": PRECOS,
        "desconto_combo": DESCONTO_COMBO,
        "banhos_para_gratis": BANHOS_PARA_GRATIS,
    })


# GET /pets -> lista todos os pets
@app.route("/pets", methods=["GET"])
def listar_pets():
    return jsonify(pets)


# GET /pets/<id> -> um pet específico
@app.route("/pets/<int:pet_id>", methods=["GET"])
def get_pet(pet_id):
    pet = buscar_pet_por_id(pet_id)
    if pet is None:
        return jsonify({"erro": "Pet não encontrado"}), 404
    return jsonify(pet)


# POST /pets -> cadastra pet
# body: {"nome": "Rex", "especie": "cachorro", "porte": "medio", "tutor": "Ana"}
@app.route("/pets", methods=["POST"])
def cadastrar_pet():
    dados = request.get_json(silent=True) or {}

    nome = str(dados.get("nome", "")).strip()
    especie = str(dados.get("especie", "")).strip().lower()
    porte = str(dados.get("porte", "")).strip().lower()
    tutor = str(dados.get("tutor", "")).strip()

    if nome == "" or tutor == "":
        return jsonify({"erro": "'nome' e 'tutor' são obrigatórios"}), 400
    if especie not in ESPECIES:
        return jsonify({"erro": f"'especie' deve ser: {', '.join(ESPECIES)}"}), 400
    if porte not in PORTES:
        return jsonify({"erro": f"'porte' deve ser: {', '.join(PORTES)}"}), 400
    if buscar_duplicado(nome, tutor) is not None:
        return jsonify({"erro": "Esse tutor já tem um pet com esse nome"}), 409

    global proximo_id
    pet = {
        "id": proximo_id,
        "nome": nome,
        "especie": especie,
        "porte": porte,
        "tutor": tutor,
        "banhos_pagos": 0,
    }
    proximo_id += 1
    pets.append(pet)
    return jsonify(pet), 201


# POST /atendimentos/simular -> calcula o preço SEM registrar
# body: {"pet_id": 1, "servicos": ["banho", "tosa"]}
@app.route("/atendimentos/simular", methods=["POST"])
def simular_atendimento():
    dados = request.get_json(silent=True) or {}
    pet = buscar_pet_por_id(dados.get("pet_id"))
    if pet is None:
        return jsonify({"erro": "Pet não encontrado"}), 404

    servicos = dados.get("servicos")
    erro = validar_servicos(servicos)
    if erro:
        return jsonify({"erro": erro}), 400

    total, desconto, banho_gratis = calcular_atendimento(pet, servicos)
    return jsonify({
        "pet": pet["nome"],
        "servicos": servicos,
        "desconto_combo": desconto,
        "banho_gratis": banho_gratis,
        "total": total,
    })


# POST /atendimentos -> registra o atendimento (atualiza fidelidade)
# body: {"pet_id": 1, "servicos": ["banho", "tosa"]}
@app.route("/atendimentos", methods=["POST"])
def registrar_atendimento():
    dados = request.get_json(silent=True) or {}
    pet = buscar_pet_por_id(dados.get("pet_id"))
    if pet is None:
        return jsonify({"erro": "Pet não encontrado"}), 404

    servicos = dados.get("servicos")
    erro = validar_servicos(servicos)
    if erro:
        return jsonify({"erro": erro}), 400

    total, desconto, banho_gratis = calcular_atendimento(pet, servicos)

    # atualiza contador de fidelidade
    if "banho" in servicos:
        if banho_gratis:
            pet["banhos_pagos"] = 0
        else:
            pet["banhos_pagos"] += 1

    atendimento = {
        "pet_id": pet["id"],
        "pet": pet["nome"],
        "tutor": pet["tutor"],
        "servicos": servicos,
        "desconto_combo": desconto,
        "banho_gratis": banho_gratis,
        "total": total,
        "banhos_para_gratis": BANHOS_PARA_GRATIS - pet["banhos_pagos"],
    }
    historico.append(atendimento)
    return jsonify(atendimento), 201


# GET /historico -> atendimentos + faturamento
@app.route("/historico", methods=["GET"])
def get_historico():
    faturamento = 0.0
    for item in historico:
        faturamento += item["total"]
    return jsonify({
        "atendimentos": historico,
        "faturamento_total": round(faturamento, 2),
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
