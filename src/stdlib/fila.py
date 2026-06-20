import json
import queue
import threading
import time


class _Fila:
    def __init__(self):
        self._fila = queue.Queue()
        self._workers = []
        self._rodando = threading.Event()

    def adicionar(self, item):
        self._fila.put(item)
        return True

    def retirar(self, timeout=None):
        try:
            return self._fila.get(timeout=timeout)
        except queue.Empty:
            return None

    def tamanho(self):
        return self._fila.qsize()

    def vazia(self):
        return self._fila.empty()

    def limpar(self):
        while not self._fila.empty():
            try:
                self._fila.get_nowait()
            except queue.Empty:
                break
        return True

    def pegar_todos(self):
        itens = []
        while not self._fila.empty():
            try:
                itens.append(self._fila.get_nowait())
            except queue.Empty:
                break
        return itens

    def processar(self, quantidade, callback, intervalo=0):
        if quantidade < 1:
            raise ValueError("quantidade deve ser >= 1")

        self._rodando.set()

        def _worker():
            while self._rodando.is_set():
                try:
                    item = self._fila.get(timeout=0.5)
                    try:
                        callback(item)
                    except Exception as e:
                        pass
                    self._fila.task_done()
                except queue.Empty:
                    continue

        for _ in range(quantidade):
            t = threading.Thread(target=_worker, daemon=True)
            t.start()
            self._workers.append(t)

        return f"{quantidade} worker(s) iniciado(s)"

    def parar_workers(self, aguardar=True):
        self._rodando.clear()
        if aguardar:
            for t in self._workers:
                t.join(timeout=5)
        self._workers.clear()
        return f"{len(self._workers)} worker(s) parado(s)"

    def aguardar(self, timeout=None):
        self._fila.join()
        return True

    def salvar(self, caminho):
        itens = []
        while not self._fila.empty():
            try:
                itens.append(self._fila.get_nowait())
            except queue.Empty:
                break
        with open(str(caminho), "w", encoding="utf-8") as f:
            json.dump(itens, f, ensure_ascii=False)
        for item in itens:
            self._fila.put(item)
        return True

    def carregar(self, caminho):
        with open(str(caminho), "r", encoding="utf-8") as f:
            itens = json.load(f)
        for item in itens:
            self._fila.put(item)
        return len(itens)


MODULO = _Fila()
