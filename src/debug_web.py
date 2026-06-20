import sys
import os
import threading
import json
import io
from http.server import HTTPServer, BaseHTTPRequestHandler
from src.interpreter.interpreter import Interpreter
from src.lexer.lexer import Lexer
from src.parser.parser import Parser
from src.parser.ast import *
from src.interpreter.environment import Environment


class _WebDebugger:
    def __init__(self):
        self._event = threading.Event()
        self._lock = threading.Lock()
        self.pausado = False
        self.modo = "executar"
        self.node_atual = None
        self.env_atual = None
        self.interp_atual = None
        self.linha_atual = 0
        self._linhas = []
        self.variaveis = []
        self.pilha = []
        self.erro = None
        self.finalizado = False
        self.resultado = None

    def _notify(self, node, env, interp):
        if self.finalizado:
            return
        self.node_atual = node
        self.env_atual = env
        self.interp_atual = interp
        self.linha_atual = getattr(node, 'linha', None) or 0

        with self._lock:
            self.variaveis = self._extrair_vars(env)
            self.pilha = self._extrair_pilha(env)

        if self.modo == "passo" or self.modo == "break":
            self._pausar()

    def _extrair_vars(self, env):
        vars_ = {}
        while env:
            for k, v in env.values.items():
                if not k.startswith("_"):
                    vars_[k] = v
            env = env.parent
        return [[k, repr(v)] for k, v in sorted(vars_.items())]

    def _extrair_pilha(self, env):
        pilha = []
        while env:
            nomes = [k for k in env.values if not k.startswith("_")]
            if nomes:
                pilha.append(" | ".join(nomes[:5]))
            env = env.parent
        return pilha

    def _pausar(self):
        self.pausado = True
        self._event.clear()
        self._event.wait()

    def continuar(self):
        with self._lock:
            self.modo = "executar"
            self.pausado = False
            self._event.set()

    def passo(self):
        with self._lock:
            self.modo = "passo"
            self.pausado = False
            self._event.set()

    def info(self):
        with self._lock:
            return {
                "linha": self.linha_atual,
                "linha_texto": self._linhas[self.linha_atual - 1].rstrip() if self._linhas and 0 < self.linha_atual <= len(self._linhas) else "",
                "variaveis": self.variaveis,
                "pilha": self.pilha,
                "pausado": self.pausado,
                "finalizado": self.finalizado,
                "erro": str(self.erro) if self.erro else None,
                "resultado": str(self.resultado) if self.resultado is not None else None,
            }

    def avaliar(self, expr):
        try:
            lex = Lexer(expr + "\n")
            toks = lex.tokenizar()
            par = Parser(toks)
            ast = par.programa()
            if ast.nodes and self.interp_atual:
                env = Environment(self.env_atual)
                val = self.interp_atual._avaliar(ast.nodes[-1], env)
                return repr(val)
            return "(nada)"
        except Exception as e:
            return str(e)


_SESSOES = {}
_NEXT_ID = 0


class _Handler(BaseHTTPRequestHandler):
    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def _body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length).decode("utf-8")) if length else {}

    def do_GET(self):
        from urllib.parse import urlparse, parse_qs
        p = urlparse(self.path)
        path = p.path.rstrip("/") or "/"
        qs = parse_qs(p.query)

        if path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(_HTML.encode("utf-8"))
            return

        if path == "/api/scripts":
            diretorio = self.server._diretorio
            scripts = []
            if os.path.isdir(diretorio):
                for f in sorted(os.listdir(diretorio)):
                    if f.endswith(".spt"):
                        fp = os.path.join(diretorio, f)
                        scripts.append({"nome": f, "caminho": fp, "tamanho": os.path.getsize(fp)})
            self._json(scripts)
            return

        if path == "/api/script":
            arquivo = qs.get("arquivo", [""])[0]
            if arquivo and os.path.exists(arquivo):
                with open(arquivo, "r", encoding="utf-8") as f:
                    self._json({"conteudo": f.read(), "caminho": arquivo})
            else:
                self._json({"erro": "nao encontrado"}, 404)
            return

        if path == "/api/sessao":
            sid = qs.get("sid", [""])[0]
            s = _SESSOES.get(sid)
            if s:
                self._json(s.info())
            else:
                self._json({"finalizado": True, "erro": "sessao inexistente"})
            return

        self._json({"erro": "nao encontrada"}, 404)

    def do_POST(self):
        from urllib.parse import urlparse
        path = urlparse(self.path).path.rstrip("/") or "/"
        body = self._body()

        if path == "/api/iniciar":
            global _NEXT_ID
            arquivo = body.get("arquivo", "")
            if not os.path.exists(arquivo):
                self._json({"erro": "arquivo nao encontrado"}, 404)
                return
            dbg = _WebDebugger()
            with open(arquivo, "r", encoding="utf-8") as f:
                dbg._linhas = f.readlines()
                texto = "".join(dbg._linhas)
            nome = os.path.basename(arquivo)
            lex = Lexer(texto, nome)
            toks = lex.tokenizar()
            par = Parser(toks, nome)
            ast = par.programa()
            interp = Interpreter()
            interp.debugger = dbg

            def roda():
                try:
                    dbg.resultado = interp.interpretar(ast)
                except Exception as e:
                    dbg.erro = e
                finally:
                    dbg.finalizado = True
                    dbg.pausado = False
                    dbg._event.set()

            _NEXT_ID += 1
            sid = f"s{_NEXT_ID}"
            _SESSOES[sid] = dbg
            t = threading.Thread(target=roda, daemon=True)
            t.start()
            self._json({"sid": sid})
            return

        if path == "/api/passo":
            sid = body.get("sid", "")
            s = _SESSOES.get(sid)
            if s:
                s.passo()
                self._json({"ok": True})
            else:
                self._json({"erro": "sessao nao encontrada"}, 404)
            return

        if path == "/api/continuar":
            sid = body.get("sid", "")
            s = _SESSOES.get(sid)
            if s:
                s.continuar()
                self._json({"ok": True})
            else:
                self._json({"erro": "sessao nao encontrada"}, 404)
            return

        if path == "/api/avaliar":
            sid = body.get("sid", "")
            s = _SESSOES.get(sid)
            expr = body.get("expressao", "")
            if s:
                self._json({"resultado": s.avaliar(expr)})
            else:
                self._json({"erro": "sessao nao encontrada"}, 404)
            return

        if path == "/api/parar":
            sid = body.get("sid", "")
            s = _SESSOES.pop(sid, None)
            if s:
                s.finalizado = True
                s._event.set()
            self._json({"ok": True})
            return

        self._json({"erro": "nao encontrada"}, 404)

    def log_message(self, *a):
        pass


def iniciar(host="127.0.0.1", porta=5000, diretorio=None):
    if diretorio is None:
        diretorio = os.getcwd()
    diretorio = os.path.abspath(diretorio)
    server = HTTPServer((host, porta), _Handler)
    server._diretorio = diretorio
    print(f"Debugger Web: http://{host}:{porta}")
    print(f"Diretorio: {diretorio}")
    server.serve_forever()


_HTML = """<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>SimpliPT Debugger</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',system-ui,sans-serif;background:#0d1117;color:#c9d1d9;display:flex;height:100vh;overflow:hidden}
.sidebar{width:220px;background:#161b22;border-right:1px solid #30363d;padding:16px;overflow-y:auto;flex-shrink:0}
.sidebar h2{font-size:13px;color:#58a6ff;margin-bottom:12px;text-transform:uppercase;letter-spacing:.5px}
.script-item{padding:7px 10px;border-radius:6px;font-size:13px;margin-bottom:2px;cursor:pointer}
.script-item:hover{background:#21262d}
.script-item.ativo{background:#1f6ebf33;color:#58a6ff}
.main{flex:1;display:flex;flex-direction:column}
.toolbar{padding:10px 16px;background:#161b22;border-bottom:1px solid #30363d;display:flex;gap:6px;align-items:center}
.toolbar button{padding:6px 14px;border:none;border-radius:6px;font-size:12px;cursor:pointer;font-weight:600}
.btn-go{background:#238636;color:#fff}
.btn-step{background:#1f6ebf;color:#fff}
.btn-stop{background:#da3633;color:#fff}
.btn-eval{background:#21262d;color:#c9d1d9;border:1px solid #30363d}
.toolbar input{flex:1;padding:6px 10px;background:#0d1117;border:1px solid #30363d;border-radius:6px;color:#c9d1d9;font-size:12px;margin-left:8px}
.content{flex:1;display:flex;overflow:hidden}
.editor{flex:1;padding:16px;overflow:auto;font:13px/1.7 'Cascadia Code','Fira Code','Consolas',monospace}
.editor .linha{display:flex;padding:0 4px;border-radius:4px}
.editor .linha.ativa{background:#1f6ebf22;outline:1px solid #1f6ebf44}
.editor .num{color:#484f58;min-width:36px;text-align:right;margin-right:16px;user-select:none}
.info{width:300px;background:#161b22;border-left:1px solid #30363d;padding:16px;overflow-y:auto;flex-shrink:0}
.info h3{font-size:11px;color:#8b949e;text-transform:uppercase;letter-spacing:.5px;margin:16px 0 8px}
.info h3:first-child{margin-top:0}
.info .vazio{color:#484f58;font-size:12px;font-style:italic}
.vtable{width:100%;font-size:12px;border-collapse:collapse}
.vtable td{padding:3px 6px;border-bottom:1px solid #21262d}
.vtable td:nth-child(1){color:#79c0ff}
.vtable td:nth-child(2){color:#a5d6ff;font-family:monospace}
.eval-out{background:#0d1117;border:1px solid #30363d;border-radius:6px;padding:8px;font:12px monospace;margin-top:4px;min-height:24px}
</style>
</head>
<body>
<div class="sidebar">
<h2>Scripts</h2>
<div id="scripts">carregando...</div>
</div>
<div class="main">
<div class="toolbar">
<button class="btn-go" onclick="iniciar()">▶ Iniciar</button>
<button class="btn-step" onclick="passo()">⤷ Passo</button>
<button class="btn-go" onclick="continuar()">▶ Continuar</button>
<button class="btn-stop" onclick="parar()">■ Parar</button>
<input id="evalExpr" placeholder="expressao..." onkeydown="if(event.key==='Enter')avaliar()">
<button class="btn-eval" onclick="avaliar()">Avaliar</button>
</div>
<div class="content">
<div class="editor" id="editor">selecione um script</div>
<div class="info">
<h3>Variaveis</h3>
<div id="vars" class="vazio">(nenhuma)</div>
<h3>Pilha</h3>
<div id="stack" class="vazio">(vazia)</div>
<h3>Expressao</h3>
<div id="evalResult" class="eval-out"></div>
</div>
</div>
</div>
<script>
let SID=null, ARQ=null, LINHAS=[];
function api(m,p,d){return fetch(p,{method:m,headers:{'Content-Type':'application/json'},body:d?JSON.stringify(d):null}).then(r=>r.json())}
async function carregar(){let r=await api('GET','/api/scripts');let e=document.getElementById('scripts');e.innerHTML=r.map(s=>'<div class="script-item" onclick="sel(\\''+s.caminho+'\\')">'+s.nome+'</div>').join('')}
async function sel(c){ARQ=c;document.querySelectorAll('.script-item').forEach(s=>s.classList.remove('ativo'));event.target.classList.add('ativo');let r=await api('GET','/api/script?arquivo='+encodeURIComponent(c));LINHAS=r.conteudo.split('\\n');document.getElementById('editor').innerHTML=LINHAS.map((l,i)=>'<div class="linha" id="l'+(i+1)+'"><span class="num">'+(i+1)+'</span>'+l.replace(/&/g,'&amp;').replace(/</g,'&lt;')+'</div>').join('');document.getElementById('vars').innerHTML='<span class=\\"vazio\\">(nenhuma)</span>';document.getElementById('stack').innerHTML='<span class=\\"vazio\\">(vazia)</span>'}
async function iniciar(){if(!ARQ)return;let r=await api('POST','/api/iniciar',{arquivo:ARQ});SID=r.sid;pool()}
async function passo(){SID&&(await api('POST','/api/passo',{sid:SID}),atualiza())}
async function continuar(){SID&&(await api('POST','/api/continuar',{sid:SID}),setTimeout(atualiza,150))}
async function parar(){SID&&(await api('POST','/api/parar',{sid:SID}),SID=null,document.querySelectorAll('.linha').forEach(l=>l.classList.remove('ativa')),document.getElementById('vars').innerHTML='<span class=\\"vazio\\">(nenhuma)</span>')}
async function avaliar(){if(!SID)return;let v=document.getElementById('evalExpr').value;if(!v)return;let r=await api('POST','/api/avaliar',{sid:SID,expressao:v});document.getElementById('evalResult').textContent=r.resultado||'(nada)'}
async function atualiza(){if(!SID)return;let r=await api('GET','/api/sessao?sid='+SID);if(r.finalizado){SID=null;return}
document.querySelectorAll('.linha').forEach(l=>l.classList.remove('ativa'));if(r.linha){let el=document.getElementById('l'+r.linha);if(el)el.classList.add('ativa')}
document.getElementById('vars').innerHTML=r.variaveis&&r.variaveis.length?'<table class="vtable">'+r.variaveis.map(v=>'<tr><td>'+v[0]+'</td><td>'+v[1]+'</td></tr>').join('')+'</table>':'<span class=\\"vazio\\">(nenhuma)</span>'
document.getElementById('stack').innerHTML=r.pilha&&r.pilha.length?r.pilha.map(p=>'<div style="font-size:12px;padding:2px 0">'+p+'</div>').join(''):'<span class=\\"vazio\\">(vazia)</span>'}
async function pool(){if(!SID)return;let r=await api('GET','/api/sessao?sid='+SID);if(r.finalizado){SID=null;return}
if(r.pausado)atualiza();else setTimeout(pool,200)}
carregar();
</script>
</body>
</html>"""
