from flask import Flask, render_template, request, redirect, session, send_file
import os, json
from datetime import datetime

from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)
app.secret_key = "lacell_secret"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_DB = os.path.join(BASE_DIR, "os.json")

# ================= USUARIOS =================
USUARIOS = {
    "adriano": "jesus",
    "pytty": "diemfafa"
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
def gerar_pdf(numero, dados):
    caminho = os.path.join(BASE_DIR, f"OS_{numero}.pdf")

    doc = SimpleDocTemplate(caminho, pagesize=A4)
    styles = getSampleStyleSheet()
    el = []

    el.append(Paragraph(f"<b>OS Nº {numero}</b>", styles["Title"]))
    el.append(Paragraph(f"Cliente: {dados.get('cliente','')}", styles["Normal"]))
    el.append(Paragraph(f"Telefone: {dados.get('telefone','')}", styles["Normal"]))
    el.append(Paragraph(f"Aparelho: {dados.get('aparelho','')}", styles["Normal"]))
    el.append(Paragraph(f"Valor: R$ {dados.get('valor',0)}", styles["Normal"]))
    el.append(Paragraph(f"Sinal: R$ {dados.get('sinal',0)}", styles["Normal"]))
    el.append(Paragraph(f"Restante: R$ {dados.get('restante',0)}", styles["Normal"]))
    el.append(Paragraph(f"Data: {dados.get('data','')}", styles["Normal"]))

    doc.build(el)
    return caminho

# ================= LOGIN (CORRIGIDO) =================
@app.route("/", methods=["GET","POST"])
def login():
    erro = None

    if request.method == "POST":
        usuario = (request.form.get("usuario") or "").strip().lower()
        senha = (request.form.get("senha") or "").strip()

        if usuario in USUARIOS and USUARIOS[usuario] == senha:
            session["logado"] = True
            session["usuario"] = usuario
            session["fin_ok"] = False
            return redirect("/painel")
        else:
            erro = "Usuário ou senha inválidos"

    return render_template("login.html", erro=erro)

# ================= PAINEL =================
@app.route("/painel")
def painel():
    if not session.get("logado"):
        return redirect("/")
    lista = carregar()
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

        nova_os = {
            "numero": n,
            "cliente": request.form.get("cliente"),
            "telefone": request.form.get("telefone"),
            "aparelho": request.form.get("aparelho"),
            "valor": v,
            "sinal": s,
            "restante": v - s,
            "custo": float(request.form.get("custo") or 0),
            "frete": float(request.form.get("frete") or 0),
            "status": "aberto",
            "data": datetime.now().strftime("%Y-%m-%d")
        }

        lista.append(nova_os)
        salvar(lista)

        pdf = gerar_pdf(n, nova_os)
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

# ================= EDITAR =================
@app.route("/editar/<numero>", methods=["GET","POST"])
def editar(numero):
    if not session.get("logado"):
        return redirect("/")

    lista = carregar()
    os_encontrada = next((x for x in lista if x["numero"] == numero), None)

    if not os_encontrada:
        return "OS não encontrada"

    if request.method == "POST":
        os_encontrada.update({
            "cliente": request.form.get("cliente"),
            "telefone": request.form.get("telefone"),
            "aparelho": request.form.get("aparelho"),
            "valor": float(request.form.get("valor") or 0),
            "sinal": float(request.form.get("sinal") or 0),
            "custo": float(request.form.get("custo") or 0),
            "frete": float(request.form.get("frete") or 0),
        })

        os_encontrada["restante"] = os_encontrada["valor"] - os_encontrada["sinal"]

        salvar(lista)
        return redirect("/financeiro")

    return render_template("editar.html", os=os_encontrada)

# ================= HISTORICO =================
@app.route("/historico")
def historico():
    if not session.get("logado"):
        return redirect("/")

    busca = request.args.get("busca","").lower()
    lista = carregar()

    if busca:
        lista = [
            o for o in lista
            if busca in (
                str(o.get("cliente","")).lower() +
                str(o.get("aparelho","")).lower() +
                str(o.get("telefone","")).lower()
            )
        ]

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

    if request.args.get("aberto") == "1":
        lista = [o for o in lista if o.get("status") != "pago"]

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

# ================= PAGAR =================
@app.route("/pagar/<numero>")
def pagar(numero):
    lista = carregar()
    for o in lista:
        if o["numero"] == numero:
            o["status"] = "pago"
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
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
