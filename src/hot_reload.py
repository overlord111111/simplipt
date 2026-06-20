import os
import time
import sys
import threading


def observar(caminho, callback, intervalo=1.0):
    mtime_anterior = None
    while True:
        try:
            mtime = os.path.getmtime(caminho)
            if mtime_anterior is not None and mtime != mtime_anterior:
                callback(caminho)
            mtime_anterior = mtime
        except FileNotFoundError:
            pass
        time.sleep(intervalo)


def executar_com_watch(caminho, funcao_executar):
    print(f"Assistindo: {caminho}")
    print("Pressione Ctrl+C para parar")

    def recarregar(arquivo):
        print(f"\n--- Alterado: {arquivo} ---")
        try:
            funcao_executar(arquivo)
        except SystemExit:
            pass
        except Exception:
            import traceback
            traceback.print_exc()
        print("--- Aguardando alteracoes ---")

    thread = threading.Thread(
        target=observar, args=(caminho, recarregar), daemon=True
    )
    thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nWatch encerrado.")
