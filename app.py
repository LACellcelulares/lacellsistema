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

# ===== GERAR PDF =====
def gerar_pdf(os_data):

    pasta = os.path.join(BASE_DIR, "pdfs")
    os.makedirs(pasta, exist_ok=True)

    caminho = os.path.join(pasta, f"{os_data['numero']}.pdf")

    doc = SimpleDocTemplate(caminho, pagesize=A4)
    styles = getSampleStyleSheet()

    conteudo = []

    conteudo.append(Paragraph("ORDEM DE SERVIÇO - L&A CELL", styles['Title']))
    conteudo.append(Spacer(1, 10))

    for campo, valor in os_data.items():
        conteudo.append(Paragraph(f"<b>{campo.upper()}:</b> {valor}", styles['Normal']))
        conteudo.append(Spacer(1, 5))

    doc.build(conteudo)

# ===== LOGIN =====
@app.route("/", methods=["GET","POST"])
def login():
    erro = None

    if request.method == "POST":
        usuario = (request.form.get("usuario") or "").lower()
        senha = request.form.get("senha") or ""

        if usuario in USUARIOS and USUARIOS[usuario]["senha"] == senha:
            session["logado"] = True
            session["usuario"] = usuario
            return redirect("/painel")
        else:
            erro = "Usuário ou senha inválidos"

    return render_template("login.html", erro=erro)

# ===== PAINEL =====
@app.route("/painel")
def painel():
    if not session.get("logado"):
        return redirect("/")

    usuario = session["usuario"]
    loja = USUARIOS[usuario]["loja"]

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

        usuario = session["usuario"]

        d = {
            "numero": numero,
            "cliente": request.form.get("cliente"),
            "telefone": request.form.get("telefone"),
            "cpf": request.form.get("cpf"),
            "imei": request.form.get("imei"),
            "aparelho": request.form.get("aparelho"),
            "defeito": request.form.get("defeito"),
            "valor": valor,
            "sinal": sinal,
            "restante": valor - sinal,
            "custo": float(request.form.get("custo") or 0),
            "frete": float(request.form.get("frete") or 0),
            "pagamento": request.form.get("pagamento"),
            "entrega": request.form.get("entrega"),
            "garantia": request.form.get("garantia"),
            "senha": request.form.get("senha"),
            "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "loja": USUARIOS[usuario]["loja"]
        }

        lista.append(d)
        salvar(lista)

        # 🔥 GERA PDF AUTOMÁTICO
        gerar_pdf(d)

        return redirect("/historico")

    return render_template("nova_os.html")

# ===== HISTÓRICO =====
@app.route("/historico")
def historico():
    if not session.get("logado"):
        return redirect("/")

    usuario = session["usuario"]
    loja = USUARIOS[usuario]["loja"]

    lista = [o for o in carregar() if o.get("loja") == loja]

    busca = (request.args.get("busca") or "").lower()

    if busca:
        lista = [
            o for o in lista
            if busca in str(o.get("cliente","")).lower()
            or busca in str(o.get("aparelho","")).lower()
            or busca in str(o.get("telefone","")).lower()
            or busca in str(o.get("numero",""))
        ]

    lista = sorted(lista, key=lambda x: x.get("data",""), reverse=True)

    return render_template("historico.html", lista=lista)

# ===== ABRIR PDF =====
@app.route("/ver_pdf/<numero>")
def ver_pdf(numero):

    caminho = os.path.join(BASE_DIR, "pdfs", f"{numero}.pdf")

    if not os.path.exists(caminho):
        return "PDF não encontrado"

    return send_file(caminho)

# ===== FINANCEIRO =====
@app.route("/financeiro", methods=["GET","POST"])
def financeiro():

    if not session.get("logado"):
        return redirect("/")

    if not session.get("financeiro"):

        if request.method == "POST":
            if request.form.get("senha") == "jesus":
                session["financeiro"] = True
                return redirect("/financeiro")
            else:
                return render_template("financeiro_login.html", erro="Senha incorreta")

        return render_template("financeiro_login.html")

    usuario = session["usuario"]
    loja = USUARIOS[usuario]["loja"]

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

# ===== SAIR =====
@app.route("/sair")
def sair():
    session.clear()
    return redirect("/")

# ===== START =====
if __name__ == "__main__":
    app.run(debug=True)
