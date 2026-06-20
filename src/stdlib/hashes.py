import hashlib


def _md5(texto):
    if isinstance(texto, str):
        texto = texto.encode("utf-8")
    return hashlib.md5(texto).hexdigest()


def _sha1(texto):
    if isinstance(texto, str):
        texto = texto.encode("utf-8")
    return hashlib.sha1(texto).hexdigest()


def _sha256(texto):
    if isinstance(texto, str):
        texto = texto.encode("utf-8")
    return hashlib.sha256(texto).hexdigest()


def _arquivo_md5(caminho):
    h = hashlib.md5()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(4096), b""):
            h.update(bloco)
    return h.hexdigest()


def _arquivo_sha256(caminho):
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(4096), b""):
            h.update(bloco)
    return h.hexdigest()


MODULO = {
    "md5": _md5,
    "sha1": _sha1,
    "sha256": _sha256,
    "arquivo_md5": _arquivo_md5,
    "arquivo_sha256": _arquivo_sha256,
}
