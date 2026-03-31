from flask import Flask, render_template, request, redirect, session, send_file
import os, json
from datetime import datetime

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

app = Flask(__name__)
app.secret_key = "lacell_secret"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_DB = os.path.join(BASE_DIR, "os.json")
PASTA_PDF = os.path.join(BASE_DIR, "pdfs")

os.makedirs(PASTA_PDF, exist_ok=True)

USUARIOS = {
    "pytty": {"senha": "diemfafa", "loja": "L&A CELL Celulares", "whats": "(11)98083-3734"},
    "adriano": {"senha": "jesus", "loja": "MILLENNIUM SOLUTIONS ATIBAIA", "whats": "(11)99846-8349"}
}

# ------------------ BANCO ------------------

def carregar():
    if not os.path.exists(ARQUIVO_DB):
        return []
    try:
        with open(ARQUIVO_DB, "r") as f:
            return json.load(f)
    except:
        return []

def salvar(lista):
    with open(ARQUIVO_DB, "w") as f:
        json.dump(lista, f, indent=2)

    with open("backup_os.json", "w") as f:
        json.dump(lista, f, indent=2)

# ------------------ PDF ------------------

def senha9():
    t = Table([["○"]*3 for _ in range(3)], 15, 15)
    t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),1,colors.black)]))
    return t

def gerar_pdf(numero, d):
    caminho = os.path.join(PASTA_PDF, f"OS_{numero}.pdf")

    doc = SimpleDocTemplate(caminho, pagesize=A4,
        leftMargin=15,rightMargin=15,topMargin=10,bottomMargin=10)

    styles = getSampleStyleSheet()

    def bloco(titulo):
        el = []
        el.append(Paragraph(f"<b>{titulo}</b>", styles["Heading4"]))
        el.append(Paragraph(d.get("loja",""), styles["Normal"]))
        el.append(Paragraph(f"WhatsApp: {d.get('whats','')}", styles["Normal"]))
        el.append(Spacer(1,4))

        status = d.get("status","aberto").upper()

        dados = [
            f"OS Nº {numero}",
            f"Status: {status}",
            f"Data: {d.get('data','')}",
            f"Cliente: {d.get('cliente','')}",
            f"Telefone: {d.get('telefone','')}",
            f"Aparelho: {d.get('aparelho','')}",
            f"Defeito: {d.get('defeito','')}",
            f"<b>Valor: R$ {d.get('valor',0)}</b>",
            f"Sinal: R$ {d.get('sinal',0)}",
            f"<b>Restante: R$ {d.get('restante',0)}</b>",
            f"Senha: {d.get('senha','')}",
        ]

        for x in dados:
            el.append(Paragraph(x, styles["Normal"]))

        el.append(Spacer(1,4))
        el.append(senha9())
        el.append(Spacer(1,6))
        el.append(Paragraph("Assinatura: ____________________", styles["Normal"]))

        return el

    linha = Table([[""]], colWidths=[520])
    linha.setStyle(TableStyle([('LINEABOVE',(0,0),(-1,-1),1,colors.black)]))

    elementos = []
    elementos.extend(bloco("VIA CLIENTE"))
    elementos.append(Spacer(1,10))
    elementos.append(linha)
    elementos.append(Spacer(1,10))
    elementos.extend(bloco("VIA LOJA"))

    doc.build(elementos)
    return caminho

# ------------------ ROTAS ------------------

@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = (request.form.get("usuario") or "").lower()
        s = request.form.get("senha") or ""

        if u in USUARIOS and USUARIOS[u]["senha"] == s:
            session["logado"] = True
            session["usuario"] = u
            session["fin_ok"] = False
            return redirect("/painel")

    return render_template("login.html")

@app.route("/painel")
def painel():
    if not session.get("logado"):
        return redirect("/")

    loja = USUARIOS[session["usuario"]]["loja"]
    lista = [o for o in carregar() if o.get("loja")==loja]

    return render_template("painel.html", total_os=len(lista))

@app.route("/nova", methods=["GET","POST"])
def nova():
    if not session.get("logado"):
        return redirect("/")

    if request.method == "POST":
        lista = carregar()
        n = datetime.now().strftime("%Y%m%d%H%M%S")

        v = float(request.form.get("valor") or 0)
        s = float(request.form.get("sinal") or 0)
        restante = v - s

        usuario = session["usuario"]

        telefone = request.form.get("telefone") or ""
        telefone = ''.join(filter(str.isdigit, telefone))

        d = {
            "numero": n,
            "cliente": request.form.get("cliente"),
            "telefone": telefone,
            "whats_link": f"https://wa.me/55{telefone}",
            "aparelho": request.form.get("aparelho"),
            "defeito": request.form.get("defeito"),
            "valor": v,
            "sinal": s,
            "restante": restante,
            "status": "pago" if restante <= 0 else "aberto",
            "data": datetime.now().strftime("%Y-%m-%d"),
            "loja": USUARIOS[usuario]["loja"],
            "whats": USUARIOS[usuario]["whats"]
        }

        lista.append(d)
        salvar(lista)

        pdf = gerar_pdf(n, d)
        return send_file(pdf, as_attachment=True)

    return render_template("nova_os.html")

@app.route("/historico")
def historico():
    if not session.get("logado"):
        return redirect("/")

    loja = USUARIOS[session["usuario"]]["loja"]
    lista = [o for o in carregar() if o.get("loja")==loja]

    return render_template("historico.html", lista=lista)

@app.route("/financeiro", methods=["GET","POST"])
def financeiro():
    if not session.get("logado"):
        return redirect("/")

    if not session.get("fin_ok"):
        if request.method == "POST":
            if request.form.get("senha") == "jesus":
                session["fin_ok"] = True
                return redirect("/financeiro")
        return render_template("financeiro_login.html")

    loja = USUARIOS[session["usuario"]]["loja"]
    lista = [o for o in carregar() if o.get("loja")==loja]

    mes = request.args.get("mes")

    if mes:
        lista = [o for o in lista if o.get("data","")[5:7] == mes]

    total = sum(float(o.get("valor",0))-float(o.get("restante",0)) for o in lista)
    total_aberto = sum(float(o.get("restante",0)) for o in lista)

    return render_template("financeiro.html",
        lista=lista,
        total=total,
        total_aberto=total_aberto
    )

@app.route("/receber/<numero>", methods=["POST"])
def receber(numero):
    lista = carregar()
    valor = float(request.form.get("valor") or 0)

    for o in lista:
        if o["numero"] == numero:
            o["restante"] -= valor
            if o["restante"] <= 0:
                o["restante"] = 0
                o["status"] = "pago"

    salvar(lista)
    return redirect("/financeiro")

@app.route("/pagar/<numero>")
def pagar(numero):
    lista = carregar()
    for o in lista:
        if o["numero"] == numero:
            o["restante"] = 0
            o["status"] = "pago"
    salvar(lista)
    return redirect("/financeiro")

@app.route("/cancelar/<numero>")
def cancelar(numero):
    lista = [o for o in carregar() if o["numero"] != numero]
    salvar(lista)
    return redirect("/financeiro")

@app.route("/sair")
def sair():
    session.clear()
    return redirect("/")
    
if __name__ == "__main__":
    app.run(debug=True)
