import sys
import os
import traceback
import atexit

try:
    import colorama
    colorama.init()
    _TEM_COR = True
except ImportError:
    _TEM_COR = False


def _cor(codigo):
    return f"\033[{codigo}m" if _TEM_COR else ""


VERDE = _cor("32")
AZUL = _cor("94")
CINZA = _cor("90")
VERMELHO = _cor("91")
AMARELO = _cor("93")
RESET = _cor("0")
NEGRITO = _cor("1")


from src.erros import ErroLexico, ErroSintaxe, ErroRuntime
from src.lexer.lexer import Lexer
from src.parser.parser import Parser
from src.interpreter.interpreter import Interpreter


_HISTORICO = os.path.join(os.path.expanduser("~"), ".simplipt_history")
_MAX_HIST = 500


def _carregar_historico():
    if not os.path.exists(_HISTORICO):
        return []
    try:
        with open(_HISTORICO, "r", encoding="utf-8") as f:
            return [l.rstrip("\n") for l in f if l.strip()]
    except:
        return []


def _salvar_historico(linhas):
    try:
        with open(_HISTORICO, "w", encoding="utf-8") as f:
            f.writelines(f"{l}\n" for l in linhas[-_MAX_HIST:])
    except:
        pass


def _inicia_bloco(linha):
    palavra = linha.split()[0].lower() if linha else ""
    return palavra in ("se", "para", "enquanto", "funcao", "paralelo", "tentar", "corresponder", "classe")


def executar_arquivo(caminho, modo_debug=False, breakpoints=None, com_perfil=False):
    nome_arquivo = os.path.basename(caminho)
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            texto = f.read()
    except FileNotFoundError:
        print(f"{VERMELHO}Erro{RESET}: arquivo '{caminho}' não encontrado", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"{VERMELHO}Erro{RESET}: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        lexer = Lexer(texto, nome_arquivo)
        tokens = lexer.tokenizar()
        parser = Parser(tokens, nome_arquivo)
        ast = parser.programa()
        if modo_debug:
            from src.debug import Debugger
            dbg = Debugger(breakpoints=breakpoints, arquivo=caminho)
            interpreter = Interpreter(debugger=dbg)
        else:
            interpreter = Interpreter(perfil=com_perfil)
        interpreter.interpretar(ast)
        if com_perfil and interpreter.perfil:
            print(interpreter.perfil.relatorio())
    except (ErroLexico, ErroSintaxe, ErroRuntime) as e:
        print(f"{VERMELHO}Erro{RESET}: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"{VERMELHO}Erro interno{RESET}: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)


def cmd_formatar(caminho):
    with open(caminho, "r", encoding="utf-8") as f:
        texto = f.read()
    lexer = Lexer(texto, os.path.basename(caminho))
    tokens = lexer.tokenizar()
    parser = Parser(tokens, os.path.basename(caminho))
    ast = parser.programa()
    from src.ferramentas.formatador import formatar
    print(formatar(ast))


def cmd_transpilar(caminho):
    with open(caminho, "r", encoding="utf-8") as f:
        texto = f.read()
    lexer = Lexer(texto, os.path.basename(caminho))
    tokens = lexer.tokenizar()
    parser = Parser(tokens, os.path.basename(caminho))
    ast = parser.programa()
    from src.ferramentas.transpilador import transpilar
    print(transpilar(ast))


def cmd_install(pacote):
    import urllib.request
    import json
    url = f"https://packages.simplipt.dev/api/packages/{pacote}"
    try:
        resp = urllib.request.urlopen(url, timeout=10)
        dados = json.loads(resp.read())
        with open(f"{pacote}.spt", "w", encoding="utf-8") as f:
            f.write(dados["codigo"])
        print(f"{VERDE}Pacote '{pacote}' instalado como {pacote}.spt{RESET}")
    except Exception as e:
        print(f"{VERMELHO}Erro ao instalar pacote '{pacote}': {e}{RESET}", file=sys.stderr)
        sys.exit(1)


def _completar(texto, estado):
    from src.lsp import completar
    try:
        sugestoes = completar(texto, len(texto))
        return [s["texto"] for s in sugestoes[:10]]
    except:
        return []


def repl():
    print(f"{AZUL}{NEGRITO}SimpliPT v5.3 — REPL{RESET}")
    print(f"{CINZA}Digite 'sair' para encerrar. Use blocos multi-linha livremente. Tab para autocomplete.{RESET}")
    interpreter = Interpreter()

    try:
        import readline
        readline.set_completer(_completar)
        readline.parse_and_bind("tab: complete")
    except ImportError:
        pass
    historico = _carregar_historico()
    atexit.register(_salvar_historico, historico)

    while True:
        try:
            linha = input(f"{VERDE}>{RESET} ")
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if linha.strip() == "":
            continue
        if linha.strip().lower() in ("sair", "exit", "quit"):
            break

        historico.append(linha)

        if _inicia_bloco(linha.strip()):
            linhas = [linha]
            nivel = 1
            while nivel > 0:
                try:
                    bloco = input(f"{AZUL}...{RESET} ")
                except (EOFError, KeyboardInterrupt):
                    print()
                    break
                if bloco.strip() == "":
                    continue
                linhas.append(bloco)
                historico.append(bloco)
                if bloco.strip() == "fim":
                    nivel -= 1
                elif _inicia_bloco(bloco.strip()):
                    nivel += 1
            texto = "\n".join(linhas) + "\n"
        else:
            texto = linha + "\n"

        try:
            lexer = Lexer(texto)
            tokens = lexer.tokenizar()
            parser = Parser(tokens, "<repl>")
            ast = parser.programa()
            resultado = interpreter.interpretar(ast)
            if resultado is not None:
                print(f"{AZUL}=>{RESET} {resultado}")
        except (ErroLexico, ErroSintaxe) as e:
            print(f"{AMARELO}Erro{RESET}: {e}", file=sys.stderr)
        except ErroRuntime as e:
            print(f"{VERMELHO}Runtime{RESET}: {e}", file=sys.stderr)
        except Exception as e:
            print(f"{VERMELHO}Erro inesperado{RESET}: {e}", file=sys.stderr)


def main():
    modo_debug = False
    modo_watch = False
    modo_hot = False
    modo_json = False
    modo_perfil = False
    breakpoints = set()
    args = sys.argv[1:]

    i = 0
    while i < len(args):
        a = args[i]
        if a == "--debug":
            modo_debug = True
            i += 1
        elif a in ("--watch", "-w"):
            modo_watch = True
            i += 1
        elif a == "--json":
            modo_json = True
            i += 1
        elif a == "--profile":
            modo_perfil = True
            i += 1
        elif a in ("-b", "--breakpoint"):
            i += 1
            if i < len(args):
                for p in args[i].split(","):
                    try:
                        breakpoints.add(int(p))
                    except ValueError:
                        pass
                i += 1
        elif a == "--strict":
            from src.strict import main as strict_main
            strict_main()
            return
        elif a == "--hot":
            modo_hot = True
            i += 1
        else:
            break

    args = args[i:]

    if not args:
        repl()
        return

    cmd = args[0]

    if modo_json and cmd and os.path.isfile(cmd):
        from src.json_mode import executar_json
        import json
        resultado = executar_json(cmd)
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
        sys.exit(0 if resultado["sucesso"] else 1)

    if cmd in ("-h", "--help", "ajuda"):
        print(f"{AZUL}SimpliPT — Linguagem em português{RESET}")
        print()
        print(f"{NEGRITO}Uso:{RESET}")
        print(f"  simplipt                     REPL interativo")
        print(f"  simplipt <arquivo.spt>       Executar script")
        print(f"  simplipt formatar <arquivo>  Formatador")
        print(f"  simplipt transpilar <arquivo> Transpilar para Python")
        print(f"  simplipt build <arquivo>     Compilar para executavel (.pyz)")
        print(f"  simplipt build --exe <arq>    Compilar para .exe (requer PyInstaller)")
        print(f"  simplipt dashboard [dir]      IDE web (admin dashboard)")
        print(f"  simplipt lsp                  Iniciar servidor LSP")
        print(f"  simplipt install <pacote>    Instalar pacote")
        print(f"  simplipt new <nome>          Criar novo projeto")
        print(f"  simplipt test [dir]           Rodar testes")
        print(f"  simplipt debug [dir]           Debugger web")
        print(f"  simplipt modulo install <pkg>  Instalar modulo Python externo")
        print(f"  simplipt modulo listar         Listar modulos externos")
        print()
        print(f"{NEGRITO}Opções:{RESET}")
        print(f"  --debug                      Modo debug passo a passo")
        print(f"  -b, --breakpoint N1,N2       Breakpoints no modo debug")
        print(f"  -w, --watch                  Assistir arquivo e recarregar")
        print(f"  --strict                     Checagem estatica de tipos")
        print(f"  --hot                        Hot-reload no servidor web")
        print(f"  --json                       Saida em JSON estruturado")
        print(f"  --profile                    Profiling de performance")
        print(f"  --json                       Saida JSON estruturada")
        return

    if cmd in ("formatar", "fmt"):
        if len(args) < 2:
            print(f"{VERMELHO}Uso: simplipt formatar <arquivo.spt>{RESET}", file=sys.stderr)
            sys.exit(1)
        return cmd_formatar(args[1])

    if cmd == "transpilar":
        if len(args) < 2:
            print(f"{VERMELHO}Uso: simplipt transpilar <arquivo.spt>{RESET}", file=sys.stderr)
            sys.exit(1)
        return cmd_transpilar(args[1])

    if cmd == "install":
        if len(args) < 2:
            print(f"{VERMELHO}Uso: simplipt install <pacote>{RESET}", file=sys.stderr)
            sys.exit(1)
        return cmd_install(args[1])

    if cmd == "new":
        if len(args) < 2:
            print(f"{VERMELHO}Uso: simplipt new <nome_do_projeto>{RESET}", file=sys.stderr)
            sys.exit(1)
        from src.scaffold import criar
        criar(args[1])
        return

    if cmd in ("test", "testar"):
        from src.test_runner import rodar
        diretorio = args[1] if len(args) > 1 else "."
        verbose = "-v" in args or "--verbose" in args
        sucesso = rodar(diretorio, verbose)
        sys.exit(0 if sucesso else 1)

    if cmd == "debug":
        from src.debug_web import iniciar as iniciar_debug
        porta = 5000
        diretorio = "."
        resto = args[1:]
        i = 0
        while i < len(resto):
            if resto[i] == "--porta" and i + 1 < len(resto):
                porta = int(resto[i + 1])
                i += 2
            elif not resto[i].startswith("--"):
                diretorio = resto[i]
                i += 1
            else:
                i += 1
        iniciar_debug(porta=porta, diretorio=diretorio)
        return

    if cmd in ("modulo", "modulos", "ext"):
        if len(args) > 1 and args[1] == "listar":
            from src.ext_modules import listar
            mods = listar()
            if mods:
                for m in mods:
                    print(f"  {m['simplipt']} -> {m['python']}")
            else:
                print("Nenhum modulo externo instalado")
            return
        if len(args) > 1 and args[1] in ("instalar", "install"):
            if len(args) < 3:
                print(f"{VERMELHO}Uso: simplipt modulo install <pacote_python> [nome_simplipt]{RESET}", file=sys.stderr)
                sys.exit(1)
            from src.ext_modules import instalar
            nome_simplipt = args[3] if len(args) > 3 else None
            resultado = instalar(args[2], nome_simplipt)
            if "erro" in resultado:
                print(f"{VERMELHO}Erro: {resultado['erro']}{RESET}", file=sys.stderr)
                sys.exit(1)
            print(f"{VERDE}Modulo '{resultado['modulo']}' instalado com sucesso{RESET}")
            return
        print(f"{VERMELHO}Uso: simplipt modulo <install|listar>{RESET}", file=sys.stderr)
        sys.exit(1)

    if cmd == "lsp":
        from src.lsp import iniciar as iniciar_lsp
        return iniciar_lsp()

    if cmd == "build":
        if len(args) < 2:
            print(f"{VERMELHO}Uso: simplipt build [--exe] <arquivo.spt>{RESET}", file=sys.stderr)
            sys.exit(1)
        modo = "exe" if args[1] == "--exe" else "zipapp"
        caminho = args[2] if args[1] == "--exe" else args[1]
        from src.build import compilar
        resultado = compilar(caminho, modo=modo)
        if resultado is None:
            sys.exit(1)
        return

    if cmd in ("dashboard", "admin", "ide"):
        from src.dashboard import iniciar as iniciar_dashboard
        porta = None
        diretorio = None
        resto = args[1:]
        i = 0
        while i < len(resto):
            if resto[i] == "--porta" and i + 1 < len(resto):
                porta = int(resto[i + 1])
                i += 2
            elif not resto[i].startswith("--"):
                diretorio = resto[i]
                i += 1
            else:
                i += 1
        return iniciar_dashboard(porta=porta, diretorio=diretorio)

    caminho = cmd
    if not os.path.exists(caminho):
        print(f"{VERMELHO}Erro{RESET}: arquivo '{caminho}' não encontrado", file=sys.stderr)
        sys.exit(1)
    if not caminho.endswith(".spt"):
        print(f"{AMARELO}Aviso{RESET}: arquivo '{caminho}' não tem extensão .spt", file=sys.stderr)

    if modo_hot:
        from src.hot_reload import executar_com_watch
        from src.stdlib.servidor import MODULO as _srv_mod

        def _recarregar_hot(arq):
            _srv_mod._recarregar(os.path.abspath(arq))

        executar_arquivo(caminho, modo_debug=modo_debug, breakpoints=breakpoints, com_perfil=modo_perfil)
        executar_com_watch(caminho, _recarregar_hot)
        return

    if modo_watch:
        from src.hot_reload import executar_com_watch

        def _exec(arq):
            executar_arquivo(os.path.abspath(arq), modo_debug=modo_debug, breakpoints=breakpoints, com_perfil=modo_perfil)

        executar_arquivo(caminho, modo_debug=modo_debug, breakpoints=breakpoints, com_perfil=modo_perfil)
        executar_com_watch(caminho, _exec)
        return

    executar_arquivo(caminho, modo_debug=modo_debug, breakpoints=breakpoints, com_perfil=modo_perfil)


if __name__ == "__main__":
    main()
