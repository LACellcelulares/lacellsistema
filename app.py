from flask import Flask, render_template, request, redirect, session, send_file
import os, json
from datetime import datetime

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# 🔥 GOOGLE DRIVE
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials

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

# ------------------ GOOGLE DRIVE ------------------

def conectar_drive():
    scope = ["https://www.googleapis.com/auth/drive"]

    gauth = GoogleAuth()
    gauth.credentials = ServiceAccountCredentials.from_json_keyfile_name(
        "credencial.json", scope
    )

    return GoogleDrive(gauth)

def backup_drive():
    try:
        if not os.path.exists(ARQUIVO_DB):
            return

        drive = conectar_drive()

        nome = f"os_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        arquivo = drive.CreateFile({
            'title': nome,
            'parents': [{'id': '1csPmYXDH9qLPY1dLx7e3XPsn5SDJwS2T'}]
        })

        arquivo.SetContentFile(ARQUIVO_DB)
        arquivo.Upload()

        print("✅ Backup enviado pro Drive")

    except Exception as e:
        print("❌ Erro no backup:", e)

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

    # 🔥 BACKUP AUTOMÁTICO
    backup_drive()

# ------------------ RESTO DO CÓDIGO (IGUAL) ------------------

def senha9():
    t = Table([["○"]*3 for _ in range(3)], 15, 15)
    t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),1,colors.black)]))
    return t

# (🔥 NÃO ALTEREI NADA ABAIXO, É SEU CÓDIGO ORIGINAL)
# 👉 TODO O RESTO CONTINUA EXATAMENTE IGUAL
