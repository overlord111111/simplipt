from src.lexer.lexer import Lexer
from src.parser.parser import Parser
from src.interpreter.interpreter import Interpreter
import io, contextlib

# Test: capture output of a script
test_code = 'falar "Ola, mundo!"\nfalar 2+2\n'
lex = Lexer(test_code, 'test')
tokens = lex.tokenizar()
parser = Parser(tokens, 'test')
ast = parser.programa()

buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    interp = Interpreter()
    interp.interpretar(ast)
output = buf.getvalue()

print("OUTPUT:", repr(output))
print("RSTRIP:", repr(output.rstrip("\n")))
print("SEM SAIDA:", output.rstrip("\n") or "(sem saida)")
