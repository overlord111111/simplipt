import os
import re


class _Ctx:
    def __init__(self, dados):
        self._d = dados

    def __getattr__(self, k):
        v = self._d[k]
        return self._env(v)

    def __getitem__(self, k):
        v = self._d[k]
        return self._env(v)

    def __contains__(self, k):
        return k in self._d

    def __bool__(self):
        return bool(self._d)

    @staticmethod
    def _env(v):
        if isinstance(v, dict):
            return _Ctx(v)
        if isinstance(v, list):
            return [_Ctx._env(i) for i in v]
        return v


class _SafeDict(dict):
    def __getitem__(self, k):
        try:
            return dict.__getitem__(self, k)
        except KeyError:
            return ""


class _TemplateEngine:
    def __init__(self):
        self._diretorio = "modelos"
        self._cache = {}

    def diretorio(self, path=None):
        if path is not None:
            self._diretorio = path
        return self._diretorio

    def renderizar(self, nome, contexto=None):
        if contexto is None:
            contexto = {}
        cache_key = nome
        if cache_key not in self._cache:
            fn, _ = self._carregar(nome, cache_key)
        else:
            fn, _ = self._cache[cache_key]
        return fn(contexto, self._renderizar_incluido, _Ctx._env, self)

    def recarregar(self):
        self._cache.clear()

    # ─── HTMX Helpers ─────────────────────────────────────────
    def botao(self, texto, url, metodo="get", alvo=None, classe="", extras=""):
        atr = f'hx-{metodo}="{url}"'
        if alvo:
            atr += f' hx-target="{alvo}"'
        cls = f' class="{classe}"' if classe else ""
        return f'<button {atr}{cls} {extras}>{texto}</button>'

    def link(self, texto, url, metodo="get", alvo=None, classe="", extras=""):
        atr = f'hx-{metodo}="{url}"'
        if alvo:
            atr += f' hx-target="{alvo}"'
        cls = f' class="{classe}"' if classe else ""
        return f'<a href="#" {atr}{cls} {extras}>{texto}</a>'

    def input_texto(self, nome, url, gatilho="change", alvo=None, classes=""):
        atr = f'type="text" name="{nome}" hx-post="{url}" hx-trigger="{gatilho}"'
        if alvo:
            atr += f' hx-target="{alvo}"'
        cls = f' class="{classes}"' if classes else ""
        return f'<input {atr}{cls}>'

    def formulario(self, url, metodo="post", alvo=None, enctype=None, classes=""):
        atr = f'hx-{metodo}="{url}"'
        if alvo:
            atr += f' hx-target="{alvo}"'
        ct = f' enctype="{enctype}"' if enctype else ""
        cls = f' class="{classes}"' if classes else ""
        return f'<form {atr}{ct}{cls}>'

    def mostrar(self, url, intervalo_segundos=5, metodo="get", alvo=None, classes=""):
        atr = f'hx-{metodo}="{url}" hx-trigger="every {intervalo_segundos}s"'
        if alvo:
            atr += f' hx-target="{alvo}"'
        cls = f' class="{classes}"' if classes else ""
        return f'<div {atr}{cls}>'

    def enviar(self, url, metodo="post", alvo=None, gatilho="submit"):
        atr = f'hx-{metodo}="{url}" hx-trigger="{gatilho}"'
        if alvo:
            atr += f' hx-target="{alvo}"'
        return f'<button {atr}>Enviar</button>'

    def deletar(self, url, alvo=None, confirmacao=None, classes=""):
        atr = f'hx-delete="{url}"'
        if alvo:
            atr += f' hx-target="{alvo}"'
        if confirmacao:
            atr += f' hx-confirm="{confirmacao}"'
        cls = f' class="{classes}"' if classes else ""
        return f'<button {atr}{cls}>Deletar</button>'

    def carregar(self, url, alvo, modo="innerHTML", classe=""):
        """Carrega HTML de uma URL em um elemento ao clicar"""
        cls = f' class="{classe}"' if classe else ""
        return f'<div hx-get="{url}" hx-target="{alvo}" hx-trigger="click" hx-swap="{modo}"{cls}>Carregar</div>'

    def _carregar(self, nome, cache_key):
        caminho = os.path.join(self._diretorio, nome)
        with open(caminho, "r", encoding="utf-8") as f:
            texto = f.read()
        mtime = os.path.getmtime(caminho)
        fn = self._compilar(texto)
        self._cache[cache_key] = (fn, mtime)
        return fn, mtime

    def _renderizar_incluido(self, nome, contexto):
        return self.renderizar(nome, contexto)

    def _compilar(self, texto):
        nodes = self._tokenizar(texto)
        lines = []
        lines.append("def _template(_ctx, _incluir, _w, _eng):")
        lines.append("    _b = []")
        lines.append("    _v = _SafeDict({_k: _w(_val) for _k, _val in _ctx.items()})")
        lines.append("    _mod = __import__('builtins')")
        lines.append("    _eb = {_k: _v for _k, _v in vars(_mod).items() if _k not in ('eval','exec','compile','open','__import__','input')}")
        lines.append("    _v['htmx'] = _eng")
        lines.append("    def _e(_x):")
        lines.append("        return eval(_x, {'__builtins__': _eb}, _v)")

        indent = 1
        for tipo, conteudo in nodes:
            pad = "    " * indent
            if tipo == "texto":
                if conteudo:
                    lines.append(f"{pad}_b.append({repr(conteudo)})")
            elif tipo == "expr":
                lines.append(f"{pad}_b.append(str(_e({repr(conteudo)})))")
            elif tipo == "se":
                lines.append(f"{pad}if _e({repr(conteudo)}):")
                indent += 1
            elif tipo == "senao":
                indent -= 1
                pad = "    " * indent
                lines.append(f"{pad}else:")
                indent += 1
            elif tipo == "fim":
                indent -= 1
            elif tipo == "para":
                parts = conteudo.split(" em ", 1)
                if len(parts) == 2:
                    var = parts[0].strip()
                    colecao = parts[1].strip()
                    lines.append(f"{pad}for {var} in _e({repr(colecao)}):")
                    lines.append(f"{pad}    _v[{repr(var)}] = {var}")
                    indent += 1
            elif tipo == "incluir":
                lines.append(f"{pad}_b.append(_incluir({repr(conteudo)}, _ctx))")

        lines.append(f"{'    ' * indent}return ''.join(_b)")
        codigo = "\n".join(lines)
        namespace = {"_Ctx": _Ctx, "_SafeDict": _SafeDict}
        exec(compile(codigo, "<template>", "exec"), namespace)
        return namespace["_template"]

    def _tokenizar(self, texto):
        nodes = []
        pos = 0
        padrao = re.compile(r"\{\{.*?\}\}|\{%.*?%\}")
        for m in padrao.finditer(texto):
            ini, fim = m.start(), m.end()
            if ini > pos:
                nodes.append(("texto", texto[pos:ini]))
            raw = m.group()[2:-2].strip()
            if m.group().startswith("{{"):
                nodes.append(("expr", raw))
            else:
                if raw.startswith("se "):
                    nodes.append(("se", raw[3:]))
                elif raw == "senao":
                    nodes.append(("senao", ""))
                elif raw.startswith("para "):
                    nodes.append(("para", raw[5:]))
                elif raw.startswith("incluir "):
                    nodes.append(("incluir", raw[8:].strip("'\"")))
                elif raw == "fim":
                    nodes.append(("fim", ""))
            pos = fim
        if pos < len(texto):
            nodes.append(("texto", texto[pos:]))
        return nodes


MODULO = _TemplateEngine()
