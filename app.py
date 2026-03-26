from flask import Flask, render_template, request, redirect, session, send_file, abort
import os, json
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# ===============================
# CONFIG
# ===============================
app = Flask(__name__)
app.secret_key = "lacell_secret"

USUARIOS = {
    "pytty": {"senha": "diemfafa", "loja": "L&A CELL"},
    "adriano": {"senha": "jesus", "loja": "Millenium"}
}

PASTA_PDF = "pdfs"
ARQUIVO_DB = "os.json"
os.makedirs(PASTA_PDF, exist_ok=True)

# ===============================
# BANCO JSON
# ===============================
def carregar_os():
    if not os.path.exists(ARQUIVO_DB):
        return []
    with open(ARQUIVO_DB, "r") as f:
        return json.load(f)

def salvar_os(d):
    lista = carregar_os()
    lista.append(d)
    with open(ARQUIVO_DB, "w") as f:
        json.dump(lista, f, indent=2)

# ===============================
# PDF (2 vias)
# ===============================
def desenhar_padrao():
    pontos = [["○"] * 3 for _ in range(3)]
    t = Table(pontos, 18, 18)
    t.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER')
    ]))
    return t

def gerar_pdf_os(numero, dados, loja):
    caminho = os.path.join(PASTA_PDF, f"OS_{numero}.pdf")

    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    normal.fontSize = 9

    doc = SimpleDocTemplate(caminho, pagesize=A4)
    elementos = []

    def bloco(titulo):
        elementos.append(Paragraph(f"<b>{titulo}</b>", styles["Heading4"]))
        elementos.append(Spacer(1, 5))

        linhas = [
            f"OS Nº {numero}",
            f"Data: {dados['data']}",
            f"Cliente: {dados['cliente']}",
            f"Aparelho: {dados['aparelho']}",
            f"Defeito: {dados['defeito']}",
            f"Valor: R$ {dados['valor']}",
            f"Sinal: R$ {dados['sinal']}",
            f"Restante: R$ {dados['restante']}",
            f"Garantia: {dados['garantia']}",
            f"Senha: {dados['senha']}",
        ]

        for l in linhas:
            elementos.append(Paragraph(l, normal))

        elementos.append(Spacer(1, 6))
        elementos.append(Paragraph("Assinatura: ____________________", normal))

    bloco("VIA CLIENTE")
    elementos.append(Spacer(1, 10))
    elementos.append(Paragraph("-------------------------------", normal))
    elementos.append(Spacer(1, 10))
    bloco("VIA LOJA")

    doc.build(elementos)
    return caminho

# ===============================
# LOGIN
# ===============================
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form.get("usuario")
        s = request.form.get("senha")

        if u in USUARIOS and USUARIOS[u]["senha"] == s:
            session["logado"] = True
            session["usuario"] = u
            return redirect("/painel")

    return render_template("login.html")

# ===============================
# PAINEL
# ===============================
@app.route("/painel")
def painel():
    if not session.get("logado"):
        return redirect("/")

    lista = carregar_os()
    total = len(lista)
    valor = sum(float(o["valor"]) for o in lista)

    return render_template("painel.html", total_os=total, total_valor=valor)

# ===============================
# NOVA OS
# ===============================
@app.route("/nova", methods=["GET","POST"])
def nova():
    if not session.get("logado"):
        return redirect("/")

    if request.method == "POST":
        n = datetime.now().strftime("%Y%m%d%H%M")

        v = float(request.form.get("valor") or 0)
        s = float(request.form.get("sinal") or 0)
        custo = float(request.form.get("custo") or 0)
        frete = float(request.form.get("frete") or 0)

        d = {
            "numero": n,
            "cliente": request.form.get("cliente"),
            "telefone": request.form.get("telefone"),
            "aparelho": request.form.get("aparelho"),
            "defeito": request.form.get("defeito"),
            "valor": v,
            "sinal": s,
            "restante": v - s,
            "custo": custo,
            "frete": frete,
            "garantia": request.form.get("garantia"),
            "senha": request.form.get("senha"),
            "data": datetime.now().strftime("%d/%m/%Y")
        }

        salvar_os(d)

        pdf = gerar_pdf_os(n, d, "Sistema")
        return send_file(pdf, as_attachment=True)

    return render_template("nova_os.html")

# ===============================
# HISTORICO
# ===============================
@app.route("/historico")
def historico():
    if not session.get("logado"):
        return redirect("/")

    lista = carregar_os()
    return render_template("historico.html", lista=lista)

# ===============================
# VER OS
# ===============================
@app.route("/os/<numero>")
def ver_os(numero):
    lista = carregar_os()
    o = next((x for x in lista if x["numero"] == numero), None)

    if not o:
        abort(404)

    pdf = gerar_pdf_os(numero, o, "Sistema")
    return send_file(pdf)

# ===============================
# RELATORIO MENSAL
# ===============================
@app.route("/relatorio")
def relatorio():
    lista = carregar_os()
    mes = datetime.now().strftime("%m-%Y")

    total = sum(float(o["valor"]) for o in lista)

    caminho = os.path.join(PASTA_PDF, f"relatorio_{mes}.txt")
    with open(caminho, "w") as f:
        f.write(f"Relatório {mes}\nTotal: {total}")

    return send_file(caminho, as_attachment=True)

# ===============================
# RELATORIO DIA
# ===============================
@app.route("/relatorio_dia")
def relatorio_dia():
    hoje = datetime.now().strftime("%d/%m/%Y")

    lista = [o for o in carregar_os() if o["data"] == hoje]
    total = sum(float(o["valor"]) for o in lista)

    return render_template("relatorio_dia.html",
        lista=lista,
        total=total,
        qtd=len(lista)
    )

# ===============================
# FINANCEIRO
# ===============================
@app.route("/financeiro_login", methods=["GET","POST"])
def financeiro_login():
    if request.method == "POST":
        if request.form.get("senha") == "1234":
            session["financeiro"] = True
            return redirect("/financeiro")

    return render_template("financeiro_login.html")

@app.route("/financeiro")
def financeiro():
    if not session.get("financeiro"):
        return redirect("/financeiro_login")

    lista = carregar_os()

    total = sum(float(o.get("valor",0)) for o in lista)
    custo = sum(float(o.get("custo",0)) for o in lista)
    frete = sum(float(o.get("frete",0)) for o in lista)
    aberto = sum(float(o.get("restante",0)) for o in lista)

    lucro = total - custo - frete

    return render_template("financeiro.html",
        total=total,
        custo=custo,
        frete=frete,
        lucro=lucro,
        aberto=aberto,
        lista=lista
    )

# ===============================
# SAIR
# ===============================
@app.route("/sair")
def sair():
    session.clear()
    return redirect("/")

# ===============================
# RUN
# ===============================
if __name__ == "__main__":
    app.run(debug=True)
