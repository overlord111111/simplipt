import math
import random


def _arredondar(valor, casas=0):
    return round(valor, casas)


def _abs(valor):
    return abs(valor)


def _max(*args):
    return max(args)


def _min(*args):
    return min(args)


def _sqrt(valor):
    return math.sqrt(valor)


def _sen(valor):
    return math.sin(valor)


def _cos(valor):
    return math.cos(valor)


def _tan(valor):
    return math.tan(valor)


def _aleatorio(inicio=0, fim=1):
    return random.uniform(inicio, fim)


def _aleatorio_int(inicio, fim):
    return random.randint(inicio, fim)


def _pi():
    return math.pi


MODULO = {
    "arredondar": _arredondar,
    "abs": _abs,
    "max": _max,
    "min": _min,
    "sqrt": _sqrt,
    "sen": _sen,
    "cos": _cos,
    "tan": _tan,
    "aleatorio": _aleatorio,
    "aleatorio_int": _aleatorio_int,
    "pi": _pi,
}
