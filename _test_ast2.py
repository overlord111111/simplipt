from src.lexer.lexer import Lexer
from src.parser.parser import Parser
from src.parser.ast import *

code = """servidor.rota("GET", "/_admin/executar/:nome", fn(req)
    caminho = diretorio_spt + "/" + req.params.nome
    se arquivos.existe(caminho)
        conteudo = arquivos.ler(caminho)
        saida = executar.spt(conteudo)
    senao
        saida = "nao encontrado"
    fim
    retornar servidor.html("executar.spt.html", {"nome": req.params.nome, "saida": saida})
fim)
"""
lex = Lexer(code, 'parse_test')
tokens = lex.tokenizar()
parser = Parser(tokens, 'parse_test')
ast = parser.programa()

# Recursively find all nodes
def find_nodes(node, depth=0):
    if node is None:
        return
    if isinstance(node, list):
        for n in node:
            find_nodes(n, depth)
        return
    indent = "  " * depth
    cls_name = type(node).__name__
    if hasattr(node, 'nome'):
        print(f"{indent}{cls_name}: nome={node.nome}")
    elif hasattr(node, 'valor'):
        if hasattr(node.valor, 'nome'):
            print(f"{indent}{cls_name}: valor.nome={node.valor.nome}")
        else:
            print(f"{indent}{cls_name}: valor={node.valor}")
    else:
        print(f"{indent}{cls_name}")
    
    for attr_name in dir(node):
        if attr_name.startswith('_') or attr_name in ('tipo', 'condicao', 'verdadeiro', 'falso', 'objeto', 'corpo', 'senao', 'esquerda', 'direita', 'operador'):
            continue
        attr = getattr(node, attr_name)
        if isinstance(attr, (Node, list, tuple)) or (hasattr(attr, '__dataclass_fields__')):
            try:
                find_nodes(attr, depth+1)
            except:
                pass

find_nodes(ast)
