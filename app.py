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

# 🔐 DROPBOX TOKEN
DROPBOX_TOKEN = "sl.u.AGZ4ZN5fgJtTVSKYe-r_9Jw1nf3vhW-I5pWwNYvi9xXux6m-rCtGF9_9PggQd9HK0zstOGmEH2JG0HZGtEmra7TaPzNd0xOhBmN4hhdfBD_yl3zPokOIUGZcAMgNTDQS6S5iCgZ_CZ9AddffMeqRwgvV1APXsbfMBk9pifnX720uesXMjtSWqmuwLPXM1NiT6_hsNHJthDGfp-cdlrAWWFNT7p5dbi7XCeQ2KB4Uqy1g_Aej5QrOxUsCDVbkwUqiYWyheMjWV5j3ZLnbnZgY8CPTeyYV4LHbDyWS1wzlrRb4sx5wWGfD4tqJayc6fkQ5-Jwk-fqb3FT-SAIkf-MpSg1iUotodGvBPwVkd7VAWIZl1I9aYA317zP-t-YV3EXgJIyKcuId1wOH7VBTbgJNHGdnT1BVQEyfcujRkVOl0Y6kDuQFv7OP8W0mvCJfZSUaLuyoLwEN2t1SuulX_W7O2-dPTWdBOCfEUbLUe8RfTSV7lmRmtUJgKd4JHtspXtnAv5cz4lL2Cl2wiXkWy0pB4sLl0RLA9xNv9fzX_atUDlw8YMfaAuevUde_WwA98ATlhfs4mt5h0l5qjq68FLCrXVgS-m1RubzyNVNdcXo8pseib1TLuVmGyTeShu7cokPx8hbO51VkIh2JuyZzyjDwlZYiPTbt8U_x6H1p-Sywawq1Lbd6Zkrubczm5hYUUfMYeWrDD08I5yxI_Z5fsMHQd-TxuVGsUo-5PpA3_C04f96d8yK8PGmDonw53KTxmD2B9VgBo1Ly-ds7-QhT72SyM4EIdFNeZ0PyDKjSuJZxzoTCaIMJxS298qBs8qS3X-7X5ftkVlsUKikwyg0GhRpiR6o5PGB_WHOpNgoVpYIVyZV3vrpJgBbAEl3vwcD7bwt1sj-yT8k6qqerBOYJC79e59QJGt3DwAFf33L5DJPA0XLtHJru-4eBfHbTfdWYOuf8Q-qqFZtkSX3QLoEGfXIN5WyaMFQ8-9D-lyFze50NEZ8qjrM9ES8Ni-0nVa-g-IsV2gXeuvGVx_Le2ahPidB2lbKI-acO66lnKViu0lbG9ftnbKZIannJiP-kHNv-OG65kh8BHWa-wpGKMrcBulepc2URkH_z9YnhXaNvzxErtvZszmPIY-N-Ek7wKW9OjTBVhiHm3d2blLC_-WzIFUTsBbrCHh54HReHZHnQRmczn3mxqbDL4y-e5B2cSFfe5hJuiv8joxin9QL0BNyyCOL579ZUhYJOwY9kEFtJrrI9z5bTvbQfcCJxUVJx2WZrEPkWGeazbnHaS3zvaS-MZN0Zjhy2KJtdX1puaOQkq7XV6TAKuMX_WLtwNX5SmBba9aMWdbbY_2ZsCfWd0YOyBs7-F0ufaOKfiBJ5nUg9WyKZAQAm0suC0R_px3ALT1aEn0Ir3dNqz5y-Dk1jbShHoIN59lHt7zcYQUlpnIoE-M30zb0fQw"

# 🔥 ARQUIVOS SEPARADOS PARA CADA LOJA
ARQUIVOS_DROPBOX = {
    "L&A CELL Celulares": "/os_pytty.json",
    "MILLENNIUM SOLUTIONS ATIBAIA": "/os_adriano.json"
}

ARQUIVOS_LOCAIS = {
    "L&A CELL Celulares": os.path.join(BASE_DIR, "os_pytty.json"),
    "MILLENNIUM SOLUTIONS ATIBAIA": os.path.join(BASE_DIR, "os_adriano.json")
}

# LOGINS
USUARIOS = {
    "pytty": {"senha": "diemfafa", "loja": "L&A CELL Celulares", "whats": "(11)98083-3734"},
    "adriano": {"senha": "jesus", "loja": "MILLENNIUM SOLUTIONS ATIBAIA", "whats": "(11)99846-8349"}
}

# ------------------ BANCO ------------------

def carregar(loja):
    arquivo = ARQUIVOS_LOCAIS[loja]
    if not os.path.exists(arquivo):
        return []
    try:
        with open(arquivo, "r") as f:
            return json.load(f)
    except:
        return []

def salvar(lista, loja):
    # LOCAL
    arquivo = ARQUIVOS_LOCAIS[loja]
    with open(arquivo, "w") as f:
        json.dump(lista, f, indent=2)

    # DROPBOX
    try:
        url = "https://content.dropboxapi.com/2/files/upload"
        headers = {
            "Authorization": f"Bearer {DROPBOX_TOKEN}",
            "Dropbox-API-Arg": json.dumps({
                "path": ARQUIVOS_DROPBOX[loja],
                "mode": "overwrite"
            }),
            "Content-Type": "application/octet-stream"
        }
        requests.post(url, headers=headers, data=json.dumps(lista))
    except:
        pass

# ------------------ PDF ------------------

def senha9():
    t = Table([["○"] * 3 for _ in range(3)], 15, 15)
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black)]))
    return t

def gerar_pdf(numero, d):
    caminho = os.path.join(PASTA_PDF, f"OS_{numero}.pdf")

    doc = SimpleDocTemplate(
        caminho,
        pagesize=A4,
        leftMargin=15, rightMargin=15,
        topMargin=10, bottomMargin=10
    )
    styles = getSampleStyleSheet()

    # 🔥 PYTTY TEM HORÁRIO
    mostrar_horario = d["loja"] == "L&A CELL Celulares"

    horario_html = """
    <para align='right'>
    <b>Horário de funcionamento:</b><br/>
    Seg a Qua: 09:00–17:30<br/>
    <b>Qui: 12:00–17:30</b><br/>
    Sex: 09:00–17:30<br/>
    Sáb: 09:00–14:00<br/>
    Dom: Fechado
    </para>
    """

    def bloco(titulo, cliente=False):
        el = []

        if cliente and mostrar_horario:
            el.append(Paragraph(horario_html, styles["Normal"]))
            el.append(Spacer(1, 8))

        el.append(Paragraph(f"<b>{titulo}</b>", styles["Heading4"]))
        el.append(Paragraph(d["loja"], styles["Normal"]))
        el.append(Paragraph(f"WhatsApp: {d['whats']}", styles["Normal"]))
        el.append(Spacer(1, 4))

        dados = [
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
            f"Senha: {d['senha']}",
        ]

        for x in dados:
            el.append(Paragraph(x, styles["Normal"]))

        el.append(Spacer(1, 4))
        el.append(Paragraph("Desenho da senha:", styles["Normal"]))
        el.append(senha9())

        el.append(Spacer(1, 8))
        el.append(Paragraph("Assinatura: ___________________________", styles["Normal"]))
        el.append(Spacer(1, 4))

        el.append(Paragraph("Obs: Garantia não cobre queda, trincos, riscos ou contato com água.", styles["Normal"]))
        el.append(Paragraph("Após 30 dias sem retirada, o aparelho será desmontado para cobrir despesas.", styles["Normal"]))

        return el

    linha = Table([[""]], colWidths=[520])
    linha.setStyle(TableStyle([("LINEABOVE", (0,0), (-1,-1), 1, colors.black)]))

    elementos = []
    elementos.extend(bloco("VIA CLIENTE", cliente=True))
    elementos.append(Spacer(1, 10))
    elementos.append(linha)
    elementos.append(Spacer(1, 10))
    elementos.extend(bloco("VIA LOJA"))

    doc.build(elementos)
    return caminho

# ------------------ ROTAS ------------------

@app.route("/", methods=["GET", "POST"])
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

@app.route("/nova", methods=["GET", "POST"])
def nova():
    if not session.get("logado"):
        return redirect("/")

    if request.method == "POST":
        usuario = session["usuario"]
        loja = USUARIOS[usuario]["loja"]

        lista = carregar(loja)
        n = datetime.now().strftime("%Y%m%d%H%M%S")

        v = float(request.form.get("valor") or 0)
        s = float(request.form.get("sinal") or 0)
        restante = v - s

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
            "restante": restante,
            "custo": float(request.form.get("custo") or 0),
            "frete": float(request.form.get("frete") or 0),
            "pagamento": request.form.get("pagamento"),
            "entrega": request.form.get("entrega"),
            "garantia": request.form.get("garantia"),
            "senha": request.form.get("senha"),
            "status": "pago" if restante <= 0 else "aberto",
            "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "loja": loja,
            "whats": USUARIOS[usuario]["whats"]
        }

        lista.append(d)
        salvar(lista, loja)

        pdf = gerar_pdf(n, d)
        return send_file(pdf, as_attachment=True)

    return render_template("nova_os.html")

@app.route("/os/<numero>")
def ver(numero):
    if not session.get("logado"):
        return redirect("/")

    usuario = session["usuario"]
    loja = USUARIOS[usuario]["loja"]
    lista = carregar(loja)

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
    lista = carregar(loja)

    if busca:
        lista = [o for o in lista if busca in str(o).lower()]

    return render_template("historico.html", lista=lista)

@app.route("/sair")
def sair():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
