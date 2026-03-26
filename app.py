from flask import Flask, render_template, request, redirect, session, send_file, abort
import os, json
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

app = Flask(__name__)
app.secret_key = "lacell_secret"

USUARIOS = {
    "pytty": {"senha":"diemfafa","loja":"L&A CELL","whatsapp":"11980833734"},
    "adriano": {"senha":"jesus","loja":"Millenium Solutions","whatsapp":"11998468349"}
}

ARQUIVO_DB = "os.json"
PASTA_PDF = "pdfs"
os.makedirs(PASTA_PDF, exist_ok=True)

# ================= BANCO =================
def carregar_os():
    if not os.path.exists(ARQUIVO_DB):
        return []
    with open(ARQUIVO_DB) as f:
        return json.load(f)

def salvar_os(d):
    lista = carregar_os()
    lista.append(d)
    with open(ARQUIVO_DB,"w") as f:
        json.dump(lista,f,indent=2)

# ================= PDF =================
def desenhar_padrao():
    pontos = [["●"]*3 for _ in range(3)]
    t = Table(pontos,18,18)
    t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),1,colors.black)]))
    return t

def gerar_pdf_os(numero, dados, loja, whatsapp):
    caminho = f"{PASTA_PDF}/OS_{numero}.pdf"
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(caminho, pagesize=A4)
    el = []

    def bloco(titulo):
        el.append(Paragraph(f"<b>{titulo}</b>", styles["Heading4"]))
        el.append(Paragraph(loja, styles["Normal"]))
        el.append(Paragraph(f"WhatsApp: {whatsapp}", styles["Normal"]))
        el.append(Spacer(1,5))

        linhas = [
            f"OS Nº {numero}",
            f"Data: {dados['data']}",
            f"Cliente: {dados['cliente']}",
            f"Aparelho: {dados['aparelho']}",
            f"Defeito: {dados['defeito']}",
            f"Valor: R$ {dados['valor']:.2f}",
            f"Sinal: R$ {dados['sinal']:.2f}",
            f"Restante: R$ {dados['restante']:.2f}",
            f"Senha: {dados['senha']}",
        ]

        for l in linhas:
            el.append(Paragraph(l, styles["Normal"]))

        el.append(Spacer(1,5))
        el.append(Paragraph("Senha padrão:", styles["Normal"]))
        el.append(desenhar_padrao())
        el.append(Spacer(1,10))

    bloco("VIA DO CLIENTE")
    el.append(Paragraph("------------------------------------", styles["Normal"]))
    bloco("VIA DA LOJA")

    doc.build(el)
    return caminho

# ================= LOGIN =================
@app.route("/", methods=["GET","POST"])
def login():
    if request.method=="POST":
        u=request.form["usuario"]
        s=request.form["senha"]
        if u in USUARIOS and USUARIOS[u]["senha"]==s:
            session["logado"]=True
            session["usuario"]=u
            return redirect("/painel")
    return render_template("login.html")

# ================= PAINEL =================
@app.route("/painel")
def painel():
    if not session.get("logado"): return redirect("/")
    loja = USUARIOS[session["usuario"]]["loja"]
    lista = [o for o in carregar_os() if o["loja"]==loja]
    return render_template("painel.html",
        total_os=len(lista),
        total_valor=sum(o["valor"] for o in lista)
    )

# ================= NOVA OS =================
@app.route("/nova", methods=["GET","POST"])
def nova():
    if not session.get("logado"): return redirect("/")

    if request.method=="POST":
        loja = USUARIOS[session["usuario"]]["loja"]

        def moeda(v):
            return float(v.replace("R$","").replace(".","").replace(",",".") or 0)

        valor = moeda(request.form.get("valor","0"))
        sinal = moeda(request.form.get("sinal","0"))
        custo = moeda(request.form.get("custo","0"))
        frete = moeda(request.form.get("frete","0"))

        numero = datetime.now().strftime("%Y%m%d%H%M")

        d = {
            "numero":numero,
            "loja":loja,
            "cliente":request.form.get("cliente"),
            "telefone":request.form.get("telefone"),
            "aparelho":request.form.get("aparelho"),
            "defeito":request.form.get("defeito"),
            "valor":valor,
            "sinal":sinal,
            "restante":valor-sinal,
            "custo":custo,
            "frete":frete,
            "lucro":valor-(custo+frete),
            "senha":request.form.get("senha"),
            "data":datetime.now().strftime("%d/%m/%Y %H:%M")
        }

        salvar_os(d)

        pdf = gerar_pdf_os(numero,d,loja,USUARIOS[session["usuario"]]["whatsapp"])
        return send_file(pdf, as_attachment=True)

    return render_template("nova_os.html")

# ================= HISTORICO =================
@app.route("/historico")
def historico():
    if not session.get("logado"): return redirect("/")
    loja = USUARIOS[session["usuario"]]["loja"]
    lista = [o for o in carregar_os() if o["loja"]==loja]
    return render_template("historico.html", lista=lista, busca="")

# ================= VER OS =================
@app.route("/os/<numero>")
def ver_os(numero):
    if not session.get("logado"): return redirect("/")
    loja = USUARIOS[session["usuario"]]["loja"]

    o = next((x for x in carregar_os() if x["numero"]==numero and x["loja"]==loja),None)
    if not o: abort(404)

    pdf = gerar_pdf_os(numero,o,loja,USUARIOS[session["usuario"]]["whatsapp"])
    return send_file(pdf)

# ================= FINANCEIRO =================
@app.route("/financeiro")
def financeiro():
    if not session.get("logado"): return redirect("/")
    loja = USUARIOS[session["usuario"]]["loja"]

    lista = [o for o in carregar_os() if o["loja"]==loja]

    return render_template("financeiro.html",
        lista=lista,
        total=sum(o["valor"] for o in lista),
        lucro=sum(o["lucro"] for o in lista),
        aberto=sum(o["restante"] for o in lista)
    )

# ================= SAIR =================
@app.route("/sair")
def sair():
    session.clear()
    return redirect("/")

if __name__=="__main__":
    app.run(debug=True)
