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
    "pytty": {
        "senha": "diemfafa",
        "loja": "L&A CELL",
        "whatsapp": "11980833734"
    },
    "adriano": {
        "senha": "jesus",
        "loja": "Millenium Solutions",
        "whatsapp": "11998468349"
    }
}

PASTA_PDF = "pdfs"
ARQUIVO_DB = "os.json"
os.makedirs(PASTA_PDF, exist_ok=True)

# ===============================
# BANCO
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
# SENHA 9 PONTOS
# ===============================
def desenhar_padrao():
    pontos = [["●"] * 3 for _ in range(3)]
    t = Table(pontos, 18, 18)
    t.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER')
    ]))
    return t

# ===============================
# PDF OS (DUAS VIAS)
# ===============================
def gerar_pdf_os(numero, dados, loja, whatsapp):
    caminho = os.path.join(PASTA_PDF, f"OS_{numero}.pdf")

    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    normal.fontSize = 9
    h4 = styles["Heading4"]

    doc = SimpleDocTemplate(caminho, pagesize=A4)
    elementos = []

    def bloco(titulo):
        elementos.append(Paragraph(f"<b>{titulo}</b>", h4))
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
            f"Senha: {dados['senha']}",
        ]

        for l in linhas:
            elementos.append(Paragraph(l, normal))

        elementos.append(Spacer(1, 5))
        elementos.append(Paragraph("Senha padrão:", normal))
        elementos.append(desenhar_padrao())
        elementos.append(Spacer(1, 10))

    bloco("VIA DO CLIENTE")
    elementos.append(Spacer(1, 10))
    elementos.append(Paragraph("------------------------------------------------------", normal))
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
        u = request.form["usuario"]
        s = request.form["senha"]

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

        numero = datetime.now().strftime("%Y%m%d%H%M")

        valor = float(request.form.get("valor") or 0)
        sinal = float(request.form.get("sinal") or 0)

        custo = float(request.form.get("custo","0").replace("R$","").replace(".","").replace(",",".") or 0)
        frete = float(request.form.get("frete","0").replace("R$","").replace(".","").replace(",",".") or 0)

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
            "senha": request.form.get("senha"),
            "data": datetime.now().strftime("%d/%m/%Y %H:%M")
        }

        salvar_os(dados)

        pdf = gerar_pdf_os(numero, dados, loja, USUARIOS[u]["whatsapp"])
        return send_file(pdf, as_attachment=True)

    return render_template("nova_os.html")

# ===============================
# HISTORICO
# ===============================
@app.route("/historico")
def historico():
    if not session.get("logado"):
        return redirect("/")

    u = session["usuario"]
    loja = USUARIOS[u]["loja"]

    lista = [o for o in carregar_os() if o["loja"] == loja]

    return render_template("historico.html", lista=lista, busca="")

# ===============================
# VER OS (CORRIGIDO)
# ===============================
@app.route("/os/<numero>")
def ver_os(numero):
    if not session.get("logado"):
        return redirect("/")

    u = session["usuario"]
    loja = USUARIOS[u]["loja"]

    o = next((x for x in carregar_os() if x["numero"] == numero and x["loja"] == loja), None)

    if not o:
        abort(404)

    pdf = gerar_pdf_os(numero, o, loja, USUARIOS[u]["whatsapp"])
    return send_file(pdf)

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
