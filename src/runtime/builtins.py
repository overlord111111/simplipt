import builtins as py_builtins
import time
import os


def builtin_falar(*args):
    texto = " ".join(str(a) for a in args)
    print(texto)


builtin_mostrar = builtin_falar
builtin_dizer = builtin_falar
builtin_escrever = builtin_falar


def builtin_ler(prompt=""):
    return input(str(prompt) if prompt else "")


def builtin_limpar():
    os.system("cls" if os.name == "nt" else "clear")


def builtin_pausa(segundos):
    time.sleep(float(segundos))


def builtin_tipo(valor):
    return type(valor).__name__


def builtin_tamanho(valor):
    if isinstance(valor, (list, dict, str)):
        return len(valor)
    raise TypeError(f"tamanho() não suportado para {type(valor).__name__}")


def builtin_texto(valor):
    return str(valor)


def builtin_numero(valor):
    return float(valor)


def builtin_inteiro(valor):
    return int(valor)


def builtin_intervalo(*args):
    if len(args) == 1:
        return list(range(1, int(args[0]) + 1))
    if len(args) == 2:
        return list(range(int(args[0]), int(args[1]) + 1))
    if len(args) == 3:
        return list(range(int(args[0]), int(args[1]) + 1, int(args[2])))
    raise TypeError(f"intervalo() espera 1-3 argumentos, recebeu {len(args)}")


REGISTRY_BUILTINS = {
    "falar": builtin_falar,
    "mostrar": builtin_mostrar,
    "dizer": builtin_dizer,
    "escrever": builtin_escrever,
    "ler": builtin_ler,
    "limpar": builtin_limpar,
    "pausa": builtin_pausa,
    "tipo": builtin_tipo,
    "tamanho": builtin_tamanho,
    "texto": builtin_texto,
    "numero": builtin_numero,
    "inteiro": builtin_inteiro,
    "intervalo": builtin_intervalo,
}
