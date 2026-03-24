from flask import Flask, render_template, request, redirect, url_for, session, send_file
import os
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)
app.secret_key = "lacell_secret"

USUARIO = "admin"
SENHA = "1234"

PASTA_PDF = "pdfs"
os.makedirs(PASTA_PDF, exist_ok=True)

def gerar_pdf(numero, dados):
    caminho = os.path.join(PASTA_PDF, f"OS_{numero}.pdf")
    styles = getSampleStyleSheet()

    doc = SimpleDocTemplate(caminho, pagesize=A4)
    el = []

    def bloco(tipo):
        el.append(Paragraph(f"<b>{tipo}</b>", styles['Heading3']))
        el.append(Spacer(1,10))

        el.append(Paragraph("L&A CELL - Assistência Técnica", styles['Heading2']))
        el.append(Spacer(1,10))

        el.append(Paragraph(f"ORDEM DE SERVIÇO Nº {numero}", styles['Normal']))
        el.append(Paragraph(f"Data: {dados['data']}", styles['Normal']))
        el.append(Paragraph(f"Cliente: {dados['cliente']}", styles['Normal']))
        el.append(Paragraph(f"Telefone: {dados['telefone']}", styles['Normal']))
        el.append(Paragraph(f"Aparelho: {dados['aparelho']}", styles['Normal']))
        el.append(Paragraph(f"IMEI: {dados['imei']} CPF/CNPJ: {dados['cpf']}", styles['Normal']))
        el.append(Paragraph(f"Defeito: {dados['defeito']}", styles['Normal']))
        el.append(Paragraph(f"Valor: R$ {dados['valor']}", styles['Normal']))
        el.append(Paragraph(f"Forma de Pagamento: {dados['pagamento']}", styles['Normal']))
        el.append(Paragraph(f"Sinal: R$ {dados['sinal']}", styles['Normal']))
        el.append(Paragraph(f"Restante: R$ {dados['restante']}", styles['Normal']))
        el.append(Paragraph(f"Garantia: {dados['garantia']}", styles['Normal']))
        el.append(Paragraph(f"Senha: {dados['senha']}", styles['Normal']))
        el.append(Paragraph(f"Senha padrão: {dados['senha_padrao']}", styles['Normal']))
        el.append(Paragraph("Assinatura: ____________________________", styles['Normal']))

        el.append(Spacer(1,20))
        el.append(Paragraph("----------------------------------------", styles['Normal']))
        el.append(Spacer(1,20))

    bloco("VIA DO CLIENTE")
    bloco("VIA DA LOJA")

    doc.build(el)
    return caminho


@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form.get("usuario") == USUARIO and request.form.get("senha") == SENHA:
            session["logado"] = True
            return redirect(url_for("painel"))
    return render_template("login.html")


@app.route("/painel")
def painel():
    if not session.get("logado"):
        return redirect(url_for("login"))
    return render_template("painel.html")


@app.route("/nova", methods=["GET","POST"])
def nova():
    if not session.get("logado"):
        return redirect(url_for("login"))

    if request.method == "POST":
        numero = datetime.now().strftime("%d%H%M%S")

        dados = {
            "cliente": request.form.get("cliente"),
            "telefone": request.form.get("telefone"),
            "aparelho": request.form.get("aparelho"),
            "imei": request.form.get("imei"),
            "cpf": request.form.get("cpf"),
            "defeito": request.form.get("defeito"),
            "valor": request.form.get("valor"),
            "pagamento": request.form.get("pagamento"),
            "sinal": request.form.get("sinal"),
            "restante": request.form.get("restante"),
            "garantia": request.form.get("garantia"),
            "senha": request.form.get("senha"),
            "senha_padrao": request.form.get("senha_padrao"),
            "data": datetime.now().strftime("%d/%m/%Y %H:%M")
        }

        pdf = gerar_pdf(numero, dados)
        return send_file(pdf, as_attachment=True)

    return render_template("nova_os.html")


@app.route("/sair")
def sair():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
