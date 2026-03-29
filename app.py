from flask import Flask, render_template, request, redirect, session, send_file, abort
import os, json, shutil
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
        if os.path.exists(ARQUIVO_DB + ".bak"):
            with open(ARQUIVO_DB + ".bak", "r") as f:
                return json.load(f)
        return []

def salvar(lista):
    try:
        if os.path.exists(ARQUIVO_DB):
            shutil.copy(ARQUIVO_DB, ARQUIVO_DB + ".bak")

        with open(ARQUIVO_DB, "w") as f:
            json.dump(lista, f, indent=2)
    except Exception as e:
        print("ERRO AO SALVAR:", e)

# ================= PDF =================
def senha9():
    t = Table([["○"]*3 for _ in range(3)], 18, 18)
    t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),1,colors.black)]))
    return t

def gerar_pdf(n, d, loja, whats):
    try:
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
                f"CPF/CNPJ: {d.get('cpf','')}",
                f"IMEI: {d.get('imei','')}",
                f"Aparelho: {d.get('aparelho','')}",
                f"Defeito: {d.get('defeito','')}",
                f"Valor: R$ {d.get('valor',0)}",
                f"Pagamento: {d.get('pagamento','')}",
                f"Sinal: R$ {d.get('sinal',0)}",
                f"Restante: R$ {d.get('restante',0)}",
                f"Garantia: {d.get('garantia','')}",
                f"Senha: {d.get('senha','')}"
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

    except Exception as e:
        print("ERRO PDF:", e)
        return None

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

    return render_template(
        "painel.html",
        total_os=len(lista),
        total_valor=sum(float(o.get("valor",0)) for o in lista)
    )

# ================= NOVA OS =================
@app.route("/nova", methods=["GET","POST"])
def nova():
    if not session.get("logado"):
        return redirect("/")

    if request.method == "POST":
        try:
            u = session["usuario"]
            loja = USUARIOS[u]["loja"]

            lista = carregar()
            n = datetime.now().strftime("%Y%m%d%H%M%S")

            v = float(request.form.get("valor") or 0)
            s = float(request.form.get("sinal") or 0)

            d = {
                "numero": n,
                "loja": loja,
                "cliente": request.form.get("cliente") or "",
                "telefone": request.form.get("telefone") or "",
                "cpf": request.form.get("cpf") or "",
                "imei": request.form.get("imei") or "",
                "aparelho": request.form.get("aparelho") or "",
                "defeito": request.form.get("defeito") or "",
                "valor": v,
                "pagamento": request.form.get("pagamento") or "",
                "sinal": s,
                "restante": v - s,
                "garantia": request.form.get("garantia") or "",
                "senha": request.form.get("senha") or "",
                "entrega": request.form.get("entrega") or "",
                "data": datetime.now().strftime("%d/%m/%Y %H:%M")
            }

            lista.append(d)
            salvar(lista)

            pdf = gerar_pdf(n, d, loja, USUARIOS[u]["whatsapp"])

            if pdf:
                return send_file(pdf, as_attachment=True)

            return "Erro ao gerar PDF"

        except Exception as e:
            return f"ERRO: {str(e)}"

    return render_template("nova_os.html")

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
            "cpf": request.form.get("cpf"),
            "imei": request.form.get("imei"),
            "aparelho": request.form.get("aparelho"),
            "defeito": request.form.get("defeito"),
            "valor": float(request.form.get("valor") or 0),
            "sinal": float(request.form.get("sinal") or 0)
        })

        os_encontrada["restante"] = os_encontrada["valor"] - os_encontrada["sinal"]

        salvar(lista)
        return redirect("/historico")

    return render_template("editar.html", os=os_encontrada)

# ================= HISTORICO =================
@app.route("/historico")
def historico():
    if not session.get("logado"):
        return redirect("/")

    u = session["usuario"]
    loja = USUARIOS[u]["loja"]

    lista = [o for o in carregar() if o.get("loja") == loja]

    return render_template("historico.html", lista=lista)

# ================= SAIR =================
@app.route("/sair")
def sair():
    session.clear()
    return redirect("/")
