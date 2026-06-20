import sys
import json
import io
import traceback as tb

from src.erros import ErroLexico, ErroSintaxe, ErroRuntime
from src.lexer.lexer import Lexer
from src.parser.parser import Parser


def executar_json(caminho):
    resultado = {
        "arquivo": caminho,
        "sucesso": False,
        "saida": "",
        "erro": None,
        "tipo_erro": None,
        "ast": None,
    }

    try:
        with open(caminho, "r", encoding="utf-8") as f:
            texto = f.read()
    except FileNotFoundError:
        resultado["erro"] = f"Arquivo nao encontrado: {caminho}"
        return resultado
    except IOError as e:
        resultado["erro"] = str(e)
        return resultado

    nome = caminho.split("/")[-1].split("\\")[-1]

    try:
        lex = Lexer(texto, nome)
        toks = lex.tokenizar()
        par = Parser(toks, nome)
        ast = par.programa()
    except (ErroLexico, ErroSintaxe) as e:
        resultado["erro"] = str(e)
        resultado["tipo_erro"] = "sintaxe"
        return resultado

    from src.interpreter.interpreter import Interpreter
    buf = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buf
    try:
        interp = Interpreter()
        interp.interpretar(ast)
        resultado["sucesso"] = True
        resultado["saida"] = buf.getvalue()
    except (ErroLexico, ErroSintaxe, ErroRuntime) as e:
        resultado["erro"] = str(e)
        resultado["tipo_erro"] = "runtime"
        resultado["saida"] = buf.getvalue()
    except Exception as e:
        resultado["erro"] = f"{e}\n{tb.format_exc()}"
        resultado["tipo_erro"] = "interno"
        resultado["saida"] = buf.getvalue()
    finally:
        sys.stdout = old_stdout

    return resultado


def main():
    args = sys.argv[1:]
    caminho = args[0] if args else "."
    resultado = executar_json(caminho)
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    if not resultado["sucesso"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
