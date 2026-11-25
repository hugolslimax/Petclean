# Petclean
Projeto simples com Back-end, Front-end e Banco de dados. CODING

## Rodar o Petclean com SQLite

Requisitos: Python 3.10+ com SQLite 3.35+.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python petclean_web.py
```

Abra http://127.0.0.1:5000. O iniciador serve o front-end e as rotas originais
do Flask na mesma origem. Na primeira execução, cria o banco
`petclean.sqlite3` usando `schema.sql`. Use `--banco caminho.sqlite3` para
escolher o arquivo e `--porta 5001` para usar outra porta.

Os cadastros, o histórico e o contador de fidelidade persistem no SQLite.
Os preços e os cálculos vêm da API original. Para usar a versão com persistência,
inicie pelo `petclean_web.py`. Dados de sessões antigas da API em memória
não são importados automaticamente.
