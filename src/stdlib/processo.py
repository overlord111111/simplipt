import subprocess
import os
import threading


def _executar(comando, capturar=False):
    if capturar:
        r = subprocess.run(comando, shell=True, capture_output=True, text=True)
        return {
            "codigo": r.returncode,
            "saida": r.stdout,
            "erro": r.stderr,
        }
    else:
        codigo = os.system(comando)
        return {"codigo": codigo}


def _executar_async(comando, callback=None):
    resultado = {}

    def _run():
        r = subprocess.run(comando, shell=True, capture_output=True, text=True)
        resultado["codigo"] = r.returncode
        resultado["saida"] = r.stdout
        resultado["erro"] = r.stderr
        if callback:
            callback(resultado)

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return t


MODULO = {
    "executar": _executar,
    "executar_async": _executar_async,
}
