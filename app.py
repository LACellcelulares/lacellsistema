# ================= FINANCEIRO =================
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

    busca = (request.args.get("busca") or "").lower()

    lista = [o for o in carregar() if o.get("loja") == loja]

    if busca:
        lista = [o for o in lista if busca in str(o).lower()]

    if request.args.get("aberto") == "1":
        lista = [o for o in lista if float(o.get("restante",0)) > 0]

    # 🔥 CORREÇÃO AQUI (lucro só do que foi pago)
    total = sum(float(o.get("valor",0)) - float(o.get("restante",0)) for o in lista)

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

# ================= EDITAR =================
@app.route("/editar/<numero>", methods=["GET","POST"])
def editar(numero):
    if not session.get("logado"):
        return redirect("/")

    lista = carregar()
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

        os_edit["custo"] = float(request.form.get("custo") or 0)
        os_edit["frete"] = float(request.form.get("frete") or 0)

        os_edit["pagamento"] = request.form.get("pagamento")
        os_edit["entrega"] = request.form.get("entrega")
        os_edit["garantia"] = request.form.get("garantia")
        os_edit["senha"] = request.form.get("senha")

        salvar(lista)
        return redirect("/financeiro")

    return render_template("editar.html", os=os_edit)
