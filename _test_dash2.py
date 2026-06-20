import sys, io, contextlib, urllib.request, re, time, os

os.chdir(r'C:\Users\Master\Documents\Projetos\ia jarbs\projetos\simplipt')

# Save test file
with open('testar_exec2.spt', 'w') as f:
    f.write('falar "hello from script"\n')

code = """usar servidor
usar arquivos
usar executar

servidor.rota("GET", "/teste2/:nome", fn(req)
    caminho = req.params.nome
    se arquivos.existe(caminho)
        codigo = arquivos.ler(caminho)
        saida = executar.codigo(codigo)
    senao
        saida = "not found"
    fim
    retornar {"saida": saida}
fim)

falar servidor.iniciar(19883)
"""

from src.lexer.lexer import Lexer
from src.parser.parser import Parser
from src.interpreter.interpreter import Interpreter

lex = Lexer(code, "dashboard2")
tokens = lex.tokenizar()
parser = Parser(tokens, "dashboard2")
ast = parser.programa()

buf = io.StringIO()
old_stderr = sys.stderr
with contextlib.redirect_stdout(buf):
    interp = Interpreter()
    interp.interpretar(ast)
print("STDOUT:", buf.getvalue())

time.sleep(1)
try:
    body = urllib.request.urlopen("http://localhost:19883/teste2/testar_exec2.spt").read().decode()
    print("HTTP:", repr(body))
except Exception as e:
    print("HTTP ERRO:", e)

os.remove('testar_exec2.spt')
