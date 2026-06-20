import os
import sys
import webbrowser
import threading
import socket


def _porta_livre(inicio=3000, fim=9000):
    for p in range(inicio, fim):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", p)) != 0:
                return p
    return inicio


def _encontrar_modelos():
    base = os.path.dirname(os.path.abspath(__file__))
    candidatos = [
        os.path.join(base, "..", "modelos", "admin"),
        os.path.join(os.getcwd(), "modelos", "admin"),
    ]
    for c in candidatos:
        c = os.path.normpath(c)
        if os.path.isdir(c):
            return c
    alt = os.path.join(base, "..", "..", "modelos", "admin")
    alt = os.path.normpath(alt)
    if os.path.isdir(alt):
        return alt
    return None


def iniciar(porta=None, diretorio=None):
    if porta is None:
        porta = _porta_livre(8080)

    modelos = _encontrar_modelos()
    if not modelos:
        print("Erro: pasta modelos/admin nao encontrada", file=sys.stderr)
        sys.exit(1)

    if diretorio is None:
        diretorio = os.getcwd()

    m = modelos.replace("\\", "/")
    d = diretorio.replace("\\", "/")

    codigo = (
        "usar servidor\n"
        "usar arquivos\n"
        f"MD = '{m}'\n"
        f"DIR = '{d}'\n"
        "servidor.modelos(MD)\n"
        "servidor.estatico('/_admin/estatico', MD + '/estatico')\n"

        "servidor.rota('GET', '/_admin/', fn(req)\n"
        "    arqs = arquivos.listar(DIR)\n"
        "    lista = []\n"
        "    para a em arqs\n"
        "        se a.endswith('.spt')\n"
        "            lista = lista + [a]\n"
        "        fim\n"
        "    fim\n"
        "    retornar servidor.html('index.spt.html', {arquivos: lista, total: tamanho(lista)})\n"
        "fim)\n"

        "servidor.rota('GET', '/_admin/editar/:nome', fn(req)\n"
        "    caminho = DIR + '/' + req.params.nome\n"
        "    c = ''\n"
        "    se arquivos.existe(caminho)\n"
        "        c = arquivos.ler(caminho)\n"
        "    fim\n"
        "    retornar servidor.html('editor.spt.html', {nome: req.params.nome, codigo: c})\n"
        "fim)\n"

        "servidor.rota('POST', '/_admin/salvar/:nome', fn(req)\n"
        "    caminho = DIR + '/' + req.params.nome\n"
        "    cod = ''\n"
        "    se req.formulario\n"
        "        cod = req.formulario.codigo\n"
        "    fim\n"
        "    arquivos.escrever(caminho, cod)\n"
        "    retornar servidor.html('executar.spt.html', {nome: req.params.nome, saida: 'Salvo!', tipo: 'info'})\n"
        "fim)\n"

        "servidor.rota('POST', '/_admin/criar', fn(req)\n"
        "    nome = 'novo.spt'\n"
        "    se req.formulario\n"
        "        nome = req.formulario.nome\n"
        "    fim\n"
        "    se nao nome.endswith('.spt')\n"
        "        nome = nome + '.spt'\n"
        "    fim\n"
        "    caminho = DIR + '/' + nome\n"
        "    se nao arquivos.existe(caminho)\n"
        "        arquivos.escrever(caminho, 'falar \"Ola, mundo!\"\\n')\n"
        "    fim\n"
        "    retornar servidor.html('executar.spt.html', {nome: nome, saida: 'Criado: ' + nome, tipo: 'info'})\n"
        "fim)\n"

        "servidor.rota('GET', '/_admin/executar/:nome', fn(req)\n"
        "    caminho = DIR + '/' + req.params.nome\n"
        "    se arquivos.existe(caminho)\n"
        "        saida = servidor.codigo(arquivos.ler(caminho))\n"
        "        retornar servidor.html('executar.spt.html', {nome: req.params.nome, saida: saida, tipo: 'saida'})\n"
        "    senao\n"
        "        retornar servidor.html('executar.spt.html', {nome: req.params.nome, saida: 'Nao encontrado', tipo: 'erro'})\n"
        "    fim\n"
        "fim)\n"

        "servidor.rota('POST', '/_admin/deletar/:nome', fn(req)\n"
        "    caminho = DIR + '/' + req.params.nome\n"
        "    se arquivos.existe(caminho)\n"
        "        arquivos.deletar(caminho)\n"
        "        retornar servidor.html('executar.spt.html', {nome: req.params.nome, saida: 'Deletado: ' + req.params.nome, tipo: 'info'})\n"
        "    senao\n"
        "        retornar servidor.html('executar.spt.html', {nome: req.params.nome, saida: 'Nao encontrado', tipo: 'erro'})\n"
        "    fim\n"
        "fim)\n"

        "servidor.rota('GET', '/_admin/playground', fn(req)\n"
        "    retornar servidor.html('editor.spt.html', {nome: 'playground.spt', codigo: 'falar \"Ola, SimpliPT!\"\\n', tipo: 'play'})\n"
        "fim)\n"

        "servidor.rota('POST', '/_admin/playground', fn(req)\n"
        "    cod = ''\n"
        "    se req.formulario\n"
        "        cod = req.formulario.codigo\n"
        "    fim\n"
        "    saida = servidor.codigo(cod)\n"
        "    tipo = 'saida'\n"
        "    se saida.startswith('Erro:')\n"
        "        tipo = 'erro'\n"
        "    fim\n"
        "    retornar servidor.html('executar.spt.html', {nome: 'playground', saida: saida, tipo: tipo})\n"
        "fim)\n"

        "falar servidor.iniciar(" + str(porta) + ")\n"
    )

    from src.lexer.lexer import Lexer
    from src.parser.parser import Parser
    from src.interpreter.interpreter import Interpreter
    lex = Lexer(codigo, "dashboard")
    toks = lex.tokenizar()
    par = Parser(toks, "dashboard")
    ast = par.programa()
    interp = Interpreter()
    thread = threading.Thread(target=interp.interpretar, args=(ast,), daemon=True)
    thread.start()

    url = f"http://localhost:{porta}/_admin/"
    print(f"Dashboard: {url}")
    webbrowser.open(url)

    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nDashboard encerrado.")
