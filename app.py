import os
import re
import secrets
import sqlite3
from functools import wraps
from pathlib import Path

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from base_conhecimento import BaseConhecimento
from orientacao import Orientacao
from validador_web import analisar_url
from datetime import datetime

ROOT = Path(__file__).resolve().parent
app = Flask(__name__)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax", MAX_CONTENT_LENGTH=1024 * 1024)
INSTANCE = ROOT / "instance"
INSTANCE.mkdir(exist_ok=True)
DB = INSTANCE / "usuarios.db"
KEY_FILE = INSTANCE / "chave.txt"
if not KEY_FILE.exists():
    KEY_FILE.write_text(secrets.token_hex(32), encoding="utf-8")
app.secret_key = KEY_FILE.read_text(encoding="utf-8").strip()

BASE = BaseConhecimento(str(ROOT / "data" / "base_conhecimento.json"))
if not BASE.carregar():
    raise RuntimeError("Não foi possível carregar data/base_conhecimento.json")
LISTA = BASE.orientacoes


def conectar():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def criar_banco():
    with conectar() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL
        )''')
        colunas = [row[1] for row in conn.execute('PRAGMA table_info(usuarios)')]
        if "perfil" not in colunas:
            conn.execute("ALTER TABLE usuarios ADD COLUMN perfil TEXT NOT NULL DEFAULT 'usuario'")
        # Usuários já cadastrados permanecem com o perfil 'usuario'.
        conn.execute('''CREATE TABLE IF NOT EXISTS consultas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            pergunta TEXT NOT NULL DEFAULT '',
            orientacao_id INTEGER,
            encontrou INTEGER NOT NULL DEFAULT 0,
            ajudou INTEGER,
            criado_em TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )''')
        conn.execute("CREATE INDEX IF NOT EXISTS idx_consultas_usuario ON consultas(usuario_id, id DESC)")


criar_banco()


def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)
    return session["csrf_token"]


app.jinja_env.globals["csrf_token"] = csrf_token


@app.before_request
def validar_csrf():
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        recebido = request.form.get("csrf_token", "")
        esperado = session.get("csrf_token", "")
        if not esperado or not secrets.compare_digest(recebido, esperado):
            abort(400, "Formulário inválido. Atualize a página e tente novamente.")


def login_necessario(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "usuario_id" not in session:
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return wrapper


def admin_necessario(func):
    @wraps(func)
    @login_necessario
    def wrapper(*args, **kwargs):
        if session.get("perfil") != "admin":
            abort(403)
        return func(*args, **kwargs)
    return wrapper


def todas_orientacoes():
    itens = []
    atual = LISTA.inicio
    while atual is not None:
        itens.append(atual.orientacao)
        atual = atual.proximo
    return itens


@app.route("/")
def inicio():
    return redirect(url_for("painel" if "usuario_id" in session else "login"))


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if "usuario_id" in session:
        return redirect(url_for("painel"))
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        confirmar = request.form.get("confirmar", "")
        if not nome or not email or not senha:
            flash("Preencha todos os campos.", "erro")
        elif not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
            flash("Informe um e-mail válido.", "erro")
        elif len(senha) < 8:
            flash("A senha precisa ter pelo menos 8 caracteres.", "erro")
        elif senha != confirmar:
            flash("As senhas não coincidem.", "erro")
        else:
            try:
                with conectar() as conn:
                    conn.execute("INSERT INTO usuarios (nome,email,senha,perfil) VALUES (?,?,?,'usuario')",
                                 (nome, email, generate_password_hash(senha)))
                flash("Conta criada! Faça seu login.", "sucesso")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                flash("Este e-mail já está cadastrado.", "erro")
    return render_template("cadastro.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "usuario_id" in session:
        return redirect(url_for("painel"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        with conectar() as conn:
            usuario = conn.execute("SELECT * FROM usuarios WHERE email=?", (email,)).fetchone()
        if usuario and check_password_hash(usuario["senha"], senha):
            session.clear()
            session["usuario_id"] = usuario["id"]
            session["usuario_nome"] = usuario["nome"]
            session["perfil"] = usuario["perfil"]
            return redirect(url_for("painel"))
        flash("E-mail ou senha incorretos.", "erro")
    return render_template("login.html")


@app.post("/sair")
def sair():
    session.clear()
    return redirect(url_for("login"))


@app.get("/painel")
@login_necessario
def painel():
    itens = todas_orientacoes()
    return render_template("painel.html", nome=session["usuario_nome"],
                           categorias=BASE.categorias(), recentes=itens[:3],
                           eh_admin=session.get("perfil") == "admin")


@app.get("/buscar")
@login_necessario
def buscar():
    termo = request.args.get("q", "").strip()[:200]
    resultado_invalido = "@" in termo or sum(ch.isdigit() for ch in termo) >= 8
    if resultado_invalido:
        resultados = []
        flash("Não informe e-mail, CPF ou telefone nas pesquisas.", "erro")
        termo = ""
    else:
        resultados = BASE.buscar(termo) if termo else []
        if termo:
            with conectar() as conn:
                conn.execute(
                    "INSERT INTO consultas (usuario_id, tipo, pergunta, orientacao_id, encontrou) VALUES (?, 'pesquisa', ?, ?, ?)",
                    (session["usuario_id"], termo, resultados[0][1].id if resultados else None, int(bool(resultados)))
                )
    return render_template("buscar.html", termo=termo, resultados=resultados)


@app.get("/categorias")
@login_necessario
def categorias():
    return render_template("categorias.html", categorias=BASE.categorias())


@app.get("/categoria/<path:nome>")
@login_necessario
def categoria(nome):
    if nome not in BASE.categorias():
        abort(404)
    return render_template("categoria.html", nome=nome, itens=BASE.por_categoria(nome))


@app.get("/orientacao/<int:identificador>")
@login_necessario
def detalhe(identificador):
    orientacao = LISTA.buscar(identificador)
    if orientacao is None:
        abort(404)
    # Registra a orientação visualizada para permitir avaliação individual.
    with conectar() as conn:
        cursor = conn.execute(
            "INSERT INTO consultas (usuario_id, tipo, pergunta, orientacao_id, encontrou) VALUES (?, 'orientacao', ?, ?, 1)",
            (session["usuario_id"], orientacao.titulo, orientacao.id)
        )
        consulta_id = cursor.lastrowid
    return render_template("detalhe.html", orientacao=orientacao, consulta_id=consulta_id)


@app.route("/verificar-url", methods=["GET", "POST"])
@login_necessario
def verificar_url_pagina():
    resultado = None
    url = ""
    if request.method == "POST":
        url = request.form.get("url", "").strip()
        resultado = analisar_url(url)
    return render_template("verificar_url.html", url=url, resultado=resultado)


@app.post("/avaliar/<int:consulta_id>")
@login_necessario
def avaliar_resposta(consulta_id):
    resposta = request.form.get("ajudou", "")
    orientacao_id = request.form.get("orientacao_id", "")
    if resposta not in ("sim", "nao"):
        abort(400)
    with conectar() as conn:
        consulta = conn.execute(
            "SELECT orientacao_id, ajudou FROM consultas WHERE id=? AND usuario_id=? AND tipo='orientacao'",
            (consulta_id, session["usuario_id"])
        ).fetchone()
        if consulta is None:
            abort(404)
        if consulta["ajudou"] is None:
            conn.execute(
                "UPDATE consultas SET ajudou=? WHERE id=? AND usuario_id=?",
                (1 if resposta == "sim" else 0, consulta_id, session["usuario_id"])
            )
            flash("Obrigado! Sua avaliação foi registrada.", "sucesso")
        else:
            flash("Esta orientação já foi avaliada.", "erro")
        destino = consulta["orientacao_id"]
    if destino is None or LISTA.buscar(destino) is None:
        return redirect(url_for("historico"))
    return redirect(url_for("detalhe", identificador=destino))


@app.get("/historico")
@login_necessario
def historico():
    with conectar() as conn:
        consultas = conn.execute(
            "SELECT id, tipo, pergunta, orientacao_id, encontrou, ajudou, criado_em FROM consultas "
            "WHERE usuario_id=? ORDER BY id DESC LIMIT 100",
            (session["usuario_id"],)
        ).fetchall()
    return render_template("historico.html", consultas=consultas)


@app.get("/indicadores")
@login_necessario
def indicadores():
    uid = session["usuario_id"]
    with conectar() as conn:
        resumo = conn.execute(
            "SELECT COUNT(*) total, COALESCE(SUM(encontrou),0) encontradas "
            "FROM consultas WHERE usuario_id=? AND tipo='pesquisa'",
            (uid,)
        ).fetchone()
        detalhes = conn.execute(
            "SELECT COUNT(*) total, COUNT(ajudou) avaliadas, "
            "COALESCE(SUM(CASE WHEN ajudou=1 THEN 1 ELSE 0 END),0) positivas "
            "FROM consultas WHERE usuario_id=? AND tipo='orientacao'",
            (uid,)
        ).fetchone()
        recentes = conn.execute(
            "SELECT tipo, pergunta, encontrado, criado_em FROM "
            "(SELECT tipo, pergunta, encontrou AS encontrado, criado_em FROM consultas "
            "WHERE usuario_id=? ORDER BY id DESC LIMIT 5)",
            (uid,)
        ).fetchall()
    total = resumo["total"]
    avaliadas = detalhes["avaliadas"]
    return render_template(
        "indicadores.html", total=total, encontradas=resumo["encontradas"],
        taxa_encontradas=round(100 * resumo["encontradas"] / total, 1) if total else 0,
        visualizacoes=detalhes["total"], avaliadas=avaliadas,
        positivas=detalhes["positivas"],
        taxa_ajuda=round(100 * detalhes["positivas"] / avaliadas, 1) if avaliadas else 0,
        recentes=recentes
    )


@app.get("/admin")
@admin_necessario
def admin():
    return render_template("admin.html", itens=todas_orientacoes())


def campos_orientacao():
    return {
        "titulo": request.form.get("titulo", "").strip(),
        "categoria": request.form.get("categoria", "").strip(),
        "resposta": request.form.get("resposta", "").strip(),
        "publico_alvo": request.form.get("publico_alvo", "").strip(),
        "onde": request.form.get("onde", "").strip(),
        "fonte": request.form.get("fonte", "").strip(),
        "palavras_chave": [p.strip() for p in request.form.get("palavras_chave", "").split(",") if p.strip()],
    }


def validos(campos):
    return all(campos[chave] for chave in ("titulo", "categoria", "resposta", "publico_alvo", "onde", "fonte")) and bool(campos["palavras_chave"])


@app.route("/admin/nova", methods=["GET", "POST"])
@admin_necessario
def admin_nova():
    if request.method == "POST":
        campos = campos_orientacao()
        try:
            identificador = int(request.form.get("id", ""))
            if identificador <= 0:
                raise ValueError()
        except ValueError:
            flash("Informe um ID numérico maior que zero.", "erro")
        else:
            if not validos(campos):
                flash("Preencha todos os campos e informe palavras-chave.", "erro")
            elif LISTA.buscar(identificador) is not None:
                flash("Este ID já existe.", "erro")
            else:
                obj = Orientacao(identificador, campos["categoria"], campos["titulo"],
                                 campos["palavras_chave"], campos["resposta"], [],
                                 campos["onde"], campos["fonte"], "2026-11-16", campos["publico_alvo"])
                if LISTA.inserir(obj) and BASE.salvar():
                    flash("Orientação cadastrada.", "sucesso")
                    return redirect(url_for("admin"))
                flash("Não foi possível salvar a orientação.", "erro")
    return render_template("admin_form.html", orientacao=None)


@app.route("/admin/editar/<int:identificador>", methods=["GET", "POST"])
@admin_necessario
def admin_editar(identificador):
    obj = LISTA.buscar(identificador)
    if obj is None:
        abort(404)
    if request.method == "POST":
        campos = campos_orientacao()
        if not validos(campos):
            flash("Preencha todos os campos e informe palavras-chave.", "erro")
        else:
            for chave, valor in campos.items():
                setattr(obj, chave, valor)
            if BASE.salvar():
                flash("Orientação atualizada.", "sucesso")
                return redirect(url_for("admin"))
            flash("Não foi possível salvar as alterações.", "erro")
    return render_template("admin_form.html", orientacao=obj)


@app.post("/admin/excluir/<int:identificador>")
@admin_necessario
def admin_excluir(identificador):
    if LISTA.remover(identificador):
        if BASE.salvar():
            flash("Orientação excluída.", "sucesso")
        else:
            flash("Erro ao salvar a exclusão.", "erro")
    else:
        flash("Orientação não encontrada.", "erro")
    return redirect(url_for("admin"))


@app.post("/admin/ordenar")
@admin_necessario
def admin_ordenar():
    LISTA.ordenar()  # Bubble Sort desenvolvido na disciplina DSA
    if BASE.salvar():
        flash("Orientações organizadas por título.", "sucesso")
    else:
        flash("Erro ao salvar a ordem.", "erro")
    return redirect(url_for("admin"))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=3001, debug=True, use_reloader=False)
