import sys
import os
import subprocess
import importlib
import pkgutil
import json


_MODULOS_CACHE = {}


def _caminho_modulos():
    import tempfile
    return os.path.join(tempfile.gettempdir(), "simplipt_modulos")


def instalar(nome_python, nome_simplipt=None):
    if nome_simplipt is None:
        nome_simplipt = nome_python.lower().replace("-", "_").replace(".", "_")

    cache = _caminho_modulos()
    os.makedirs(cache, exist_ok=True)

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", nome_python, "--target", cache, "--quiet"],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            return {"erro": result.stderr.strip() or f"Falha ao instalar {nome_python}"}

        sys.path.insert(0, cache)

        nome_limp = nome_python.replace("-", "_")
        mod = importlib.import_module(nome_limp)

        _MODULOS_CACHE[nome_simplipt] = mod
        return {"ok": True, "modulo": nome_simplipt, "python": nome_python}

    except subprocess.TimeoutExpired:
        return {"erro": "Tempo limite excedido"}
    except Exception as e:
        return {"erro": str(e)}


def carregar(nome_simplipt):
    mod = _MODULOS_CACHE.get(nome_simplipt)
    if mod is None:
        return {"erro": f"Modulo '{nome_simplipt}' nao instalado. Use install primeiro"}
    return mod


def listar():
    return [{"simplipt": k, "python": getattr(v, "__name__", str(v))} for k, v in _MODULOS_CACHE.items()]


def _wrapper_modulo(mod):
    class _Proxy:
        def __init__(self, obj, nome=""):
            self._obj = obj
            self._nome = nome

        def __getattr__(self, nome):
            val = getattr(self._obj, nome, None)
            if val is None:
                raise AttributeError(f"'{self._nome}' nao tem atributo '{nome}'")
            if callable(val):
                def _fn(*args, **kwargs):
                    return val(*args, **kwargs)
                return _fn
            return val

        def __setattr__(self, nome, val):
            if nome.startswith("_"):
                super().__setattr__(nome, val)
            else:
                setattr(self._obj, nome, val)

    return _Proxy(mod, mod.__name__)


def usar(nome_simplipt):
    mod = _MODULOS_CACHE.get(nome_simplipt)
    if mod is None:
        return None
    return _wrapper_modulo(mod)
