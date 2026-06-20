from src.parser.ast import *
from src.lexer.token import TipoToken


def formatar(programa):
    lines = []
    for node in programa.nodes:
        lines.append(_formatar_node(node, 0))
    return "\n".join(lines)


def _fmt_op(op):
    for nome, val in vars(TipoToken).items():
        if isinstance(val, TipoToken) and val == op:
            return {"PIPE": "|>", "INTERVALO": "..", "IGUAL": "==", "DIFERENTE": "!=",
                    "E": "e", "OU": "ou", "NAO": "nao",
                    "MAIS": "+", "MENOS": "-", "VEZES": "*", "DIVIDIR": "/", "MOD": "%",
                    "MAIOR": ">", "MENOR": "<", "MAIOR_IGUAL": ">=", "MENOR_IGUAL": "<=",
                    "ATRIBUICAO": "=", "ADICAO_ATRIB": "+=", "SUB_ATRIB": "-="}.get(nome, nome.lower())
    return str(op)


def _formatar_node(node, nivel):
    indent = "    " * nivel
    if isinstance(node, Programa):
        return "\n".join(_formatar_node(n, nivel) for n in node.nodes)
    if isinstance(node, Atribuicao):
        return f"{indent}{node.nome} = {_formatar_expr(node.valor)}"
    if isinstance(node, AtribuicaoMembro):
        return f"{indent}{_formatar_expr(node.objeto)}.{node.nome} = {_formatar_expr(node.valor)}"
    if isinstance(node, Falar):
        return f"{indent}falar {_formatar_expr(node.expressao)}"
    if isinstance(node, Ler):
        if node.prompt:
            return f"{indent}ler {_formatar_expr(node.prompt)}"
        return f"{indent}ler"
    if isinstance(node, Limpar):
        return f"{indent}limpar"
    if isinstance(node, Log):
        return f"{indent}{node.nivel} {_formatar_expr(node.mensagem)}"
    if isinstance(node, Pausa):
        return f"{indent}pausa {_formatar_expr(node.tempo)}"
    if isinstance(node, Se):
        corpo = "\n".join(_formatar_node(n, nivel + 1) for n in node.corpo)
        s = f"{indent}se {_formatar_expr(node.condicao)}\n{corpo}"
        if node.senao:
            s += f"\n{indent}senao\n"
            s += "\n".join(_formatar_node(n, nivel + 1) for n in node.senao)
        s += f"\n{indent}fim"
        return s
    if isinstance(node, ParaAte):
        corpo = "\n".join(_formatar_node(n, nivel + 1) for n in node.corpo)
        return f"{indent}para {node.var} ate {_formatar_expr(node.ate)}\n{corpo}\n{indent}fim"
    if isinstance(node, ParaEm):
        corpo = "\n".join(_formatar_node(n, nivel + 1) for n in node.corpo)
        return f"{indent}para {node.var} em {_formatar_expr(node.colecao)}\n{corpo}\n{indent}fim"
    if isinstance(node, Enquanto):
        corpo = "\n".join(_formatar_node(n, nivel + 1) for n in node.corpo)
        return f"{indent}enquanto {_formatar_expr(node.condicao)}\n{corpo}\n{indent}fim"
    if isinstance(node, Funcao):
        params = ", ".join(node.params)
        corpo = "\n".join(_formatar_node(n, nivel + 1) for n in node.corpo)
        if node.nome:
            return f"{indent}funcao {node.nome}({params})\n{corpo}\n{indent}fim"
        return f"{indent}funcao({params})\n{corpo}\n{indent}fim"
    if isinstance(node, Retornar):
        if node.valor:
            return f"{indent}retornar {_formatar_expr(node.valor)}"
        return f"{indent}retornar"
    if isinstance(node, Chamada):
        args = ", ".join(_formatar_expr(a) for a in node.argumentos)
        return f"{indent}{node.nome}({args})"
    if isinstance(node, ChamadaMembro):
        args = ", ".join(_formatar_expr(a) for a in node.argumentos)
        return f"{_formatar_expr(node.objeto)}.{node.nome}({args})"
    if isinstance(node, Tentar):
        corpo = "\n".join(_formatar_node(n, nivel + 1) for n in node.corpo)
        capturar = "\n".join(_formatar_node(n, nivel + 1) for n in node.capturar)
        return f"{indent}tentar\n{corpo}\n{indent}capturar\n{capturar}\n{indent}fim"
    if isinstance(node, Paralelo):
        corpo = "\n".join(_formatar_node(n, nivel + 1) for n in node.corpo)
        return f"{indent}paralelo\n{corpo}\n{indent}fim"
    if isinstance(node, Usar):
        return f"{indent}usar {node.modulo}"
    if isinstance(node, Classe):
        s = f"{indent}classe {node.nome}"
        if node.base:
            s += f" extende {node.base}"
        s += "\n"
        if node.construtor:
            params = ", ".join(node.construtor.params)
            corpo = "\n".join(_formatar_node(n, nivel + 2) for n in node.construtor.corpo)
            s += f"{indent}    construtor({params})\n{corpo}\n{indent}    fim\n"
        for m in node.metodos:
            params = ", ".join(m.params)
            corpo = "\n".join(_formatar_node(n, nivel + 2) for n in m.corpo)
            s += f"{indent}    metodo {m.nome}({params})\n{corpo}\n{indent}    fim\n"
        s += f"{indent}fim"
        return s
    if isinstance(node, Novo):
        args = ", ".join(_formatar_expr(a) for a in node.argumentos)
        return f"{indent}novo {node.nome}({args})"
    if isinstance(node, Corresponder):
        s = f"{indent}corresponder {_formatar_expr(node.valor)}\n"
        for caso in node.casos:
            s += f"{indent}    caso {_formatar_expr(caso.padrao)}\n"
            s += "\n".join(_formatar_node(n, nivel + 2) for n in caso.corpo) + "\n"
        s += f"{indent}fim"
        return s
    if isinstance(node, ListaCompreensao):
        s = f"[{_formatar_expr(node.elemento)} para {node.var} em {_formatar_expr(node.colecao)}"
        if node.filtro:
            s += f" se {_formatar_expr(node.filtro)}"
        s += "]"
        return f"{indent}{s}"
    return f"{indent}({type(node).__name__})"


def _formatar_expr(expr):
    if isinstance(expr, Numero):
        return str(expr.valor)
    if isinstance(expr, Texto):
        return repr(expr.valor)
    if isinstance(expr, Booleano):
        return "verdadeiro" if expr.valor else "falso"
    if isinstance(expr, Nada):
        return "nada"
    if isinstance(expr, Variavel):
        return expr.nome
    if isinstance(expr, Este):
        return "este"
    if isinstance(expr, Super):
        return "super"
    if isinstance(expr, ListaExpr):
        elems = ", ".join(_formatar_expr(e) for e in expr.elementos)
        return f"[{elems}]"
    if isinstance(expr, DicionarioExpr):
        items = ", ".join(f"{k}: {_formatar_expr(v)}" for k, v in expr.pares.items())
        return "{" + items + "}"
    if isinstance(expr, Binario):
        op = _fmt_op(expr.operador)
        return f"{_formatar_expr(expr.esquerda)} {op} {_formatar_expr(expr.direita)}"
    if isinstance(expr, Unario):
        op = _fmt_op(expr.operador)
        return f"{op}{_formatar_expr(expr.expressao)}"
    if isinstance(expr, Indexacao):
        return f"{_formatar_expr(expr.objeto)}[{_formatar_expr(expr.indice)}]"
    if isinstance(expr, Membro):
        return f"{_formatar_expr(expr.objeto)}.{expr.nome}"
    if isinstance(expr, Template):
        result = '"'
        for parte in expr.partes:
            if isinstance(parte, Texto):
                result += parte.valor
            else:
                result += "{" + _formatar_expr(parte) + "}"
        result += '"'
        return result
    if isinstance(expr, Chamada):
        args = ", ".join(_formatar_expr(a) for a in expr.argumentos)
        return f"{expr.nome}({args})"
    if isinstance(expr, ChamadaMembro):
        args = ", ".join(_formatar_expr(a) for a in expr.argumentos)
        return f"{_formatar_expr(expr.objeto)}.{expr.nome}({args})"
    if isinstance(expr, ListaCompreensao):
        s = f"[{_formatar_expr(expr.elemento)} para {expr.var} em {_formatar_expr(expr.colecao)}"
        if expr.filtro:
            s += f" se {_formatar_expr(expr.filtro)}"
        s += "]"
        return s
    if isinstance(expr, Novo):
        args = ", ".join(_formatar_expr(a) for a in expr.argumentos)
        return f"novo {expr.nome}({args})"
    if isinstance(expr, Funcao):
        params = ", ".join(expr.params)
        corpo = "\n".join("        " + _formatar_node(n, 0) for n in expr.corpo)
        return f"funcao({params})\n{corpo}\n    fim"
    return repr(expr)
