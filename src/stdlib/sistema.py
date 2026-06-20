import os
import platform
import sys


def _info():
    return {
        "sistema": platform.system(),
        "versao": platform.version(),
        "arquitetura": platform.machine(),
        "hostname": platform.node(),
        "python": sys.version,
    }


def _variavel(nome, valor=None):
    if valor is not None:
        os.environ[nome] = str(valor)
    return os.environ.get(nome, "")


def _cmd(comando):
    return os.system(comando)


def _caminho_atual():
    return os.getcwd()


def _mudar_caminho(caminho):
    os.chdir(caminho)
    return caminho


def _pasta_temp():
    return os.environ.get("TEMP", os.environ.get("TMP", "/tmp"))


MODULO = {
    "info": _info,
    "variavel": _variavel,
    "cmd": _cmd,
    "caminho_atual": _caminho_atual,
    "mudar_caminho": _mudar_caminho,
    "pasta_temp": _pasta_temp,
    "sistema": platform.system,
    "hostname": platform.node,
}
