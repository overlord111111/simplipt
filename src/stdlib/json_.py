import json


def _ler(conteudo):
    if isinstance(conteudo, str):
        return json.loads(conteudo)
    raise TypeError("json.ler() espera uma string")


def _gerar(dados, indentado=False):
    if indentado:
        return json.dumps(dados, ensure_ascii=False, indent=2)
    return json.dumps(dados, ensure_ascii=False)


def _arquivo(caminho, encoding="utf-8"):
    with open(caminho, "r", encoding=encoding) as f:
        return json.load(f)


def _salvar(caminho, dados, encoding="utf-8"):
    with open(caminho, "w", encoding=encoding) as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    return True


MODULO = {
    "ler": _ler,
    "gerar": _gerar,
    "arquivo": _arquivo,
    "salvar": _salvar,
}
