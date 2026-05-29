from flask import Flask, render_template, Response, request, redirect, session, url_for
from detector_placa import gerar_frames
from database import get_connection
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "senai123"


@app.route("/")
def home():
    if "usuario" not in session:
        return redirect("/login")

    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        senha = request.form["senha"]

        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            "SELECT * FROM usuarios WHERE email = %s",
            (email,)
        )

        usuario = cursor.fetchone()

        cursor.close()
        conn.close()

        if usuario and check_password_hash(usuario["senha"], senha):

            session["usuario"] = usuario["nome"]

            return redirect("/")

        return render_template("login.html", erro="Email ou senha inválidos")

    return render_template("login.html")

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():

    if request.method == "POST":

        nome = request.form["nome"]
        email = request.form["email"]
        senha = request.form["senha"]

        senha_hash = generate_password_hash(senha)

        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # verifica se email já existe
        cursor.execute(
            "SELECT * FROM usuarios WHERE email = %s",
            (email,)
        )

        usuario_existente = cursor.fetchone()

        if usuario_existente:

            cursor.close()
            conn.close()

            return render_template(
                "cadastro.html",
                erro="Este email já está cadastrado."
            )

        # cadastra usuário
        cursor.execute(
            """
            INSERT INTO usuarios (nome, email, senha)
            VALUES (%s, %s, %s)
            """,
            (nome, email, senha_hash)
        )

        conn.commit()

        cursor.close()
        conn.close()

        return redirect("/login")

    return render_template("cadastro.html")


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


@app.route("/video")
def video():

    if "usuario" not in session:
        return redirect("/login")

    return Response(
        gerar_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


@app.route("/historico")
def historico():

    if "usuario" not in session:
        return redirect("/login")

    conn = get_connection()

    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute(
        "SELECT * FROM historico_placas ORDER BY data_hora DESC"
    )

    dados = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("historico.html", dados=dados)


import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)