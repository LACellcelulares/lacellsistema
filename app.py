from flask import Flask, render_template, request, redirect, session, send_file
import os, json
from datetime import datetime

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

app = Flask(__name__)
app.secret_key = "lacell_secret"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_DB = os.path.join(BASE_DIR, "os.json")
PASTA_PDF = os.path.join(BASE_DIR, "pdfs")

os.makedirs(PASTA_PDF, exist_ok=True)

USUARIOS = {
    "pytty": {"senha": "diemfafa", "loja": "L&A CELL Celulares", "whats": "(11)98083-3734"},
    "adriano": {"senha": "jesus", "loja": "MILLENNIUM SOLUTIONS ATIBAIA", "whats": "(11)99846-8349"}
}

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

# ================= PDF =================
def gerar_pdf(numero, d):
    caminho = os.path.join(PASTA_PDF, f"OS_{numero}.pdf")

    doc = SimpleDocTemplate(
        caminho,
        pagesize=A4,
        rightMargin=20,
        leftMargin=20,
        topMargin=20,
        bottomMargin=20
    )

    styles = getSampleStyleSheet()

    normal = ParagraphStyle(name="normal", fontSize=9, leading=11)
    bold = ParagraphStyle(name="bold", fontSize=9, leading=11)

    el = []

    def linha(label, valor):
        return [
            Paragraph(f"<b>{label}</b>", normal),
            Paragraph(str(valor or ""), normal)
        ]

    def bloco(titulo_txt):
        el.append(Paragraph(f"<b>{titulo_txt}</b>", styles["Heading3"]))
        el.append(Paragraph(f"<b>{d.get('loja')}</b>", normal))
        el.append(Paragraph(f"WhatsApp: {d.get('whats')}", normal))
        el.append(Spacer(1,6))

        tabela = [
            linha("OS Nº:", numero),
            linha("Data:", d.get("data")),
            linha("Cliente:", d.get("cliente")),
            linha("Telefone:", d.get("telefone")),
            linha("CPF/CNPJ:", d.get("cpf")),
            linha("IMEI:", d.get("imei")),
            linha("Aparelho:", d.get("aparelho")),
            linha("Defeito:", d.get("defeito")),
            linha("Valor:", f"R$ {d.get('valor')}"),
            linha("Pagamento:", d.get("pagamento")),
            linha("Sinal:", f"R$ {d.get('sinal')}"),
            linha("Restante:", f"R$ {d.get('restante')}"),
            linha("Entrega:", d.get("entrega")),
            linha("Garantia:", d.get("garantia")),
            linha("Senha:", d.get("senha")),
        ]

        t = Table(tabela, colWidths=[120, 300])
        t.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.3, colors.black),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ]))

        el.append(t)

        el.append(Spacer(1,8))
        el.append(Paragraph("<b>Senha de desenho:</b>", normal))
        el.append(Table([["■"]*3 for _ in range(3)], 15, 15))

        el.append(Spacer(1,10))
        el.append(Paragraph("<b>Assinatura:</b> ____________________________", normal))
        el.append(Spacer(1,15))

    bloco("VIA CLIENTE")
    el.append(Paragraph("------------------------------------------", normal))
    bloco("VIA LOJA")

    doc.build(el)
    return caminho

# ================= RESTO =================
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        usuario = (request.form.get("usuario") or "").lower()
        senha = request.form.get("senha") or ""

        if usuario in USUARIOS and USUARIOS[usuario]["senha"] == senha:
            session["logado"] = True
            session["usuario"] = usuario
            return redirect("/painel")

    return render_template("login.html")

@app.route("/painel")
def painel():
    if not session.get("logado"):
        return redirect("/")

    usuario = session["usuario"]
    loja = USUARIOS[usuario]["loja"]

    lista = [o for o in carregar() if o.get("loja") == loja]
    return render_template("painel.html", total_os=len(lista))

@app.route("/nova", methods=["GET","POST"])
def nova():
    if not session.get("logado"):
        return redirect("/")

    if request.method == "POST":
        lista = carregar()
        n = datetime.now().strftime("%Y%m%d%H%M%S")

        v = float(request.form.get("valor") or 0)
        s = float(request.form.get("sinal") or 0)

        usuario = session["usuario"]

        d = {
            "numero": n,
            "cliente": request.form.get("cliente"),
            "telefone": request.form.get("telefone"),
            "cpf": request.form.get("cpf"),
            "imei": request.form.get("imei"),
            "aparelho": request.form.get("aparelho"),
            "defeito": request.form.get("defeito"),
            "valor": v,
            "sinal": s,
            "restante": v - s,
            "custo": float(request.form.get("custo") or 0),
            "frete": float(request.form.get("frete") or 0),
            "pagamento": request.form.get("pagamento"),
            "entrega": request.form.get("entrega"),
            "garantia": request.form.get("garantia"),
            "senha": request.form.get("senha"),
            "status": "aberto",
            "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "loja": USUARIOS[usuario]["loja"],
            "whats": USUARIOS[usuario]["whats"]
        }

        lista.append(d)
        salvar(lista)

        pdf = gerar_pdf(n, d)
        return send_file(pdf, as_attachment=True)

    return render_template("nova_os.html")

@app.route("/os/<numero>")
def ver(numero):
    lista = carregar()
    o = next((x for x in lista if x["numero"] == numero), None)

    if not o:
        return "OS não encontrada"

    pdf = gerar_pdf(numero, o)
    return send_file(pdf)

@app.route("/sair")
def sair():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
