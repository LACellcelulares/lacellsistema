from flask import Flask, render_template, request, redirect, session, send_file
import os, json
from datetime import datetime
import requests

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

app = Flask(__name__)
app.secret_key = "lacell_secret"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PASTA_PDF = os.path.join(BASE_DIR, "pdfs")
os.makedirs(PASTA_PDF, exist_ok=True)

# -----------------------------------------
# CONFIGURAÇÃO DOS USUÁRIOS + DROPBOX
# -----------------------------------------
DROPBOX_TOKEN = "sl.u.AGZ4ZN5fgJtTVSKYe-r_9Jw1nf3vhW-I5pWwNYvi9xXux6m-rCtGF9_9PggQd9HK0zstOGmEH2JG0HZGtEmra7TaPzNd0xOhBmN4hhdfBD_yl3zPokOIUGZcAMgNTDQS6S5iCgZ_CZ9AddffMeqRwgvV1APXsbfMBk9pifnX720uesXMjtSWqmuwLPXM1NiT6_hsNHJthDGfp-cdlrAWWFNT7p5dbi7XCeQ2KB4Uqy1g_Aej5QrOxUsCDVbkwUqiYWyheMjWV5j3ZLnbnZgY8CPTeyYV4LHbDyWS1wzlrRb4sx5wWGfD4tqJayc6fkQ5-Jwk-fqb3FT-SAIkf-MpSg1iUotodGvBPwVkd7VAWIZl1I9aYA317zP-t-YV3EXgJIyKcuId1wOH7VBTbgJNHGdnT1BVQEyfcujRkVOl0Y6kDuQFv7OP8W0mvCJfZSUaLuyoLwEN2t1SuulX_W7O2-dPTWdBOCfEUbLUe8RfTSV7lmRmtUJgKd4JHtspXtnAv5cz4lL2Cl2wiXkWy0pB4sLl0RLA9xNv9fzX_atUDlw8YMfaAuevUde_WwA98ATlhfs4mt5h0l5qjq68FLCrXVgS-m1RubzyNVNdcXo8pseib1TLuVmGyTeShu7cokPx8hbO51VkIh2JuyZzyjDwlZYiPTbt8U_x6H1p-Sywawq1Lbd6Zkrubczm5hYUUfMYeWrDD08I5yxI_Z5fsMHQd-TxuVGsUo-5PpA3_C04f96d8yK8PGmDonw53KTxmD2B9VgBo1Ly-ds7-QhT72SyM4EIdFNeZ0PyDKjSuJZxzoTCaIMJxS298qBs8qS3X-7X5ftkVlsUKikwyg0GhRpiR6o5PGB_WHOpNgoVpYIVyZV3vrpJgBbAEl3vwcD7bwt1sj-yT8k6qqerBOYJC79e59QJGt3DwAFf33L5DJPA0XLtHJru-4eBfHbTfdWYOuf8Q-qqFZtkSX3QLoEGfXIN5WyaMFQ8-9D-lyFze50NEZ8qjrM9ES8Ni-0nVa-g-IsV2gXeuvGVx_Le2ahPidB2lbKI-acO66lnKViu0lbG9ftnbKZIannJiP-kHNv-OG65kh8BHWa-wpGKMrcBulepc2URkH_z9YnhXaNvzxErtvZszmPIY-N-Ek7wKW9OjTBVhiHm3d2blLC_-WzIFUTsBbrCHh54HReHZHnQRmczn3mxqbDL4y-e5B2cSFfe5hJuiv8joxin9QL0BNyyCOL579ZUhYJOwY9kEFtJrrI9z5bTvbQfcCJxUVJx2WZrEPkWGeazbnHaS3zvaS-MZN0Zjhy2KJtdX1puaOQkq7XV6TAKuMX_WLtwNX5SmBba9aMWdbbY_2ZsCfWd0YOyBs7-F0ufaOKfiBJ5nUg9WyKZAQAm0suC0R_px3ALT1aEn0Ir3dNqz5y-Dk1jbShHoIN59lHt7zcYQUlpnIoE-M30zb0fQw"

USUARIOS = {
    "pytty": {
        "senha": "diemfafa",
        "loja": "L&A CELL Celulares",
        "whats": "(11)98083-3734",
        "dropbox": "/os_pytty.json",
        "horario": True
    },
    "adriano": {
        "senha": "jesus",
        "loja": "MILLENNIUM SOLUTIONS ATIBAIA",
        "whats": "(11)99846-8349",
        "dropbox": "/os_adriano.json",
        "horario": False
    }
}

# -----------------------------------------
# BANCO POR LOJA
# -----------------------------------------
def caminho_db(loja):
    nome = loja.lower().replace(" ", "_").replace("&", "e")
    return os.path.join(BASE_DIR, f"os_{nome}.json")

def carregar(loja):
    arq = caminho_db(loja)
    if not os.path.exists(arq):
        return []
    try:
        with open(arq, "r") as f:
            return json.load(f)
    except:
        return []

def salvar(lista, loja):
    arq = caminho_db(loja)

    with open(arq, "w") as f:
        json.dump(lista, f, indent=2)

    backup = datetime.now().strftime(f"backup_{loja.replace(' ','_')}_%Y%m%d_%H%M%S.json")
    with open(backup, "w") as f:
        json.dump(lista, f, indent=2)

    usuario = None
    for u, info in USUARIOS.items():
        if info["loja"] == loja:
            usuario = u
            break

    if not usuario:
        return

    dropbox_path = USUARIOS[usuario]["dropbox"]

    try:
        url = "https://content.dropboxapi.com/2/files/upload"

        headers = {
            "Authorization": f"Bearer {DROPBOX_TOKEN}",
            "Dropbox-API-Arg": json.dumps({
                "path": dropbox_path,
                "mode": "overwrite"
            }),
            "Content-Type": "application/octet-stream"
        }

        requests.post(url, headers=headers, data=json.dumps(lista))

    except:
        pass

# -----------------------------------------
# PDF
# -----------------------------------------
def senha9():
    t = Table([["○"] * 3 for _ in range(3)], 15, 15)
    t.setStyle(TableStyle([("GRID", (0,0), (-1,-1), 1, colors.black)]))
    return t

def gerar_pdf(numero, d, horario=False):
    caminho = os.path.join(PASTA_PDF, f"OS_{numero}.pdf")

    doc = SimpleDocTemplate(
        caminho,
        pagesize=A4,
        leftMargin=15,
        rightMargin=15,
        topMargin=10,
        bottomMargin=10
    )

    styles = getSampleStyleSheet()
    elementos = []

    if horario:
        elementos.append(Paragraph("""
        <b>Horário de funcionamento:</b><br/>
        Seg–Qua: 09:00–17:30<br/>
        <b>Qui: 12:00–17:30</b><br/>
        Sex: 09:00–17:30<br/>
        Sáb: 09:00–14:00<br/>
        Dom: Fechado<br/>
        """, styles["Normal"]))
        elementos.append(Spacer(1,6))

    def bloco(titulo):
        el = []
        el.append(Paragraph(f"<b>{titulo}</b>", styles["Heading4"]))
        el.append(Paragraph(d.get("loja",""), styles["Normal"]))
        el.append(Paragraph(f"WhatsApp: {d.get('whats','')}", styles["Normal"]))
        el.append(Spacer(1,4))

        campos = [
            f"OS Nº {numero}",
            f"Data: {d['data']}",
            f"Cliente: {d['cliente']}",
            f"Telefone: {d['telefone']}",
            f"CPF/CNPJ: {d['cpf']}",
            f"IMEI: {d['imei']}",
            f"Aparelho: {d['aparelho']}",
            f"Defeito: {d['defeito']}",
            f"Valor: R$ {d['valor']}",
            f"Sinal: R$ {d['sinal']}",
            f"Restante: R$ {d['restante']}",
            f"Pagamento: {d['pagamento']}",
            f"Entrega: {d['entrega']}",
            f"Garantia: {d['garantia']}",
            f"Senha: {d['senha']}"
        ]

        for c in campos:
            el.append(Paragraph(c, styles["Normal"]))

        el.append(Spacer(1,4))
        el.append(Paragraph("Desenho da senha:", styles["Normal"]))
        el.append(senha9())
        el.append(Spacer(1,10))
        el.append(Paragraph("Assinatura: ___________________________", styles["Normal"]))

        return el

    elementos += bloco("VIA CLIENTE")
    elementos.append(Spacer(1,10))

    linha = Table([[""]], colWidths=[520])
    linha.setStyle(TableStyle([("LINEABOVE", (0,0), (-1,-1), 1, colors.black)]))
    elementos.append(linha)

    elementos.append(Spacer(1,10))
    elementos += bloco("VIA LOJA")

    doc.build(elementos)
    return caminho

# -----------------------------------------
# ROTAS
# -----------------------------------------
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
    lista = carregar(loja)

    return render_template("painel.html", total_os=len(lista))

@app.route("/nova", methods=["GET","POST"])
def nova():
    if not session.get("logado"):
        return redirect("/")

    usuario = session["usuario"]
    loja = USUARIOS[usuario]["loja"]
    whats = USUARIOS[usuario]["whats"]
    horario = USUARIOS[usuario]["horario"]

    if request.method == "POST":
        lista = carregar(loja)
        n = datetime.now().strftime("%Y%m%d%H%M%S")

        v = float(request.form.get("valor") or 0)
        s = float(request.form.get("sinal") or 0)

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
            "status": "pago" if v - s <= 0 else "aberto",
            "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "loja": loja,
            "whats": whats
        }

        lista.append(d)
        salvar(lista, loja)

        pdf = gerar_pdf(n, d, horario)
        return send_file(pdf, as_attachment=True)

    return render_template("nova_os.html")

@app.route("/os/<numero>")
def ver(numero):
    if not session.get("logado"):
        return redirect("/")
        
    usuario = session["usuario"]
    loja = USUARIOS[usuario]["loja"]
    horario = USUARIOS[usuario]["horario"]

    lista = carregar(loja)
    o = next((x for x in lista if x["numero"] == numero), None)

    if not o:
        return "OS não encontrada"

    pdf = gerar_pdf(numero, o, horario)
    return send_file(pdf)

@app.route("/historico")
def historico():
    if not session.get("logado"):
        return redirect("/")

    usuario = session["usuario"]
    loja = USUARIOS[usuario]["loja"]

    busca = (request.args.get("busca") or "").lower()
    lista = carregar(loja)

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
    lista = carregar(loja)

    busca = (request.args.get("busca") or "").lower()
    if busca:
        lista = [o for o in lista if busca in str(o).lower()]

    if request.args.get("aberto") == "1":
        lista = [o for o in lista if float(o["restante"]) > 0]

    total = sum(float(o["valor"]) - float(o["restante"]) for o in lista)
    total_aberto = sum(float(o["restante"]) for o in lista)
    custo = sum(float(o["custo"]) for o in lista)
    frete = sum(float(o["frete"]) for o in lista)
    lucro = total - custo - frete

    lucro_por_dia = {}
    for o in lista:
        recebido = float(o["valor"]) - float(o["restante"])
        lucro_os = recebido - float(o["custo"]) - float(o["frete"])
        data = o["data"]

        if data not in lucro_por_dia:
            lucro_por_dia[data] = 0
        lucro_por_dia[data] += lucro_os

    return render_template(
        "financeiro.html",
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
    usuario = session["usuario"]
    loja = USUARIOS[usuario]["loja"]
    lista = carregar(loja)

    valor = float(request.form.get("valor") or 0)

    for o in lista:
        if o["numero"] == numero:
            o["restante"] = max(0, float(o["restante"]) - valor)
            o["status"] = "pago" if o["restante"] <= 0 else "aberto"

    salvar(lista, loja)
    return redirect("/financeiro")

@app.route("/pagar/<numero>")
def pagar(numero):
    usuario = session["usuario"]
    loja = USUARIOS[usuario]["loja"]
    lista = carregar(loja)

    for o in lista:
        if o["numero"] == numero:
            o["restante"] = 0
            o["status"] = "pago"

    salvar(lista, loja)
    return redirect("/financeiro")

@app.route("/cancelar/<numero>")
def cancelar(numero):
    usuario = session["usuario"]
    loja = USUARIOS[usuario]["loja"]
    lista = carregar(loja)

    lista = [o for o in lista if o["numero"] != numero]
    salvar(lista, loja)

    return redirect("/financeiro")

@app.route("/editar/<numero>", methods=["GET","POST"])
def editar(numero):
    usuario = session["usuario"]
    loja = USUARIOS[usuario]["loja"]
    lista = carregar(loja)

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
        os_edit["status"] = "pago" if os_edit["restante"] <= 0 else "aberto"

        os_edit["custo"] = float(request.form.get("custo") or 0)
        os_edit["frete"] = float(request.form.get("frete") or 0)

        os_edit["pagamento"] = request.form.get("pagamento")
        os_edit["entrega"] = request.form.get("entrega")
        os_edit["garantia"] = request.form.get("garantia")
        os_edit["senha"] = request.form.get("senha")

        salvar(lista, loja)
        return redirect("/financeiro")

    return render_template("editar.html", os=os_edit)

@app.route("/sair")
def sair():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
