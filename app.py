from flask import Flask, render_template, request, redirect, send_file, session
import os, json
from datetime import datetime

app = Flask(__name__)
app.secret_key = "1234"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "os.json")


# ================= BANCO =================
def load_db():
    if not os.path.exists(DB):
        return []
    try:
        with open(DB, "r") as f:
            return json.load(f)
    except:
        return []

def save_db(data):
    with open(DB, "w") as f:
        json.dump(data, f, indent=4)


# ================= PDF =================
def gerar_pdf(os_data):
    try:
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
    except:
        print("Instale: pip install reportlab")
        return

    pasta = os.path.join(BASE_DIR, "pdfs")
    os.makedirs(pasta, exist_ok=True)

    file = os.path.join(pasta, f"{os_data['numero']}.pdf")

    doc = SimpleDocTemplate(file, pagesize=A4)
    styles = getSampleStyleSheet()

    def bloco(titulo):
        return [
            Paragraph(f"<b>{titulo}</b>", styles["Title"]),
            Spacer(1, 5),
            Table([
                ["OS", os_data["numero"], "Data", os_data["data"]],
                ["Cliente", os_data["cliente"], "Telefone", os_data["telefone"]],
                ["Aparelho", os_data["aparelho"], "IMEI", os_data["imei"]],
                ["Defeito", os_data["defeito"], "Senha", os_data["senha"]],
                ["Valor", f"R$ {os_data['valor']}", "Sinal", f"R$ {os_data['sinal']}"],
                ["Restante", f"R$ {os_data['restante']}", "Pagamento", os_data["pagamento"]],
            ], colWidths=[70,150,70,150]),
            Spacer(1, 15),
            Paragraph("Assinatura: ____________________", styles["Normal"]),
            Spacer(1, 30)
        ]

    elements = []
    elements += bloco("VIA CLIENTE - L&A CELL")
    elements.append(Paragraph("-------------------------------", styles["Normal"]))
    elements.append(Spacer(1, 10))
    elements += bloco("VIA LOJA - L&A CELL")

    doc.build(elements)


# ================= ROTAS =================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/salvar", methods=["POST"])
def salvar():
    db = load_db()

    numero = datetime.now().strftime("%Y%m%d%H%M%S")

    os_data = {
        "numero": numero,
        "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "cliente": request.form.get("cliente",""),
        "telefone": request.form.get("telefone",""),
        "aparelho": request.form.get("aparelho",""),
        "imei": request.form.get("imei",""),
        "defeito": request.form.get("defeito",""),
        "senha": request.form.get("senha",""),
        "valor": float(request.form.get("valor") or 0),
        "custo": float(request.form.get("custo") or 0),
        "frete": float(request.form.get("frete") or 0),
        "sinal": float(request.form.get("sinal") or 0),
        "restante": float(request.form.get("restante") or 0),
        "pagamento": request.form.get("pagamento",""),
        "status": "EM ABERTO"
    }

    db.append(os_data)
    save_db(db)

    gerar_pdf(os_data)

    return redirect("/historico")


@app.route("/historico")
def historico():
    return render_template("historico.html", lista=load_db())


@app.route("/ver/<numero>")
def ver(numero):
    path = os.path.join(BASE_DIR, "pdfs", f"{numero}.pdf")
    if not os.path.exists(path):
        return "PDF não encontrado"
    return send_file(path)


@app.route("/excluir/<numero>")
def excluir(numero):
    db = load_db()
    db = [x for x in db if x["numero"] != numero]
    save_db(db)
    return redirect("/historico")


# ================= FINANCEIRO =================

@app.route("/financeiro", methods=["GET","POST"])
def financeiro():

    if not session.get("logado"):
        if request.method == "POST":
            if request.form.get("senha") == "1234":
                session["logado"] = True
                return redirect("/financeiro")
        return render_template("login.html")

    db = load_db()
    pagos = [x for x in db if x["status"] == "PAGO"]

    total = sum(x["valor"] for x in pagos)
    custo = sum(x["custo"] for x in pagos)
    frete = sum(x["frete"] for x in pagos)

    lucro = total - custo - frete

    return render_template("financeiro.html",
                           lista=db,
                           total=total,
                           custo=custo,
                           frete=frete,
                           lucro=lucro)


@app.route("/pagar/<numero>")
def pagar(numero):
    db = load_db()
    for x in db:
        if x["numero"] == numero:
            x["status"] = "PAGO"
    save_db(db)
    return redirect("/financeiro")


# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
