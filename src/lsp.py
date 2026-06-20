import sys
import json
import io
import traceback

from src.lexer.lexer import Lexer
from src.parser.parser import Parser
from src.erros import ErroLexico, ErroSintaxe
from src.parser.ast import (
    Programa, Atribuicao, Funcao, Chamada, Se, ParaEm, ParaAte,
    Enquanto, Tentar, Falar, Retornar, Usar, Variavel, Classe, Novo,
)


TOKENS_LSP = {
    "se": "keyword",
    "senao": "keyword",
    "fim": "keyword",
    "para": "keyword",
    "em": "keyword",
    "enquanto": "keyword",
    "funcao": "keyword",
    "retornar": "keyword",
    "falar": "keyword",
    "ler": "keyword",
    "tentar": "keyword",
    "capturar": "keyword",
    "usar": "keyword",
    "classe": "keyword",
    "novo": "keyword",
    "este": "keyword",
    "super": "keyword",
    "nada": "constant",
    "verdadeiro": "constant",
    "falso": "constant",
    "eh": "keyword",
    "e": "keyword",
    "ou": "keyword",
    "nao": "keyword",
}

MODULOS_STDLIB = [
    "servidor", "arquivos", "sistema", "template", "json",
    "matematica", "data", "texto", "regex", "banco", "cache",
    "hashes", "http", "processo", "fila", "executar", "config",
    "navegador",
]


def _extrair_definicoes(ast, nome_arquivo):
    """Extrai funcoes e variaveis definidas no AST para symbols/documentacao"""
    definicoes = []
    for node in (ast.nodes if isinstance(ast, Programa) else [ast]):
        if isinstance(node, Funcao) and node.nome:
            definicoes.append({
                "nome": node.nome,
                "tipo": "funcao",
                "params": node.params,
            })
        elif isinstance(node, Atribuicao):
            definicoes.append({
                "nome": node.nome,
                "tipo": "variavel",
                "tipo_anotado": node.tipo,
            })
        elif isinstance(node, Classe):
            definicoes.append({
                "nome": node.nome,
                "tipo": "classe",
            })
    return definicoes


class _LSPConnection:
    def __init__(self, stdin, stdout):
        self._stdin = stdin
        self._stdout = stdout
        self._buf = ""
        self._abertos = {}  # uri -> texto
        self._diagnosticos = {}

    def _ler_mensagem(self):
        while True:
            if "\r\n\r\n" in self._buf:
                cabecalho, self._buf = self._buf.split("\r\n\r\n", 1)
                comprimento = 0
                for linha in cabecalho.split("\r\n"):
                    if linha.lower().startswith("content-length:"):
                        comprimento = int(linha.split(":", 1)[1].strip())
                if comprimento > 0 and len(self._buf) >= comprimento:
                    corpo = self._buf[:comprimento]
                    self._buf = self._buf[comprimento:]
                    return json.loads(corpo)
            chunk = self._stdin.read(4096)
            if not chunk:
                return None
            self._buf += chunk

    def _enviar(self, msg):
        corpo = json.dumps(msg, ensure_ascii=False)
        cab = f"Content-Length: {len(corp.encode('utf-8'))}\r\n\r\n"
        self._stdout.write(cab)
        self._stdout.write(corp)
        self._stdout.flush()

    def _diagnosticar(self, uri, texto):
        try:
            lex = Lexer(texto, uri)
            toks = lex.tokenizar()
            par = Parser(toks, uri)
            par.programa()
            self._enviar_diagnosticos(uri, [])
        except (ErroLexico, ErroSintaxe) as e:
            msg = str(e)
            lin, col = 0, 0
            for parte in msg.split("|"):
                p = parte.strip()
                if p.startswith("linha"):
                    try:
                        lin = int(p.split()[1].rstrip(",")) - 1
                    except (IndexError, ValueError):
                        pass
                elif p.startswith("coluna"):
                    try:
                        col = int(p.split()[1].rstrip(",")) - 1
                    except (IndexError, ValueError):
                        pass
            diag = [{
                "range": {
                    "start": {"line": max(lin, 0), "character": max(col, 0)},
                    "end": {"line": max(lin, 0), "character": max(col + 10, 1)},
                },
                "severity": 1,
                "message": e.args[0] if e.args else str(e),
            }]
            self._enviar_diagnosticos(uri, diag)
        except Exception:
            pass

    def _enviar_diagnosticos(self, uri, diags):
        self._enviar({
            "jsonrpc": "2.0",
            "method": "textDocument/publishDiagnostics",
            "params": {"uri": uri, "diagnostics": diags},
        })

    def executar(self):
        self._enviar({
            "jsonrpc": "2.0",
            "method": "window/showMessage",
            "params": {
                "type": 3,
                "message": "SimpliPT LSP iniciado",
            },
        })

        while True:
            msg = self._ler_mensagem()
            if msg is None:
                break
            metodo = msg.get("method", "")
            msg_id = msg.get("id")
            params = msg.get("params", {})

            if metodo == "initialize":
                self._enviar({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "capabilities": {
                            "textDocumentSync": {
                                "openClose": True,
                                "change": 1,
                            },
                            "completionProvider": {
                                "triggerCharacters": [".", ":"],
                            },
                            "hoverProvider": True,
                            "documentSymbolProvider": True,
                            "definitionProvider": True,
                        },
                        "serverInfo": {
                            "name": "SimpliPT LSP",
                            "version": "5.1",
                        },
                    },
                })

            elif metodo == "initialized":
                pass

            elif metodo == "shutdown":
                self._enviar({"jsonrpc": "2.0", "id": msg_id, "result": None})
                break

            elif metodo == "exit":
                break

            elif metodo == "textDocument/didOpen":
                uri = params["textDocument"]["uri"]
                texto = params["textDocument"]["text"]
                self._abertos[uri] = texto
                self._diagnosticar(uri, texto)

            elif metodo == "textDocument/didChange":
                uri = params["textDocument"]["uri"]
                for change in params.get("contentChanges", []):
                    self._abertos[uri] = change["text"]
                self._diagnosticar(uri, self._abertos.get(uri, ""))

            elif metodo == "textDocument/didClose":
                uri = params["textDocument"]["uri"]
                self._abertos.pop(uri, None)

            elif metodo == "textDocument/completion":
                uri = params["textDocument"]["uri"]
                com = []
                for palavra, tipo in TOKENS_LSP.items():
                    com.append({
                        "label": palavra,
                        "kind": 14 if tipo == "keyword" else 13,
                        "detail": tipo,
                    })
                for mod in MODULOS_STDLIB:
                    com.append({
                        "label": mod,
                        "kind": 9,
                        "detail": "modulo",
                        "insertText": mod,
                    })
                self._enviar({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "isIncomplete": False,
                        "items": com,
                    },
                })

            elif metodo == "textDocument/hover":
                uri = params["textDocument"]["uri"]
                texto = self._abertos.get(uri, "")
                try:
                    lex = Lexer(texto, uri)
                    toks = lex.tokenizar()
                    par = Parser(toks, uri)
                    ast = par.programa()
                    definicoes = _extrair_definicoes(ast, uri)
                    if definicoes:
                        items = []
                        for d in definicoes:
                            info = f"**{d['nome']}** ({d['tipo']})"
                            if d.get("params"):
                                info += f"\\nParams: {', '.join(d['params'])}"
                            if d.get("tipo_anotado"):
                                info += f"\\nTipo: {d['tipo_anotado']}"
                            items.append(f"- {info}")
                        conteudo = "\\n".join(items)
                    else:
                        conteudo = "SimpliPT - Linguagem em portugues\\n\\nKeywords: se, senao, fim, para, em, enquanto, funcao, retornar, falar, ler, tentar, capturar, usar, classe, novo, este, super"
                    self._enviar({
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {
                            "contents": {"kind": "markdown", "value": conteudo},
                        },
                    })
                except Exception:
                    self._enviar({
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {"contents": "SimpliPT LSP"},
                    })

            elif metodo == "textDocument/documentSymbol":
                uri = params["textDocument"]["uri"]
                texto = self._abertos.get(uri, "")
                simbolos = []
                try:
                    lex = Lexer(texto, uri)
                    toks = lex.tokenizar()
                    par = Parser(toks, uri)
                    ast = par.programa()
                    definicoes = _extrair_definicoes(ast, uri)
                    for i, d in enumerate(definicoes):
                        kind = 2 if d["tipo"] == "funcao" else (5 if d["tipo"] == "classe" else 13)
                        simbolos.append({
                            "name": d["nome"],
                            "kind": kind,
                            "range": {
                                "start": {"line": i, "character": 0},
                                "end": {"line": i + 1, "character": 0},
                            },
                            "selectionRange": {
                                "start": {"line": i, "character": 0},
                                "end": {"line": i + 1, "character": 0},
                            },
                        })
                except Exception:
                    pass
                self._enviar({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": simbolos,
                })

            elif msg_id is not None:
                self._enviar({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": None,
                })


def completar(prefixo, pos):
    sugestoes = []
    prefixo_lower = prefixo.lower()
    for palavra, tipo in TOKENS_LSP.items():
        if palavra.startswith(prefixo_lower):
            sugestoes.append({"texto": palavra, "tipo": tipo})
    for mod in MODULOS_STDLIB:
        if mod.startswith(prefixo_lower) or mod.startswith(prefixo):
            sugestoes.append({"texto": mod, "tipo": "modulo"})
    sugestoes.sort(key=lambda x: x["texto"])
    return sugestoes[:20]


def iniciar():
    conn = _LSPConnection(
        sys.stdin if hasattr(sys.stdin, "buffer") else sys.stdin,
        sys.stdout if hasattr(sys.stdout, "buffer") else sys.stdout,
    )
    conn.executar()


if __name__ == "__main__":
    iniciar()
