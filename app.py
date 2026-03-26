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

# 🔒 senha financeiro
SENHA_FINANCEIRO = "jesus"

USUARIOS = {
    "pytty": {"senha": "diemfafa", "loja": "L&A CELL", "whatsapp": "(11)980833734"},
    "adriano": {"senha": "jesus", "loja": "Millenium", "whatsapp": "(11)998468349"}
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
        pass

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

# ================= PDF ORIGINAL (SEU PADRÃO) =================
def desenhar_padrao():
    pontos = [["○"] * 3 for _ in range(3)]
    t = Table(pontos, 18, 18)
    t.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER')
    ]))
    return t

def gerar_pdf_os(numero, dados, loja, whatsapp):
    caminho = os.path.join(PASTA_PDF, f"OS_{numero}.pdf")
    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    h4 = styles["Heading4"]

    doc = SimpleDocTemplate(caminho, pagesize=A4)
    elementos = []

    def bloco(titulo):
        elementos.append(Paragraph(f"<b>{titulo}</b>", h4))
        elementos.append(Spacer(1, 4))
        elementos.append(Paragraph(loja, normal))
        elementos.append(Paragraph(f"WhatsApp: {whatsapp}", normal))
        elementos.append(Spacer(1, 4))

        linhas = [
            f"OS Nº {numero}",
            f"Data: {dados['data']}",
            f"Entrega: {dados['entrega']}",
            f"Cliente: {dados['cliente']}",
            f"Telefone: {dados['telefone']}",
            f"Aparelho: {dados['aparelho']}",
            f"Defeito: {dados['defeito']}",
            f"Valor: R$ {dados['valor']:.2f}",
            f"Sinal: R$ {dados['sinal']:.2f}",
            f"Restante: R$ {dados['restante']:.2f}",
            f"Garantia: {dados['garantia']}",
            f"Senha: {dados['senha']}",
        ]

        for l in linhas:
            elementos.append(Paragraph(l, normal))

        elementos.append(Spacer(1, 6))
        elementos.append(Paragraph("Senha padrão:", normal))
        elementos.append(desenhar_padrao())

    bloco("VIA DO CLIENTE")
    elementos.append(Spacer(1, 10))
    bloco("VIA DA LOJA")

    doc.build(elementos)
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

        n = datetime.now().strftime("%Y%m%d%H%M")
        v = float(request.form.get("valor") or 0)
        s = float(request.form.get("sinal") or 0)

        custo = float(request.form.get("custo") or 0)
        frete = float(request.form.get("frete") or 0)

        d = {
            "numero": n,
            "usuario": u,
            "loja": loja,
            "cliente": request.form.get("cliente"),
            "telefone": request.form.get("telefone"),
            "aparelho": request.form.get("aparelho"),
            "defeito": request.form.get("defeito"),
            "valor": v,
            "sinal": s,
            "restante": v-s,
            "custo": custo,
            "frete": frete,
            "lucro": v - (custo + frete),
            "garantia": request.form.get("garantia"),
            "senha": request.form.get("senha"),
            "entrega": request.form.get("entrega"),
            "data": datetime.now().strftime("%d/%m/%Y")
        }

        salvar_os(d)

        pdf = gerar_pdf_os(n, d, loja, USUARIOS[u]["whatsapp"])
        upload_drive(pdf, f"OS_{n}.pdf")

        return send_file(pdf, as_attachment=True)

    return render_template("nova_os.html")

# ================= FINANCEIRO (BLINDADO) =================
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

# ================= SAIR =================
@app.route("/sair")
def sair():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
