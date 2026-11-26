CREATE TABLE IF NOT EXISTS pets (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    nome_normalizado TEXT NOT NULL,
    tutor_normalizado TEXT NOT NULL,
    especie TEXT NOT NULL CHECK (especie IN ('cachorro', 'gato')),
    porte TEXT NOT NULL CHECK (porte IN ('pequeno', 'medio', 'grande')),
    tutor TEXT NOT NULL,
    banhos_pagos INTEGER NOT NULL CHECK (banhos_pagos >= 0),
    UNIQUE (nome_normalizado, tutor_normalizado)
);

CREATE TABLE IF NOT EXISTS atendimentos (
    id INTEGER PRIMARY KEY,
    pet_id INTEGER NOT NULL REFERENCES pets(id),
    tutor TEXT NOT NULL,
    servicos TEXT NOT NULL,
    desconto_centavos INTEGER NOT NULL,
    banho_gratis INTEGER NOT NULL CHECK (banho_gratis IN (0, 1)),
    total_centavos INTEGER NOT NULL,
    banhos_para_gratis INTEGER NOT NULL
);
