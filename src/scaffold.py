import os
import sys


_TEMPLATES = {
    "main.spt": '''usar servidor
usar banco
usar json

BANCO = "dados.db"
PORTA = 3000

banco.conectar(BANCO)
banco.criar_tabela("CREATE TABLE IF NOT EXISTS itens (id INTEGER PRIMARY KEY, nome TEXT, criado_em TEXT DEFAULT CURRENT_TIMESTAMP)")

servidor.estatico("/estatico", "estatico")
servidor.modelos("modelos")

servidor.rota("GET", "/", fn(req)
    itens = banco.buscar("SELECT * FROM itens ORDER BY criado_em DESC")
    retornar servidor.html("index.spt.html", {itens: itens})
fim)

servidor.rota("GET", "/api/itens", fn(req)
    retornar banco.buscar("SELECT * FROM itens ORDER BY criado_em DESC")
fim)

servidor.rota("POST", "/api/itens", fn(req)
    nome = req.corpo.nome se req.corpo senao "item"
    banco.inserir("itens", {nome: nome})
    retornar {ok: verdadeiro, id: banco.ultimo_id()}
fim)

servidor.rota("POST", "/deletar/:id", fn(req)
    banco.deletar("itens", "id = ?", [req.params.id])
    retornar servidor.redirect("/")
fim)

falar "=== {{nome}} ==="
falar "http://localhost:{PORTA}"
falar servidor.iniciar(PORTA)

enquanto verdadeiro
    pausa 1
fim
''',

    "modelos/index.spt.html": '''<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{{nome}}</title>
<link rel="stylesheet" href="/estatico/style.css">
</head>
<body>
<div class="topo">
    <h1>&#x2B21; {{nome}}</h1>
</div>
<div class="conteudo">
    <div class="cartao">
        <h2>Itens</h2>
        <form action="/api/itens" method="POST" id="formItem">
            <input type="text" name="nome" placeholder="Novo item" required>
            <button type="submit">Adicionar</button>
        </form>
        {% se itens %}
        <ul>
        {% para item em itens %}
            <li>{{ item.nome }} <a href="/deletar/{{ item.id }}">[x]</a></li>
        {% fim %}
        </ul>
        {% senao %}
        <p class="vazio">Nenhum item ainda. Adicione um acima.</p>
        {% fim %}
    </div>
</div>
<script>
document.getElementById('formItem').addEventListener('submit', function(e) {
    e.preventDefault();
    var fd = new FormData(this);
    fetch('/api/itens', {method:'POST', body:JSON.stringify({nome: fd.get('nome')}), headers:{'Content-Type':'application/json'}})
    .then(function(){ location.reload(); });
});
</script>
</body>
</html>
''',

    "estatico/style.css": '''*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',system-ui,sans-serif;background:#0d1117;color:#c9d1d9;min-height:100vh}
.topo{background:#161b22;border-bottom:1px solid #30363d;padding:12px 24px}
.topo h1{font-size:18px;color:#58a6ff}
.conteudo{max-width:800px;margin:0 auto;padding:24px}
.cartao{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:20px;margin-bottom:16px}
.cartao h2{font-size:16px;margin-bottom:12px;color:#f0f6fc}
input{padding:8px 12px;background:#0d1117;border:1px solid #30363d;border-radius:6px;color:#c9d1d9;font-size:14px;margin-right:8px}
button{padding:8px 16px;background:#238636;border:none;border-radius:6px;color:#fff;font-size:14px;cursor:pointer}
button:hover{background:#2ea043}
ul{list-style:none;margin-top:12px}
li{padding:8px 0;border-bottom:1px solid #21262d;font-size:14px}
li a{color:#f85149;text-decoration:none;margin-left:12px}
.vazio{color:#8b949e;font-size:14px;padding:24px;text-align:center}
''',
}


def criar(projeto_nome):
    if os.path.exists(projeto_nome):
        print(f"Diretorio ja existe: {projeto_nome}", file=sys.stderr)
        return False

    os.makedirs(projeto_nome)
    os.makedirs(os.path.join(projeto_nome, "modelos"))
    os.makedirs(os.path.join(projeto_nome, "estatico"))

    for caminho_rel, conteudo in _TEMPLATES.items():
        caminho_abs = os.path.join(projeto_nome, caminho_rel)
        with open(caminho_abs, "w", encoding="utf-8") as f:
            f.write(conteudo.replace("{{nome}}", projeto_nome))

    print(f"Projeto '{projeto_nome}' criado!")
    print(f"  cd {projeto_nome}")
    print(f"  simplipt main.spt")
    return True


def main():
    args = sys.argv[1:]
    if not args:
        print("Uso: simplipt new <nome_do_projeto>", file=sys.stderr)
        return
    criar(args[0])


if __name__ == "__main__":
    main()
