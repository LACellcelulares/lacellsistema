from flask import Flask, render_template, request, redirect, session, send_file
import os, json
from datetime import datetime

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

app = Flask(__name__)
app.secret_key = "lacell_secret"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_DB = os.path.join(BASE_DIR, "os.json")
PASTA_PDF = os.path.join(BASE_DIR, "pdfs")

os.makedirs(PASTA_PDF, exist_ok=True)

# ================= USUARIOS =================
USUARIOS = {
    "pytty": {"senha": "diemfafa", "loja": "L&A CELL Celulares", "whats": "(11)98083-3734"},
    "adriano": {"senha": "jesus", "loja": "MILLENNIUM SOLUTIONS ATIBAIA", "whats": "(11)99846-8349"}
}

# ================= DB =================
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

# ================= SENHA DESENHO =================
def senha9():
    t = Table([["○"]*3 for _ in range(3)], 20, 20)
    t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),1,colors.black)]))
    return t

# ================= PDF COMPLETO =================
def gerar_pdf(numero, d):
    caminho = os.path.join(PASTA_PDF, f"OS_{numero}.pdf")

    doc = SimpleDocTemplate(caminho, pagesize=A4)
    styles = getSampleStyleSheet()
    el = []

    def bloco(titulo):
        el.append(Paragraph(f"<b>{titulo}</b>", styles["Heading3"]))
        el.append(Paragraph(d.get("loja",""), styles["Normal"]))
        el.append(Paragraph(f"WhatsApp: {d.get('whats','')}", styles["Normal"]))
        el.append(Spacer(1,10))

        dados = [
            f"OS Nº {numero}",
            f"Data: {d.get('data','')}",
            f"Cliente: {d.get('cliente','')}",
            f"Telefone: {d.get('telefone','')}",
            f"CPF/CNPJ: {d.get('cpf','')}",
            f"IMEI: {d.get('imei','')}",
            f"Aparelho: {d.get('aparelho','')}",
            f"Defeito: {d.get('defeito','')}",
            f"Valor: R$ {d.get('valor',0)}",
            f"Sinal: R$ {d.get('sinal',0)}",
            f"Restante: R$ {d.get('restante',0)}",
            f"Custo: R$ {d.get('custo',0)}",
            f"Frete: R$ {d.get('frete',0)}",
            f"Pagamento: {d.get('pagamento','')}",
            f"Entrega: {d.get('entrega','')}",
            f"Garantia: {d.get('garantia','')}",
            f"Senha: {d.get('senha','')}",
        ]

        for x in dados:
            el.append(Paragraph(x, styles["Normal"]))

        el.append(Spacer(1,10))
        el.append(Paragraph("Desenho da senha:", styles["Normal"]))
        el.append(senha9())
        el.append(Spacer(1,20))

    bloco("VIA CLIENTE")
    bloco("VIA LOJA")

    doc.build(el)
    return caminho

# ================= LOGIN =================
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

# ================= PAINEL =================
@app.route("/painel")
def painel():
    if not session.get("logado"):
        return redirect("/")

    usuario = session["usuario"]
    loja = USUARIOS[usuario]["loja"]

    lista = [o for o in carregar() if o.get("loja") == loja]

    return render_template("painel.html", total_os=len(lista))

# ================= NOVA =================
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
            "data": datetime.now().strftime("%Y-%m-%d"),
            "loja": USUARIOS[usuario]["loja"],
            "whats": USUARIOS[usuario]["whats"]
        }

        lista.append(d)
        salvar(lista)

        pdf = gerar_pdf(n, d)
        return send_file(pdf, as_attachment=True)

    return render_template("nova_os.html")

# ================= VER PDF =================
@app.route("/os/<numero>")
def ver(numero):
    if not session.get("logado"):
        return redirect("/")

    lista = carregar()
    o = next((x for x in lista if x["numero"] == numero), None)

    if not o:
        return "OS não encontrada"

    pdf = gerar_pdf(numero, o)
    return send_file(pdf)

# ================= HISTORICO =================
@app.route("/historico")
def historico():
    if not session.get("logado"):
        return redirect("/")

    usuario = session["usuario"]
    loja = USUARIOS[usuario]["loja"]

    busca = (request.args.get("busca") or "").lower()

    lista = [o for o in carregar() if o.get("loja") == loja]

    if busca:
        lista = [o for o in lista if busca in str(o).lower()]

    return render_template("historico.html", lista=lista)

# ================= FINANCEIRO =================
@app.route("/financeiro")
def financeiro():
    if not session.get("logado"):
        return redirect("/")

    usuario = session["usuario"]
    loja = USUARIOS[usuario]["loja"]

    busca = (request.args.get("busca") or "").lower()

    lista = [o for o in carregar() if o.get("loja") == loja]

    if busca:
        lista = [o for o in lista if busca in str(o).lower()]

    if request.args.get("aberto") == "1":
        lista = [o for o in lista if float(o.get("restante",0)) > 0]

    total = sum(float(o.get("valor",0)) for o in lista)
    custo = sum(float(o.get("custo",0)) for o in lista)
    frete = sum(float(o.get("frete",0)) for o in lista)

    # ✅ lucro só do que foi pago
    lucro = sum(
        float(o.get("valor",0)) - float(o.get("custo",0)) - float(o.get("frete",0))
        for o in lista if float(o.get("restante",0)) == 0
    )

    return render_template("financeiro.html",
        lista=lista,
        total=total,
        custo=custo,
        frete=frete,
        lucro=lucro
    )

# ================= PAGAR =================
@app.route("/pagar/<numero>")
def pagar(numero):
    lista = carregar()
    for o in lista:
        if o["numero"] == numero:
            o["status"] = "pago"
            o["restante"] = 0
    salvar(lista)
    return redirect("/financeiro")

# ================= CANCELAR =================
@app.route("/cancelar/<numero>")
def cancelar(numero):
    lista = [o for o in carregar() if o["numero"] != numero]
    salvar(lista)
    return redirect("/financeiro")

# ================= SAIR =================
@app.route("/sair")
def sair():
    session.clear()
    return redirect("/")

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
