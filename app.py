from flask import Flask, render_template, request, redirect, session, send_file
import os
import json
from datetime import datetime
import matplotlib.pyplot as plt

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

app = Flask(__name__)
app.secret_key = "lacell_secret"

# ===== USUÁRIOS =====
USUARIOS = {
    "pytty": {
        "senha": "diemfafa",
        "loja": "L&A CELL - Assistência Técnica",
        "whatsapp": "(11) 98083-3734"
    },
    "adriano": {
        "senha": "jesus",
        "loja": "Millenium Solutions Atibaia Center",
        "whatsapp": "(11) 99846-8349"
    }
}

PASTA_PDF = "pdfs"
ARQUIVO_DB = "os.json"
os.makedirs(PASTA_PDF, exist_ok=True)

# ===== SALVAR OS =====
def salvar_os(dados):
    if not os.path.exists(ARQUIVO_DB):
        with open(ARQUIVO_DB, "w") as f:
            json.dump([], f)

    with open(ARQUIVO_DB, "r") as f:
        lista = json.load(f)

    lista.append(dados)

    with open(ARQUIVO_DB, "w") as f:
        json.dump(lista, f, indent=2)

# ===== DESENHO SENHA =====
def desenhar_padrao(padrao):
    pontos = [["○","○","○"],["○","○","○"],["○","○","○"]]
    if padrao:
        try:
            nums = [int(x) for x in padrao.split("-")]
            for n in nums:
                linha = (n-1)//3
                col = (n-1)%3
                pontos[linha][col] = "●"
        except:
            pass

    tabela = Table(pontos, colWidths=18, rowHeights=18)
    tabela.setStyle(TableStyle([
        ('GRID',(0,0),(-1,-1),1,colors.black),
        ('ALIGN',(0,0),(-1,-1),'CENTER')
    ]))
    return tabela

# ===== PDF OS A4 =====
def gerar_pdf(numero, dados, loja, whatsapp):
    caminho = os.path.join(PASTA_PDF, f"OS_{numero}.pdf")
    styles = getSampleStyleSheet()

    doc = SimpleDocTemplate(
        caminho,
        pagesize=A4,
        rightMargin=30,leftMargin=30,
        topMargin=30,bottomMargin=30
    )

    el = []

    def bloco(tipo):
        el.append(Paragraph(f"<b>{tipo}</b>", styles['Heading4']))
        el.append(Spacer(1,6))

        el.append(Paragraph(loja, styles['Heading3']))
        el.append(Paragraph(f"WhatsApp: {whatsapp}", styles['Normal']))
        el.append(Spacer(1,6))

        linhas = [
            f"ORDEM DE SERVIÇO Nº {numero}",
            f"Data: {dados['data']}",
            f"Data de Entrega: {dados['entrega']}",
            f"Cliente: {dados['cliente']}",
            f"Telefone: {dados['telefone']}",
            f"Aparelho: {dados['aparelho']}",
            f"IMEI: {dados['imei']}    CPF/CNPJ: {dados['cpf']}",
            f"Defeito: {dados['defeito']}",
            f"Valor: R$ {dados['valor']:.2f}",
            f"Forma de Pagamento: {dados['pagamento']}",
            f"Sinal: R$ {dados['sinal']:.2f}",
            f"Restante: R$ {dados['restante']:.2f}",
            f"Garantia: {dados['garantia']}",
            f"Senha: {dados['senha']}",
        ]

        for linha in linhas:
            el.append(Paragraph(linha, styles['Normal']))

        el.append(Spacer(1,6))
        el.append(Paragraph("Senha padrão (desenho):", styles['Normal']))
        el.append(desenhar_padrao(dados['senha_padrao']))

        el.append(Spacer(1,10))
        el.append(Paragraph("Assinatura: ____________________________________", styles['Normal']))
        el.append(Spacer(1,12))
        el.append(Paragraph("------------------------------------------------------------", styles['Normal']))
        el.append(Spacer(1,12))

    bloco("VIA DO CLIENTE")
    bloco("VIA DA LOJA")

    doc.build(el)
    return caminho

# ===== LOGIN =====
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario")
        senha = request.form.get("senha")

        if usuario in USUARIOS and USUARIOS[usuario]["senha"] == senha:
            session["logado"] = True
            session["usuario"] = usuario
            return redirect("/painel")

        return render_template("login.html", erro="Login inválido")

    return render_template("login.html")

@app.route("/painel")
def painel():
    if not session.get("logado"):
        return redirect("/")
    return render_template("painel.html")

# ===== NOVA OS =====
@app.route("/nova", methods=["GET","POST"])
def nova():
    if not session.get("logado"):
        return redirect("/")

    if request.method == "POST":
        numero = datetime.now().strftime("%Y%m%d%H%M")
        valor = float(request.form.get("valor") or 0)
        sinal = float(request.form.get("sinal") or 0)
        restante = valor - sinal

        dados = {
            "numero": numero,
            "cliente": request.form.get("cliente"),
            "telefone": request.form.get("telefone"),
            "aparelho": request.form.get("aparelho"),
            "imei": request.form.get("imei"),
            "cpf": request.form.get("cpf"),
            "defeito": request.form.get("defeito"),
            "valor": valor,
            "pagamento": request.form.get("pagamento"),
            "sinal": sinal,
            "restante": restante,
            "garantia": request.form.get("garantia"),
            "senha": request.form.get("senha"),
            "senha_padrao": request.form.get("senha_padrao"),
            "entrega": request.form.get("entrega"),
            "data": datetime.now().strftime("%d/%m/%Y %H:%M")
        }

        salvar_os(dados)

        usuario = session["usuario"]
        loja = USUARIOS[usuario]["loja"]
        whatsapp = USUARIOS[usuario]["whatsapp"]

        pdf = gerar_pdf(numero, dados, loja, whatsapp)
        return send_file(pdf, as_attachment=True)

    return render_template("nova_os.html")

# ===== SAIR =====
@app.route("/sair")
def sair():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
