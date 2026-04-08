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
# CONFIG
# -----------------------------------------
DROPBOX_TOKEN = "sl.u.AGb4nbA8_Qw7bkliaW6SXFAgj_tKbEGSMZn7k7n1lQyFjdkDp4VDlQglLFf-r-QkfN0ns_PBA3dW5c9z_WP7PqzUXMPtHRldzQ1PT34AmbGt1_95UwKQ2rTCxO0AWSsB0IrRPY4CL41KMK4Nybf1suaSUaRkjFVlGXT0TcACC6xfG3KvoQrxj2w4v_F_ljNfXrRh4ob955IRUZGHmBgHf0RONG6fhgnIXFBoaBnDK-z9AiEFIcZvy6qQzmaZRjBErXLYH2mpocGrJPs9U8ObRvjnBxFE2Ok_d5JE9jsXxX2SiSNNFaxs5UAgGDE66cgddWWIuD2BO0aXwC7_TNQbFzdplxXsfo0tnU-zXrxjcjfvUhHdcd_5211ZMXaheUKz5IQ9YeAU_8klZc_AIjtYIW0Ezum1VlWwd480VKGOokRmuMp_wfAESqFTZIJAYZZW6t4qELpf97gHm_UL8jLhPwiUKQGgBEzcjvjBsMydyHV4Eab17FNxpZusQ5KdUeATnR05-qMccKpk1reFp1x4jjJY-8VH0cIoW3VDMb9N32F2wGA8BD0sqCLS3BuAneZ-83hHLEnnuyAVn-Bqts0CAzHmgQy6Pfb2V_r_-1xr8peJlecBpFMYg3o8SHbZndMFiUVgywAfKQqr2di114HOIycEL6GrMWe8u216jfeGPaknyPUJklQUxS4-YscMzQ_3lFy-GixGH6Pp8k5zpVSFobAoqD3O_Ps3GcNetS1urt1a5_Pm9TDV4525coXZanQ6axsjkMhQP6hqSg5MQM-InSEbbEUO7OSn5ZdRbt1SJ7VqbUawKIoEps8Ng0MypZlhMiNTJcvcAk35U5BdH8zCquvjYqjXDGJ5lphSKaj5POhBUHwEHJZvIpZ3Y0f1EKLuRa6BxefY7wPrqQgx2qv0ons52BDbY2Td4LlEF7JWUFiy3V-7bvm7PekVIu5C2w4OzywFZJ-pb_tv-JCTK6Uqt_00_0GmhzXpacgjx0GiXRYY4Bt6IpADqfZhFqXa009qH2zYLDxn5BEl7qNsd_UNyHnm_geSDPh4F6hIXFJ4LHgXW9Fn2EahT8OkJzab5RcZSf3TcIRr_gqIQOveuAsir9OEv1pjUgnde8CoN9AWh13ss0Pm1B5o9VeL1aoemsYdSevsT3xEdKdqLbkrbUPakEbiTGEMPscAmKz2XNrL1StgtemS-T7qJjJiC-MDyolv98AxIjZElSsOZbDRdCfKB_jqMzbnvPZ-jNzfbFoY6HLmk7I428_4D6lJ6lUgOk_lADTHF9PDQPoILX9yxRa4mMNThKnKtKxwTxDyQDTfUc_hYmWnf1HiDiEgZ6P2MNCG4RyK-c03LUS4zOe7MbHNaf6eMlWE61pSVXvSbokL7wtQTOofDd-TIRWybxkU2uw_uniJxQngEfawm4DObLOfs7RZYuHuZ5_SdmLewKthCGubWw"

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
# BANCO
# -----------------------------------------
def caminho_db(loja):
    nome = loja.lower().replace(" ", "_").replace("&", "e")
    return os.path.join(BASE_DIR, f"os_{nome}.json")

# 🔥 NOVO: baixa da nuvem
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
    # 🔥 sincroniza antes de tudo
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
# PDF (IGUAL)
# -----------------------------------------
def senha9():
    t = Table([["○"] * 3 for _ in range(3)], 15, 15)
    t.setStyle(TableStyle([("GRID", (0,0), (-1,-1), 1, colors.black)]))
    return t

def gerar_pdf(numero, d, horario=False):
    caminho = os.path.join(PASTA_PDF, f"OS_{numero}.pdf")

    doc = SimpleDocTemplate(caminho, pagesize=A4)
    styles = getSampleStyleSheet()
    elementos = []

    def bloco():
        el = []
        el.append(Paragraph(f"OS Nº {numero}", styles["Normal"]))
        el.append(Paragraph(f"Cliente: {d['cliente']}", styles["Normal"]))
        return el

    elementos += bloco()
    doc.build(elementos)
    return caminho

# -----------------------------------------
# ROTAS (TODAS IGUAIS)
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

    if request.method == "POST":
        lista = carregar(loja)
        n = datetime.now().strftime("%Y%m%d%H%M%S")

        d = {
            "numero": n,
            "cliente": request.form.get("cliente"),
            "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
        }

        lista.append(d)
        salvar(lista, loja)

        return redirect("/historico")

    return render_template("nova_os.html")

@app.route("/historico")
def historico():
    if not session.get("logado"):
        return redirect("/")

    usuario = session["usuario"]
    loja = USUARIOS[usuario]["loja"]
    lista = carregar(loja)

    return render_template("historico.html", lista=lista)

@app.route("/sair")
def sair():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
