from flask import Flask, render_template, request, redirect, session, send_file
import os, json, io
from datetime import datetime

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

app = Flask(__name__)
app.secret_key = "lacell_secret"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_DB = os.path.join(BASE_DIR, "os.json")

USUARIOS = {
    "pytty": {"senha": "diemfafa", "loja": "L&A CELL Celulares", "whats": "(11)98083-3734"},
    "adriano": {"senha": "jesus", "loja": "MILLENNIUM SOLUTIONS ATIBAIA", "whats": "(11)99846-8349"}
}

# ------------------ JSON ------------------

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

    # 🔥 NÃO QUEBRA MAIS O SISTEMA
    try:
        backup_drive()
    except:
        print("⚠️ Backup falhou, mas sistema continua")

# ------------------ GOOGLE DRIVE (SEGURO) ------------------

def backup_drive():
    if not os.path.exists("credencial.json"):
        print("⚠️ credencial.json não encontrado")
        return

    try:
        from pydrive2.auth import GoogleAuth
        from pydrive2.drive import GoogleDrive
        from oauth2client.service_account import ServiceAccountCredentials

        scope = ["https://www.googleapis.com/auth/drive"]

        gauth = GoogleAuth()
        gauth.credentials = ServiceAccountCredentials.from_json_keyfile_name(
            "credencial.json", scope
        )

        drive = GoogleDrive(gauth)

        nome = f"os_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        arquivo = drive.CreateFile({
            'title': nome,
            'parents': [{'id': '1csPmYXDH9qLPY1dLx7e3XPsn5SDJwS2T'}]
        })

        arquivo.SetContentFile(ARQUIVO_DB)
        arquivo.Upload()

        print("✅ Backup OK")

    except Exception as e:
        print("❌ Erro no backup:", e)

# ------------------ PDF ------------------

def senha9():
    t = Table([["○"]*3 for _ in range(3)], 15, 15)
    t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),1,colors.black)]))
    return t

def gerar_pdf(numero, d):
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=15,
        rightMargin=15,
        topMargin=10,
        bottomMargin=10
    )

    styles = getSampleStyleSheet()

    def bloco(titulo):
        el = []

        el.append(Paragraph(f"<b>{titulo}</b>", styles["Heading4"]))
        el.append(Paragraph(d.get("loja",""), styles["Normal"]))
        el.append(Paragraph(f"WhatsApp: {d.get('whats','')}", styles["Normal"]))
        el.append(Spacer(1,4))

        dados = [
            f"OS Nº {numero}",
            f"Cliente: {d.get('cliente','')}",
            f"Aparelho: {d.get('aparelho','')}",
            f"Valor: R$ {d.get('valor',0)}",
            f"Restante: R$ {d.get('restante',0)}",
        ]

        for x in dados:
            el.append(Paragraph(x, styles["Normal"]))

        el.append(Spacer(1,6))
        el.append(Paragraph("Assinatura: ___________________________", styles["Normal"]))

        return el

    elementos = []
    elementos.extend(bloco("VIA CLIENTE"))
    elementos.append(Spacer(1,15))
    elementos.extend(bloco("VIA LOJA"))

    doc.build(elementos)
    buffer.seek(0)
    return buffer

# ------------------ ROTAS ------------------

@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        usuario = (request.form.get("usuario") or "").lower()
        senha = request.form.get("senha") or ""

        if usuario in USUARIOS and USUARIOS[usuario]["senha"] == senha:
            session["logado"] = True
            session["usuario"] = usuario
            session["fin_ok"] = False
            return redirect("/painel")

    return render_template("login.html")

@app.route("/painel")
def painel():
    if not session.get("logado"):
        return redirect("/")

    return render_template("painel.html")

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

    return render_template("financeiro.html", lista=lista)

@app.route("/os/<numero>")
def ver(numero):
    lista = carregar()
    o = next((x for x in lista if x["numero"] == numero), None)

    if not o:
        return "OS não encontrada"

    pdf = gerar_pdf(numero, o)
    return send_file(pdf, download_name=f"OS_{numero}.pdf")

@app.route("/nova", methods=["POST"])
def nova():
    lista = carregar()

    n = datetime.now().strftime("%Y%m%d%H%M%S")
    v = float(request.form.get("valor") or 0)
    s = float(request.form.get("sinal") or 0)

    d = {
        "numero": n,
        "cliente": request.form.get("cliente"),
        "aparelho": request.form.get("aparelho"),
        "valor": v,
        "restante": v - s,
        "status": "pago" if v - s <= 0 else "aberto"
    }

    lista.append(d)
    salvar(lista)

    return redirect("/painel")

if __name__ == "__main__":
    app.run(debug=True)
