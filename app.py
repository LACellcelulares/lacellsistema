from flask import Flask, render_template, request, redirect, session, send_file
import os, json
from datetime import datetime

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)
app.secret_key = "lacell_secret"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_DB = os.path.join(BASE_DIR, "os.json")

# ===== USUÁRIOS =====
USUARIOS = {
    "pytty": {"senha": "diemfafa", "loja": "L&A CELL"},
    "adriano": {"senha": "jesus", "loja": "MILLENNIUM"}
}

# ===== BANCO =====
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

# ===== PDF =====
def gerar_pdf(os_data):
    try:
        pasta = os.path.join(BASE_DIR, "pdfs")
        os.makedirs(pasta, exist_ok=True)

        caminho = os.path.join(pasta, f"{os_data['numero']}.pdf")

        doc = SimpleDocTemplate(caminho, pagesize=A4)
        styles = getSampleStyleSheet()

        c = []
        c.append(Paragraph("ORDEM DE SERVIÇO - L&A CELL", styles['Title']))
        c.append(Spacer(1, 10))

        c.append(Paragraph(f"OS: {os_data['numero']}", styles['Normal']))
        c.append(Paragraph(f"Cliente: {os_data['cliente']}", styles['Normal']))
        c.append(Paragraph(f"Telefone: {os_data['telefone']}", styles['Normal']))
        c.append(Paragraph(f"Aparelho: {os_data['aparelho']}", styles['Normal']))
        c.append(Paragraph(f"Defeito: {os_data['defeito']}", styles['Normal']))
        c.append(Paragraph(f"Valor: R$ {os_data['valor']}", styles['Normal']))
        c.append(Paragraph(f"Sinal: R$ {os_data['sinal']}", styles['Normal']))
        c.append(Paragraph(f"Restante: R$ {os_data['restante']}", styles['Normal']))

        doc.build(c)

        print("PDF OK:", caminho)

    except Exception as e:
        print("ERRO PDF:", e)

# ===== LOGIN =====
@app.route("/", methods=["GET","POST"])
def login():
    erro = None

    if request.method == "POST":
        u = (request.form.get("usuario") or "").lower()
        s = request.form.get("senha") or ""

        if u in USUARIOS and USUARIOS[u]["senha"] == s:
            session["logado"] = True
            session["usuario"] = u
            session.pop("financeiro", None)
            return redirect("/painel")
        else:
            erro = "Login inválido"

    return render_template("login.html", erro=erro)

# ===== PAINEL =====
@app.route("/painel")
def painel():
    if not session.get("logado"):
        return redirect("/")

    loja = USUARIOS[session["usuario"]]["loja"]
    lista = [o for o in carregar() if o.get("loja") == loja]

    return render_template("painel.html", total_os=len(lista))

# ===== NOVA OS =====
@app.route("/nova", methods=["GET","POST"])
def nova():
    if not session.get("logado"):
        return redirect("/")

    if request.method == "POST":

        lista = carregar()
        numero = datetime.now().strftime("%Y%m%d%H%M%S")

        valor = float(request.form.get("valor") or 0)
        sinal = float(request.form.get("sinal") or 0)

        loja = USUARIOS[session["usuario"]]["loja"]

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
            "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "loja": loja
        }

        lista.append(d)
        salvar(lista)

        gerar_pdf(d)  # 🔥 gera PDF

        return redirect("/historico")

    return render_template("nova_os.html")

# ===== HISTÓRICO =====
@app.route("/historico")
def historico():
    if not session.get("logado"):
        return redirect("/")

    loja = USUARIOS[session["usuario"]]["loja"]
    lista = [o for o in carregar() if o.get("loja") == loja]

    lista = sorted(lista, key=lambda x: x.get("data",""), reverse=True)

    return render_template("historico.html", lista=lista)

# ===== VER PDF =====
@app.route("/ver_pdf/<numero>")
def ver_pdf(numero):
    caminho = os.path.join(BASE_DIR, "pdfs", f"{numero}.pdf")

    if not os.path.exists(caminho):
        return f"PDF não encontrado: {numero}"

    return send_file(caminho)

# ===== EDITAR =====
@app.route("/editar/<numero>", methods=["GET","POST"])
def editar(numero):
    lista = carregar()
    os_edit = next((o for o in lista if o["numero"] == numero), None)

    if not os_edit:
        return "OS não encontrada"

    if request.method == "POST":
        os_edit["cliente"] = request.form.get("cliente")
        os_edit["telefone"] = request.form.get("telefone")
        os_edit["aparelho"] = request.form.get("aparelho")
        os_edit["defeito"] = request.form.get("defeito")

        os_edit["valor"] = float(request.form.get("valor") or 0)
        os_edit["sinal"] = float(request.form.get("sinal") or 0)
        os_edit["restante"] = os_edit["valor"] - os_edit["sinal"]

        salvar(lista)
        return redirect("/financeiro")

    return render_template("editar.html", os=os_edit)

# ===== PAGAR =====
@app.route("/pagar/<numero>")
def pagar(numero):
    lista = carregar()
    for o in lista:
        if o["numero"] == numero:
            o["sinal"] = o["valor"]
            o["restante"] = 0
    salvar(lista)
    return redirect("/financeiro")

# ===== EXCLUIR =====
@app.route("/cancelar/<numero>")
def cancelar(numero):
    lista = carregar()
    lista = [o for o in lista if o["numero"] != numero]
    salvar(lista)
    return redirect("/financeiro")

# ===== FINANCEIRO =====
@app.route("/financeiro", methods=["GET","POST"])
def financeiro():

    if not session.get("logado"):
        return redirect("/")

    if "financeiro" not in session:
        if request.method == "POST":
            if request.form.get("senha") == "jesus":
                session["financeiro"] = True
                return redirect("/financeiro")
            else:
                return render_template("financeiro_login.html", erro="Senha errada")
        return render_template("financeiro_login.html")

    loja = USUARIOS[session["usuario"]]["loja"]
    lista = [o for o in carregar() if o.get("loja") == loja]

    pagos = [o for o in lista if float(o.get("restante",0)) == 0]

    total = sum(float(o.get("valor",0)) for o in pagos)
    custo = sum(float(o.get("custo",0)) for o in pagos)
    frete = sum(float(o.get("frete",0)) for o in pagos)

    lucro = total - (custo + frete)

    return render_template("financeiro.html",
        lista=lista,
        total=round(total,2),
        custo=round(custo,2),
        frete=round(frete,2),
        lucro=round(lucro,2)
    )

# ===== SAIR =====
@app.route("/sair")
def sair():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
