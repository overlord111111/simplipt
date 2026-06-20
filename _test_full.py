import sys, io, contextlib
from src.lexer.lexer import Lexer
from src.parser.parser import Parser
from src.interpreter.interpreter import Interpreter
from src.erros import ErroRuntime

# Exact dashboard code (simplified)
code = """usar servidor
usar arquivos
usar executar

servidor.rota("GET", "/_admin/executar/:nome", fn(req)
    codigo = arquivos.ler("teste_exec.spt")
    saida = executar.codigo(codigo)
    retornar servidor.html("executar.spt.html", {"nome": "teste", "saida": saida})
fim)

falar servidor.iniciar(19880)
"""
lex = Lexer(code, 'dashboard')
tokens = lex.tokenizar()
parser = Parser(tokens, 'dashboard')
ast = parser.programa()

buf = io.StringIO()
errors = io.StringIO()

interp = Interpreter()
old_stderr = sys.stderr
sys.stderr = errors
try:
    with contextlib.redirect_stdout(buf):
        interp.interpretar(ast)
    print("STDOUT:", repr(buf.getvalue()))
    print("STDERR:", repr(errors.getvalue()))
    print("MODULOS:", list(interp.modulos.keys()))
except Exception as e:
    print("ERRO:", e)
    import traceback
    traceback.print_exc()
finally:
    sys.stderr = old_stderr

# Now test HTTP
import urllib.request
import time
time.sleep(1)
try:
    body = urllib.request.urlopen("http://localhost:8080/_admin/executar/teste_exec.spt").read().decode()
    import re
    m = re.search(r'class="saida">(.+?)</pre>', body, re.DOTALL)
    print("RESPONSE:", repr(m.group(1).strip() if m else "no match"))
except Exception as e:
    print("HTTP ERRO:", e)
