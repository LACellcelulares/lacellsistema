from flask import Flask, render_template, request, redirect, session, send_file
import os, json, sqlite3
from datetime import datetime

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

app = Flask(__name__)
app.secret_key = "lacell_secret"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PASTA_PDF = os.path.join(BASE_DIR, "pdfs")
os.makedirs(PASTA_PDF, exist_ok=True)

# ---------------- BANCO ----------------

DB_PATH = os.path.join(BASE_DIR, "os.db")

def conectar():
    return sqlite3.connect(DB_PATH)

def criar_tabela():
    conn = conectar()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS os (
        numero TEXT PRIMARY KEY,
        dados TEXT
    )
    """)

    conn.commit()
    conn.close()

criar_tabela()

def salvar_os(o):
    conn = conectar()
    c = conn.cursor()

    c.execute("""
    INSERT OR REPLACE INTO os (numero, dados)
    VALUES (?, ?)
    """, (o["numero"], json.dumps(o)))

    conn.commit()
    conn.close()

def deletar_os(numero):
    conn = conectar()
    c = conn.cursor()

    c.execute("DELETE FROM os WHERE numero = ?", (numero,))

    conn.commit()
    conn.close()

def carregar():
    conn = conectar()
    c = conn.cursor()

    c.execute("SELECT dados FROM os")
    rows = c.fetchall()

    conn.close()

    return [json.loads(r[0]) for r in rows]

# ---------------- USUÁRIOS ----------------

USUARIOS = {
    "pytty": {"senha": "diemfafa", "loja": "L&A CELL Celulares", "whats": "(11)98083-3734"},
    "adriano": {"senha": "jesus", "loja": "MILLENNIUM SOLUTIONS ATIBAIA", "whats": "(11)99846-8349"}
}

# ---------------- PDF ----------------

def senha9():
    t = Table([["○"]*3 for _ in range(3)], 15, 15)
    t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),1,colors.black)]))
    return t

def horario_funcionamento():
    return """
    <font size=7>
    Horário:<br/>
    Seg a Qua: 09:00–17:30<br/>
    Quinta: 12:00–17:30<br/>
    Sexta: 09:00–17:30<br/>
    Sábado: 09:00–14:00<br/>
    Domingo: Fechado
    </font>
    """

def gerar_pdf(numero, d):
    caminho = os.path.join(PASTA_PDF, f"OS_{numero}.pdf")

    doc = SimpleDocTemplate(
        caminho,
        pagesize=A4,
        leftMargin=15,
        rightMargin=15,
        topMargin=10,
        bottomMargin=10
    )

    styles = getSampleStyleSheet()

    def bloco(titulo):
        el = []

        if session.get("usuario") == "pytty":
            tabela = Table([
                [Paragraph(f"<b>{titulo}</b>", styles["Heading4"]),
                 Paragraph(horario_funcionamento(), styles["Normal"])]
            ], colWidths=[350,150])

            el.append(tabela)
        else:
            el.append(Paragraph(f"<b>{titulo}</b>", styles["Heading4"]))

        el.append(Paragraph(d.get("loja",""), styles["Normal"]))
        el.append(Paragraph(f"WhatsApp: {d.get('whats','')}", styles["Normal"]))
        el.append(Spacer(1,4))

        for x in [
            f"OS Nº {numero}",
            f"Data: {d.get('data','')}",
            f"Cliente: {d.get('cliente','')}",
            f"Telefone: {d.get('telefone','')}",
            f"Defeito: {d.get('defeito','')}",
            f"Valor: R$ {d.get('valor',0)}",
            f"Restante: R$ {d.get('restante',0)}"
        ]:
            el.append(Paragraph(x, styles["Normal"]))

        return el

    elementos = []
    elementos.extend(bloco("VIA CLIENTE"))
    elementos.append(Spacer(1,20))
    elementos.extend(bloco("VIA LOJA"))

    doc.build(elementos)
    return caminho

# ---------------- ROTAS ----------------

@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        usuario = (request.form.get("usuario") or "").lower()
        senha = request.form.get("senha") or ""

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

    usuario = session["usuario"]
    loja = USUARIOS[usuario]["loja"]

    lista = [o for o in carregar() if o.get("loja") == loja]
    return render_template("painel.html", total_os=len(lista))

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
            "defeito": request.form.get("defeito"),
            "valor": v,
            "sinal": s,
            "restante": v - s,
            "status": "pago" if (v - s) <= 0 else "aberto",
            "data": datetime.now().strftime("%Y-%m-%d"),
            "loja": USUARIOS[usuario]["loja"],
            "whats": USUARIOS[usuario]["whats"]
        }

        salvar_os(d)

        pdf = gerar_pdf(n, d)
        return send_file(pdf, as_attachment=True)

    return render_template("nova_os.html")

@app.route("/historico")
def historico():
    if not session.get("logado"):
        return redirect("/")

    usuario = session["usuario"]
    loja = USUARIOS[usuario]["loja"]

    lista = [o for o in carregar() if o.get("loja") == loja]

    return render_template("historico.html", lista=lista)

@app.route("/financeiro")
def financeiro():
    if not session.get("logado"):
        return redirect("/")

    usuario = session["usuario"]
    loja = USUARIOS[usuario]["loja"]

    lista = [o for o in carregar() if o.get("loja") == loja]

    total = sum(float(o.get("valor",0)) for o in lista)

    return render_template("financeiro.html",
        lista=lista,
        total=total,
        total_aberto=0,
        custo=0,
        frete=0,
        lucro=total,
        lucro_por_dia={}
    )

@app.route("/cancelar/<numero>")
def cancelar(numero):
    deletar_os(numero)
    return redirect("/financeiro")

@app.route("/sair")
def sair():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
