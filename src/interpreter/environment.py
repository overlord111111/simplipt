from src.erros import ErroRuntime


class Environment:
    def __init__(self, parent=None):
        self.values = {}
        self.parent = parent

    def definir(self, nome, valor):
        self.values[nome] = valor

    def obter(self, nome):
        if nome in self.values:
            return self.values[nome]
        if self.parent is not None:
            return self.parent.obter(nome)
        raise ErroRuntime(f"Variável '{nome}' não definida")

    def atribuir(self, nome, valor):
        if nome in self.values:
            self.values[nome] = valor
        elif self.parent is not None:
            self.parent.atribuir(nome, valor)
        else:
            raise ErroRuntime(f"Variável '{nome}' não definida")

    def tem(self, nome):
        if nome in self.values:
            return True
        if self.parent is not None:
            return self.parent.tem(nome)
        return False

    def copia_global(self):
        env = Environment()
        env.values = self.values.copy()
        return env
