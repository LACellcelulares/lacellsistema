from flask import Flask, render_template, request, redirect, session, send_file, abort
import os
import json
from datetime import datetime

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

app = Flask(__name__)
app.secret_key = "lacell_secret"

# ===== USUÁRIOS / LOJAS =====
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

# ===== BANCO JSON =====
def carregar_os():
    if not os.path.exists(ARQUIVO_DB):
        return []
    with open(ARQUIVO_DB, "r") as f:
        return json.load(f)

def salvar_os(dados):
    lista = carregar_os()
    lista.append(dados)
    with open(ARQUIVO_DB, "w") as f:
        json.dump(lista, f, indent=2)

# ===== DESENHO SENHA PADRÃO =====
def desenhar_padrao():
    pontos = [["○","○","○"],["○","○","○"],["○","○","○"]]
    tabela = Table(pontos, colWidths=22, rowHeights=22)
    tabela.setStyle(TableStyle([
        ('GRID',(0,0),(-1,-1),1,colors.black),
        ('ALIGN',(0,0),(-1,-1),'CENTER')
    ]))
    return tabela

# ===== PDF OS — 2 VIAS A4 =====
def gerar_pdf_os(numero, dados, loja, whatsapp):
    caminho = os.path.join(PASTA_PDF, f"OS_{numero}.pdf")
    styles = getSampleStyleSheet()

    doc = SimpleDocTemplate(caminho, pagesize=A4,
        rightMargin=30,leftMargin=30,topMargin=25,bottomMargin=25)

    el = []

    def bloco(titulo):
        el.append(Paragraph(f"<b>{titulo}</b>", styles['Heading4']))
        el.append(Spacer(1,6))
        el.append(Paragraph(loja, styles['Heading2']))
        el.append(Paragraph(f"WhatsApp: {whatsapp}", styles['Normal']))
        el.append(Spacer(1,6))

        linhas = [
            f"ORDEM DE SERVIÇO Nº {numero}",
            f"Data: {dados['data']}",
            f"Entrega: {dados['entrega']}",
            f"Cliente: {dados['cliente']}",
            f"Telefone: {dados['telefone']}",
            f"Aparelho: {dados['aparelho']}",
            f"IMEI: {dados['imei']}    CPF/CNPJ: {dados['cpf']}",
            f"Defeito: {dados['defeito']}",
            f"Valor: R$ {dados['valor']:.2f}",
            f"Pagamento: {dados['pagamento']}",
            f"Sinal: R$ {dados['sinal']:.2f}",
            f"Restante: R$ {dados['restante']:.2f}",
            f"Garantia: {dados['garantia']}",
            f"Senha Numérica: {dados['senha']}",
        ]

        for l in linhas:
            el.append(Paragraph(l, styles['Normal']))

        el.append(Spacer(1,8))
        el.append(Paragraph("Senha Padrão:", styles['Normal']))
        el.append(Spacer(1,4))
        el.append(desenhar_padrao())

        el.append(Spacer(1,14))
        el.append(Paragraph("Assinatura Cliente: _________________________________", styles['Normal']))
        el.append(Spacer(1,10))
        el.append(Paragraph("Assinatura Loja: ____________________________________", styles['Normal']))

    bloco("VIA DO CLIENTE")
    el.append(Spacer(1,14))
    el.append(Paragraph("✂️ --------------------------------------------------------------", styles['Normal']))
    el.append(Spacer(1,14))
    bloco("VIA DA LOJA")

    doc.build(el)
    return caminho

# ===== PDF RELATÓRIO =====
def gerar_pdf_relatorio(lista, loja_nome, mes_ref):
    caminho = os.path.join(PASTA_PDF, f"RELATORIO_{mes_ref}.pdf")
    styles = getSampleStyleSheet()

    total_qtd = len(lista)
    total_valor = sum(float(o["valor"]) for o in lista)

    doc = SimpleDocTemplate(caminho, pagesize=A4)
    el = []

    el.append(Paragraph("RELATÓRIO MENSAL DE OS", styles['Heading2']))
    el.append(Spacer(1,8))
    el.append(Paragraph(f"Loja: {loja_nome}", styles['Normal']))
    el.append(Paragraph(f"Mês: {mes_ref}", styles['Normal']))
    el.append(Paragraph(f"Total OS: {total_qtd}", styles['Normal']))
    el.append(Paragraph(f"Faturamento: R$ {total_valor:.2f}", styles['Normal']))
    el.append(Spacer(1,12))

    dados_tabela = [["OS","Cliente","Aparelho","Valor"]]
    for o in lista:
        dados_tabela.append([
            o["numero"], o["cliente"], o["aparelho"],
            f"R$ {float(o['valor']):.2f}"
        ])

    tabela = Table(dados_tabela, colWidths=[80,150,150,80])
    tabela.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.lightgrey),
        ('GRID',(0,0),(-1,-1),1,colors.black),
        ('ALIGN',(3,1),(3,-1),'RIGHT')
    ]))

    el.append(tabela)
    doc.build(el)
    return caminho

# ===== LOGIN =====
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario","").strip().lower()
        senha = request.form.get("senha","").strip()

        if usuario in USUARIOS and USUARIOS[usuario]["senha"] == senha:
            session["logado"] = True
            session["usuario"] = usuario
            return redirect("/painel")

        return render_template("login.html", erro="Usuário ou senha inválidos")

    return render_template("login.html")

# ===== PAINEL =====
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
        usuario = session["usuario"]
        numero = datetime.now().strftime("%Y%m%d%H%M")

        valor = float(request.form.get("valor") or 0)
        sinal = float(request.form.get("sinal") or 0)

        dados = {
            "numero": numero,
            "loja": usuario,
            "cliente": request.form.get("cliente"),
            "telefone": request.form.get("telefone"),
            "aparelho": request.form.get("aparelho"),
            "imei": request.form.get("imei"),
            "cpf": request.form.get("cpf"),
            "defeito": request.form.get("defeito"),
            "valor": valor,
            "pagamento": request.form.get("pagamento"),
            "sinal": sinal,
            "restante": valor - sinal,
            "garantia": request.form.get("garantia"),
            "senha": request.form.get("senha"),
            "entrega": request.form.get("entrega"),
            "data": datetime.now().strftime("%d/%m/%Y %H:%M")
        }

        salvar_os(dados)

        loja_nome = USUARIOS[usuario]["loja"]
        whatsapp = USUARIOS[usuario]["whatsapp"]

        pdf = gerar_pdf_os(numero, dados, loja_nome, whatsapp)
        return send_file(pdf, as_attachment=True)

    return render_template("nova_os.html")

# ===== HISTÓRICO + BUSCA =====
@app.route("/historico")
def historico():
    if not session.get("logado"):
        return redirect("/")

    usuario = session["usuario"]
    busca = request.args.get("q","").lower()

    lista = carregar_os()
    lista = [o for o in lista if o.get("loja")==usuario]

    if busca:
        lista = [
            o for o in lista
            if busca in o["cliente"].lower()
            or busca in o["aparelho"].lower()
            or busca in o["numero"].lower()
        ]

    return render_template("historico.html", lista=lista, busca=busca)

# ===== VISUALIZAR OS =====
@app.route("/os/<numero>")
def ver_os(numero):
    if not session.get("logado"):
        return redirect("/")

    usuario = session["usuario"]
    lista = carregar_os()

    os_encontrada = next((o for o in lista if o["numero"]==numero and o["loja"]==usuario), None)
    if not os_encontrada:
        abort(404)

    loja_nome = USUARIOS[usuario]["loja"]
    whatsapp = USUARIOS[usuario]["whatsapp"]

    pdf = gerar_pdf_os(numero, os_encontrada, loja_nome, whatsapp)
    return send_file(pdf)

# ===== RELATÓRIO =====
@app.route("/relatorio")
def relatorio():
    if not session.get("logado"):
        return redirect("/")

    usuario = session["usuario"]
    loja_nome = USUARIOS[usuario]["loja"]
    mes_ref = datetime.now().strftime("%m-%Y")

    lista = carregar_os()
    lista = [o for o in lista if o.get("loja")==usuario]

    pdf = gerar_pdf_relatorio(lista, loja_nome, mes_ref)
    return send_file(pdf, as_attachment=True)

# ===== SAIR =====
@app.route("/sair")
def sair():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
