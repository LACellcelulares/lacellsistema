from flask import Flask, render_template, request, redirect, session, send_file, abort
import os, json
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

app = Flask(__name__)
app.secret_key = "lacell_secret"

# ================= CAMINHOS =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PASTA_PDF = os.path.join(BASE_DIR, "pdfs")
ARQUIVO_DB = os.path.join(BASE_DIR, "os.json")

os.makedirs(PASTA_PDF, exist_ok=True)

# ================= USUARIOS =================
USUARIOS = {
    "pytty": {"senha":"diemfafa","loja":"L&A CELL Celulares","whatsapp":"(11)98083-3734"},
    "adriano": {"senha":"jesus","loja":"MILLENNIUM SOLUTIONS ATIBAIA","whatsapp":"(11)99846-8349"}
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

# ================= PDF =================
def senha9():
    t = Table([["○"]*3 for _ in range(3)], 18, 18)
    t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),1,colors.black)]))
    return t

def gerar_pdf(n, d, loja, whats):
    caminho = os.path.join(PASTA_PDF, f"OS_{n}.pdf")
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(caminho, pagesize=A4)
    el = []

    def bloco(t):
        el.append(Paragraph(f"<b>{t}</b>", styles["Heading4"]))
        el.append(Paragraph(loja, styles["Normal"]))
        el.append(Paragraph(f"WhatsApp: {whats}", styles["Normal"]))
        el.append(Spacer(1,5))

        dados = [
            f"OS Nº {n}",
            f"Data: {d.get('data','')}",
            f"Entrega: {d.get('entrega','')}",
            f"Cliente: {d.get('cliente','')}",
            f"Telefone: {d.get('telefone','')}",
            f"Aparelho: {d.get('aparelho','')}",
            f"Defeito: {d.get('defeito','')}",
            f"Valor: R$ {d.get('valor',0)}",
            f"Sinal: R$ {d.get('sinal',0)}",
            f"Restante: R$ {d.get('restante',0)}",
            f"Pagamento: {d.get('pagamento','')}",
            f"Garantia: {d.get('garantia','')}"
        ]

        for x in dados:
            el.append(Paragraph(x, styles["Normal"]))

        el.append(Spacer(1,5))
        el.append(senha9())

    bloco("VIA CLIENTE")
    el.append(Spacer(1,15))
    bloco("VIA LOJA")

    doc.build(el)
    return caminho

# ================= LOGIN =================
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = (request.form.get("usuario") or "").lower()
        s = request.form.get("senha") or ""

        if u in USUARIOS and USUARIOS[u]["senha"] == s:
            session["logado"] = True
            session["usuario"] = u
            session["fin_ok"] = False
            return redirect("/painel")

    return render_template("login.html")

# ================= PAINEL =================
@app.route("/painel")
def painel():
    if not session.get("logado"):
        return redirect("/")

    u = session["usuario"]
    loja = USUARIOS[u]["loja"]

    lista = [o for o in carregar() if o.get("loja") == loja]

    return render_template("painel.html",
        total_os=len(lista),
        total_valor=sum(float(o.get("valor",0)) for o in lista)
    )

# ================= NOVA OS =================
@app.route("/nova", methods=["GET","POST"])
def nova():
    if not session.get("logado"):
        return redirect("/")

    if request.method == "POST":
        lista = carregar()
        n = datetime.now().strftime("%Y%m%d%H%M%S")

        v = float(request.form.get("valor") or 0)
        s = float(request.form.get("sinal") or 0)

        d = {
            "numero": n,
            "loja": USUARIOS[session["usuario"]]["loja"],
            "cliente": request.form.get("cliente"),
            "telefone": request.form.get("telefone"),
            "aparelho": request.form.get("aparelho"),
            "defeito": request.form.get("defeito"),
            "valor": v,
            "sinal": s,
            "restante": v - s,
            "custo": float(request.form.get("custo") or 0),
            "frete": float(request.form.get("frete") or 0),
            "pagamento": request.form.get("pagamento"),
            "garantia": request.form.get("garantia"),
            "entrega": request.form.get("entrega"),
            "status": "aberto",
            "data": datetime.now().strftime("%d/%m/%Y %H:%M")
        }

        lista.append(d)
        salvar(lista)

        pdf = gerar_pdf(n, d, d["loja"], USUARIOS[session["usuario"]]["whatsapp"])
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
        abort(404)

    pdf = gerar_pdf(numero, o, o["loja"], USUARIOS[session["usuario"]]["whatsapp"])
    return send_file(pdf)

# ================= HISTORICO =================
@app.route("/historico")
def historico():
    if not session.get("logado"):
        return redirect("/")

    u = session["usuario"]
    loja = USUARIOS[u]["loja"]

    lista = [o for o in carregar() if o.get("loja") == loja]

    return render_template("historico.html", lista=lista)

# ================= FINANCEIRO =================
@app.route("/financeiro", methods=["GET","POST"])
def financeiro():
    if not session.get("logado"):
        return redirect("/")

    if not session.get("fin_ok"):
        if request.method == "POST":
            if request.form.get("senha") == "jesus":
                session["fin_ok"] = True
                return redirect("/financeiro")
        return render_template("financeiro_login.html")

    lista = carregar()

    total = sum(float(o.get("valor",0)) for o in lista)
    custo = sum(float(o.get("custo",0)) for o in lista)
    frete = sum(float(o.get("frete",0)) for o in lista)
    lucro = total - custo - frete

    return render_template("financeiro.html",
        lista=lista,
        total=total,
        custo=custo,
        frete=frete,
        lucro=lucro
    )

# ================= MARCAR PAGO =================
@app.route("/pagar/<numero>")
def pagar(numero):
    lista = carregar()
    for o in lista:
        if o["numero"] == numero:
            o["status"] = "pago"
    salvar(lista)
    return redirect("/financeiro")

# ================= CANCELAR OS =================
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

# ================= RAILWAY =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
