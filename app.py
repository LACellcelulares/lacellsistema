from flask import Flask, render_template, request, redirect, session, send_file
import os, json
from datetime import datetime

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

app = Flask(__name__)
app.secret_key = "lacell_secret"

# ===== USUARIOS =====
USUARIOS = {
    "pytty": {
        "senha": "diemfafa",
        "loja": "L&A Cell Celulares",
        "whatsapp": "(11)98083-3734"
    },
    "adriano": {
        "senha": "jesus",
        "loja": "MILLENNIUM SOLUTIONS ATIBAIA",
        "whatsapp": "(11)99846-8349"
    }
}

ARQUIVO_DB = "os.json"
PASTA_PDF = "pdfs"
os.makedirs(PASTA_PDF, exist_ok=True)

def agora():
    return datetime.now().strftime("%d/%m/%Y %H:%M")

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

# ===== SENHA PADRAO =====
def desenhar_padrao():
    pontos = [["●"] * 3 for _ in range(3)]
    t = Table(pontos, 18, 18)
    t.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER')
    ]))
    return t

# ===== PDF =====
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

        el.append(Spacer(1,10))
        el.append(Paragraph("Senha padrão:", normal))
        el.append(desenhar_padrao())

        el.append(Spacer(1,20))

    bloco("VIA DO CLIENTE")
    el.append(Spacer(1,20))
    bloco("VIA DA LOJA")

    doc.build(el)
    return caminho

# ===== LOGIN =====
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

# ===== PAINEL =====
@app.route("/painel")
def painel():
    if not session.get("logado"):
        return redirect("/")

    lista = carregar_os()
    total = len(lista)
    valor = sum(float(o["valor"]) for o in lista)

    return render_template("painel.html", total_os=total, total_valor=valor)

# ===== NOVA OS =====
@app.route("/nova", methods=["GET","POST"])
def nova():
    if not session.get("logado"):
        return redirect("/")

    if request.method=="POST":
        u = session["usuario"]
        loja = USUARIOS[u]["loja"]
        whats = USUARIOS[u]["whatsapp"]

        numero = datetime.now().strftime("%Y%m%d%H%M%S")

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
            "data": agora()
        }

        salvar_os(d)

        pdf = gerar_pdf_os(numero, d, loja, whats)
        return send_file(pdf, as_attachment=True)

    return render_template("nova_os.html")

# ===== HISTORICO =====
@app.route("/historico")
def historico():
    if not session.get("logado"):
        return redirect("/")

    lista = carregar_os()
    return render_template("historico.html", lista=lista)

# ===== VER OS =====
@app.route("/os/<numero>")
def ver_os(numero):
    if not session.get("logado"):
        return redirect("/")

    u = session["usuario"]
    loja = USUARIOS[u]["loja"]
    whats = USUARIOS[u]["whatsapp"]

    lista = carregar_os()
    o = next((x for x in lista if x["numero"]==numero), None)

    pdf = gerar_pdf_os(numero, o, loja, whats)
    return send_file(pdf)

# ===== FINANCEIRO =====
@app.route("/financeiro")
def financeiro():
    if not session.get("logado"):
        return redirect("/")

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
    if not session.get("logado"):
        return redirect("/")

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
    return "Relatório funcionando"

@app.route("/relatorio-dia")
def relatorio_dia():
    return "Relatório do dia funcionando"

# ===== SAIR =====
@app.route("/sair")
def sair():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
