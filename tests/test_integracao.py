import os
import unittest


_EXEMPLOS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "exemplos")
_EXAMPLES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "examples")


def _compila(caminho):
    from src.lexer.lexer import Lexer
    from src.parser.parser import Parser
    with open(caminho, "r", encoding="utf-8") as f:
        texto = f.read()
    lex = Lexer(texto, os.path.basename(caminho))
    toks = lex.tokenizar()
    par = Parser(toks, os.path.basename(caminho))
    return par.programa()


def _lista_spt(diretorio):
    arquivos = []
    if os.path.isdir(diretorio):
        for f in sorted(os.listdir(diretorio)):
            if f.endswith(".spt") and not f.startswith("_"):
                arquivos.append(os.path.join(diretorio, f))
    return arquivos


class TestExemplosCompilam(unittest.TestCase):
    pass


def _cria_teste(caminho):
    nome = os.path.basename(caminho).replace(".", "_")

    def test(self):
        self.assertTrue(os.path.exists(caminho))
        ast = _compila(caminho)
        self.assertIsNotNone(ast)

    test.__name__ = f"test_{nome}"
    return test


for arq in _lista_spt(_EXAMPLES_DIR) + _lista_spt(_EXEMPLOS_DIR) + [os.path.join(os.path.dirname(os.path.dirname(__file__)), "validar_exemplos.spt")]:
    if os.path.exists(arq):
        nome = os.path.basename(arq).replace(".", "_")
        setattr(TestExemplosCompilam, f"test_{nome}", _cria_teste(arq))


if __name__ == "__main__":
    unittest.main()
