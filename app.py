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

# ================= DB =================
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

# ================= PDF =================
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

# ================= LOGIN =================
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

# ================= PAINEL =================
@app.route("/painel")
def painel():
    if not session.get("logado"): return redirect("/")
    u=session["usuario"]
    loja=USUARIOS[u]["loja"]

    lista=[o for o in carregar() if o.get("loja")==loja]

    total=len(lista)
    valor=sum(float(o.get("valor",0)) for o in lista)

    return render_template("painel.html",total_os=total,total_valor=valor)

# ================= NOVA OS =================
@app.route("/nova",methods=["GET","POST"])
def nova():
    if not session.get("logado"): return redirect("/")

    if request.method=="POST":
        u=session["usuario"]
        loja=USUARIOS[u]["loja"]

        lista=carregar()
        n=datetime.now().strftime("%Y%m%d%H%M%S")

        v=float(request.form.get("valor") or 0)
        s=float(request.form.get("sinal") or 0)
        c=float(request.form.get("custo") or 0)
        f=float(request.form.get("frete") or 0)

        d={
            "numero":n,
            "loja":loja,
            "cliente":request.form.get("cliente"),
            "telefone":request.form.get("telefone"),
            "cpf":request.form.get("cpf"),
            "imei":request.form.get("imei"),
            "aparelho":request.form.get("aparelho"),
            "defeito":request.form.get("defeito"),
            "valor":v,
            "pagamento":request.form.get("pagamento"),
            "sinal":s,
            "restante":v-s,
            "custo":c,
            "frete":f,
            "garantia":request.form.get("garantia"),
            "senha":request.form.get("senha"),
            "entrega":request.form.get("entrega"),
            "data":datetime.now().strftime("%d/%m/%Y %H:%M")
        }

        lista.append(d)
        salvar(lista)

        pdf=gerar_pdf(n,d,loja,USUARIOS[u]["whatsapp"])
        return send_file(pdf,as_attachment=True)

    return render_template("nova_os.html")

# ================= EDITAR =================
@app.route("/editar/<numero>",methods=["GET","POST"])
def editar(numero):
    if not session.get("logado"): return redirect("/")

    lista=carregar()
    os_encontrada=next((x for x in lista if x["numero"]==numero),None)

    if not os_encontrada:
        return "OS não encontrada"

    if request.method=="POST":
        os_encontrada["cliente"]=request.form.get("cliente")
        os_encontrada["telefone"]=request.form.get("telefone")
        os_encontrada["cpf"]=request.form.get("cpf")
        os_encontrada["imei"]=request.form.get("imei")
        os_encontrada["aparelho"]=request.form.get("aparelho")
        os_encontrada["defeito"]=request.form.get("defeito")

        os_encontrada["valor"]=float(request.form.get("valor") or 0)
        os_encontrada["sinal"]=float(request.form.get("sinal") or 0)
        os_encontrada["custo"]=float(request.form.get("custo") or 0)
        os_encontrada["frete"]=float(request.form.get("frete") or 0)

        os_encontrada["restante"]=os_encontrada["valor"]-os_encontrada["sinal"]

        os_encontrada["pagamento"]=request.form.get("pagamento")
        os_encontrada["garantia"]=request.form.get("garantia")
        os_encontrada["senha"]=request.form.get("senha")
        os_encontrada["entrega"]=request.form.get("entrega")

        salvar(lista)
        return redirect("/historico")

    return render_template("editar.html",os=os_encontrada)

# ================= HISTORICO =================
@app.route("/historico")
def historico():
    if not session.get("logado"): return redirect("/")
    u=session["usuario"]
    loja=USUARIOS[u]["loja"]

    lista=[o for o in carregar() if o.get("loja")==loja]

    return render_template("historico.html",lista=lista)

# ================= VER =================
@app.route("/os/<numero>")
def ver(numero):
    if not session.get("logado"): return redirect("/")

    u=session["usuario"]
    loja=USUARIOS[u]["loja"]

    o=next((x for x in carregar() if x["numero"]==numero and x["loja"]==loja),None)
    if not o: abort(404)

    pdf=gerar_pdf(numero,o,loja,USUARIOS[u]["whatsapp"])
    return send_file(pdf)

# ================= FINANCEIRO =================
@app.route("/financeiro",methods=["GET","POST"])
def financeiro():
    if not session.get("logado"): return redirect("/")

    if not session.get("fin_ok"):
        if request.method=="POST":
            if request.form.get("senha")=="jesus":
                session["fin_ok"]=True
                return redirect("/financeiro")
        return render_template("financeiro_login.html")

    u=session["usuario"]
    loja=USUARIOS[u]["loja"]

    lista=[o for o in carregar() if o.get("loja")==loja]

    total=sum(o["valor"] for o in lista)
    custo=sum(o["custo"] for o in lista)
    frete=sum(o["frete"] for o in lista)
    lucro=total-custo-frete

    return render_template("financeiro.html",lista=lista,total=total,custo=custo,frete=frete,lucro=lucro)

# ================= RELATORIO DIA =================
@app.route("/relatorio_dia")
def relatorio_dia():
    hoje=datetime.now().strftime("%d/%m/%Y")

    lista=[o for o in carregar() if hoje in o["data"]]

    total=sum(o["valor"] for o in lista)
    custo=sum(o["custo"] for o in lista)
    frete=sum(o["frete"] for o in lista)
    lucro=total-custo-frete

    return render_template("relatorio.html",titulo="Relatório do Dia",lista=lista,total=total,custo=custo,frete=frete,lucro=lucro)

# ================= RELATORIO MES =================
@app.route("/relatorio")
def relatorio_mes():
    mes=datetime.now().strftime("%m/%Y")

    lista=[o for o in carregar() if mes in o["data"]]

    total=sum(o["valor"] for o in lista)
    custo=sum(o["custo"] for o in lista)
    frete=sum(o["frete"] for o in lista)
    lucro=total-custo-frete

    return render_template("relatorio.html",titulo="Relatório Mensal",lista=lista,total=total,custo=custo,frete=frete,lucro=lucro)

# ================= SAIR =================
@app.route("/sair")
def sair():
    session.clear()
    return redirect("/")

if __name__=="__main__":
    app.run(debug=True)
