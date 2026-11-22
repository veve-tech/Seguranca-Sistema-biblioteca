from http import HTTPStatus
import sqlite3
from pathlib import Path
from starlette.responses import Response

from fastapi import FastAPI, HTTPException

from schemas import (
    LivroList,
    LivroPublic,
    LivroSchema,
    Message,
)

app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

import re
from urllib.parse import unquote
from fastapi.responses import JSONResponse


@app.middleware("http")
async def waf(request, call_next):

    conteudo = unquote(
        request.url.path + "?" + request.url.query
    ).lower()

    ataques = [
        r"union\s+select",
        r"or\s+1\s*=\s*1",
        r"<script",
        r"javascript:",
        r"\.\./",
        r"onerror\s*=",
    ]

    for ataque in ataques:
        if re.search(ataque, conteudo):
            return JSONResponse(
                status_code=403,
                content={
                    "erro": "Requisição bloqueada pelo WAF"
                }
            )

    return await call_next(request)

# DLP - Data Loss Prevention

@app.middleware("http")
async def dlp(request, call_next):

    response = await call_next(request)

    # Capturar o conteúdo da resposta
    body = b""

    async for chunk in response.body_iterator:
        body += chunk

    conteudo = body.decode("utf-8", errors="ignore")

    # Identificar possíveis CPFs
    padrao_cpf = r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"

    if re.search(padrao_cpf, conteudo):
        return JSONResponse(
            status_code=403,
            content={
                "erro": "Resposta bloqueada pelo DLP",
                "motivo": "Possível exposição de dado pessoal."
            }
        )

    # Devolver resposta normalmente
    headers = {
        chave: valor
        for chave, valor in response.headers.items()
        if chave.lower() not in (
            "content-length",
            "content-encoding",
            "transfer-encoding"
        )
    }

    return Response(
        content=body,
        status_code=response.status_code,
        headers=headers,
        media_type=response.media_type
    )

import sqlite3

conn = sqlite3.connect("biblioteca.db")

conn.execute("""
CREATE TABLE IF NOT EXISTS livros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    autor TEXT NOT NULL,
    isbn TEXT NOT NULL,
    ano_publicacao INTEGER NOT NULL
)
""")

conn.commit()
conn.close()

# Caminho do banco de dados
DB = Path(__file__).with_name('biblioteca.db')


# Conectar ao banco
def conectar():
    return sqlite3.connect(DB)


# Criar tabela automaticamente
def criar_tabela():
    with conectar() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS livros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                autor TEXT NOT NULL,
                isbn TEXT NOT NULL,
                ano_publicacao INTEGER NOT NULL
            )
        """)


criar_tabela()


@app.get('/', status_code=HTTPStatus.OK, response_model=Message)
def read_root():
    return Message(message='Olá, mundo!')


# Cadastrar livro
@app.post(
    '/livros/',
    status_code=HTTPStatus.CREATED,
    response_model=LivroPublic,
)
def create_livro(livro: LivroSchema):
    with conectar() as conn:
        cursor = conn.execute(
            """
            INSERT INTO livros (titulo, autor, isbn, ano_publicacao)
            VALUES (?, ?, ?, ?)
            """,
            (
                livro.titulo,
                livro.autor,
                livro.isbn,
                livro.ano_publicacao,
            ),
        )

        livro_id = cursor.lastrowid

        resultado = conn.execute(
            'SELECT * FROM livros WHERE id = ?',
            (livro_id,),
        ).fetchone()

    return LivroPublic(
        id=resultado[0],
        titulo=resultado[1],
        autor=resultado[2],
        isbn=resultado[3],
        ano_publicacao=resultado[4],
    )


# Listar livros
@app.get('/livros/', response_model=LivroList)
def read_livros():
    with conectar() as conn:
        conn.row_factory = sqlite3.Row
        livros = conn.execute(
            'SELECT * FROM livros'
        ).fetchall()

    return LivroList(livros=[dict(livro) for livro in livros])


# Consultar livro por ID
@app.get('/livros/{livro_id}', response_model=LivroPublic)
def read_livro(livro_id: int):
    with conectar() as conn:
        livro = conn.execute(
            'SELECT * FROM livros WHERE id = ?',
            (livro_id,),
        ).fetchone()

    if livro is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Livro não encontrado',
        )

    return LivroPublic(
        id=livro[0],
        titulo=livro[1],
        autor=livro[2],
        isbn=livro[3],
        ano_publicacao=livro[4],
    )


# Atualizar livro
@app.put('/livros/{livro_id}', response_model=LivroPublic)
def update_livro(livro_id: int, livro: LivroSchema):
    with conectar() as conn:
        cursor = conn.execute(
            """
            UPDATE livros
            SET titulo = ?, autor = ?, isbn = ?, ano_publicacao = ?
            WHERE id = ?
            """,
            (
                livro.titulo,
                livro.autor,
                livro.isbn,
                livro.ano_publicacao,
                livro_id,
            ),
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail='Livro não encontrado',
            )

        resultado = conn.execute(
            'SELECT * FROM livros WHERE id = ?',
            (livro_id,),
        ).fetchone()

    return LivroPublic(
        id=resultado[0],
        titulo=resultado[1],
        autor=resultado[2],
        isbn=resultado[3],
        ano_publicacao=resultado[4],
    )


# Deletar livro
@app.delete('/livros/{livro_id}', response_model=Message)
def delete_livro(livro_id: int):
    with conectar() as conn:
        cursor = conn.execute(
            'DELETE FROM livros WHERE id = ?',
            (livro_id,),
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail='Livro não encontrado',
            )

    return Message(message='Livro deletado')
