from flask import Flask, render_template, request, redirect, session, send_file
import os
from datetime import datetime
import psycopg2

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

app = Flask(__name__)
app.secret_key = "lacell_secret"

DATABASE_URL = os.getenv("DATABASE_URL")

USUARIOS = {
    "pytty": {"senha": "diemfafa", "loja": "L&A CELL Celulares", "whats": "(11)98083-3734"},
    "adriano": {"senha": "jesus", "loja": "MILLENNIUM SOLUTIONS ATIBAIA", "whats": "(11)99846-8349"}
}

# ------------------ BANCO ------------------

def conectar():
    return psycopg2.connect(DATABASE_URL)

def criar_tabela():
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS os (
        numero TEXT PRIMARY KEY,
        cliente TEXT,
        telefone TEXT,
        cpf TEXT,
        imei TEXT,
        aparelho TEXT,
        defeito TEXT,
        valor REAL,
        sinal REAL,
        restante REAL,
        custo REAL,
        frete REAL,
        pagamento TEXT,
        entrega TEXT,
        garantia TEXT,
        senha TEXT,
        status TEXT,
        data TEXT,
        loja TEXT,
        whats TEXT
    )
    """)
    conn.commit()
    cur.close()
    conn.close()

def inserir(d):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO os VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, tuple(d.values()))
    conn.commit()
    cur.close()
    conn.close()

def listar(loja):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT * FROM os WHERE loja=%s ORDER BY data DESC", (loja,))
    cols = [desc[0] for desc in cur.description]
    dados = [dict(zip(cols, row)) for row in cur.fetchall()]
    cur.close()
    conn.close()
    return dados

def atualizar(lista):
    conn = conectar()
    cur = conn.cursor()
    for o in lista:
        cur.execute("""
        UPDATE os SET restante=%s, status=%s WHERE numero=%s
        """, (o["restante"], o["status"], o["numero"]))
    conn.commit()
    cur.close()
    conn.close()

def deletar(numero):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("DELETE FROM os WHERE numero=%s", (numero,))
    conn.commit()
    cur.close()
    conn.close()

# ------------------ PDF ------------------

def senha9():
    t = Table([["○"]*3 for _ in range(3)], 15, 15)
    t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),1,colors.black)]))
    return t

def gerar_pdf(numero, d):
    caminho = f"/tmp/OS_{numero}.pdf"

    doc = SimpleDocTemplate(caminho, pagesize=A4)
    styles = getSampleStyleSheet()

    elementos = []
    elementos.append(Paragraph(d["loja"], styles["Heading3"]))
    elementos.append(Paragraph(f"OS Nº {numero}", styles["Normal"]))
    elementos.append(Paragraph(f"Cliente: {d['cliente']}", styles["Normal"]))
    elementos.append(Paragraph(f"Valor: R$ {d['valor']}", styles["Normal"]))
    elementos.append(Spacer(1,10))

    doc.build(elementos)
    return caminho

# ------------------ ROTAS ------------------

@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario").lower()
        senha = request.form.get("senha")

        if usuario in USUARIOS and USUARIOS[usuario]["senha"] == senha:
            session["logado"] = True
            session["usuario"] = usuario
            session["fin_ok"] = False
            return redirect("/painel")

    return render_template("login.html")

@app.route("/painel")
def painel():
    if not session.get("logado"):
        return redirect("/")

    loja = USUARIOS[session["usuario"]]["loja"]
    lista_os = listar(loja)

    return render_template("painel.html", total_os=len(lista_os))

@app.route("/nova", methods=["GET","POST"])
def nova():
    if not session.get("logado"):
        return redirect("/")

    if request.method == "POST":
        n = datetime.now().strftime("%Y%m%d%H%M%S")

        v = float(request.form.get("valor") or 0)
        s = float(request.form.get("sinal") or 0)

        usuario = session["usuario"]

        d = {
            "numero": n,
            "cliente": request.form.get("cliente"),
            "telefone": request.form.get("telefone"),
            "cpf": request.form.get("cpf"),
            "imei": request.form.get("imei"),
            "aparelho": request.form.get("aparelho"),
            "defeito": request.form.get("defeito"),
            "valor": v,
            "sinal": s,
            "restante": v - s,
            "custo": float(request.form.get("custo") or 0),
            "frete": float(request.form.get("frete") or 0),
            "pagamento": request.form.get("pagamento"),
            "entrega": request.form.get("entrega"),
            "garantia": request.form.get("garantia"),
            "senha": request.form.get("senha"),
            "status": "pago" if (v - s) <= 0 else "aberto",
            "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "loja": USUARIOS[usuario]["loja"],
            "whats": USUARIOS[usuario]["whats"]
        }

        inserir(d)

        pdf = gerar_pdf(n, d)
        return send_file(pdf, as_attachment=True)

    return render_template("nova_os.html")

@app.route("/historico")
def historico():
    if not session.get("logado"):
        return redirect("/")

    loja = USUARIOS[session["usuario"]]["loja"]
    lista_os = listar(loja)

    return render_template("historico.html", lista=lista_os)

@app.route("/financeiro")
def financeiro():
    if not session.get("logado"):
        return redirect("/")

    loja = USUARIOS[session["usuario"]]["loja"]
    lista = listar(loja)

    total = sum(float(o["valor"]) - float(o["restante"]) for o in lista)
    total_aberto = sum(float(o["restante"]) for o in lista)

    return render_template("financeiro.html", lista=lista, total=total, total_aberto=total_aberto)

@app.route("/pagar/<numero>")
def pagar(numero):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("UPDATE os SET restante=0, status='pago' WHERE numero=%s", (numero,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect("/financeiro")

@app.route("/cancelar/<numero>")
def cancelar(numero):
    deletar(numero)
    return redirect("/financeiro")

@app.route("/sair")
def sair():
    session.clear()
    return redirect("/")

# 🔥 cria tabela ao iniciar
criar_tabela()

if __name__ == "__main__":
    app.run(debug=True)
