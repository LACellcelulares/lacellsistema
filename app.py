from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "123"

# BANCO
def get_db():
    return sqlite3.connect("banco.db")

# HOME
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        session["logado"] = True
        return redirect("/painel")
    return render_template("login.html")

# PAINEL
@app.route("/painel")
def painel():
    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT COUNT(*) FROM os")
    total_os = cur.fetchone()[0]

    cur.execute("SELECT SUM(valor) FROM os")
    total_valor = cur.fetchone()[0] or 0

    return render_template("painel.html", total_os=total_os, total_valor=total_valor)

# NOVA OS
@app.route("/nova", methods=["GET","POST"])
def nova():
    if request.method == "POST":
        db = get_db()
        cur = db.cursor()

        cur.execute("""
        INSERT INTO os(cliente, valor, sinal, custo, frete)
        VALUES (?,?,?,?,?)
        """, (
            request.form["cliente"],
            float(request.form.get("valor") or 0),
            float(request.form.get("sinal") or 0),
            float(request.form.get("custo") or 0),
            float(request.form.get("frete") or 0)
        ))

        db.commit()
        return redirect("/historico")

    return render_template("nova_os.html")

# HISTORICO
@app.route("/historico")
def historico():
    db = get_db()
    lista = db.execute("SELECT * FROM os").fetchall()
    return render_template("historico.html", lista=lista)

# VER OS
@app.route("/ver/<int:id>")
def ver(id):
    db = get_db()
    os = db.execute("SELECT * FROM os WHERE id=?", (id,)).fetchone()
    return str(os)

# EDITAR
@app.route("/editar/<int:id>", methods=["GET","POST"])
def editar(id):
    db = get_db()

    if request.method == "POST":
        db.execute("""
        UPDATE os SET valor=?, custo=?, frete=?
        WHERE id=?
        """, (
            request.form["valor"],
            request.form["custo"],
            request.form["frete"],
            id
        ))
        db.commit()
        return redirect("/financeiro")

    os = db.execute("SELECT * FROM os WHERE id=?", (id,)).fetchone()
    return f"""
    <form method="post">
    Valor <input name="valor" value="{os[2]}"><br>
    Custo <input name="custo" value="{os[4]}"><br>
    Frete <input name="frete" value="{os[5]}"><br>
    <button>Salvar</button>
    </form>
    """

# FINANCEIRO
@app.route("/financeiro")
def financeiro():
    db = get_db()
    lista = db.execute("SELECT * FROM os").fetchall()
    return render_template("financeiro.html", lista=lista)

# RELATORIO
@app.route("/relatorio")
def relatorio():
    db = get_db()
    total = db.execute("SELECT SUM(valor) FROM os").fetchone()[0] or 0
    return f"Total: {total}"

# RELATORIO DIA
@app.route("/relatorio_dia")
def relatorio_dia():
    db = get_db()
    total = db.execute("SELECT SUM(valor) FROM os").fetchone()[0] or 0
    return f"Hoje: {total}"

# RUN
if __name__ == "__main__":
    app.run(debug=True)
