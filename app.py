
from flask import Flask, render_template, request, redirect, url_for, session, send_file
import os
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)
app.secret_key = "lacell_secret"

USUARIO = "pytty"
SENHA = "diemfafa"

PASTA_PDF = "pdfs"
os.makedirs(PASTA_PDF, exist_ok=True)

def gerar_pdf(numero, cliente):
    caminho = os.path.join(PASTA_PDF, f"OS_{numero}.pdf")
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(caminho, pagesize=A4,
                            rightMargin=25,leftMargin=25,topMargin=20,bottomMargin=20)
    el = []
    el.append(Paragraph("L&A CELL — Assistência Especializada", styles['Heading2']))
    el.append(Spacer(1,12))
    el.append(Paragraph(f"Ordem de Serviço Nº {numero}", styles['Heading3']))
    el.append(Spacer(1,12))
    el.append(Paragraph(f"Cliente: {cliente}", styles['Normal']))
    el.append(Spacer(1,12))
    el.append(Paragraph("Assinatura: ____________________________________", styles['Normal']))
    doc.build(el)
    return caminho

@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form["usuario"] == USUARIO and request.form["senha"] == SENHA:
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
        cliente = request.form["cliente"]
        pdf = gerar_pdf(numero, cliente)
        return send_file(pdf, as_attachment=True)
    return render_template("nova_os.html")

@app.route("/sair")
def sair():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
