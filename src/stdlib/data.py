import datetime


def _agora():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _hoje():
    return datetime.date.today().strftime("%Y-%m-%d")


def _hora():
    return datetime.datetime.now().strftime("%H:%M:%S")


def _timestamp():
    return datetime.datetime.now().timestamp()


def _formatar(formato, timestamp=None):
    if timestamp is not None:
        dt = datetime.datetime.fromtimestamp(float(timestamp))
    else:
        dt = datetime.datetime.now()
    return dt.strftime(formato)


def _parsear(data_str, formato="%Y-%m-%d"):
    dt = datetime.datetime.strptime(data_str, formato)
    return dt.timestamp()


def _ano():
    return datetime.date.today().year


def _mes():
    return datetime.date.today().month


def _dia():
    return datetime.date.today().day


def _diferenca_dias(data1, data2, formato="%Y-%m-%d"):
    d1 = datetime.datetime.strptime(data1, formato)
    d2 = datetime.datetime.strptime(data2, formato)
    return abs((d2 - d1).days)


MODULO = {
    "agora": _agora,
    "hoje": _hoje,
    "hora": _hora,
    "timestamp": _timestamp,
    "formatar": _formatar,
    "parsear": _parsear,
    "ano": _ano,
    "mes": _mes,
    "dia": _dia,
    "diferenca_dias": _diferenca_dias,
}
