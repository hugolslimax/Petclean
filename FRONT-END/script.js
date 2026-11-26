// ==============================
// CONFIGURAÇÃO DA API
// Endereço base do servidor Flask
// ==============================
const API = "";
const moeda = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const nomes = { banho: "Banho", tosa: "Tosa", hidratacao: "Hidratação", medio: "Médio" };
let banhosParaGratis = 10;


// ==============================
// FUNÇÃO: CARREGAR TABELA DE PREÇOS
// Busca os preços na API e monta a tabela na página
// ==============================
async function carregarPrecos() {
  const resposta = await fetch(`${API}/precos`);
  if (!resposta.ok) throw new Error("Falha ao consultar preços.");
  const dados = await resposta.json();

  const precos = dados.precos;
  banhosParaGratis = dados.banhos_para_gratis;
  const container = document.getElementById("tabela-precos");

  // Monta uma tabela para cada serviço disponível
  let html = "";
  for (const servico of ["banho", "tosa", "hidratacao"]) {
    html += `<table>
      <tr>
        <th colspan="2">${capitalizar(servico)}</th>
      </tr>`;

    for (const porte of ["pequeno", "medio", "grande"]) {
      html += `<tr>
        <td>${capitalizar(porte)}</td>
        <td>${moeda.format(precos[servico][porte])}</td>
      </tr>`;
    }

    html += `</table>`;
  }

  container.innerHTML = html;
}


// ==============================
// FUNÇÃO: CADASTRAR PET
// Lê os campos do formulário e envia para a API
// ==============================
async function cadastrarPet() {
  const nome    = document.getElementById("nome").value.trim();
  const tutor   = document.getElementById("tutor").value.trim();
  const especie = document.getElementById("especie").value;
  const porte   = document.getElementById("porte").value;
  const msg     = document.getElementById("msg-cadastro");

  // Validação básica no front: não envia se campos obrigatórios estiverem vazios
  if (!nome || !tutor) {
    msg.style.color = "#c0392b";
    msg.textContent = "Preencha o nome do pet e do tutor.";
    return;
  }

  // Envia os dados para a API via POST
  const resposta = await fetch(`${API}/pets`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ nome, tutor, especie, porte })
  });

  const dados = await resposta.json();

  if (resposta.ok) {
    msg.style.color = "#2d7a2d";
    msg.textContent = `✅ ${dados.nome} cadastrado com sucesso!`;

    // Limpa os campos após o cadastro
    document.getElementById("nome").value  = "";
    document.getElementById("tutor").value = "";

  } else {
    msg.style.color = "#c0392b";
    msg.textContent = `❌ ${dados.erro}`;
  }
}


// ==============================
// FUNÇÃO: CARREGAR LISTA DE PETS
// Busca todos os pets cadastrados e exibe como cards
// ==============================
async function carregarPets() {
  const resposta = await fetch(`${API}/pets`);
  if (!resposta.ok) throw new Error("Falha ao consultar pets.");
  const pets = await resposta.json();
  const container = document.getElementById("lista-pets-conteudo");

  if (pets.length === 0) {
    container.innerHTML = `<p class="vazio">Nenhum pet cadastrado ainda.</p>`;
    return;
  }

  let html = "";
  for (const pet of pets) {
    const faltam = Math.max(0, banhosParaGratis - pet.banhos_pagos);
    const fidelidade = faltam === 0 ? "Próximo banho grátis" :
      faltam === 1 ? "Falta 1 banho para ganhar um grátis" :
      `Faltam ${faltam} banhos para ganhar um grátis`;

    html += `
      <div class="pet-card">
        <div>
          <strong>${escaparHtml(pet.nome)}</strong><br>
          <span>${capitalizar(pet.especie)} · ${capitalizar(pet.porte)} · Tutor: ${escaparHtml(pet.tutor)}</span>
        </div>
        <span class="badge-fidelidade">🐾 ${fidelidade}</span>
      </div>`;
  }

  container.innerHTML = html;
}


// ==============================
// FUNÇÃO: SIMULAR ATENDIMENTO
// Calcula o valor sem registrar e exibe o resultado
// ==============================
async function carregarPetsAtendimento() {
  const seletor = document.getElementById("pet-atend");
  const anterior = seletor.value;
  seletor.disabled = true;
  seletor.replaceChildren(new Option("Carregando pets…", ""));

  try {
    const resposta = await fetch(`${API}/pets`);
    if (!resposta.ok) throw new Error("Falha ao consultar pets.");
    const pets = await resposta.json();
    seletor.replaceChildren(new Option(pets.length ? "Selecione um pet" : "Nenhum pet cadastrado", ""));
    for (const pet of pets) {
      seletor.add(new Option(`${pet.nome} · Tutor: ${pet.tutor}`, String(pet.id)));
    }
    if ([...seletor.options].some(opcao => opcao.value === anterior)) {
      seletor.value = anterior;
    }
    seletor.disabled = pets.length === 0;
  } catch {
    seletor.replaceChildren(new Option("Não foi possível carregar os pets", ""));
  }
}

async function simularAtendimento() {
  const petId    = Number(document.getElementById("pet-atend").value);
  const servicos = getServicosSelecionados();
  const msg      = document.getElementById("msg-atendimento");
  const box      = document.getElementById("resultado-simulacao");
  const btnConf  = document.getElementById("btn-confirmar");

  // Oculta botão de confirmar e limpa resultado anterior
  btnConf.style.display = "none";
  box.style.display     = "none";
  msg.textContent        = "";

  if (!petId) {
    msg.style.color = "#c0392b";
    msg.textContent = "Selecione um pet.";
    return;
  }

  if (servicos.length === 0) {
    msg.style.color = "#c0392b";
    msg.textContent = "Selecione pelo menos um serviço.";
    return;
  }

  // Envia a simulação para a API
  const resposta = await fetch(`${API}/atendimentos/simular`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pet_id: petId, servicos })
  });

  const dados = await resposta.json();

  if (resposta.ok) {
    // Monta o resumo da simulação
    let resumo = `<strong>Pet:</strong> ${escaparHtml(dados.pet)}<br>`;
    resumo += `<strong>Serviços:</strong> ${dados.servicos.map(capitalizar).join(", ")}<br>`;

    if (dados.banho_gratis) {
      resumo += `🎉 <strong>Banho grátis</strong> (fidelidade)<br>`;
    }

    if (dados.desconto_combo > 0) {
      resumo += `🏷️ Desconto combo: -${moeda.format(dados.desconto_combo)}<br>`;
    }

    resumo += `<strong>Total: ${moeda.format(dados.total)}</strong>`;

    box.innerHTML    = resumo;
    box.style.display = "block";

    // Exibe o botão de confirmar
    btnConf.style.display = "block";
  } else {
    msg.style.color = "#c0392b";
    msg.textContent = `❌ ${dados.erro}`;
  }
}


// ==============================
// FUNÇÃO: CONFIRMAR ATENDIMENTO
// Registra o atendimento na API (atualiza fidelidade)
// ==============================
async function confirmarAtendimento() {
  const petId    = Number(document.getElementById("pet-atend").value);
  const servicos = getServicosSelecionados();
  const msg      = document.getElementById("msg-atendimento");
  const btnConf  = document.getElementById("btn-confirmar");
  const box      = document.getElementById("resultado-simulacao");

  if (!petId || !servicos.length) return;

  // Envia o registro definitivo para a API
  const resposta = await fetch(`${API}/atendimentos`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pet_id: petId, servicos })
  });

  const dados = await resposta.json();

  if (resposta.ok) {
    msg.style.color = "#2d7a2d";
    msg.textContent = `✅ Atendimento registrado! Total: ${moeda.format(dados.total)}`;

    // Limpa o formulário de atendimento
    document.getElementById("pet-atend").value = "";
    document.getElementById("serv-banho").checked      = false;
    document.getElementById("serv-tosa").checked       = false;
    document.getElementById("serv-hidratacao").checked = false;

    box.style.display      = "none";
    btnConf.style.display  = "none";

  } else {
    msg.style.color = "#c0392b";
    msg.textContent = `❌ ${dados.erro}`;
  }
}


// ==============================
// FUNÇÃO: CARREGAR HISTÓRICO
// Busca todos os atendimentos registrados
// ==============================
async function carregarHistorico() {
  const resposta = await fetch(`${API}/historico`);
  if (!resposta.ok) {
    mostrarErro("historico-conteudo", "Não foi possível carregar o histórico.");
    return;
  }
  const dados = await resposta.json();
  const container = document.getElementById("historico-conteudo");

  if (dados.atendimentos.length === 0) {
    container.innerHTML = `<p class="vazio">Nenhum atendimento registrado.</p>`;
    return;
  }

  let html = "";
  for (const item of dados.atendimentos) {
    html += `
      <div class="historico-card">
        <strong>${escaparHtml(item.pet)}</strong> (tutor: ${escaparHtml(item.tutor)})<br>
        Serviços: ${item.servicos.map(capitalizar).join(", ")}<br>`;

    if (item.banho_gratis) {
      html += `🎉 Banho grátis (fidelidade)<br>`;
    }

    if (item.desconto_combo > 0) {
      html += `Desconto combo: -${moeda.format(item.desconto_combo)}<br>`;
    }

    html += `Total: <strong>${moeda.format(item.total)}</strong>
      </div>`;
  }

  // Exibe faturamento total
  html += `<p class="faturamento-total">💰 Faturamento total: ${moeda.format(dados.faturamento_total)}</p>`;

  container.innerHTML = html;
}


// ==============================
// FUNÇÃO AUXILIAR: SERVIÇOS SELECIONADOS
// Retorna uma lista com os serviços marcados nos checkboxes
// ==============================
function getServicosSelecionados() {
  const servicos = [];
  if (document.getElementById("serv-banho").checked)      servicos.push("banho");
  if (document.getElementById("serv-tosa").checked)       servicos.push("tosa");
  if (document.getElementById("serv-hidratacao").checked) servicos.push("hidratacao");
  return servicos;
}


// ==============================
// FUNÇÃO AUXILIAR: CAPITALIZAR
// Deixa a primeira letra maiúscula
// ==============================
function escaparHtml(texto) {
  const elemento = document.createElement("span");
  elemento.textContent = texto;
  return elemento.innerHTML;
}

function capitalizar(texto) {
  return nomes[texto] ?? (texto.charAt(0).toUpperCase() + texto.slice(1));
}


// ==============================
// INICIALIZAÇÃO
// Carrega os dados ao abrir a página
// ==============================
const paginas = [...document.querySelectorAll("main > .pagina")];
const links = document.querySelectorAll("nav a");

function mostrarErro(id, mensagem) {
  const aviso = document.createElement("p");
  aviso.className = "vazio";
  aviso.textContent = mensagem;
  document.getElementById(id).replaceChildren(aviso);
}

function abrirPagina() {
  const id = location.hash.slice(1);
  const pagina = paginas.find(secao => secao.id === id) ?? paginas[0];

  for (const secao of paginas) {
    secao.hidden = secao !== pagina;
  }
  for (const link of links) {
    if (link.hash === `#${pagina.id}`) {
      link.setAttribute("aria-current", "page");
    } else {
      link.removeAttribute("aria-current");
    }
  }

  if (pagina.id === "precos") {
    carregarPrecos().catch(() => mostrarErro("tabela-precos", "Não foi possível carregar os preços."));
  } else if (pagina.id === "lista-pets") {
    carregarPets().catch(() => mostrarErro("lista-pets-conteudo", "Não foi possível carregar os pets."));
  } else if (pagina.id === "atendimento") {
    carregarPetsAtendimento();
  } else if (pagina.id === "historico") {
    carregarHistorico().catch(() => mostrarErro("historico-conteudo", "Não foi possível carregar o histórico."));
  }
}

window.addEventListener("hashchange", () => {
  abrirPagina();
  window.scrollTo(0, 0);
});
abrirPagina();

document.querySelectorAll("#atendimento select, #atendimento input").forEach(campo => {
  campo.addEventListener("change", () => {
    document.getElementById("resultado-simulacao").style.display = "none";
    document.getElementById("btn-confirmar").style.display = "none";
  });
});
