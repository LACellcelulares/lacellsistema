from flask import Flask, render_template, request, redirect, session, send_file
import os, json
from datetime import datetime

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

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

# 🔥 PDF NOVO (1 folha, 2 vias lado a lado)
def gerar_pdf(numero, d):
    caminho = os.path.join(PASTA_PDF, f"OS_{numero}.pdf")
    doc = SimpleDocTemplate(caminho, pagesize=A4)
    styles = getSampleStyleSheet()
    el = []

    def conteudo():
        dados = []

        def linha(label, valor, negrito=False):
            if negrito:
                return f"<b>{label}: {valor}</b>"
            return f"{label}: {valor}"

        dados.append(Paragraph(f"<b>OS Nº {numero}</b>", styles["Normal"]))
        dados.append(Paragraph(linha("Data", d.get('data','')), styles["Normal"]))
        dados.append(Paragraph(linha("Cliente", d.get('cliente','')), styles["Normal"]))
        dados.append(Paragraph(linha("Telefone", d.get('telefone','')), styles["Normal"]))
        dados.append(Paragraph(linha("Aparelho", d.get('aparelho','')), styles["Normal"]))
        dados.append(Paragraph(linha("Defeito", d.get('defeito','')), styles["Normal"]))

        dados.append(Spacer(1,5))

        dados.append(Paragraph(linha("Valor", f"R$ {d.get('valor',0)}", True), styles["Normal"]))
        dados.append(Paragraph(linha("Sinal", f"R$ {d.get('sinal',0)}"), styles["Normal"]))
        dados.append(Paragraph(linha("Em aberto", f"R$ {d.get('restante',0)}", True), styles["Normal"]))

        dados.append(Spacer(1,5))

        dados.append(Paragraph(linha("Pagamento", d.get('pagamento','')), styles["Normal"]))
        dados.append(Paragraph(linha("Entrega", d.get('entrega','')), styles["Normal"]))
        dados.append(Paragraph(linha("Garantia", d.get('garantia','')), styles["Normal"]))

        dados.append(Spacer(1,5))

        dados.append(Paragraph(linha("Senha", d.get('senha','')), styles["Normal"]))

        dados.append(Spacer(1,10))

        dados.append(Paragraph("<b>Assinatura:</b> ___________________________", styles["Normal"]))

        dados.append(Spacer(1,5))

        dados.append(Paragraph(
            "Obs: Garantia não cobre queda, trincos, riscos ou contato com água.",
            styles["Normal"]
        ))

        dados.append(Paragraph(
            "Após 30 dias sem retirada, o aparelho será desmontado para cobrir despesas.",
            styles["Normal"]
        ))

        return dados

    titulo = Paragraph(f"<b>{d.get('loja','')}</b><br/>WhatsApp: {d.get('whats','')}", styles["Normal"])

    tabela = Table([
        [titulo, titulo],
        [conteudo(), conteudo()]
    ], colWidths=[270,270])

    tabela.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))

    el.append(tabela)

    doc.build(el)
    return caminho

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

    usuario = session["usuario"]
    loja = USUARIOS[usuario]["loja"]

    lista = [o for o in carregar() if o.get("loja") == loja]
    return render_template("painel.html", total_os=len(lista))

@app.route("/nova", methods=["GET","POST"])
def nova():
    if not session.get("logado"):
        return redirect("/")

    if request.method == "POST":
        lista = carregar()
        n = datetime.now().strftime("%Y%m%d%H%M%S")

        v = float(request.form.get("valor") or 0)
        s = float(request.form.get("sinal") or 0)

        usuario = session["usuario"]

        d = {
            "numero": n,
            "cliente": request.form.get("cliente"),
            "telefone": request.form.get("telefone"),
            "cpf": request.form.get("cpf"),
            "imei": request.form.get("imei"),
            "aparelho": request.form.get("aparelho"),
            "defeito": request.form.get("defeito"),
            "valor": v,
            "sinal": s,
            "restante": v - s,
            "custo": float(request.form.get("custo") or 0),
            "frete": float(request.form.get("frete") or 0),
            "pagamento": request.form.get("pagamento"),
            "entrega": request.form.get("entrega"),
            "garantia": request.form.get("garantia"),
            "senha": request.form.get("senha"),
            "status": "aberto",
            "data": datetime.now().strftime("%Y-%m-%d"),
            "loja": USUARIOS[usuario]["loja"],
            "whats": USUARIOS[usuario]["whats"]
        }

        lista.append(d)
        salvar(lista)

        pdf = gerar_pdf(n, d)
        return send_file(pdf, as_attachment=True)

    return render_template("nova_os.html")

@app.route("/os/<numero>")
def ver(numero):
    if not session.get("logado"):
        return redirect("/")

    lista = carregar()
    o = next((x for x in lista if x["numero"] == numero), None)

    if not o:
        return "OS não encontrada"

    pdf = gerar_pdf(numero, o)
    return send_file(pdf)

@app.route("/historico")
def historico():
    if not session.get("logado"):
        return redirect("/")

    usuario = session["usuario"]
    loja = USUARIOS[usuario]["loja"]

    busca = (request.args.get("busca") or "").lower()
    lista = [o for o in carregar() if o.get("loja") == loja]

    if busca:
        lista = [o for o in lista if busca in str(o).lower()]

    return render_template("historico.html", lista=lista)

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

    usuario = session["usuario"]
    loja = USUARIOS[usuario]["loja"]

    busca = (request.args.get("busca") or "").lower()
    lista = [o for o in carregar() if o.get("loja") == loja]

    if busca:
        lista = [o for o in lista if busca in str(o).lower()]

    if request.args.get("aberto") == "1":
        lista = [o for o in lista if float(o.get("restante",0)) > 0]

    total = sum(float(o.get("valor",0)) - float(o.get("restante",0)) for o in lista)
    total_aberto = sum(float(o.get("restante",0)) for o in lista)

    custo = sum(float(o.get("custo",0)) for o in lista)
    frete = sum(float(o.get("frete",0)) for o in lista)
    lucro = total - custo - frete

    lucro_por_dia = {}
    for o in lista:
        recebido = float(o.get("valor",0)) - float(o.get("restante",0))
        data = o.get("data")

        lucro_os = recebido - float(o.get("custo",0)) - float(o.get("frete",0))

        if data not in lucro_por_dia:
            lucro_por_dia[data] = 0

        lucro_por_dia[data] += lucro_os

    return render_template("financeiro.html",
        lista=lista,
        total=total,
        total_aberto=total_aberto,
        custo=custo,
        frete=frete,
        lucro=lucro,
        lucro_por_dia=lucro_por_dia
    )

@app.route("/receber/<numero>", methods=["POST"])
def receber(numero):
    lista = carregar()
    valor_recebido = float(request.form.get("valor") or 0)

    for o in lista:
        if o["numero"] == numero:
            restante = float(o.get("restante", 0))
            restante -= valor_recebido

            if restante <= 0:
                o["restante"] = 0
                o["status"] = "pago"
            else:
                o["restante"] = restante

    salvar(lista)
    return redirect("/financeiro")

@app.route("/pagar/<numero>")
def pagar(numero):
    lista = carregar()
    for o in lista:
        if o["numero"] == numero:
            o["status"] = "pago"
            o["restante"] = 0
    salvar(lista)
    return redirect("/financeiro")

@app.route("/cancelar/<numero>")
def cancelar(numero):
    lista = [o for o in carregar() if o["numero"] != numero]
    salvar(lista)
    return redirect("/financeiro")

@app.route("/editar/<numero>", methods=["GET","POST"])
def editar(numero):
    if not session.get("logado"):
        return redirect("/")

    lista = carregar()
    os_edit = next((x for x in lista if x["numero"] == numero), None)

    if not os_edit:
        return "OS não encontrada"

    if request.method == "POST":
        os_edit["cliente"] = request.form.get("cliente")
        os_edit["telefone"] = request.form.get("telefone")
        os_edit["cpf"] = request.form.get("cpf")
        os_edit["imei"] = request.form.get("imei")
        os_edit["aparelho"] = request.form.get("aparelho")
        os_edit["defeito"] = request.form.get("defeito")

        v = float(request.form.get("valor") or 0)
        s = float(request.form.get("sinal") or 0)

        os_edit["valor"] = v
        os_edit["sinal"] = s
        os_edit["restante"] = v - s

        os_edit["custo"] = float(request.form.get("custo") or 0)
        os_edit["frete"] = float(request.form.get("frete") or 0)

        os_edit["pagamento"] = request.form.get("pagamento")
        os_edit["entrega"] = request.form.get("entrega")
        os_edit["garantia"] = request.form.get("garantia")
        os_edit["senha"] = request.form.get("senha")

        salvar(lista)
        return redirect("/financeiro")

    return render_template("editar.html", os=os_edit)

@app.route("/sair")
def sair():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
