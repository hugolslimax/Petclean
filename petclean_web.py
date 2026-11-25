"""Serve a interface e adiciona persistência à API Flask original."""

import argparse
from contextlib import closing
from functools import wraps
import importlib.util
import json
from pathlib import Path
import sqlite3
from threading import Lock

from flask import request, send_from_directory

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "FRONT-END"


def criar_app(banco):
    spec = importlib.util.spec_from_file_location("petclean_api", FRONTEND / "api (1).py")
    api = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api)

    app = api.app
    lock = Lock()

    def conectar():
        conexao = sqlite3.connect(banco)
        conexao.row_factory = sqlite3.Row
        conexao.execute("PRAGMA foreign_keys = ON")
        return conexao

    with closing(conectar()) as conexao:
        conexao.executescript((ROOT / "schema.sql").read_text(encoding="utf-8"))

    def persistir(view, *, grava=False, carrega_historico=False):
        @wraps(view)
        def executar(*args, **kwargs):
            # A API usa listas globais. Serializa seu uso dentro de cada processo.
            with lock, closing(conectar()) as conexao, conexao:
                conexao.execute("BEGIN IMMEDIATE" if grava else "BEGIN")
                api.pets = [
                    dict(row) for row in conexao.execute(
                        "SELECT nome, especie, porte, tutor, banhos_pagos FROM pets ORDER BY id"
                    )
                ]
                api.historico = []
                if carrega_historico:
                    api.historico = [
                        {
                            "pet": row["nome"],
                            "tutor": row["tutor"],
                            "servicos": json.loads(row["servicos"]),
                            "desconto_combo": row["desconto_centavos"] / 100,
                            "banho_gratis": bool(row["banho_gratis"]),
                            "total": row["total_centavos"] / 100,
                            "banhos_para_gratis": row["banhos_para_gratis"],
                        }
                        for row in conexao.execute("""
                            SELECT p.nome, a.*
                            FROM atendimentos AS a JOIN pets AS p ON p.id = a.pet_id
                            ORDER BY a.id
                        """)
                    ]
                try:
                    resposta = app.make_response(view(*args, **kwargs))
                    if grava and resposta.status_code == 201:
                        if view.__name__ == "cadastrar_pet":
                            pet = api.pets[-1]
                            conexao.execute("""
                                INSERT INTO pets
                                    (nome, nome_normalizado, especie, porte, tutor, banhos_pagos)
                                VALUES (:nome, :nome_normalizado, :especie, :porte, :tutor, :banhos_pagos)
                            """, {**pet, "nome_normalizado": pet["nome"].lower()})
                        else:
                            atendimento = api.historico[-1]
                            pet = api.buscar_pet(atendimento["pet"])
                            pet_id = conexao.execute("""
                                UPDATE pets SET banhos_pagos = ?
                                WHERE nome_normalizado = ? RETURNING id
                            """, (pet["banhos_pagos"], pet["nome"].lower())).fetchone()["id"]
                            conexao.execute("""
                                INSERT INTO atendimentos
                                    (pet_id, tutor, servicos, desconto_centavos,
                                     banho_gratis, total_centavos, banhos_para_gratis)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (
                                pet_id, atendimento["tutor"], json.dumps(atendimento["servicos"]),
                                round(atendimento["desconto_combo"] * 100),
                                atendimento["banho_gratis"], round(atendimento["total"] * 100),
                                atendimento["banhos_para_gratis"],
                            ))
                    return resposta
                finally:
                    api.pets = []
                    api.historico = []

        return executar

    for endpoint in ("listar_pets", "get_pet", "simular_atendimento",
                     "cadastrar_pet", "registrar_atendimento", "get_historico"):
        app.view_functions[endpoint] = persistir(
            app.view_functions[endpoint],
            grava=endpoint in ("cadastrar_pet", "registrar_atendimento"),
            carrega_historico=endpoint == "get_historico",
        )

    @app.get("/")
    def pagina():
        return send_from_directory(FRONTEND, "index.html")

    @app.get("/script.js")
    @app.get("/style.css")
    def recurso():
        return send_from_directory(FRONTEND, request.path[1:])

    return app


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inicia o Petclean com SQLite.")
    parser.add_argument("--banco", type=Path, default=ROOT / "petclean.sqlite3")
    parser.add_argument("--porta", type=int, default=5000)
    args = parser.parse_args()
    criar_app(args.banco).run(host="127.0.0.1", port=args.porta)
