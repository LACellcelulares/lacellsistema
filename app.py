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
    "pytty": {"senha":"diemfafa","loja":"L&A CELL Celulares","whatsapp":"(11)98083-3734"},
    "adriano": {"senha":"jesus","loja":"MILLENNIUM SOLUTIONS ATIBAIA","whatsapp":"(11)99846-8349"}
}

PASTA_PDF="pdfs"
ARQUIVO_DB="os.json"
os.makedirs(PASTA_PDF, exist_ok=True)

def carregar():
    if not os.path.exists(ARQUIVO_DB): return []
    try:
        with open(ARQUIVO_DB,"r") as f:
            return json.load(f)
    except:
        return []

def salvar(lista):
    with open(ARQUIVO_DB,"w") as f:
        json.dump(lista,f,indent=2)

def senha9():
    t=Table([["○"]*3 for _ in range(3)],18,18)
    t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),1,colors.black)]))
    return t

def gerar_pdf(n,d,loja,whats):
    caminho=f"{PASTA_PDF}/OS_{n}.pdf"
    styles=getSampleStyleSheet()
    doc=SimpleDocTemplate(caminho,pagesize=A4)
    el=[]

    def bloco(t):
        el.append(Paragraph(f"<b>{t}</b>",styles["Heading4"]))
        el.append(Paragraph(loja,styles["Normal"]))
        el.append(Paragraph(f"WhatsApp: {whats}",styles["Normal"]))
        el.append(Spacer(1,5))

        dados=[
            f"OS Nº {n}",
            f"Data: {d.get('data','')}",
            f"Entrega: {d.get('entrega','')}",
            f"Cliente: {d.get('cliente','')}",
            f"Telefone: {d.get('telefone','')}",
            f"CPF/CNPJ: {d.get('cpf','')}",
            f"IMEI: {d.get('imei','')}",
            f"Aparelho: {d.get('aparelho','')}",
            f"Defeito: {d.get('defeito','')}",
            f"Valor: R$ {d.get('valor',0)}",
            f"Pagamento: {d.get('pagamento','')}",
            f"Sinal: R$ {d.get('sinal',0)}",
            f"Restante: R$ {d.get('restante',0)}",
            f"Garantia: {d.get('garantia','')}",
            f"Senha: {d.get('senha','')}"
        ]

        for x in dados:
            el.append(Paragraph(x,styles["Normal"]))

        el.append(Spacer(1,5))
        el.append(senha9())

    bloco("VIA CLIENTE")
    el.append(Spacer(1,15))
    bloco("VIA LOJA")

    doc.build(el)
    return caminho

@app.route("/",methods=["GET","POST"])
def login():
    if request.method=="POST":
        u=(request.form.get("usuario") or "").lower()
        s=request.form.get("senha") or ""

        if u in USUARIOS and USUARIOS[u]["senha"]==s:
            session["logado"]=True
            session["usuario"]=u
            session["fin_ok"]=False
            return redirect("/painel")

    return render_template("login.html")

@app.route("/painel")
def painel():
    if not session.get("logado"): return redirect("/")
    u=session["usuario"]
    loja=USUARIOS[u]["loja"]

    lista=[o for o in carregar() if o.get("loja")==loja]

    total=len(lista)
    valor=sum(float(o.get("valor",0)) for o in lista)

    return render_template("painel.html",total_os=total,total_valor=valor)

@app.route("/financeiro",methods=["GET","POST"])
def financeiro():
    if not session.get("logado"): return redirect("/")

    if not session.get("fin_ok"):
        if request.method=="POST":
            if request.form.get("senha")=="jesus":
                session["fin_ok"]=True
                return redirect("/financeiro")
        return render_template("financeiro_login.html")

    lista = carregar()

    total = sum(float(o.get("valor",0)) for o in lista)
    custo = sum(float(o.get("custo",0)) for o in lista)
    frete = sum(float(o.get("frete",0)) for o in lista)
    lucro = total - custo - frete

    return render_template("financeiro.html",lista=lista,total=total,custo=custo,frete=frete,lucro=lucro)

@app.route("/relatorio_dia")
def relatorio_dia():
    hoje=datetime.now().strftime("%d/%m/%Y")

    lista=[o for o in carregar() if hoje in o["data"]]

    total=sum(float(o.get("valor",0)) for o in lista)

    return render_template("relatorio_dia.html", total=total)

@app.route("/relatorio")
def relatorio_mes():
    mes=datetime.now().strftime("%m/%Y")

    lista=[o for o in carregar() if mes in o["data"]]

    total=sum(float(o.get("valor",0)) for o in lista)

    return render_template("relatorio_mes.html", total=total)

@app.route("/sair")
def sair():
    session.clear()
    return redirect("/")

if __name__=="__main__":
    app.run(debug=True)
