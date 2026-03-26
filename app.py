from flask import Flask, render_template, request, redirect, session, send_file, abort
import os, json
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# Google Drive
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

app = Flask(__name__)
app.secret_key = "lacell_secret"

SENHA_FINANCEIRO = "jesus"

USUARIOS = {
    "pytty": {
        "senha": "diemfafa",
        "loja": "L&A CELL",
        "whatsapp": "(11) 98083-3734"
    },
    "adriano": {
        "senha": "jesus",
        "loja": "Millenium",
        "whatsapp": "(11) 99846-8349"
    }
}

PASTA_PDF = "pdfs"
ARQUIVO_DB = "os.json"
os.makedirs(PASTA_PDF, exist_ok=True)

# ================= GOOGLE DRIVE =================
SERVICE_ACCOUNT_FILE = r"C:\Users\wagner Casa\Downloads\pacific-aurora-491315-s1-ab1b66e00d32.json"
DRIVE_FOLDER_ID = "1csPmYXDH9qLPY1dLx7e3XPsn5SDJwS2T"

SCOPES = ['https://www.googleapis.com/auth/drive.file']
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
drive_service = build('drive', 'drive', credentials=credentials)

def upload_drive(file_path, file_name):
    try:
        file_metadata = {'name': file_name, 'parents':[DRIVE_FOLDER_ID]}
        media = MediaFileUpload(file_path, mimetype='application/pdf')
        drive_service.files().create(body=file_metadata, media_body=media).execute()
    except:
        pass  # evita quebrar se der erro

# ================= BANCO =================
def carregar_os():
    if not os.path.exists(ARQUIVO_DB):
        return []
    with open(ARQUIVO_DB, "r") as f:
        return json.load(f)

def salvar_os(d):
    lista = carregar_os()
    lista.append(d)
    with open(ARQUIVO_DB, "w") as f:
        json.dump(lista, f, indent=2)

# ================= PDF =================
def gerar_pdf_os(numero, dados, loja, whatsapp):
    caminho = os.path.join(PASTA_PDF, f"OS_{numero}.pdf")
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(caminho, pagesize=A4)
    el = []

    el.append(Paragraph(f"<b>{loja}</b>", styles["Heading2"]))
    el.append(Spacer(1,10))

    for k,v in dados.items():
        el.append(Paragraph(f"{k}: {v}", styles["Normal"]))

    doc.build(el)
    return caminho

# ================= LOGIN =================
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form.get("usuario","").lower()
        s = request.form.get("senha","")

        if u in USUARIOS and USUARIOS[u]["senha"] == s:
            session["logado"] = True
            session["usuario"] = u
            return redirect("/painel")

        return render_template("login.html", erro="Login inválido")

    return render_template("login.html")

# ================= PAINEL =================
@app.route("/painel")
def painel():
    if not session.get("logado"): return redirect("/")

    u = session["usuario"]

    lista = [o for o in carregar_os() if o["usuario"] == u]

    total = len(lista)
    valor = sum(float(o.get("valor",0)) for o in lista)

    return render_template("painel.html", total_os=total, total_valor=valor)

# ================= NOVA OS =================
@app.route("/nova", methods=["GET","POST"])
def nova():
    if not session.get("logado"): return redirect("/")

    if request.method == "POST":
        u = session["usuario"]
        loja = USUARIOS[u]["loja"]

        numero = datetime.now().strftime("%Y%m%d%H%M")

        valor = float(request.form.get("valor") or 0)
        sinal = float(request.form.get("sinal") or 0)

        custo = float(request.form.get("custo") or 0)
        frete = float(request.form.get("frete") or 0)

        lucro = valor - (custo + frete)

        d = {
            "numero": numero,
            "usuario": u,
            "loja": loja,
            "cliente": request.form.get("cliente"),
            "telefone": request.form.get("telefone"),
            "aparelho": request.form.get("aparelho"),
            "defeito": request.form.get("defeito"),
            "valor": valor,
            "sinal": sinal,
            "restante": valor - sinal,
            "custo": custo,
            "frete": frete,
            "lucro": lucro,
            "data": datetime.now().strftime("%d/%m/%Y")
        }

        salvar_os(d)

        pdf = gerar_pdf_os(numero, d, loja, USUARIOS[u]["whatsapp"])
        upload_drive(pdf, f"OS_{numero}.pdf")

        return send_file(pdf, as_attachment=True)

    return render_template("nova_os.html")

# ================= HISTORICO =================
@app.route("/historico")
def historico():
    if not session.get("logado"): return redirect("/")

    u = session["usuario"]
    q = request.args.get("q","").lower()

    lista = [o for o in carregar_os() if o["usuario"] == u]

    if q:
        lista = [o for o in lista if q in o["cliente"].lower()]

    return render_template("historico.html", lista=lista, busca=q)

# ================= FINANCEIRO =================
@app.route("/financeiro", methods=["GET","POST"])
def financeiro():

    if request.method == "POST":
        if request.form.get("senha") == SENHA_FINANCEIRO:
            session["financeiro"] = True
            return redirect("/financeiro")
        return "Senha incorreta"

    if not session.get("financeiro"):
        return render_template("senha_financeiro.html")

    u = session["usuario"]
    lista = [o for o in carregar_os() if o["usuario"] == u]

    total = sum(float(o.get("lucro",0)) for o in lista)

    return render_template("financeiro.html", lista=lista, total=total)

# ================= RELATORIO DIA =================
@app.route("/relatorio_dia")
def relatorio_dia():
    u = session["usuario"]
    hoje = datetime.now().strftime("%d/%m/%Y")

    lista = [o for o in carregar_os() if o["usuario"] == u and o["data"] == hoje]

    total = sum(float(o.get("valor",0)) for o in lista)

    return render_template("relatorio_dia.html", lista=lista, total=total)

# ================= RELATORIO =================
@app.route("/relatorio")
def relatorio():
    u = session["usuario"]
    lista = [o for o in carregar_os() if o["usuario"] == u]

    total = sum(float(o.get("valor",0)) for o in lista)

    return render_template("relatorio.html", qtd=len(lista), total=total)

# ================= SAIR =================
@app.route("/sair")
def sair():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
