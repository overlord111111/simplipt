import json
import re
import os
import uuid
import threading
import time
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from src.stdlib.template import MODULO as _template_mod
from src.erros import ErroRuntime, ErroLexico, ErroSintaxe
from src.lexer.lexer import Lexer
from src.parser.parser import Parser
from src.interpreter.interpreter import Interpreter


class _Handler(BaseHTTPRequestHandler):
    def _responder(self, codigo, dados, tipo="json"):
        self.send_response(codigo)
        if codigo in (301, 302):
            self.send_header("Location", dados)
        if tipo == "html":
            self.send_header("Content-Type", "text/html; charset=utf-8")
        else:
            self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        if hasattr(self, "_novo_sid"):
            self.send_header("Set-Cookie", f"sessao={self._novo_sid}; Path=/; HttpOnly")
        self.end_headers()
        if codigo in (301, 302):
            return
        if isinstance(dados, str):
            self.wfile.write(dados.encode("utf-8"))
        else:
            self.wfile.write(json.dumps(dados, ensure_ascii=False).encode("utf-8"))

    def _errar(self, codigo, msg):
        self._responder(codigo, {"erro": msg})

    def _ler_corpo(self):
        comprimento = int(self.headers.get("Content-Length", 0))
        if comprimento == 0:
            return None
        raw = self.rfile.read(comprimento)
        ct = self.headers.get("Content-Type", "")
        if ct.startswith("application/json"):
            try:
                return json.loads(raw.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
        if ct.startswith("application/x-www-form-urlencoded"):
            parsed = parse_qs(raw.decode("utf-8"))
            return {k: v[0] if len(v) == 1 else v for k, v in parsed.items()}
        return raw.decode("utf-8", errors="replace")

    def _ler_sessao(self):
        srv = self.server
        cookies = self.headers.get("Cookie", "")
        for parte in cookies.split(";"):
            parte = parte.strip()
            if parte.startswith("sessao="):
                sid = parte[7:]
                if sid in srv._sessoes:
                    return srv._sessoes[sid]
        sid = str(uuid.uuid4())
        srv._sessoes[sid] = {}
        self._novo_sid = sid
        return srv._sessoes[sid]

    def _servir_estatico(self, caminho):
        srv = self.server
        for prefixo, diretorio in srv._estaticos:
            if caminho.startswith(prefixo):
                rel = caminho[len(prefixo):].lstrip("/")
                path = os.path.join(diretorio, rel)
                path = os.path.normpath(path)
                if path.startswith(os.path.normpath(diretorio)) and os.path.isfile(path):
                    ext = os.path.splitext(path)[1].lower()
                    tipos = {
                        ".html": "text/html",
                        ".css": "text/css",
                        ".js": "application/javascript",
                        ".png": "image/png",
                        ".jpg": "image/jpeg",
                        ".jpeg": "image/jpeg",
                        ".gif": "image/gif",
                        ".svg": "image/svg+xml",
                        ".ico": "image/x-icon",
                        ".json": "application/json",
                        ".txt": "text/plain",
                        ".woff2": "font/woff2",
                        ".woff": "font/woff",
                    }
                    ct = tipos.get(ext, "application/octet-stream")
                    with open(path, "rb") as f:
                        dados = f.read()
                    self.send_response(200)
                    self.send_header("Content-Type", ct)
                    self.end_headers()
                    self.wfile.write(dados)
                    return True
        return False

    def _rotear(self, metodo):
        parsed = urlparse(self.path)
        caminho = parsed.path.rstrip("/") or "/"
        query_params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
        corpo = self._ler_corpo()
        srv = self.server

        if metodo == "GET":
            if self._servir_estatico(caminho):
                return

        sessao = self._ler_sessao()

        for r_metodo, r_pattern, r_param_names, fn in srv.rotas:
            if r_metodo != metodo:
                continue
            m = r_pattern.match(caminho)
            if m:
                path_params = {}
                for i, nome in enumerate(r_param_names):
                    path_params[nome] = m.group(i + 1)
                req = {
                    "params": {**query_params, **path_params},
                    "corpo": corpo,
                    "sessao": sessao,
                    "cabecalhos": dict(self.headers),
                    "caminho": caminho,
                    "metodo": metodo,
                }
                if isinstance(corpo, dict):
                    req["formulario"] = corpo
                try:
                    resultado = fn(req)
                    if resultado is None:
                        self._responder(200, {"ok": True})
                    elif isinstance(resultado, tuple) and len(resultado) == 2:
                        self._responder(resultado[0], resultado[1])
                    elif isinstance(resultado, str):
                        self._responder(200, resultado, "html")
                    else:
                        self._responder(200, resultado)
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    self._errar(500, str(e))
                return

        self._errar(404, f"Rota nao encontrada: {metodo} {caminho}")

    def do_GET(self):
        self._rotear("GET")

    def do_POST(self):
        self._rotear("POST")

    def do_PUT(self):
        self._rotear("PUT")

    def do_DELETE(self):
        self._rotear("DELETE")

    def log_message(self, format, *args):
        pass


class _Servidor:
    def __init__(self):
        self.rotas = []
        self._httpd = None
        self._thread = None
        self._estaticos = []

    def rota(self, metodo, path, fn):
        path = path.rstrip("/") or "/"
        param_names = []
        partes = []
        for parte in path.split("/"):
            if parte.startswith(":"):
                param_names.append(parte[1:])
                partes.append(r"([^/]+)")
            else:
                partes.append(re.escape(parte))
        pattern = re.compile("^" + "/".join(partes) + "$")
        self.rotas.append((metodo.upper(), pattern, param_names, fn))

    def estatico(self, prefixo, diretorio):
        prefixo = prefixo.rstrip("/")
        self._estaticos.append((prefixo, os.path.abspath(diretorio)))

    def modelos(self, diretorio):
        _template_mod.diretorio(os.path.abspath(diretorio))

    def html(self, nome_template, contexto=None):
        if contexto is None:
            contexto = {}
        return _template_mod.renderizar(nome_template, contexto)

    def sessao(self, req):
        return req.get("sessao", {})

    def codigo(self, texto):
        import io
        import contextlib
        import traceback
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            try:
                lexer = Lexer(texto, "<servidor>")
                tokens = lexer.tokenizar()
                parser = Parser(tokens, "<servidor>")
                ast = parser.programa()
                interp = Interpreter()
                interp.interpretar(ast)
            except (ErroLexico, ErroSintaxe, ErroRuntime) as e:
                return f"Erro: {e}"
            except Exception as e:
                return f"Erro: {e}\n{traceback.format_exc()}"
        return buf.getvalue().rstrip("\n") or "(sem saida)"

    def _criar_handler(self):
        return type("HandlerCustomizado", (_Handler,), {})

    def lista_rotas(self):
        return [
            {"metodo": m, "path": str(p.pattern)}
            for m, p, _, _ in self.rotas
        ]

    def vigiar(self, script_path, intervalo=1.0):
        estado = {"anterior": None}
        def _observar():
            while True:
                try:
                    mtime = os.path.getmtime(script_path)
                    if estado["anterior"] is not None and mtime != estado["anterior"]:
                        print(f"[hot-reload] Alterado: {script_path}")
                        self._recarregar(script_path)
                    estado["anterior"] = mtime
                except FileNotFoundError:
                    pass
                time.sleep(intervalo)
        t = threading.Thread(target=_observar, daemon=True)
        t.start()
        return f"Vigiando: {script_path}"

    def _recarregar(self, script_path):
        try:
            with open(script_path, "r", encoding="utf-8") as f:
                texto = f.read()
            self.rotas.clear()
            lexer = Lexer(texto, os.path.basename(script_path))
            tokens = lexer.tokenizar()
            parser = Parser(tokens, os.path.basename(script_path))
            ast = parser.programa()
            interp = Interpreter()
            import io, contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                interp.interpretar(ast)
            saida = buf.getvalue()
            if saida.strip():
                print(saida)
        except Exception as e:
            import traceback
            print(f"[hot-reload] Erro ao recarregar: {e}", file=sys.stderr)
            traceback.print_exc()

    def limpar(self):
        self.rotas.clear()
        self._estaticos.clear()
        self._httpd = None
        self._thread = None

    def iniciar(self, porta=8080):
        if self._httpd:
            raise RuntimeError("Servidor ja esta rodando")
        handler = self._criar_handler()
        self._httpd = HTTPServer(("0.0.0.0", int(porta)), handler)
        self._httpd.rotas = self.rotas
        self._httpd._sessoes = {}
        self._httpd._estaticos = self._estaticos
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        return f"Servidor rodando na porta {porta}"

    def parar(self):
        if self._httpd:
            self._httpd.shutdown()
            self._httpd.server_close()
            self._httpd = None
            self._thread = None
            return "Servidor parado"
        return "Servidor nao estava rodando"

    def rodando(self):
        return self._httpd is not None


MODULO = _Servidor()
