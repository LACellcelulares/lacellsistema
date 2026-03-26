from flask import Flask, render_template, request, redirect, session, send_file, abort
import os, json
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

app = Flask(__name__)
app.secret_key = "lacell_secret"

# ===============================
# USUÁRIOS
# ===============================
USUARIOS = {
    "pytty": {
        "senha": "diemfafa",
        "loja": "L&A CELL Celulares",
        "whatsapp": "(11)98083-3734"
    },
    "adriano": {
        "senha": "jesus",
        "loja": "MILLENNIUM SOLUTIONS ATIBAIA",
        "whatsapp": "(11)99846-8349"
    }
}

# ===============================
# ARQUIVOS
# ===============================
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

def salvar_os(lista):
    with open(ARQUIVO_DB, "w") as f:
        json.dump(lista, f, indent=2)

# ===============================
# PDF COM DUAS VIAS + SENHA 9 PONTOS
# ===============================
def senha_9_pontos():
    pontos = [["○"] * 3 for _ in range(3)]
    t = Table(pontos, 18, 18)
    t.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER')
    ]))
    return t

def gerar_pdf(numero, dados, loja, whatsapp):
    caminho = os.path.join(PASTA_PDF, f"OS_{numero}.pdf")

    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    normal.fontSize = 9

    doc = SimpleDocTemplate(caminho, pagesize=A4)
    elementos = []

    def bloco(titulo):
        elementos.append(Paragraph(f"<b>{titulo}</b>", styles["Heading4"]))
        elementos.append(Spacer(1, 4))

        elementos.append(Paragraph(loja, normal))
        elementos.append(Paragraph(f"WhatsApp: {whatsapp}", normal))

        elementos.append(Spacer(1, 4))

        linhas = [
            f"OS Nº {numero}",
            f"Data: {dados['data']}",
            f"Cliente: {dados['cliente']}",
            f"Telefone: {dados['telefone']}",
            f"Aparelho: {dados['aparelho']}",
            f"Defeito: {dados['defeito']}",
            f"Valor: R$ {dados['valor']:.2f}",
            f"Sinal: R$ {dados['sinal']:.2f}",
            f"Restante: R$ {dados['restante']:.2f}",
            f"Garantia: {dados['garantia']}",
        ]

        for l in linhas:
            elementos.append(Paragraph(l, normal))

        elementos.append(Spacer(1, 6))
        elementos.append(Paragraph("Senha padrão:", normal))
        elementos.append(senha_9_pontos())

        elementos.append(Spacer(1, 6))
        elementos.append(Paragraph("Assinatura Cliente: ____________________", normal))
        elementos.append(Paragraph("Assinatura Loja: ____________________", normal))

    bloco("VIA DO CLIENTE")
    elementos.append(Spacer(1, 10))
    bloco("VIA DA LOJA")

    doc.build(elementos)
    return caminho

# ===============================
# LOGIN
# ===============================
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form.get("usuario","").lower()
        s = request.form.get("senha","")

        if u in USUARIOS and USUARIOS[u]["senha"] == s:
            session["usuario"] = u
            session["logado"] = True
            return redirect("/painel")

        return render_template("login.html", erro="Login inválido")

    return render_template("login.html")

# ===============================
# PAINEL
# ===============================
@app.route("/painel")
def painel():
    if not session.get("logado"):
        return redirect("/")

    u = session["usuario"]
    loja = USUARIOS[u]["loja"]

    lista = [o for o in carregar_os() if o["loja"] == loja]

    total = len(lista)
    valor = sum(o["valor"] for o in lista)

    return render_template("painel.html", total_os=total, total_valor=valor)

# ===============================
# NOVA OS
# ===============================
@app.route("/nova", methods=["GET","POST"])
def nova():
    if not session.get("logado"):
        return redirect("/")

    if request.method == "POST":
        u = session["usuario"]
        loja = USUARIOS[u]["loja"]

        lista = carregar_os()

        numero = datetime.now().strftime("%Y%m%d%H%M%S")

        valor = float(request.form.get("valor") or 0)
        sinal = float(request.form.get("sinal") or 0)
        custo = float(request.form.get("custo") or 0)
        frete = float(request.form.get("frete") or 0)

        dados = {
            "numero": numero,
            "loja": loja,
            "cliente": request.form.get("cliente"),
            "telefone": request.form.get("telefone"),
            "aparelho": request.form.get("aparelho"),
            "defeito": request.form.get("defeito"),
            "valor": valor,
            "sinal": sinal,
            "restante": valor - sinal,
            "custo": custo,
            "frete": frete,
            "garantia": request.form.get("garantia"),
            "data": datetime.now().strftime("%d/%m/%Y %H:%M")
        }

        lista.append(dados)
        salvar_os(lista)

        pdf = gerar_pdf(numero, dados, loja, USUARIOS[u]["whatsapp"])

        return send_file(pdf, as_attachment=True)

    return render_template("nova_os.html")

# ===============================
# HISTÓRICO
# ===============================
@app.route("/historico")
def historico():
    if not session.get("logado"):
        return redirect("/")

    u = session["usuario"]
    loja = USUARIOS[u]["loja"]

    lista = [o for o in carregar_os() if o["loja"] == loja]

    return render_template("historico.html", lista=lista)

# ===============================
# VER OS (ARRUMADO)
# ===============================
@app.route("/os/<numero>")
def ver_os(numero):
    if not session.get("logado"):
        return redirect("/")

    u = session["usuario"]
    loja = USUARIOS[u]["loja"]

    lista = carregar_os()

    os_encontrada = next((o for o in lista if o["numero"] == numero and o["loja"] == loja), None)

    if not os_encontrada:
        abort(404)

    pdf = gerar_pdf(numero, os_encontrada, loja, USUARIOS[u]["whatsapp"])

    return send_file(pdf)

# ===============================
# FINANCEIRO
# ===============================
@app.route("/financeiro")
def financeiro():
    if not session.get("logado"):
        return redirect("/")

    u = session["usuario"]
    loja = USUARIOS[u]["loja"]

    lista = [o for o in carregar_os() if o["loja"] == loja]

    total = sum(o["valor"] for o in lista)
    custo_total = sum(o.get("custo",0) for o in lista)
    frete_total = sum(o.get("frete",0) for o in lista)

    lucro = total - custo_total - frete_total

    return render_template("financeiro.html",
        lista=lista,
        total=total,
        custo=custo_total,
        frete=frete_total,
        lucro=lucro
    )

# ===============================
# RELATÓRIO MENSAL
# ===============================
@app.route("/relatorio")
def relatorio():
    if not session.get("logado"):
        return redirect("/")

    return "Relatório funcionando"

# ===============================
# RELATÓRIO DIA
# ===============================
@app.route("/relatorio_dia")
def relatorio_dia():
    if not session.get("logado"):
        return redirect("/")

    return "Relatório do dia funcionando"

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
