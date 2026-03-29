from flask import Flask, render_template, request, redirect, session
import os, json
from datetime import datetime

app = Flask(__name__)
app.secret_key = "lacell_secret"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_DB = os.path.join(BASE_DIR, "os.json")

# ================= DB =================
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

# ================= LOGIN =================
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form.get("usuario") == "adriano" and request.form.get("senha") == "jesus":
            session["logado"] = True
            session["fin_ok"] = False
            return redirect("/painel")
    return render_template("login.html")

# ================= PAINEL =================
@app.route("/painel")
def painel():
    if not session.get("logado"):
        return redirect("/")
    lista = carregar()
    return render_template("painel.html", total_os=len(lista))

# ================= NOVA =================
@app.route("/nova", methods=["GET","POST"])
def nova():
    if not session.get("logado"):
        return redirect("/")

    if request.method == "POST":
        lista = carregar()
        n = datetime.now().strftime("%Y%m%d%H%M%S")

        v = float(request.form.get("valor") or 0)
        s = float(request.form.get("sinal") or 0)

        lista.append({
            "numero": n,
            "cliente": request.form.get("cliente"),
            "telefone": request.form.get("telefone"),
            "aparelho": request.form.get("aparelho"),
            "valor": v,
            "sinal": s,
            "restante": v - s,
            "custo": float(request.form.get("custo") or 0),
            "frete": float(request.form.get("frete") or 0),
            "status": "aberto",
            "data": datetime.now().strftime("%Y-%m-%d")  # 🔥 formato certo p/ filtro
        })

        salvar(lista)
        return redirect("/historico")

    return render_template("nova_os.html")

# ================= EDITAR =================
@app.route("/editar/<numero>", methods=["GET","POST"])
def editar(numero):
    if not session.get("logado"):
        return redirect("/")

    lista = carregar()
    os_encontrada = next((x for x in lista if x["numero"] == numero), None)

    if not os_encontrada:
        return "OS não encontrada"

    if request.method == "POST":
        os_encontrada.update({
            "cliente": request.form.get("cliente"),
            "telefone": request.form.get("telefone"),
            "aparelho": request.form.get("aparelho"),
            "valor": float(request.form.get("valor") or 0),
            "sinal": float(request.form.get("sinal") or 0),
            "custo": float(request.form.get("custo") or 0),
            "frete": float(request.form.get("frete") or 0),
        })

        os_encontrada["restante"] = os_encontrada["valor"] - os_encontrada["sinal"]

        salvar(lista)
        return redirect("/financeiro")

    return render_template("editar.html", os=os_encontrada)

# ================= HISTORICO =================
@app.route("/historico")
def historico():
    if not session.get("logado"):
        return redirect("/")

    busca = request.args.get("busca","").lower()

    lista = carregar()

    if busca:
        lista = [
            o for o in lista
            if busca in (str(o.get("cliente","")).lower() +
                         str(o.get("aparelho","")).lower() +
                         str(o.get("telefone","")).lower())
        ]

    return render_template("historico.html", lista=lista)

# ================= FINANCEIRO =================
@app.route("/financeiro", methods=["GET","POST"])
def financeiro():
    if not session.get("logado"):
        return redirect("/")

    # 🔒 senha financeiro
    if not session.get("fin_ok"):
        if request.method == "POST":
            if request.form.get("senha") == "jesus":
                session["fin_ok"] = True
                return redirect("/financeiro")
        return render_template("financeiro_login.html")

    lista = carregar()

    # 🔥 filtros novos
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")
    aberto = request.args.get("aberto")

    if aberto:
        lista = [o for o in lista if o.get("status") != "pago"]

    if data_inicio and data_fim:
        lista_filtrada = []
        for o in lista:
            try:
                d = datetime.strptime(o.get("data"), "%Y-%m-%d")
                if data_inicio <= d.strftime("%Y-%m-%d") <= data_fim:
                    lista_filtrada.append(o)
            except:
                pass
        lista = lista_filtrada

    total = sum(float(o.get("valor",0)) for o in lista)
    custo = sum(float(o.get("custo",0)) for o in lista)
    frete = sum(float(o.get("frete",0)) for o in lista)
    lucro = total - custo - frete

    return render_template("financeiro.html",
        lista=lista,
        total=total,
        custo=custo,
        frete=frete,
        lucro=lucro
    )

# ================= PAGAR =================
@app.route("/pagar/<numero>")
def pagar(numero):
    lista = carregar()
    for o in lista:
        if o["numero"] == numero:
            o["status"] = "pago"
    salvar(lista)
    return redirect("/financeiro")

# ================= CANCELAR =================
@app.route("/cancelar/<numero>")
def cancelar(numero):
    lista = [o for o in carregar() if o["numero"] != numero]
    salvar(lista)
    return redirect("/financeiro")

# ================= SAIR =================
@app.route("/sair")
def sair():
    session.clear()
    return redirect("/")

# ================= RAILWAY =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
