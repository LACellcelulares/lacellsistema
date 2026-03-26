from flask import Flask, render_template, request, redirect, session
from datetime import datetime

app = Flask(__name__)
app.secret_key = "123"

# BANCO SIMPLES (MEMORIA)
lista_os = []
contador = 1

# LOGIN
USUARIO = "admin"
SENHA = "123"

# SENHA FINANCEIRO
SENHA_FIN = "jesus"

# ================= LOGIN =================
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form["user"] == USUARIO and request.form["senha"] == SENHA:
            session["logado"] = True
            return redirect("/painel")
    return render_template("login.html")


# ================= PAINEL =================
@app.route("/painel")
def painel():
    if not session.get("logado"):
        return redirect("/")
    total = len(lista_os)
    total_valor = sum(float(o["valor"] or 0) for o in lista_os)
    return render_template("painel.html", total_os=total, total_valor=total_valor)


# ================= NOVA OS =================
@app.route("/nova", methods=["GET","POST"])
def nova():
    global contador

    if request.method == "POST":
        data = {
            "id": contador,
            "cliente": request.form.get("cliente"),
            "telefone": request.form.get("telefone"),
            "aparelho": request.form.get("aparelho"),
            "defeito": request.form.get("defeito"),

            "valor": float(request.form.get("valor") or 0),
            "sinal": float(request.form.get("sinal") or 0),
            "custo": float(request.form.get("custo") or 0),
            "frete": float(request.form.get("frete") or 0),

            "pagamento": request.form.get("pagamento"),
            "senha": request.form.get("senha"),
            "garantia": request.form.get("garantia"),

            "data": datetime.now().strftime("%d/%m/%Y")
        }

        lista_os.append(data)
        contador += 1

        return redirect("/historico")

    return render_template("nova_os.html")


# ================= HISTORICO =================
@app.route("/historico")
def historico():
    return render_template("historico.html", lista=lista_os)


# ================= VER OS =================
@app.route("/ver/<int:id>")
def ver(id):
    for o in lista_os:
        if o["id"] == id:
            return f"""
            <h2>OS {o['id']}</h2>
            Cliente: {o['cliente']}<br>
            Aparelho: {o['aparelho']}<br>
            Defeito: {o['defeito']}<br>
            Valor: {o['valor']}<br>
            """
    return "OS não encontrada"


# ================= EDITAR =================
@app.route("/editar/<int:id>", methods=["GET","POST"])
def editar(id):
    for o in lista_os:
        if o["id"] == id:

            if request.method == "POST":
                o["valor"] = float(request.form.get("valor") or 0)
                o["custo"] = float(request.form.get("custo") or 0)
                o["frete"] = float(request.form.get("frete") or 0)
                return redirect("/historico")

            return f"""
            <h2>Editar OS {o['id']}</h2>
            <form method="post">
            Valor: <input name="valor" value="{o['valor']}"><br>
            Custo: <input name="custo" value="{o['custo']}"><br>
            Frete: <input name="frete" value="{o['frete']}"><br>
            <button>Salvar</button>
            </form>
            """

    return "Erro"


# ================= FINANCEIRO LOGIN =================
@app.route("/financeiro", methods=["GET","POST"])
def financeiro_login():
    if request.method == "POST":
        if request.form.get("senha") == SENHA_FIN:
            session["fin"] = True
            return redirect("/financeiro/lista")
    return """
    <h2>Senha Financeiro</h2>
    <form method="post">
    <input type="password" name="senha">
    <button>Entrar</button>
    </form>
    """


# ================= FINANCEIRO =================
@app.route("/financeiro/lista")
def financeiro():
    if not session.get("fin"):
        return redirect("/financeiro")

    return render_template("financeiro.html", lista=lista_os)


# ================= RELATORIO DIA =================
@app.route("/relatorio_dia")
def relatorio_dia():
    hoje = datetime.now().strftime("%d/%m/%Y")

    lista = [o for o in lista_os if o["data"] == hoje]

    total = sum(o["valor"] for o in lista)

    return f"""
    <h2>Relatório do Dia</h2>
    Total: {total}
    """


# ================= RELATORIO MES =================
@app.route("/relatorio_mes")
def relatorio_mes():
    mes = datetime.now().strftime("%m/%Y")

    lista = [o for o in lista_os if mes in o["data"]]

    total = sum(o["valor"] for o in lista)

    return f"""
    <h2>Relatório do Mês</h2>
    Total: {total}
    """


# ================= SAIR =================
@app.route("/sair")
def sair():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run()
