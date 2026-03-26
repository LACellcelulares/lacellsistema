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
        "loja": "L&A CELL - Assistência Técnica",
        "whatsapp": "(11) 98083-3734"
    },
    "adriano": {
        "senha": "jesus",
        "loja": "Millenium Solutions Atibaia Center",
        "whatsapp": "(11) 99846-8349"
    }
}

# ===============================
# CONFIG
# ===============================
PASTA_PDF = "pdfs"
ARQUIVO_DB = "os.json"
os.makedirs(PASTA_PDF, exist_ok=True)

# ===============================
# DRIVE DESATIVADO
# ===============================
def upload_drive(file_path, file_name):
    pass

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
# PDF
# ===============================
def desenhar_padrao():
    pontos = [["○"] * 3 for _ in range(3)]
    t = Table(pontos, 18, 18)
    t.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER')
    ]))
    return t

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
        elementos.append(Paragraph(loja, normal))
        elementos.append(Paragraph(f"WhatsApp: {whatsapp}", normal))

        linhas = [
            f"OS Nº {numero}",
            f"Data: {dados['data']}",
            f"Cliente: {dados['cliente']}",
            f"Aparelho: {dados['aparelho']}",
            f"Defeito: {dados['defeito']}",
            f"Valor: R$ {dados['valor']:.2f}",
        ]

        for l in linhas:
            elementos.append(Paragraph(l, normal))

        elementos.append(Spacer(1, 5))
        elementos.append(Paragraph("Senha padrão:", normal))
        elementos.append(desenhar_padrao())
        elementos.append(Spacer(1, 5))

    bloco("VIA CLIENTE")
    elementos.append(Spacer(1, 10))
    bloco("VIA LOJA")

    doc.build(elementos)
    return caminho

# ===============================
# ROTAS
# ===============================
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form.get("usuario","").lower()
        s = request.form.get("senha","")
        if u in USUARIOS and USUARIOS[u]["senha"] == s:
            session["logado"] = True
            session["usuario"] = u
            return redirect("/painel")
        return render_template("login.html", erro="Login inválido")
    return render_template("login.html")

@app.route("/painel")
def painel():
    if not session.get("logado"): return redirect("/")
    u = session["usuario"]
    loja = USUARIOS[u]["loja"]

    lista = [o for o in carregar_os() if o["loja"] == loja]
    total = len(lista)
    valor = sum(float(o["valor"]) for o in lista)

    return render_template("painel.html", total_os=total, total_valor=valor)

# ===============================
# NOVA OS (COM FINANCEIRO)
# ===============================
@app.route("/nova", methods=["GET","POST"])
def nova():
    if not session.get("logado"): return redirect("/")

    if request.method == "POST":
        u = session["usuario"]
        loja = USUARIOS[u]["loja"]

        n = datetime.now().strftime("%Y%m%d%H%M")

        valor = float(request.form.get("valor") or 0)
        custo = float(request.form.get("custo") or 0)
        lucro = valor - custo

        d = {
            "numero": n,
            "usuario": u,
            "loja": loja,
            "cliente": request.form.get("cliente"),
            "telefone": request.form.get("telefone"),
            "aparelho": request.form.get("aparelho"),
            "defeito": request.form.get("defeito"),
            "valor": valor,
            "custo": custo,
            "lucro": lucro,
            "data": datetime.now().strftime("%d/%m/%Y")
        }

        salvar_os(d)

        pdf = gerar_pdf_os(n, d, loja, USUARIOS[u]["whatsapp"])
        return send_file(pdf, as_attachment=True)

    return render_template("nova_os.html")

# ===============================
# HISTORICO
# ===============================
@app.route("/historico")
def historico():
    if not session.get("logado"): return redirect("/")
    u = session["usuario"]
    loja = USUARIOS[u]["loja"]

    lista = [o for o in carregar_os() if o["loja"] == loja]

    return render_template("historico.html", lista=lista)

# ===============================
# FINANCEIRO (PROTEGIDO)
# ===============================
@app.route("/financeiro", methods=["GET","POST"])
def financeiro():
    if not session.get("logado"): return redirect("/")

    if request.method == "POST":
        senha = request.form.get("senha")
        if senha == "jesus":
            session["financeiro"] = True
        else:
            return render_template("financeiro_login.html", erro="Senha errada")

    if not session.get("financeiro"):
        return render_template("financeiro_login.html")

    u = session["usuario"]
    loja = USUARIOS[u]["loja"]

    lista = [o for o in carregar_os() if o["loja"] == loja]

    total_lucro = sum(o.get("lucro",0) for o in lista)

    return render_template("financeiro.html", lista=lista, lucro=total_lucro)

# ===============================
# RELATORIO DIA
# ===============================
@app.route("/relatorio_dia")
def relatorio_dia():
    if not session.get("logado"): return redirect("/")

    hoje = datetime.now().strftime("%d/%m/%Y")

    u = session["usuario"]
    loja = USUARIOS[u]["loja"]

    lista = [o for o in carregar_os() if o["loja"] == loja and o["data"] == hoje]

    total = len(lista)
    valor = sum(float(o["valor"]) for o in lista)

    return render_template("relatorio_dia.html", total=total, valor=valor)

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
