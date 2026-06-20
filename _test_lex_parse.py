from src.lexer.lexer import Lexer
from src.parser.parser import Parser

codigo = """usar servidor
usar arquivos
usar sistema
usar executar

servidor.rota("GET", "/_admin/executar/:nome", fn(req)
    caminho = "teste_exec.spt"
    se arquivos.existe(caminho)
        codigo = arquivos.ler(caminho)
        saida = executar.codigo(codigo)
    senao
        saida = "not found"
    fim
    retornar servidor.html("executar.spt.html", {"nome": "teste", "saida": saida})
fim)
"""
lex = Lexer(codigo, 'test')
tokens = lex.tokenizar()
print("=== TOKENS ===")
for t in tokens:
    if t.tipo.name in ('FIM_DE_LINHA',):
        continue
    print(f'{t.tipo.name:20} {repr(t.valor)}')
print()
print("=== PARSE ===")
parser = Parser(tokens, 'test')
try:
    ast = parser.programa()
    print("OK:", ast)
except Exception as e:
    print("ERRO:", e)
