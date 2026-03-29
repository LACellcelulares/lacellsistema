from flask import Flask, render_template, request, redirect, session, send_file
import os, json
from datetime import datetime

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
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

# ===== PDF PROFISSIONAL =====
def gerar_pdf(os_data):

    pasta = os.path.join(BASE_DIR, "pdfs")
    os.makedirs(pasta, exist_ok=True)

    caminho = os.path.join(pasta, f"{os_data['numero']}.pdf")

    doc = SimpleDocTemplate(caminho, pagesize=A4)
    styles = getSampleStyleSheet()

    elementos = []

    # TÍTULO
    elementos.append(Paragraph("L&A CELL - ASSISTÊNCIA TÉCNICA", styles['Title']))
    elementos.append(Spacer(1, 10))

    elementos.append(Paragraph(f"<b>OS Nº:</b> {os_data['numero']}", styles['Normal']))
    elementos.append(Paragraph(f"<b>Data:</b> {os_data['data']}", styles['Normal']))
    elementos.append(Spacer(1, 10))

    # CLIENTE
    tabela_cliente = Table([
        ["Cliente", os_data.get("cliente","")],
        ["Telefone", os_data.get("telefone","")],
        ["CPF/CNPJ", os_data.get("cpf","")],
    ])

    # APARELHO
    tabela_aparelho = Table([
        ["Aparelho", os_data.get("aparelho","")],
        ["IMEI", os_data.get("imei","")],
        ["Senha", os_data.get("senha","")],
    ])

    # SERVIÇO
    tabela_servico = Table([
        ["Defeito", os_data.get("defeito","")],
        ["Garantia", os_data.get("garantia","")],
        ["Previsão", os_data.get("entrega","")],
    ])

    # FINANCEIRO
    tabela_valores = Table([
        ["Valor", f"R$ {os_data.get('valor',0)}"],
        ["Sinal", f"R$ {os_data.get('sinal',0)}"],
        ["Restante", f"R$ {os_data.get('restante',0)}"],
        ["Pagamento", os_data.get("pagamento","")],
    ])

    estilo = TableStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("BACKGROUND", (0,0), (0,-1), colors.lightgrey),
    ])

    for t in [tabela_cliente, tabela_aparelho, tabela_servico, tabela_valores]:
        t.setStyle(estilo)
        elementos.append(t)
        elementos.append(Spacer(1, 10))

    elementos.append(Spacer(1, 20))
    elementos.append(Paragraph("______________________________", styles['Normal']))
    elementos.append(Paragraph("Assinatura do Cliente", styles['Normal']))

    doc.build(elementos)

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
        os_edit["cpf"] = request.form.get("cpf")
        os_edit["imei"] = request.form.get("imei")
        os_edit["aparelho"] = request.form.get("aparelho")
        os_edit["defeito"] = request.form.get("defeito")

        os_edit["valor"] = float(request.form.get("valor") or 0)
        os_edit["sinal"] = float(request.form.get("sinal") or 0)
        os_edit["restante"] = os_edit["valor"] - os_edit["sinal"]

        os_edit["custo"] = float(request.form.get("custo") or 0)
        os_edit["frete"] = float(request.form.get("frete") or 0)

        os_edit["pagamento"] = request.form.get("pagamento")
        os_edit["entrega"] = request.form.get("entrega")
        os_edit["garantia"] = request.form.get("garantia")
        os_edit["senha"] = request.form.get("senha")

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

# ===== START =====
if __name__ == "__main__":
    app.run(debug=True)
