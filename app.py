from flask import Flask, render_template, request, redirect
import json
import requests

app = Flask(__name__)

# 🔐 SEU TOKEN DROPBOX
DROPBOX_TOKEN = "vou te dar o cod vc me da o cod.py alterado pode ser sl.u.AGYoRW3km-OzmxQNIs0b9gAnFW1aRqqN82OJUiAlMLqatJNECheNBVXBtwfZUg_0DVnwhu9cxG9qUyTlb75aGPe0QOSlvLlZPQGAZSSyJ6kVDschP-nadGCkZc9L_iavw_3Eh2jgi26YO8jkl03IGykt0jPV7W9r8Czb2xlPjpmpiWCHiKFeajcC-ylpSeY5lSGk8z8a5rOjF0PN7ACenMHMRkH1fgV119_p6xC9VY1tMU1wEtK_NW07ZyapwRBvCvxw2NBdxmdwvP_NsPile_6qkR-Xg7-AFPJjGKL0IZ_zFSuMxq8dd0YysEXSWs2GPHGTQerSNbuXZ4EYXlrXqb_5TFWYFn48JM3dTzWEXD1dq8n9ECKcoAcT2WcItfCznxT9v4OcUCI5fuIH8lWFzPWEARXrNnJ18im0pCCinRQVFo8HA3DMBiXugfTe98yRptATSPhjrtxuOqZEJfnfGJBG6t1xOAxb1rRYLNh0i0LNNNaUChvarYoADeZSidUIe_tOOYUh-6DyOVX5AsL5i_JiwwUghBCfTqc8AIJfrjsNqg4JfvE2dbaO5q7AvrVLD2Nlf4M93VrG7NQFeqGvYCstPhmrVK42NfR2eEaUBzYuRqN2jkVsgkCV-uASBh-7N5HqZFR30P7eSWiJPQpOEYOMCeKKYfVuWV0M64hNHqTfv9O8zz--JIZDVDtevQiw4mAoxab4P5SujkmBZRih2AkzyEaGQlp8B_Ax-k4dDh4vRvoZ0tk3Vh9rCjHnhmI8Gn4p4H5ENeJr_EnOw8nRwi2-7bM58b7C2JMR3EFxRg3NPW4DIXVnl7GK5jfD6pN8fzik23aH6EtV8Ps7T_FAUT1s3aNMYA5VeuBNUfWu20BCNWkOEWAaRWp14Kr_DH_NNFQXI9mbsIpJKcJnzY9gKu_8wEo8pzyZEptG3TTguJT5yjSqCJucMlOyXTvqC6RpPD4S3iRZmKX9emKNvoZmOBmx0WMpN1IrGOjAE-FJNSLXPm0sXwE1lMgzIPa2M12VHTJfBwCgYG9Fswk0hvQdLQWcsZeyhsHLzqCjtXcithR7FNoj1XdpSKzEzvg6SRMtt-Lc_dYGNDcFfJTNDyQJRWWqD0dCK9cNLaDeAfbl2-ivlPtBJmS7QzkioSW20nc91cPKA357rvJOEd4tJpabJ6sI6KDp1sNAh52gqX2rxl4dEGXnfRqKBy3Yy0AgADigR3U5YClMJ5HWtoiv0YRpw4LgF8LuaRrfNdLVyWA2IAD8tfNK-TPEIDcYQCqj69-LsWU4Dr5Kk4uHVS20jqx1lfsHSVxhLy0MMi4xWFkEVkzGuGOgQw24zdA_lK-GLfLhmXAG6DdJtFnI9Yv1PNxJj011cM9wfDGO4HQCeWtJ2w6sJVZAz6LLLngaYrll14QJP_epzzNUMVu8vvvKYYAqWFTi6BqY_lq4Xm2UM0Dp8FRVcA"

ARQUIVO_DROPBOX = "/os.json"

# ==============================
# 🔽 FUNÇÕES SEGURAS (SEM ERRO 500)
# ==============================

def carregar_dados():
    try:
        url = "https://content.dropboxapi.com/2/files/download"

        headers = {
            "Authorization": f"Bearer {DROPBOX_TOKEN}",
            "Dropbox-API-Arg": json.dumps({"path": ARQUIVO_DROPBOX})
        }

        resposta = requests.post(url, headers=headers)

        if resposta.status_code == 200:
            return json.loads(resposta.content)
        else:
            return []  # se não existir ainda

    except:
        return []


def salvar_dados(dados):
    try:
        url = "https://content.dropboxapi.com/2/files/upload"

        headers = {
            "Authorization": f"Bearer {DROPBOX_TOKEN}",
            "Dropbox-API-Arg": json.dumps({
                "path": ARQUIVO_DROPBOX,
                "mode": "overwrite"
            }),
            "Content-Type": "application/octet-stream"
        }

        requests.post(url, headers=headers, data=json.dumps(dados))

    except:
        pass  # nunca quebra o sistema


# ==============================
# 🔽 ROTAS
# ==============================

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        nova_os = {
            "cliente": request.form.get("cliente"),
            "telefone": request.form.get("telefone"),
            "aparelho": request.form.get("aparelho"),
            "defeito": request.form.get("defeito"),
            "valor": request.form.get("valor")
        }

        dados = carregar_dados()
        dados.append(nova_os)
        salvar_dados(dados)

        return redirect("/")

    dados = carregar_dados()
    return render_template("index.html", dados=dados)


# ==============================
# 🚀 START
# ==============================

if __name__ == "__main__":
    app.run(debug=True)
