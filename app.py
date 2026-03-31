@app.route("/financeiro", methods=["GET","POST"])
def financeiro():
    if not session.get("logado"):
        return redirect("/")

    # 🔐 senha financeiro
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

    # 🔍 filtro busca
    if busca:
        lista = [o for o in lista if busca in str(o).lower()]

    # 🔥 filtro aberto
    if request.args.get("aberto") == "1":
        lista = [o for o in lista if float(o.get("restante",0)) > 0]

    # 💰 totais
    total = sum(float(o.get("valor",0)) - float(o.get("restante",0)) for o in lista)
    total_aberto = sum(float(o.get("restante",0)) for o in lista)

    custo = sum(float(o.get("custo",0)) for o in lista)
    frete = sum(float(o.get("frete",0)) for o in lista)
    lucro = total - custo - frete

    # 📊 lucro por dia
    lucro_por_dia = {}
    for o in lista:
        recebido = float(o.get("valor",0)) - float(o.get("restante",0))
        data = o.get("data")

        lucro_os = recebido - float(o.get("custo",0)) - float(o.get("frete",0))

        if data not in lucro_por_dia:
            lucro_por_dia[data] = 0

        lucro_por_dia[data] += lucro_os

    return render_template("financeiro.html",
        lista=lista,
        total=total,
        total_aberto=total_aberto,
        custo=custo,
        frete=frete,
        lucro=lucro,
        lucro_por_dia=lucro_por_dia
    )
