import sys, io, contextlib, urllib.request, re, time, os

os.chdir(r'C:\Users\Master\Documents\Projetos\ia jarbs\projetos\simplipt')

code = """usar servidor
usar executar

servidor.rota("GET", "/testar", fn(req)
    r = executar.codigo("falar 42")
    retornar r
fim)

falar servidor.iniciar(19884)
"""

from src.lexer.lexer import Lexer
from src.parser.parser import Parser
from src.interpreter.interpreter import Interpreter

lex = Lexer(code, "debug")
tokens = lex.tokenizar()
parser = Parser(tokens, "debug")
ast = parser.programa()

buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    interp = Interpreter()
    interp.interpretar(ast)
print("STDOUT:", buf.getvalue())

time.sleep(1)
try:
    body = urllib.request.urlopen("http://localhost:19884/testar").read().decode()
    print("HTTP:", repr(body))
except Exception as e:
    print("HTTP ERRO:", e)
