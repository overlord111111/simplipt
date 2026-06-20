import time
from collections import defaultdict


class Profile:
    def __init__(self):
        self.tempos = defaultdict(float)
        self.contagens = defaultdict(int)
        self.pilha = []
        self._inicio_atual = None

    def entrar(self, nome):
        if self._inicio_atual is not None:
            decorrido = time.time() - self._inicio_atual
            self.tempos[self.pilha[-1]] += decorrido
        self.pilha.append(nome)
        self._inicio_atual = time.time()

    def sair(self):
        if self._inicio_atual is not None:
            decorrido = time.time() - self._inicio_atual
            nome = self.pilha[-1]
            self.tempos[nome] += decorrido
            self.contagens[nome] += 1
        self.pilha.pop()
        self._inicio_atual = time.time() if self.pilha else None

    def relatorio(self):
        total = sum(self.tempos.values())
        linhas = []
        linhas.append(f"{'Funcao':<30} {'Chamadas':<10} {'Tempo (s)':<12} {'%':<8}")
        linhas.append("-" * 60)
        for nome in sorted(self.tempos, key=lambda n: self.tempos[n], reverse=True):
            t = self.tempos[nome]
            c = self.contagens.get(nome, 0)
            pct = (t / total * 100) if total > 0 else 0
            linhas.append(f"{nome:<30} {c:<10} {t:<12.4f} {pct:<8.2f}")
        linhas.append("-" * 60)
        linhas.append(f"{'TOTAL':<30} {'':<10} {total:<12.4f} {'100.00':<8}")
        return "\n".join(linhas)

    def resetar(self):
        self.tempos.clear()
        self.contagens.clear()
        self.pilha.clear()
        self._inicio_atual = None


_PERFIL = None


def ativar():
    global _PERFIL
    if _PERFIL is None:
        _PERFIL = Profile()
    return _PERFIL


def desativar():
    global _PERFIL
    rel = None
    if _PERFIL:
        rel = _PERFIL.relatorio()
    _PERFIL = None
    return rel


def instancia():
    return _PERFIL
