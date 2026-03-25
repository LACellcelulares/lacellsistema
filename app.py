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
    "pytty": {
        "senha": "diemfafa",
        "loja": "L&A CELL - Assistência Técnica",
        "whatsapp": "(11) 98083-3734"
    },
    "adriano": {
        "senha": "jesus",
        "loja": "Millenium Solutions Atibaia Center",
        "whatsapp": "(11) 99846-8349"
    }
}

PASTA_PDF = "pdfs"
ARQUIVO_DB = "os.json"
os.makedirs(PASTA_PDF, exist_ok=True)

def carregar_os():
    if not os.path.exists(ARQUIVO_DB):
        return []
    with open(ARQUIVO_DB,"r") as f:
        return json.load(f)

def salvar_os(d):
    lista = carregar_os()
    lista.append(d)
    with open(ARQUIVO_DB,"w") as f:
        json.dump(lista,f,indent=2)

def desenhar_padrao():
    pontos=[["○"]*3 for _ in range(3)]
    t=Table(pontos,22,22)
    t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),1,colors.black),
                           ('ALIGN',(0,0),(-1,-1),'CENTER')]))
    return t

def gerar_pdf_os(numero,dados,loja,whatsapp):
    caminho=os.path.join(PASTA_PDF,f"OS_{numero}.pdf")
    styles=getSampleStyleSheet()
    doc=SimpleDocTemplate(caminho,pagesize=A4,
                          rightMargin=30,leftMargin=30,
                          topMargin=25,bottomMargin=25)
    el=[]
    def bloco(t):
        el.append(Paragraph(f"<b>{t}</b>",styles['Heading4']))
        el.append(Spacer(1,6))
        el.append(Paragraph(loja,styles['Heading2']))
        el.append(Paragraph(f"WhatsApp: {whatsapp}",styles['Normal']))
        el.append(Spacer(1,6))
        linhas=[
            f"OS Nº {numero}",
            f"Data: {dados['data']}",
            f"Entrega: {dados['entrega']}",
            f"Cliente: {dados['cliente']}",
            f"Telefone: {dados['telefone']}",
            f"Aparelho: {dados['aparelho']}",
            f"IMEI: {dados['imei']}  CPF: {dados['cpf']}",
            f"Defeito: {dados['defeito']}",
            f"Valor: R$ {dados['valor']:.2f}",
            f"Pagamento: {dados['pagamento']}",
            f"Sinal: R$ {dados['sinal']:.2f}",
            f"Restante: R$ {dados['restante']:.2f}",
            f"Garantia: {dados['garantia']}",
            f"Senha: {dados['senha']}",
        ]
        for l in linhas:
            el.append(Paragraph(l,styles['Normal']))
        el.append(Spacer(1,8))
        el.append(Paragraph("Senha padrão:",styles['Normal']))
        el.append(desenhar_padrao())
        el.append(Spacer(1,12))
        el.append(Paragraph("Assinatura Cliente: ______________________________",styles['Normal']))
        el.append(Spacer(1,10))
        el.append(Paragraph("Assinatura Loja: _________________________________",styles['Normal']))

    bloco("VIA DO CLIENTE")
    el.append(Spacer(1,14))
    el.append(Paragraph("✂️ ----------------------------------------------------------",styles['Normal']))
    el.append(Spacer(1,14))
    bloco("VIA DA LOJA")

    doc.build(el)
    return caminho

def gerar_pdf_relatorio(lista,loja,mes):
    caminho=os.path.join(PASTA_PDF,f"RELATORIO_{mes}.pdf")
    styles=getSampleStyleSheet()
    total=len(lista)
    valor=sum(float(o["valor"]) for o in lista)
    doc=SimpleDocTemplate(caminho,pagesize=A4)
    el=[]
    el.append(Paragraph("RELATÓRIO MENSAL",styles['Heading2']))
    el.append(Spacer(1,8))
    el.append(Paragraph(f"Loja: {loja}",styles['Normal']))
    el.append(Paragraph(f"Mês: {mes}",styles['Normal']))
    el.append(Paragraph(f"Total OS: {total}",styles['Normal']))
    el.append(Paragraph(f"Faturamento: R$ {valor:.2f}",styles['Normal']))
    el.append(Spacer(1,12))
    dados=[["OS","Cliente","Aparelho","Valor"]]
    for o in lista:
        dados.append([o["numero"],o["cliente"],o["aparelho"],f"R$ {float(o['valor']):.2f}"])
    t=Table(dados,[80,150,150,80])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.lightgrey),
                           ('GRID',(0,0),(-1,-1),1,colors.black)]))
    el.append(t)
    doc.build(el)
    return caminho

@app.route("/",methods=["GET","POST"])
def login():
    if request.method=="POST":
        u=request.form.get("usuario","").strip().lower()
        s=request.form.get("senha","").strip()
        if u in USUARIOS and USUARIOS[u]["senha"]==s:
            session["logado"]=True
            session["usuario"]=u
            return redirect("/painel")
        return render_template("login.html",erro="Login inválido")
    return render_template("login.html")

@app.route("/painel")
def painel():
    if not session.get("logado"): return redirect("/")
    u=session["usuario"]
    lista=[o for o in carregar_os() if o.get("loja")==u]
    total=len(lista)
    valor=sum(float(o["valor"]) for o in lista)
    return render_template("painel.html",total_os=total,total_valor=valor)

@app.route("/nova",methods=["GET","POST"])
def nova():
    if not session.get("logado"): return redirect("/")
    if request.method=="POST":
        u=session["usuario"]
        n=datetime.now().strftime("%Y%m%d%H%M")
        v=float(request.form.get("valor") or 0)
        s=float(request.form.get("sinal") or 0)
        d={
            "numero":n,"loja":u,
            "cliente":request.form.get("cliente"),
            "telefone":request.form.get("telefone"),
            "aparelho":request.form.get("aparelho"),
            "imei":request.form.get("imei"),
            "cpf":request.form.get("cpf"),
            "defeito":request.form.get("defeito"),
            "valor":v,"pagamento":request.form.get("pagamento"),
            "sinal":s,"restante":v-s,
            "garantia":request.form.get("garantia"),
            "senha":request.form.get("senha"),
            "entrega":request.form.get("entrega"),
            "data":datetime.now().strftime("%d/%m/%Y %H:%M")
        }
        salvar_os(d)
        pdf=gerar_pdf_os(n,d,USUARIOS[u]["loja"],USUARIOS[u]["whatsapp"])
        return send_file(pdf,as_attachment=True)
    return render_template("nova_os.html")

@app.route("/historico")
def historico():
    if not session.get("logado"): return redirect("/")
    u=session["usuario"]
    q=request.args.get("q","").lower()
    lista=[o for o in carregar_os() if o.get("loja")==u]
    if q:
        lista=[o for o in lista if q in o["cliente"].lower()
               or q in o["aparelho"].lower()
               or q in o["numero"].lower()]
    return render_template("historico.html",lista=lista,busca=q)

@app.route("/os/<numero>")
def ver_os(numero):
    if not session.get("logado"): return redirect("/")
    u=session["usuario"]
    o=next((x for x in carregar_os() if x["numero"]==numero and x["loja"]==u),None)
    if not o: abort(404)
    pdf=gerar_pdf_os(numero,o,USUARIOS[u]["loja"],USUARIOS[u]["whatsapp"])
    return send_file(pdf)

@app.route("/relatorio")
def relatorio():
    if not session.get("logado"): return redirect("/")
    u=session["usuario"]
    lista=[o for o in carregar_os() if o.get("loja")==u]
    mes=datetime.now().strftime("%m-%Y")
    pdf=gerar_pdf_relatorio(lista,USUARIOS[u]["loja"],mes)
    return send_file(pdf,as_attachment=True)

@app.route("/sair")
def sair():
    session.clear()
    return redirect("/")

if __name__=="__main__":
    app.run(debug=True)
