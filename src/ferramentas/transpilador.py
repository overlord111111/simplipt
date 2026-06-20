from src.parser.ast import *


def transpilar(programa):
    lines = []
    for node in programa.nodes:
        lines.append(_transpilar_node(node, 0))
    return "\n".join(lines)


def _transpilar_node(node, nivel):
    indent = "    " * nivel
    if isinstance(node, Programa):
        return "\n".join(_transpilar_node(n, nivel) for n in node.nodes)
    if isinstance(node, Atribuicao):
        return f"{indent}{node.nome} = {_transpilar_expr(node.valor)}"
    if isinstance(node, AtribuicaoMembro):
        return f"{indent}{_transpilar_expr(node.objeto)}.{node.nome} = {_transpilar_expr(node.valor)}"
    if isinstance(node, Falar):
        return f"{indent}print({_transpilar_expr(node.expressao)})"
    if isinstance(node, Ler):
        if node.prompt:
            return f"{indent}input({_transpilar_expr(node.prompt)})"
        return f"{indent}input()"
    if isinstance(node, Limpar):
        return f'{indent}print("\\033c", end="")'
    if isinstance(node, Log):
        return f'{indent}print(f"[{{__import__(\\"datetime\\").datetime.now().strftime(\\"%H:%M:%S\\")}}] [{{{node.nivel.upper()}}}] {{{_transpilar_expr(node.mensagem)}}}")'
    if isinstance(node, Pausa):
        return f"{indent}__import__('time').sleep({_transpilar_expr(node.tempo)})"
    if isinstance(node, Se):
        corpo = "\n".join(_transpilar_node(n, nivel + 1) for n in node.corpo)
        s = f"{indent}if {_transpilar_expr(node.condicao)}:\n{corpo}"
        if node.senao:
            s += f"\n{indent}else:\n"
            s += "\n".join(_transpilar_node(n, nivel + 1) for n in node.senao)
        return s
    if isinstance(node, ParaAte):
        corpo = "\n".join(_transpilar_node(n, nivel + 1) for n in node.corpo)
        return f"{indent}for {node.var} in range(1, {_transpilar_expr(node.ate)} + 1):\n{corpo}"
    if isinstance(node, ParaEm):
        corpo = "\n".join(_transpilar_node(n, nivel + 1) for n in node.corpo)
        return f"{indent}for {node.var} in {_transpilar_expr(node.colecao)}:\n{corpo}"
    if isinstance(node, Enquanto):
        corpo = "\n".join(_transpilar_node(n, nivel + 1) for n in node.corpo)
        return f"{indent}while {_transpilar_expr(node.condicao)}:\n{corpo}"
    if isinstance(node, Funcao):
        params = ", ".join(node.params)
        corpo = "\n".join(_transpilar_node(n, nivel + 1) for n in node.corpo)
        nome = node.nome if node.nome else "_anonima"
        return f"{indent}def {nome}({params}):\n{corpo}"
    if isinstance(node, Retornar):
        if node.valor:
            return f"{indent}return {_transpilar_expr(node.valor)}"
        return f"{indent}return"
    if isinstance(node, Chamada):
        args = ", ".join(_transpilar_expr(a) for a in node.argumentos)
        return f"{indent}{node.nome}({args})"
    if isinstance(node, ChamadaMembro):
        args = ", ".join(_transpilar_expr(a) for a in node.argumentos)
        return f"{_transpilar_expr(node.objeto)}.{node.nome}({args})"
    if isinstance(node, Tentar):
        corpo = "\n".join(_transpilar_node(n, nivel + 1) for n in node.corpo)
        capturar = "\n".join(_transpilar_node(n, nivel + 1) for n in node.capturar)
        return f"{indent}try:\n{corpo}\n{indent}except:\n{capturar}"
    if isinstance(node, Paralelo):
        return f"{indent}# paralelo"
    if isinstance(node, Usar):
        return f"{indent}# usar {node.modulo}"
    if isinstance(node, Classe):
        s = f"{indent}class {node.nome}"
        if node.base:
            s += f"({node.base})"
        s += ":\n"
        if node.construtor:
            params = ", ".join(node.construtor.params)
            corpo = "\n".join(_transpilar_node(n, nivel + 2) for n in node.construtor.corpo)
            s += f"{indent}    def __init__(self, {params}):\n{corpo}\n"
        for m in node.metodos:
            params = ", ".join(m.params)
            corpo = "\n".join(_transpilar_node(n, nivel + 2) for n in m.corpo)
            s += f"{indent}    def {m.nome}(self, {params}):\n{corpo}\n"
        return s.rstrip()
    if isinstance(node, Novo):
        args = ", ".join(_transpilar_expr(a) for a in node.argumentos)
        return f"{indent}{node.nome}({args})"
    if isinstance(node, Corresponder):
        s = f"{indent}match {_transpilar_expr(node.valor)}:\n"
        for caso in node.casos:
            if isinstance(caso.padrao, Variavel):
                s += f"{indent}    case _:\n"
            else:
                s += f"{indent}    case {_transpilar_expr(caso.padrao)}:\n"
            for n in caso.corpo:
                s += _transpilar_node(n, nivel + 2) + "\n"
        return s.rstrip()
    if isinstance(node, ListaCompreensao):
        s = f"[{_transpilar_expr(node.elemento)} for {node.var} in {_transpilar_expr(node.colecao)}"
        if node.filtro:
            s += f" if {_transpilar_expr(node.filtro)}"
        s += "]"
        return f"{indent}{s}"
    return f"{indent}# {type(node).__name__}"


def _transpilar_expr(expr):
    if isinstance(expr, Numero):
        return str(expr.valor)
    if isinstance(expr, Texto):
        return repr(expr.valor)
    if isinstance(expr, Booleano):
        return "True" if expr.valor else "False"
    if isinstance(expr, Nada):
        return "None"
    if isinstance(expr, Variavel):
        return expr.nome
    if isinstance(expr, Este):
        return "self"
    if isinstance(expr, Super):
        return "super()"
    if isinstance(expr, ListaExpr):
        elems = ", ".join(_transpilar_expr(e) for e in expr.elementos)
        return f"[{elems}]"
    if isinstance(expr, DicionarioExpr):
        items = ", ".join(f"{k!r}: {_transpilar_expr(v)}" for k, v in expr.pares.items())
        return "{" + items + "}"
    if isinstance(expr, Binario):
        esq = _transpilar_expr(expr.esquerda)
        direita = _transpilar_expr(expr.direita)
        from src.lexer.token import TipoToken
        if expr.operador == TipoToken.E:
            return f"({esq} and {direita})"
        if expr.operador == TipoToken.OU:
            return f"({esq} or {direita})"
        if expr.operador == TipoToken.IGUAL:
            return f"({esq} == {direita})"
        if expr.operador == TipoToken.DIFERENTE:
            return f"({esq} != {direita})"
        if expr.operador == TipoToken.INTERVALO:
            return f"list(range({esq}, {direita} + 1))"
        if expr.operador == TipoToken.PIPE:
            return f"({direita}({esq}))"
        op_str = {TipoToken.MAIS: "+", TipoToken.MENOS: "-", TipoToken.VEZES: "*",
                  TipoToken.DIVIDIR: "/", TipoToken.MOD: "%",
                  TipoToken.MAIOR: ">", TipoToken.MENOR: "<",
                  TipoToken.MAIOR_IGUAL: ">=", TipoToken.MENOR_IGUAL: "<="}.get(expr.operador, "?")
        return f"({esq} {op_str} {direita})"
    if isinstance(expr, Unario):
        from src.lexer.token import TipoToken
        val = _transpilar_expr(expr.expressao)
        if expr.operador == TipoToken.NAO:
            return f"(not {val})"
        return f"(-{val})"
    if isinstance(expr, Indexacao):
        return f"{_transpilar_expr(expr.objeto)}[{_transpilar_expr(expr.indice)}]"
    if isinstance(expr, Membro):
        return f"{_transpilar_expr(expr.objeto)}.{expr.nome}"
    if isinstance(expr, Template):
        parts = []
        for parte in expr.partes:
            if isinstance(parte, Texto):
                parts.append(repr(parte.valor))
            else:
                parts.append(f"str({_transpilar_expr(parte)})")
        return "f" + "+".join(parts) if len(parts) == 1 else "(" + "+".join(parts) + ")"
        return " + ".join(parts)
    if isinstance(expr, Chamada):
        args = ", ".join(_transpilar_expr(a) for a in expr.argumentos)
        return f"{expr.nome}({args})"
    if isinstance(expr, ChamadaMembro):
        args = ", ".join(_transpilar_expr(a) for a in expr.argumentos)
        return f"{_transpilar_expr(expr.objeto)}.{expr.nome}({args})"
    if isinstance(expr, ListaCompreensao):
        s = f"[{_transpilar_expr(expr.elemento)} for {expr.var} in {_transpilar_expr(expr.colecao)}"
        if expr.filtro:
            s += f" if {_transpilar_expr(expr.filtro)}"
        s += "]"
        return s
    if isinstance(expr, Novo):
        args = ", ".join(_transpilar_expr(a) for a in expr.argumentos)
        return f"{expr.nome}({args})"
    if isinstance(expr, Funcao):
        params = ", ".join(expr.params)
        corpo = "; ".join(_transpilar_node(n, 0) for n in expr.corpo)
        return f"(lambda {params}: {corpo})"
    return repr(expr)
