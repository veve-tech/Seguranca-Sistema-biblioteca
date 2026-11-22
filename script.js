
const API = "http://127.0.0.1:8000";

const formulario = document.querySelector("#formLivro");
const lista = document.querySelector("#listaLivros");
const mensagem = document.querySelector("#mensagem");

async function carregarLivros() {
  try {
    const resposta = await fetch(`${API}/livros/`);
    if (!resposta.ok) throw new Error();

    const dados = await resposta.json();
    lista.innerHTML = "";

    if (dados.livros.length === 0) {
      lista.textContent = "Nenhum livro cadastrado.";
      return;
    }

    dados.livros.forEach(livro => {
      const card = document.createElement("article");
      card.className = "livro";

      const capa = document.createElement("img");
      capa.src = `https://covers.openlibrary.org/b/isbn/${encodeURIComponent(livro.isbn)}-M.jpg`;
      capa.alt = `Capa de ${livro.titulo}`;
      capa.onerror = () => {
        capa.onerror = null;
        capa.src = "https://placehold.co/200x280?text=Sem+capa";
      };

      const titulo = document.createElement("h3");
      titulo.textContent = livro.titulo;

      const autor = document.createElement("p");
      autor.textContent = `Autor: ${livro.autor}`;

      const ano = document.createElement("p");
      ano.textContent = `Ano: ${livro.ano_publicacao}`;

      const excluir = document.createElement("button");
      excluir.textContent = "Excluir livro";
      excluir.onclick = () => excluirLivro(livro.id);

      card.append(capa, titulo, autor, ano, excluir);
      lista.appendChild(card);
    });

  } catch {
    lista.textContent = "Não foi possível conectar ao servidor.";
  }
}

formulario.addEventListener("submit", async event => {
  event.preventDefault();

  const dados = {
    titulo: formulario.querySelector('[name="titulo"]').value.trim(),
    autor: formulario.querySelector('[name="autor"]').value.trim(),
    isbn: formulario.querySelector('[name="isbn"]').value.trim(),
    ano_publicacao: Number(formulario.querySelector('[name="ano_publicacao"]').value)
  };

  try {
    const resposta = await fetch(`${API}/livros/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados)
    });

    if (!resposta.ok) throw new Error();

    mensagem.textContent = "Livro cadastrado com sucesso!";
    mensagem.style.color = "green";
    formulario.reset();
    carregarLivros();

  } catch {
    mensagem.textContent = "Erro ao cadastrar. Verifique o servidor.";
    mensagem.style.color = "red";
  }
});

async function excluirLivro(id) {
  if (!confirm("Deseja excluir este livro?")) return;

  try {
    const resposta = await fetch(`${API}/livros/${id}`, {
      method: "DELETE"
    });

    if (!resposta.ok) throw new Error();
    carregarLivros();

  } catch {
    alert("Não foi possível excluir o livro.");
  }
}

carregarLivros();
