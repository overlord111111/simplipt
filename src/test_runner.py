import os
import sys
import time

from src.erros import ErroLexico, ErroSintaxe, ErroRuntime
from src.lexer.lexer import Lexer
from src.parser.parser import Parser
from src.interpreter.interpreter import Interpreter


def _executar_teste(caminho):
    with open(caminho, "r", encoding="utf-8") as f:
        texto = f.read()
    nome = os.path.basename(caminho)
    lex = Lexer(texto, nome)
    toks = lex.tokenizar()
    par = Parser(toks, nome)
    ast = par.programa()
    interp = Interpreter()
    inicio = time.time()
    interp.interpretar(ast)
    duracao = time.time() - inicio
    return duracao


def rodar(diretorio=".", verbose=False):
    if not os.path.isdir(diretorio):
        print(f"Diretorio nao encontrado: {diretorio}", file=sys.stderr)
        return False

    testes = []
    for raiz, _, arquivos in os.walk(diretorio):
        for arq in sorted(arquivos):
            if arq.endswith(".spt") and not arq.startswith("_"):
                testes.append(os.path.join(raiz, arq))

    if not testes:
        print(f"Nenhum teste encontrado em {diretorio}")
        return True

    total = len(testes)
    passou = 0
    falhou = 0
    erros = 0

    print(f"Rodando {total} teste(s)...\n")

    for caminho in testes:
        nome = os.path.relpath(caminho, diretorio)
        try:
            duracao = _executar_teste(caminho)
            passou += 1
            status = "PASS"
            if verbose:
                print(f"  {status}  {nome} ({duracao:.3f}s)")
        except (ErroLexico, ErroSintaxe, ErroRuntime) as e:
            falhou += 1
            status = "FAIL"
            print(f"  {status}  {nome}")
            print(f"       {e}")
        except Exception as e:
            erros += 1
            status = "ERRO"
            print(f"  {status}  {nome}")
            import traceback
            print(f"       {e}")
            if verbose:
                traceback.print_exc()

    print(f"\nResultado: {passou}/{total} passaram", end="")
    if falhou:
        print(f", {falhou} falharam", end="")
    if erros:
        print(f", {erros} com erro", end="")
    print()

    return falhou == 0 and erros == 0


def main():
    args = sys.argv[1:]
    diretorio = args[0] if args else "."
    verbose = "-v" in args or "--verbose" in args
    if verbose:
        diretorio = [a for a in args if not a.startswith("-")][0] if [a for a in args if not a.startswith("-")] else "."

    sucesso = rodar(diretorio, verbose)
    if not sucesso:
        sys.exit(1)


if __name__ == "__main__":
    main()
