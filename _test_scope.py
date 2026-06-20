import sys, io, contextlib
from src.lexer.lexer import Lexer
from src.parser.parser import Parser
from src.interpreter.interpreter import Interpreter

# Test: does usar executar work inside a fn callback?
code = """usar executar

fn teste(req)
    saida = executar.codigo('falar "dentro do fn"')
    retornar saida
fim

resultado = teste("")
falar resultado
"""
lex = Lexer(code, 'test')
tokens = lex.tokenizar()
parser = Parser(tokens, 'test')
ast = parser.programa()

buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    interp = Interpreter()
    interp.interpretar(ast)
print("OUTPUT:", repr(buf.getvalue()))
