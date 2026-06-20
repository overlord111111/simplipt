import io
import sys
import contextlib
import traceback

from src.erros import ErroLexico, ErroSintaxe, ErroRuntime
from src.lexer.lexer import Lexer
from src.parser.parser import Parser
from src.interpreter.interpreter import Interpreter


def _executar(texto):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            lexer = Lexer(texto, "<executar>")
            tokens = lexer.tokenizar()
            parser = Parser(tokens, "<executar>")
            ast = parser.programa()
            interp = Interpreter()
            interp.interpretar(ast)
        except (ErroLexico, ErroSintaxe, ErroRuntime) as e:
            return f"Erro: {e}"
        except Exception as e:
            return f"Erro interno: {e}\n{traceback.format_exc()}"
    return buf.getvalue().rstrip("\n") or "(sem saida)"


MODULO = {
    "spt": _executar,
}
