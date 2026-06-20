import sys, io, contextlib
from src.lexer.lexer import Lexer
from src.parser.parser import Parser
from src.interpreter.interpreter import Interpreter

# Ultra-simple test: set a dict in env and call its method
code = """m = {"fn": fn(x) falar("oi " + x) fim}
m.fn("mundo")
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
