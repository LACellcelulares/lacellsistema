from flask import Flask, render_template, request, redirect, send_file, session
import json, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "123456"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARQUIVO = os.path.join(BASE_DIR, "os.json")


# ================== BANCO ==================
def carregar():
    if not os.path.exists(ARQUIVO):
        return []
    with open(ARQUIVO, "r") as f:
        return json.load(f)

def salvar(lista):
    with open(ARQUIVO, "w") as f:
        json.dump(lista, f, indent=4)


# ================== PDF ==================
def gerar_pdf(os_data):

    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet

    pasta = os.path.join(BASE_DIR, "pdfs")
    os.makedirs(pasta, exist_ok=True)

    caminho = os.path.join(pasta, f"{os_data['numero']}.pdf")

    doc = SimpleDocTemplate(caminho, pagesize=A4)
    styles = getSampleStyleSheet()

    elementos = []

    def bloco(titulo):
        return [
            Paragraph(f"<b>{titulo}</b>", styles['Title']),
            Spacer(1, 5),

            Table([
                ["OS", os_data.get("numero",""), "Data", os_data.get("data","")],
                ["Cliente", os_data.get("cliente",""), "Telefone", os_data.get("telefone","")],
                ["Aparelho", os_data.get("aparelho",""), "IMEI", os_data.get("imei","")],
                ["Defeito", os_data.get("defeito",""), "Senha", os_data.get("senha","")],
                ["Valor", f"R$ {os_data.get('valor',0)}", "Sinal", f"R$ {os_data.get('sinal',0)}"],
                ["Restante", f"R$ {os_data.get('restante',0)}", "Pagamento", os_data.get("pagamento","")],
                ["Garantia", os_data.get("garantia",""), "Previsão", os_data.get("entrega","")]
            ], colWidths=[70,150,70,150]),

            Spacer(1, 10),
            Paragraph("Assinatura: ___________________________", styles['Normal']),
            Spacer(1, 30)
        ]

    elementos += bloco("VIA DO CLIENTE - L&A CELL")

    elementos.append(Paragraph("-----------------------------------------------------", styles['Normal']))
    elementos.append(Spacer(1, 10))

    elementos += bloco("VIA DA LOJA - L&A CELL")

    doc.build(elementos)


# ================== ROTAS ==================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/salvar", methods=["POST"])
def salvar_os():
    lista = carregar()

    numero = datetime.now().strftime("%Y%m%d%H%M%S")

    os_data = {
        "numero": numero,
        "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "cliente": request.form.get("cliente"),
        "telefone": request.form.get("telefone"),
        "aparelho": request.form.get("aparelho"),
        "imei": request.form.get("imei"),
        "defeito": request.form.get("defeito"),
        "senha": request.form.get("senha"),
        "valor": float(request.form.get("valor") or 0),
        "custo": float(request.form.get("custo") or 0),
        "frete": float(request.form.get("frete") or 0),
        "sinal": float(request.form.get("sinal") or 0),
        "restante": float(request.form.get("restante") or 0),
        "pagamento": request.form.get("pagamento"),
        "garantia": request.form.get("garantia"),
        "entrega": request.form.get("entrega"),
        "status": "EM ABERTO"
    }

    lista.append(os_data)
    salvar(lista)

    gerar_pdf(os_data)

    return redirect("/historico")


@app.route("/historico")
def historico():
    lista = carregar()
    return render_template("historico.html", lista=lista)


@app.route("/ver/<numero>")
def ver(numero):
    caminho = os.path.join(BASE_DIR, "pdfs", f"{numero}.pdf")
    return send_file(caminho)


@app.route("/excluir/<numero>")
def excluir(numero):
    lista = carregar()
    lista = [x for x in lista if x["numero"] != numero]
    salvar(lista)
    return redirect("/historico")


@app.route("/editar/<numero>", methods=["GET", "POST"])
def editar(numero):
    lista = carregar()

    os_data = next((x for x in lista if x["numero"] == numero), None)

    if request.method == "POST":
        os_data["cliente"] = request.form.get("cliente")
        os_data["valor"] = float(request.form.get("valor") or 0)
        salvar(lista)
        return redirect("/historico")

    return render_template("editar.html", os=os_data)


# ================== FINANCEIRO ==================

@app.route("/financeiro", methods=["GET","POST"])
def financeiro():

    if not session.get("logado"):
        if request.method == "POST":
            if request.form.get("senha") == "1234":
                session["logado"] = True
                return redirect("/financeiro")
        return render_template("login.html")

    lista = carregar()

    total = sum(x["valor"] for x in lista if x["status"] == "PAGO")
    custo = sum(x["custo"] for x in lista if x["status"] == "PAGO")
    frete = sum(x["frete"] for x in lista if x["status"] == "PAGO")

    lucro = total - custo - frete

    return render_template("financeiro.html",
                           lista=lista,
                           total=total,
                           custo=custo,
                           frete=frete,
                           lucro=lucro)


@app.route("/pagar/<numero>")
def pagar(numero):
    lista = carregar()
    for x in lista:
        if x["numero"] == numero:
            x["status"] = "PAGO"
    salvar(lista)
    return redirect("/financeiro")


# ================== RUN ==================
if __name__ == "__main__":
    app.run(debug=True)
