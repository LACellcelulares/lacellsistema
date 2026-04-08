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
DROPBOX_TOKEN = ""sl.u.AGb4nbA8_Qw7bkliaW6SXFAgj_tKbEGSMZn7k7n1lQyFjdkDp4VDlQglLFf-r-QkfN0ns_PBA3dW5c9z_WP7PqzUXMPtHRldzQ1PT34AmbGt1_95UwKQ2rTCxO0AWSsB0IrRPY4CL41KMK4Nybf1suaSUaRkjFVlGXT0TcACC6xfG3KvoQrxj2w4v_F_ljNfXrRh4ob955IRUZGHmBgHf0RONG6fhgnIXFBoaBnDK-z9AiEFIcZvy6qQzmaZRjBErXLYH2mpocGrJPs9U8ObRvjnBxFE2Ok_d5JE9jsXxX2SiSNNFaxs5UAgGDE66cgddWWIuD2BO0aXwC7_TNQbFzdplxXsfo0tnU-zXrxjcjfvUhHdcd_5211ZMXaheUKz5IQ9YeAU_8klZc_AIjtYIW0Ezum1VlWwd480VKGOokRmuMp_wfAESqFTZIJAYZZW6t4qELpf97gHm_UL8jLhPwiUKQGgBEzcjvjBsMydyHV4Eab17FNxpZusQ5KdUeATnR05-qMccKpk1reFp1x4jjJY-8VH0cIoW3VDMb9N32F2wGA8BD0sqCLS3BuAneZ-83hHLEnnuyAVn-Bqts0CAzHmgQy6Pfb2V_r_-1xr8peJlecBpFMYg3o8SHbZndMFiUVgywAfKQqr2di114HOIycEL6GrMWe8u216jfeGPaknyPUJklQUxS4-YscMzQ_3lFy-GixGH6Pp8k5zpVSFobAoqD3O_Ps3GcNetS1urt1a5_Pm9TDV4525coXZanQ6axsjkMhQP6hqSg5MQM-InSEbbEUO7OSn5ZdRbt1SJ7VqbUawKIoEps8Ng0MypZlhMiNTJcvcAk35U5BdH8zCquvjYqjXDGJ5lphSKaj5POhBUHwEHJZvIpZ3Y0f1EKLuRa6BxefY7wPrqQgx2qv0ons52BDbY2Td4LlEF7JWUFiy3V-7bvm7PekVIu5C2w4OzywFZJ-pb_tv-JCTK6Uqt_00_0GmhzXpacgjx0GiXRYY4Bt6IpADqfZhFqXa009qH2zYLDxn5BEl7qNsd_UNyHnm_geSDPh4F6hIXFJ4LHgXW9Fn2EahT8OkJzab5RcZSf3TcIRr_gqIQOveuAsir9OEv1pjUgnde8CoN9AWh13ss0Pm1B5o9VeL1aoemsYdSevsT3xEdKdqLbkrbUPakEbiTGEMPscAmKz2XNrL1StgtemS-T7qJjJiC-MDyolv98AxIjZElSsOZbDRdCfKB_jqMzbnvPZ-jNzfbFoY6HLmk7I428_4D6lJ6lUgOk_lADTHF9PDQPoILX9yxRa4mMNThKnKtKxwTxDyQDTfUc_hYmWnf1HiDiEgZ6P2MNCG4RyK-c03LUS4zOe7MbHNaf6eMlWE61pSVXvSbokL7wtQTOofDd-TIRWybxkU2uw_uniJxQngEfawm4DObLOfs7RZYuHuZ5_SdmLewKthCGubWw"

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

# 🔥 NOVO: baixar da nuvem antes de usar
def baixar_dropbox(loja):
    usuario = None
    for u, info in USUARIOS.items():
        if info["loja"] == loja:
            usuario = u
            break

    if not usuario:
        return

    dropbox_path = USUARIOS[usuario]["dropbox"]

    try:
        url = "https://content.dropboxapi.com/2/files/download"

        headers = {
            "Authorization": f"Bearer {DROPBOX_TOKEN}",
            "Dropbox-API-Arg": json.dumps({
                "path": dropbox_path
            })
        }

        r = requests.post(url, headers=headers)

        if r.status_code == 200:
            dados = r.json()

            arq = caminho_db(loja)
            with open(arq, "w") as f:
                json.dump(dados, f, indent=2)

            print("☁️ SINCRONIZADO DA NUVEM")

    except Exception as e:
        print("❌ ERRO AO BAIXAR:", e)

def carregar(loja):
    # 🔥 sincroniza sempre antes de ler
    baixar_dropbox(loja)

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

    # salva local
    with open(arq, "w") as f:
        json.dump(lista, f, indent=2)

    # backup local
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

        r = requests.post(
            url,
            headers=headers,
            data=json.dumps(lista).encode("utf-8")
        )

        print("📡 DROPBOX STATUS:", r.status_code)

    except Exception as e:
        print("❌ ERRO DROPBOX:", e)

# -----------------------------------------
# PDF (SEM ALTERAÇÃO)
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
# ROTAS (100% IGUAL)
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
