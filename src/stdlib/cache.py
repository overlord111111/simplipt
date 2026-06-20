import time


class _Cache:
    def __init__(self):
        self._dados = {}

    def definir(self, chave, valor, expira_em=0):
        if expira_em > 0:
            expira = time.time() + expira_em
        else:
            expira = None
        self._dados[chave] = (valor, expira)
        return True

    def obter(self, chave, padrao=None):
        if chave not in self._dados:
            return padrao
        valor, expira = self._dados[chave]
        if expira is not None and time.time() > expira:
            del self._dados[chave]
            return padrao
        return valor

    def existe(self, chave):
        if chave not in self._dados:
            return False
        valor, expira = self._dados[chave]
        if expira is not None and time.time() > expira:
            del self._dados[chave]
            return False
        return True

    def remover(self, chave):
        if chave in self._dados:
            del self._dados[chave]
            return True
        return False

    def limpar(self):
        self._dados.clear()
        return True

    def tamanho(self):
        return len(self._dados)


MODULO = _Cache()
