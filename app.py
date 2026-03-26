from flask import Flask, render_template, request, redirect, session, send_file
import os, json
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

app = Flask(__name__)
app.secret_key = "lacell_secret"

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

PASTA_PDF = "pdfs"
ARQUIVO_DB = "os.json"
os.makedirs(PASTA_PDF, exist_ok=True)

# ================= BANCO =================
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

# ================= PDF =================
def desenhar_padrao():
    pontos = [["○"] * 3 for _ in range(3)]
    t = Table(pontos, 18, 18)
    t.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))
    return t

def gerar_pdf_os(numero, dados, loja, whatsapp):
    caminho = os.path.join(PASTA_PDF, f"OS_{numero}.pdf")
    styles = getSampleStyleSheet()
    normal = styles["Normal"]

    doc = SimpleDocTemplate(caminho, pagesize=A4)
    el = []

    def bloco(titulo):
        el.append(Paragraph(f"<b>{titulo}</b>", styles["Heading4"]))
        el.append(Paragraph(loja, normal))
        el.append(Paragraph(f"WhatsApp: {whatsapp}", normal))

        linhas = [
            f"OS Nº {numero}",
            f"Data: {dados['data']}",
            f"Cliente: {dados['cliente']}",
            f"Aparelho: {dados['aparelho']}",
            f"Defeito: {dados['defeito']}",
            f"Valor: R$ {dados['valor']:.2f}",
        ]

        for l in linhas:
            el.append(Paragraph(l, normal))

        el.append(Spacer(1,5))
        el.append(Paragraph("Senha padrão:", normal))
        el.append(desenhar_padrao())
        el.append(Spacer(1,10))

    bloco("VIA CLIENTE")
    bloco("VIA LOJA")

    doc.build(el)
    return caminho

# ================= LOGIN =================
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

# ================= PAINEL =================
@app.route("/painel")
def painel():
    if not session.get("logado"): return redirect("/")
    u = session["usuario"]
    loja = USUARIOS[u]["loja"]

    lista = [o for o in carregar_os() if o["loja"] == loja]

    total = len(lista)
    valor = sum(o["valor"] for o in lista)

    return render_template("painel.html", total_os=total, total_valor=valor)

# ================= NOVA OS =================
@app.route("/nova", methods=["GET","POST"])
def nova():
    if not session.get("logado"): return redirect("/")

    if request.method == "POST":
        u = session["usuario"]
        loja = USUARIOS[u]["loja"]

        n = datetime.now().strftime("%Y%m%d%H%M")

        valor = float(request.form.get("valor") or 0)
        sinal = float(request.form.get("sinal") or 0)
        custo = float(request.form.get("custo") or 0)
        frete = float(request.form.get("frete") or 0)

        custo_total = custo + frete
        lucro = valor - custo_total
        restante = valor - sinal

        d = {
            "numero": n,
            "usuario": u,
            "loja": loja,
            "cliente": request.form.get("cliente"),
            "telefone": request.form.get("telefone"),
            "aparelho": request.form.get("aparelho"),
            "defeito": request.form.get("defeito"),
            "valor": valor,
            "sinal": sinal,
            "restante": restante,
            "custo": custo,
            "frete": frete,
            "custo_total": custo_total,
            "lucro": lucro,
            "data": datetime.now().strftime("%d/%m/%Y")
        }

        salvar_os(d)

        pdf = gerar_pdf_os(n, d, loja, USUARIOS[u]["whatsapp"])
        return send_file(pdf, as_attachment=True)

    return render_template("nova_os.html")

# ================= VER OS =================
@app.route("/os/<numero>")
def ver_os(numero):
    if not session.get("logado"): return redirect("/")

    u = session["usuario"]
    loja = USUARIOS[u]["loja"]

    o = next((x for x in carregar_os() if x["numero"] == numero and x["loja"] == loja), None)

    if not o:
        return "OS não encontrada"

    pdf = gerar_pdf_os(numero, o, loja, USUARIOS[u]["whatsapp"])
    return send_file(pdf)

# ================= HISTORICO =================
@app.route("/historico")
def historico():
    if not session.get("logado"): return redirect("/")
    u = session["usuario"]
    loja = USUARIOS[u]["loja"]

    lista = [o for o in carregar_os() if o["loja"] == loja]

    return render_template("historico.html", lista=lista)

# ================= FINANCEIRO =================
@app.route("/financeiro", methods=["GET","POST"])
def financeiro():
    if not session.get("logado"): return redirect("/")

    if request.method == "POST":
        if request.form.get("senha") == "jesus":
            session["financeiro"] = True
        else:
            return render_template("financeiro_login.html", erro="Senha errada")

    if not session.get("financeiro"):
        return render_template("financeiro_login.html")

    u = session["usuario"]
    loja = USUARIOS[u]["loja"]

    lista = [o for o in carregar_os() if o["loja"] == loja]

    total_lucro = sum(o["lucro"] for o in lista)
    total_aberto = sum(o["restante"] for o in lista)

    return render_template("financeiro.html", lista=lista, lucro=total_lucro, aberto=total_aberto)

# ================= RELATORIO DIA =================
@app.route("/relatorio_dia")
def relatorio_dia():
    if not session.get("logado"): return redirect("/")

    hoje = datetime.now().strftime("%d/%m/%Y")

    u = session["usuario"]
    loja = USUARIOS[u]["loja"]

    lista = [o for o in carregar_os() if o["loja"] == loja and o["data"] == hoje]

    total = len(lista)
    valor = sum(o["valor"] for o in lista)

    return render_template("relatorio_dia.html", total=total, valor=valor)

# ================= RELATORIO =================
@app.route("/relatorio")
def relatorio():
    if not session.get("logado"): return redirect("/")

    u = session["usuario"]
    loja = USUARIOS[u]["loja"]

    lista = [o for o in carregar_os() if o["loja"] == loja]

    total = len(lista)
    valor = sum(o["valor"] for o in lista)

    return render_template("relatorio.html", qtd=total, total=valor)

@app.route("/sair")
def sair():
    session.clear()
    return redirect("/")
    
if __name__ == "__main__":
    app.run(debug=True)
