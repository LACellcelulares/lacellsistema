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
        rightMargin=15,
        leftMargin=15,
        topMargin=15,
        bottomMargin=15
    )

    styles = getSampleStyleSheet()

    normal = ParagraphStyle(name="normal", fontSize=8, leading=9)
    titulo = ParagraphStyle(name="titulo", fontSize=10, leading=11)

    el = []

    def linha(l1, v1, l2, v2):
        return [
            Paragraph(f"<b>{l1}</b>", normal),
            Paragraph(str(v1 or ""), normal),
            Paragraph(f"<b>{l2}</b>", normal),
            Paragraph(str(v2 or ""), normal),
        ]

    def bloco(titulo_txt):
        el.append(Paragraph(f"<b>{titulo_txt}</b>", titulo))
        el.append(Paragraph(f"<b>{d.get('loja')}</b>", normal))
        el.append(Paragraph(f"WhatsApp: {d.get('whats')}", normal))
        el.append(Spacer(1,4))

        dados = [
            linha("OS Nº:", numero, "Data:", d.get("data")),
            linha("Cliente:", d.get("cliente"), "Telefone:", d.get("telefone")),
            linha("CPF/CNPJ:", d.get("cpf"), "IMEI:", d.get("imei")),
            linha("Aparelho:", d.get("aparelho"), "Defeito:", d.get("defeito")),
            linha("Valor:", f"R$ {d.get('valor')}", "Pagamento:", d.get("pagamento")),
            linha("Sinal:", f"R$ {d.get('sinal')}", "Restante:", f"R$ {d.get('restante')}"),
            linha("Entrega:", d.get("entrega"), "Garantia:", d.get("garantia")),
            linha("Senha:", d.get("senha"), "", ""),
        ]

        t = Table(dados, colWidths=[60, 110, 60, 110])
        t.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.3, colors.black),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ]))

        el.append(t)

        el.append(Spacer(1,5))
        el.append(Paragraph("<b>Senha de desenho:</b>", normal))
        el.append(Table([["■"]*3 for _ in range(3)], 10, 10))

        el.append(Spacer(1,6))
        el.append(Paragraph("<b>Ass:</b> ____________________", normal))
        el.append(Spacer(1,8))

    bloco("VIA CLIENTE")

    el.append(Paragraph("----------------------------------------------", normal))

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
