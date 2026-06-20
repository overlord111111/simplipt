import os
import json


def _caminho_config():
    base = os.environ.get("APPDATA") or os.environ.get("HOME") or "."
    pasta = os.path.join(base, "SimpliPT")
    os.makedirs(pasta, exist_ok=True)
    return os.path.join(pasta, "config.json")


ARQUIVO = _caminho_config()


def _carregar():
    try:
        with open(ARQUIVO, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _salvar(dados):
    with open(ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


class _Config:
    _dados = _carregar()

    def __getattr__(self, nome):
        if nome.startswith("_"):
            return super().__getattr__(nome)
        return self._dados.get(nome, "")

    def __setattr__(self, nome, valor):
        if nome.startswith("_"):
            super().__setattr__(nome, valor)
        else:
            self._dados[nome] = valor
            _salvar(self._dados)


MODULO = _Config()
