import os
import shutil


def _ler(caminho, encoding="utf-8"):
    with open(caminho, "r", encoding=encoding) as f:
        return f.read()


def _escrever(caminho, conteudo, encoding="utf-8"):
    with open(caminho, "w", encoding=encoding) as f:
        f.write(conteudo)
    return True


def _adicionar(caminho, conteudo, encoding="utf-8"):
    with open(caminho, "a", encoding=encoding) as f:
        f.write(conteudo)
    return True


def _copiar(origem, destino):
    return shutil.copy2(origem, destino)


def _mover(origem, destino):
    return shutil.move(origem, destino)


def _deletar(caminho):
    if os.path.isfile(caminho):
        os.remove(caminho)
    elif os.path.isdir(caminho):
        shutil.rmtree(caminho)
    return True


def _listar(caminho="."):
    return os.listdir(caminho)


def _existe(caminho):
    return os.path.exists(caminho)


def _eh_arquivo(caminho):
    return os.path.isfile(caminho)


def _eh_pasta(caminho):
    return os.path.isdir(caminho)


def _criar_pasta(caminho):
    os.makedirs(caminho, exist_ok=True)
    return True


def _tamanho(caminho):
    return os.path.getsize(caminho)


MODULO = {
    "ler": _ler,
    "escrever": _escrever,
    "adicionar": _adicionar,
    "copiar": _copiar,
    "mover": _mover,
    "deletar": _deletar,
    "listar": _listar,
    "existe": _existe,
    "eh_arquivo": _eh_arquivo,
    "eh_pasta": _eh_pasta,
    "criar_pasta": _criar_pasta,
    "tamanho": _tamanho,
}
