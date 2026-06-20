from src.lexer.lexer import Lexer
from src.parser.parser import Parser

code = 'saida = executar.codigo(codigo)\n'
lex = Lexer(code, 'test')
tokens = lex.tokenizar()
parser = Parser(tokens, 'test')
ast = parser.programa()
print("AST:", ast)
for node in ast.nodes:
    if hasattr(node, 'valor') and hasattr(node.valor, 'nome'):
        print("  nome:", node.valor.nome)
    if hasattr(node, 'valor') and hasattr(node.valor, 'objeto'):
        print("  objeto:", node.valor.objeto)
        print("  nome:", node.valor.nome)
        print("  argumentos:", node.valor.argumentos)
