import os
import sys

from src.erros import ErroLexico, ErroSintaxe
from src.lexer.lexer import Lexer
from src.parser.parser import Parser
from src.parser.ast import (
    Programa, Atribuicao, Funcao, Retornar, Falar, Chamada,
    ChamadaMembro, Se, ParaEm, ParaAte, Enquanto, Tentar,
    Usar, Variavel, Novo, Classe, Numero, Texto, Booleano,
    Nada, ListaExpr, DicionarioExpr, Binario, Unario, Ternario,
    Indexacao, Membro, Template,
)


_TIPOS_SIMPLIPT = {
    "texto": str,
    "inteiro": int,
    "numero": (int, float),
    "booleano": bool,
    "nada": type(None),
    "lista": list,
    "dicionario": dict,
}


def _tipo_python(valor):
    if isinstance(valor, bool):
        return "booleano"
    if isinstance(valor, int):
        return "inteiro"
    if isinstance(valor, float):
        return "numero"
    if isinstance(valor, str):
        return "texto"
    if isinstance(valor, list):
        return "lista"
    if isinstance(valor, dict):
        return "dicionario"
    if valor is None:
        return "nada"
    return type(valor).__name__


def _inferir_tipo(node):
    if isinstance(node, (Texto, Template)):
        return "texto"
    if isinstance(node, Numero):
        v = node.valor
        return "inteiro" if isinstance(v, int) else "numero"
    if isinstance(node, Booleano):
        return "booleano"
    if isinstance(node, Nada):
        return "nada"
    if isinstance(node, ListaExpr):
        return "lista"
    if isinstance(node, DicionarioExpr):
        return "dicionario"
    if isinstance(node, Ternario):
        tipo_v = _inferir_tipo(node.verdadeiro)
        tipo_f = _inferir_tipo(node.falso)
        return tipo_v if tipo_v == tipo_f else "qualquer"
    return None


class Analisador:
    def __init__(self):
        self.erros = []
        self._funcoes = {}

    def analisar(self, nodes, nome_arquivo="<memoria>"):
        self._analisar_programa(nodes)
        saida = []
        for err in self.erros:
            saida.append(f"{err}")
        return saida

    def _err(self, msg, node=None):
        info = ""
        if hasattr(node, "linha") and node.linha is not None:
            info = f" [linha {node.linha}]"
        self.erros.append(f"{msg}{info}")

    def _analisar_programa(self, nodes):
        for node in nodes if isinstance(nodes, list) else nodes.nodes if isinstance(nodes, Programa) else [nodes]:
            self._analisar_node(node)

    def _analisar_node(self, node):
        if isinstance(node, Atribuicao):
            self._analisar_atribuicao(node)
        elif isinstance(node, Funcao):
            self._analisar_funcao(node)
        elif isinstance(node, Retornar):
            self._analisar_retornar(node)
        elif isinstance(node, Se):
            self._analisar_programa(node.corpo)
            if node.senao:
                self._analisar_programa(node.senao)
        elif isinstance(node, (ParaEm, ParaAte, Enquanto)):
            self._analisar_programa(node.corpo)
        elif isinstance(node, Tentar):
            self._analisar_programa(node.corpo)
            self._analisar_programa(node.capturar)
        elif isinstance(node, Falar):
            pass

    def _analisar_atribuicao(self, node):
        if node.tipo:
            tipo_decl = node.tipo.lower()
            if tipo_decl not in _TIPOS_SIMPLIPT:
                self._err(f"Tipo desconhecido: '{node.tipo}'", node)
                return
            tipo_inferido = _inferir_tipo(node.valor)
            if tipo_inferido and tipo_inferido != "qualquer":
                tipo_esperado = _TIPOS_SIMPLIPT[tipo_decl]
                if tipo_inferido != tipo_decl:
                    self._err(
                        f"Tipo incompativel em '{node.nome}': "
                        f"declarado como '{tipo_decl}', "
                        f"mas valor e do tipo '{tipo_inferido}'",
                        node,
                    )

    def _analisar_funcao(self, node):
        if node.nome:
            self._funcoes[node.nome] = node
        self._analisar_programa(node.corpo)

    def _analisar_retornar(self, node):
        if node.valor is None:
            return
        tipo = _inferir_tipo(node.valor)
        if tipo is not None and tipo != "qualquer":
            pass


def verificar(caminho):
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            texto = f.read()
    except FileNotFoundError:
        return [f"Arquivo nao encontrado: {caminho}"]

    nome = os.path.basename(caminho)
    try:
        lex = Lexer(texto, nome)
        toks = lex.tokenizar()
        par = Parser(toks, nome)
        ast = par.programa()
    except (ErroLexico, ErroSintaxe) as e:
        return [f"Erro de sintaxe: {e}"]

    analisador = Analisador()
    return analisador.analisar(ast.nodes, nome)


def main():
    args = sys.argv[1:]
    if not args:
        print("Uso: simplipt --strict <arquivo.spt>")
        return

    erros = 0
    for caminho in args:
        res = verificar(caminho)
        if res:
            print(f"{caminho}:")
            for r in res:
                print(f"  {r}")
                erros += 1
        else:
            print(f"{caminho}: OK")

    if erros:
        sys.exit(1)


if __name__ == "__main__":
    main()
