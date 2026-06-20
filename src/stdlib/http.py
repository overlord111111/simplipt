import urllib.request
import urllib.parse
import json as py_json


def _obter(url, cabecalhos=None):
    req = urllib.request.Request(url, headers=cabecalhos or {})
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode("utf-8")


def _postar(url, dados=None, cabecalhos=None, json=False):
    headers = cabecalhos or {}
    if json and dados is not None:
        data = py_json.dumps(dados).encode("utf-8")
        headers.setdefault("Content-Type", "application/json")
    elif dados is not None:
        data = urllib.parse.urlencode(dados).encode("utf-8")
    else:
        data = None
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode("utf-8")


def _json(url, cabecalhos=None):
    resposta = _obter(url, cabecalhos)
    return py_json.loads(resposta)


MODULO = {
    "obter": _obter,
    "postar": _postar,
    "json": _json,
}
