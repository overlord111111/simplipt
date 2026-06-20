import json
import urllib.request
import urllib.error


def _get(url, cabecalhos=None):
    req = urllib.request.Request(url, headers=cabecalhos or {})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            corpo = resp.read().decode("utf-8")
            try:
                dados = json.loads(corpo)
            except (json.JSONDecodeError, UnicodeDecodeError):
                dados = corpo
            return {
                "codigo": resp.status,
                "dados": dados,
                "cabecalhos": dict(resp.headers),
            }
    except urllib.error.HTTPError as e:
        return {"codigo": e.code, "erro": str(e), "dados": None}
    except urllib.error.URLError as e:
        return {"codigo": 0, "erro": str(e.reason), "dados": None}


def _post(url, dados=None, cabecalhos=None):
    data = None
    if dados is not None:
        data = json.dumps(dados).encode("utf-8")
    cab = cabecalhos or {}
    if data and "Content-Type" not in cab:
        cab["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=cab, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            corpo = resp.read().decode("utf-8")
            try:
                dados_resp = json.loads(corpo)
            except (json.JSONDecodeError, UnicodeDecodeError):
                dados_resp = corpo
            return {
                "codigo": resp.status,
                "dados": dados_resp,
                "cabecalhos": dict(resp.headers),
            }
    except urllib.error.HTTPError as e:
        return {"codigo": e.code, "erro": str(e), "dados": None}
    except urllib.error.URLError as e:
        return {"codigo": 0, "erro": str(e.reason), "dados": None}


MODULO = {
    "get": _get,
    "post": _post,
}
