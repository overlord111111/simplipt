import re


def _buscar(padrao, texto):
    match = re.search(padrao, texto)
    if match:
        return match.group(0)
    return ""


def _encontrar(padrao, texto):
    return re.findall(padrao, texto)


def _testar(padrao, texto):
    return bool(re.search(padrao, texto))


def _substituir(padrao, substituicao, texto):
    return re.sub(padrao, substituicao, texto)


def _dividir(padrao, texto):
    return re.split(padrao, texto)


def _grupos(padrao, texto):
    match = re.search(padrao, texto)
    if match:
        return list(match.groups())
    return []


MODULO = {
    "buscar": _buscar,
    "encontrar": _encontrar,
    "testar": _testar,
    "substituir": _substituir,
    "dividir": _dividir,
    "grupos": _grupos,
}
