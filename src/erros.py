class _BaseErro(Exception):
    def __init__(self, mensagem, linha=None, coluna=None, arquivo=None):
        self.mensagem = mensagem
        self.linha = linha
        self.coluna = coluna
        self.arquivo = arquivo
        super().__init__(self._formatar())

    def _sugestao(self):
        m = self.mensagem.lower()
        sugestoes = {
            "não definida": "Verifique o nome da variável ou crie ela antes de usar",
            "esperado 'fim'": "Adicione 'fim' no final do bloco (se, senao, para, enquanto, funcao, paralelo)",
            "expressão inválida": "Verifique a sintaxe da linha. Faltou um operador ou palavra-chave?",
            "não encontrado": "Verifique se o nome está correto",
            "não fechada": "Adicione o caractere de fechamento correspondente",
            "não é uma função": "Use o nome da função sem parênteses para acessar a variável",
            "caractere inesperado": "Remova o caractere ou substitua por um válido",
            "não tem método": "Verifique se o objeto tem esse método disponível",
            "não é chamável": "Esta variável não é uma função. Use sem parênteses",
            "esperado nova linha": "Quebre a linha após a condição/declaração",
            "esperado nome": "Adicione um nome ou identificador válido",
            "esperado '": "Verifique a sintaxe — faltou fechar ou adicionar um delimitador",
        }
        for chave, dica in sugestoes.items():
            if chave in m:
                return f"Dica: {dica}"
        return ""

    def _formatar(self):
        partes = [self.mensagem]
        if self.arquivo:
            partes.append(f"arquivo: {self.arquivo}")
        if self.linha is not None:
            partes.append(f"linha: {self.linha}")
        if self.coluna is not None:
            partes.append(f"coluna: {self.coluna}")
        sugestao = self._sugestao()
        if sugestao:
            partes.append(sugestao)
        return " | ".join(partes)


class ErroLexico(_BaseErro):
    pass


class ErroSintaxe(_BaseErro):
    pass


class ErroRuntime(_BaseErro):
    pass
