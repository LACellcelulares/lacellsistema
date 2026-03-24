from flask import Flask, render_template, request, redirect, url_for, session, send_file
import os
import json
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

app = Flask(__name__)
app.secret_key = "lacell_secret"

USUARIO = "pytty"
SENHA = "diemfafa"

PASTA_PDF = "pdfs"
ARQUIVO_DB = "os.json"

os.makedirs(PASTA_PDF, exist_ok=True)

# SALVAR OS
def salvar_os(dados):
    if not os.path.exists(ARQUIVO_DB):
        with open(ARQUIVO_DB, "w") as f:
            json.dump([], f)

    with open(ARQUIVO_DB, "r") as f:
        lista = json.load(f)

    lista.append(dados)

    with open(ARQUIVO_DB, "w") as f:
        json.dump(lista, f, indent=2)


# SENHA PADRÃO
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

    tabela = Table(pontos, colWidths=20, rowHeights=20)
    tabela.setStyle(TableStyle([
        ('GRID',(0,0),(-1,-1),1,colors.black),
        ('ALIGN',(0,0),(-1,-1),'CENTER')
    ]))
    return tabela


# PDF
def gerar_pdf(numero, dados):
    caminho = os.path.join(PASTA_PDF, f"OS_{numero}.pdf")
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(caminho, pagesize=A4)
    el = []

    def bloco(tipo):
        el.append(Paragraph(f"<b>{tipo}</b>", styles['Heading3']))
        el.append(Spacer(1,10))

        el.append(Paragraph("L&A CELL - Assistência Técnica", styles['Heading2']))
        el.append(Paragraph("WhatsApp: (11) 98083-3734", styles['Normal']))
        el.append(Spacer(1,10))

        el.append(Paragraph(f"OS Nº {numero}", styles['Normal']))
        el.append(Paragraph(f"Data: {dados['data']}", styles['Normal']))
        el.append(Paragraph(f"Cliente: {dados['cliente']}", styles['Normal']))
        el.append(Paragraph(f"Telefone: {dados['telefone']}", styles['Normal']))
        el.append(Paragraph(f"Aparelho: {dados['aparelho']}", styles['Normal']))
        el.append(Paragraph(f"Defeito: {dados['defeito']}", styles['Normal']))
        el.append(Paragraph(f"Valor: R$ {dados['valor']}", styles['Normal']))
        el.append(Paragraph(f"Garantia: {dados['garantia']}", styles['Normal']))

        el.append(Paragraph("Senha padrão:", styles['Normal']))
        el.append(desenhar_padrao(dados['senha_padrao']))

        el.append(Spacer(1,10))
        el.append(Paragraph("Assinatura: ____________________", styles['Normal']))

        el.append(Spacer(1,20))
        el.append(Paragraph("--------------------------------", styles['Normal']))
        el.append(Spacer(1,20))

    bloco("CLIENTE")
    bloco("LOJA")

    doc.build(el)
    return caminho


# LOGIN
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form.get("usuario") == USUARIO and request.form.get("senha") == SENHA:
            session["logado"] = True
            return redirect("/painel")
        return render_template("login.html", erro="Erro login")
    return render_template("login.html")


# PAINEL
@app.route("/painel")
def painel():
    if not session.get("logado"):
        return redirect("/")
    return render_template("painel.html")


# NOVA OS
@app.route("/nova", methods=["GET","POST"])
def nova():
    if not session.get("logado"):
        return redirect("/")

    if request.method == "POST":
        numero = datetime.now().strftime("%Y%m%d%H%M")

        dados = {
            "numero": numero,
            "cliente": request.form.get("cliente"),
            "telefone": request.form.get("telefone"),
            "aparelho": request.form.get("aparelho"),
            "defeito": request.form.get("defeito"),
            "valor": request.form.get("valor"),
            "garantia": request.form.get("garantia"),
            "senha_padrao": request.form.get("senha_padrao"),
            "data": datetime.now().strftime("%d/%m/%Y %H:%M")
        }

        salvar_os(dados)
        pdf = gerar_pdf(numero, dados)
        return send_file(pdf, as_attachment=True)

    return render_template("nova_os.html")


# HISTÓRICO + BUSCA
@app.route("/historico")
def historico():
    if not session.get("logado"):
        return redirect("/")

    busca = request.args.get("busca", "").lower()

    if not os.path.exists(ARQUIVO_DB):
        lista = []
    else:
        with open(ARQUIVO_DB, "r") as f:
            lista = json.load(f)

    if busca:
        lista = [os for os in lista if busca in os["cliente"].lower() or busca in os["telefone"]]

    return render_template("historico.html", lista=lista)


# RELATÓRIO MENSAL
@app.route("/relatorio")
def relatorio():
    if not session.get("logado"):
        return redirect("/")

    mes_atual = datetime.now().strftime("%m/%Y")

    if not os.path.exists(ARQUIVO_DB):
        lista = []
    else:
        with open(ARQUIVO_DB, "r") as f:
            lista = json.load(f)

    total = 0
    qtd = 0

    for os_item in lista:
        if mes_atual in os_item["data"]:
            qtd += 1
            try:
                total += float(os_item["valor"])
            except:
                pass

    return render_template("relatorio.html", total=total, qtd=qtd)


# REIMPRIMIR
@app.route("/reimprimir/<numero>")
def reimprimir(numero):
    return send_file(os.path.join(PASTA_PDF, f"OS_{numero}.pdf"), as_attachment=True)


# SAIR
@app.route("/sair")
def sair():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
