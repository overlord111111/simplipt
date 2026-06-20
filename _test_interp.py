from src.lexer.lexer import Lexer
from src.parser.parser import Parser
from src.interpreter.interpreter import Interpreter

# Simulate the dashboard code
codigo = """usar servidor
usar sistema
usar executar

caminho = sistema.caminho_atual() + "/teste_exec.spt"
cod = arquivos_ler(caminho)
saida = executar_codigo(cod)
falar(saida)
"""

# Hmm, this won't work in SimpliPT context. Let me test differently.
# Test the executar module directly in the interpreter

from src.runtime.builtins import REGISTRY_BUILTINS

interp = Interpreter()

# First, load the executar module
from src.lexer.lexer import Lexer
from src.parser.parser import Parser

test_code = """usar executar
saida = executar.codigo('falar 42')
falar(saida)
"""
lex = Lexer(test_code, 'test')
tokens = lex.tokenizar()
parser = Parser(tokens, 'test')
ast = parser.programa()
print("Parsed OK, running...")
result = interp.interpretar(ast)
print("Done")
