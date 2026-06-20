import sys
import traceback
from src.parser.ast import *

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


class Debugger:
    def __init__(self, breakpoints=None, arquivo=None):
        self.breakpoints = breakpoints or set()
        self.arquivo = arquivo
        self.modo = "executar"
        self.pausado = False
        self.node_atual = None
        self.env_atual = None
        self.interp_atual = None
        self.linha_atual = 0
        self._linhas_arquivo = None
        if arquivo:
            try:
                with open(arquivo, "r", encoding="utf-8") as f:
                    self._linhas_arquivo = f.readlines()
            except:
                pass

    def _notify(self, node, env, interp):
        self.node_atual = node
        self.env_atual = env
        self.interp_atual = interp
        linha = getattr(node, 'linha', None) or 0
        self.linha_atual = linha

        if self.modo == "passo":
            self._pausar()
        elif linha in self.breakpoints:
            print(f"\n{AZUL}Breakpoint{RESET} na linha {linha}")
            self._pausar()

    def _pausar(self):
        self.pausado = True
        self._mostrar_contexto()
        while self.pausado:
            try:
                cmd = input(f"{AMARELO}(dbg){RESET} ")
            except (EOFError, KeyboardInterrupt):
                print()
                self.modo = "executar"
                self.pausado = False
                break

            cmd = cmd.strip().lower()
            if cmd in ("",):
                self.modo = "passo"
                self.pausado = False
                break
            elif cmd in ("c", "continuar"):
                self.modo = "executar"
                self.pausado = False
                break
            elif cmd in ("s", "passo"):
                self.modo = "passo"
                self.pausado = False
                break
            elif cmd in ("v", "var", "variaveis"):
                self._mostrar_variaveis()
            elif cmd.startswith("p "):
                self._executar_expr(cmd[2:].strip())
            elif cmd in ("l", "lista"):
                self._mostrar_codigo()
            elif cmd in ("a", "ajuda", "h", "help"):
                self._mostrar_ajuda()
            elif cmd in ("q", "sair"):
                print(f"{AMARELO}Encerrando depuração{RESET}")
                sys.exit(0)
            else:
                print(f"{CINZA}Comando desconhecido. Digite 'a' para ajuda.{RESET}")

    def _mostrar_contexto(self):
        print(f"{CINZA}--- Linha {self.linha_atual} ---{RESET}")
        if self._linhas_arquivo and 0 < self.linha_atual <= len(self._linhas_arquivo):
            linha_texto = self._linhas_arquivo[self.linha_atual - 1].rstrip()
            print(f"{VERDE}{self.linha_atual:>4}{RESET} {linha_texto}")
        node = self.node_atual
        nome = type(node).__name__ if node else "?"
        print(f"{CINZA}Nó: {nome}{RESET}")

    def _mostrar_variaveis(self):
        env = self.env_atual
        vars_visiveis = {}
        while env:
            for k, v in env.values.items():
                if not k.startswith("_"):
                    vars_visiveis[k] = v
            env = env.parent
        if not vars_visiveis:
            print(f"{CINZA}(sem variáveis no escopo){RESET}")
            return
        for nome, valor in sorted(vars_visiveis.items()):
            tipo = type(valor).__name__
            val_str = repr(valor)
            if len(val_str) > 60:
                val_str = val_str[:57] + "..."
            print(f"  {VERDE}{nome}{RESET} ({CINZA}{tipo}{RESET}) = {val_str}")

    def _mostrar_codigo(self):
        if not self._linhas_arquivo:
            print(f"{CINZA}(sem arquivo fonte){RESET}")
            return
        inicio = max(0, self.linha_atual - 5)
        fim = min(len(self._linhas_arquivo), self.linha_atual + 4)
        for i in range(inicio, fim):
            num = i + 1
            prefixo = f"{VERDE}{num:>4}{RESET}" if num != self.linha_atual else f"{AZUL}{NEGRITO}{num:>4}>{RESET}"
            print(f"{prefixo} {self._linhas_arquivo[i].rstrip()}")

    def _executar_expr(self, expr):
        if not self.interp_atual:
            print(f"{VERMELHO}(sem contexto){RESET}")
            return
        try:
            from src.lexer.lexer import Lexer
            from src.parser.parser import Parser
            lex = Lexer(expr + "\n")
            toks = lex.tokenizar()
            par = Parser(toks)
            ast = par.programa()
            if ast.nodes:
                # Only evaluate the last expression
                ultimo = ast.nodes[-1]
                from src.interpreter.environment import Environment
                # Create a read-only view of current scope
                env_isolado = Environment(self.env_atual)
                valor = self.interp_atual._avaliar(ultimo, env_isolado)
                print(f"  {AZUL}=>{RESET} {repr(valor)}")
        except Exception as e:
            print(f"{VERMELHO}Erro: {e}{RESET}")

    def _mostrar_ajuda(self):
        print(f"""
{NEGRITO}Comandos do debugger:{RESET}
  {VERDE}<enter>{RESET}         Avançar para próxima linha
  {VERDE}s{RESET}, {VERDE}passo{RESET}       Avançar para próxima linha
  {VERDE}c{RESET}, {VERDE}continuar{RESET}   Continuar execução até próximo breakpoint
  {VERDE}v{RESET}, {VERDE}var{RESET}         Mostrar variáveis no escopo atual
  {VERDE}p <expr>{RESET}     Avaliar expressão SimpliPT
  {VERDE}l{RESET}, {VERDE}lista{RESET}       Mostrar código ao redor da linha atual
  {VERDE}q{RESET}, {VERDE}sair{RESET}       Encerrar execução
  {VERDE}a{RESET}, {VERDE}ajuda{RESET}       Mostrar esta ajuda
""" .strip())
