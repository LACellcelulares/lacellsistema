from flask import Flask, render_template, request, redirect, session, send_file
import os, json
from datetime import datetime
import pytz

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)
app.secret_key = "lacell_secret"

USUARIOS = {
    "admin": {
        "senha": "123",
        "loja": "Minha Loja",
        "whatsapp": "(11) 99999-9999"
    }
}

ARQUIVO_DB = "os.json"
PASTA_PDF = "pdfs"
os.makedirs(PASTA_PDF, exist_ok=True)

def agora_br():
    fuso = pytz.timezone("America/Sao_Paulo")
    return datetime.now(fuso)

def carregar_os():
    if not os.path.exists(ARQUIVO_DB):
        return []
    with open(ARQUIVO_DB, "r") as f:
        return json.load(f)

def salvar_lista(lista):
    with open(ARQUIVO_DB, "w") as f:
        json.dump(lista, f, indent=2)

def salvar_os(d):
    lista = carregar_os()
    lista.append(d)
    salvar_lista(lista)

# ================= PDF =================
def gerar_pdf_os(numero, dados, loja, whatsapp):
    caminho = os.path.join(PASTA_PDF, f"OS_{numero}.pdf")
    styles = getSampleStyleSheet()
    normal = styles["Normal"]

    doc = SimpleDocTemplate(caminho, pagesize=A4)
    el = []

    def bloco(titulo):
        el.append(Paragraph(f"<b>{titulo}</b>", styles["Heading3"]))
        el.append(Paragraph(loja, normal))
        el.append(Paragraph(f"WhatsApp: {whatsapp}", normal))
        el.append(Spacer(1,10))

        linhas = [
            f"OS: {numero}",
            f"Data: {dados['data']}",
            f"Cliente: {dados['cliente']}",
            f"Telefone: {dados['telefone']}",
            f"Aparelho: {dados['aparelho']}",
            f"Defeito: {dados['defeito']}",
            f"Valor: R$ {dados['valor']}",
            f"Sinal: R$ {dados['sinal']}",
            f"Restante: R$ {dados['restante']}",
            f"Garantia: {dados['garantia']}",
            f"Senha: {dados['senha']}",
        ]

        for l in linhas:
            el.append(Paragraph(l, normal))

        el.append(Spacer(1,20))

    bloco("VIA DO CLIENTE")
    el.append(Spacer(1,20))
    bloco("VIA DA LOJA")

    doc.build(el)
    return caminho

# ================= ROTAS =================

@app.route("/", methods=["GET","POST"])
def login():
    if request.method=="POST":
        u = request.form["usuario"]
        s = request.form["senha"]

        if u in USUARIOS and USUARIOS[u]["senha"] == s:
            session["logado"] = True
            session["usuario"] = u
            return redirect("/painel")

    return render_template("login.html")

@app.route("/painel")
def painel():
    if not session.get("logado"):
        return redirect("/")

    lista = carregar_os()
    total = len(lista)
    valor = sum(float(o["valor"]) for o in lista)

    return render_template("painel.html", total_os=total, total_valor=valor)

@app.route("/nova", methods=["GET","POST"])
def nova():
    if not session.get("logado"):
        return redirect("/")

    if request.method=="POST":
        numero = agora_br().strftime("%Y%m%d%H%M%S")

        valor = float(request.form.get("valor") or 0)
        sinal = float(request.form.get("sinal") or 0)

        d = {
            "numero": numero,
            "cliente": request.form.get("cliente"),
            "telefone": request.form.get("telefone"),
            "aparelho": request.form.get("aparelho"),
            "defeito": request.form.get("defeito"),
            "valor": valor,
            "sinal": sinal,
            "restante": valor - sinal,
            "custo": float(request.form.get("custo") or 0),
            "frete": float(request.form.get("frete") or 0),
            "garantia": request.form.get("garantia") or "Sem garantia",
            "senha": request.form.get("senha"),
            "data": agora_br().strftime("%d/%m/%Y %H:%M")
        }

        salvar_os(d)

        pdf = gerar_pdf_os(numero, d, "Minha Loja", "(11)99999")
        return send_file(pdf, as_attachment=True)

    return render_template("nova_os.html")

@app.route("/historico")
def historico():
    if not session.get("logado"):
        return redirect("/")

    lista = carregar_os()
    return render_template("historico.html", lista=lista)

@app.route("/os/<numero>")
def ver_os(numero):
    lista = carregar_os()
    o = next((x for x in lista if x["numero"]==numero), None)

    pdf = gerar_pdf_os(numero, o, "Minha Loja", "(11)99999")
    return send_file(pdf)

# ===== FINANCEIRO =====
@app.route("/financeiro")
def financeiro():
    lista = carregar_os()

    total = sum(float(o["valor"]) for o in lista)
    custo = sum(float(o["custo"]) + float(o["frete"]) for o in lista)
    aberto = sum(float(o["restante"]) for o in lista)

    return render_template("financeiro.html",
        lista=lista,
        total=total,
        custo=custo,
        lucro=total-custo,
        aberto=aberto
    )

# ===== EDITAR =====
@app.route("/editar/<numero>", methods=["GET","POST"])
def editar(numero):
    lista = carregar_os()
    o = next((x for x in lista if x["numero"]==numero), None)

    if request.method=="POST":
        o["valor"] = float(request.form.get("valor"))
        o["sinal"] = float(request.form.get("sinal"))
        o["restante"] = o["valor"] - o["sinal"]

        salvar_lista(lista)
        return redirect("/financeiro")

    return render_template("editar.html", o=o)

# ===== RELATORIO =====
@app.route("/relatorio")
def relatorio():
    lista = carregar_os()
    return str(len(lista))  # simples só pra não dar erro

@app.route("/relatorio-dia")
def relatorio_dia():
    return "OK"

@app.route("/sair")
def sair():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
