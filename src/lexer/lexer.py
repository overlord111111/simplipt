from src.erros import ErroLexico
from src.lexer.token import TipoToken, Token


class Lexer:
    PALAVRAS_RESERVADAS = {
        "verdadeiro": TipoToken.VERDADEIRO,
        "falso": TipoToken.FALSO,
        "nada": TipoToken.NADA,
        "fim": TipoToken.FIM,
        "se": TipoToken.SE,
        "senao": TipoToken.SENAO,
        "para": TipoToken.PARA,
        "ate": TipoToken.ATE,
        "em": TipoToken.EM,
        "enquanto": TipoToken.ENQUANTO,
        "fn": TipoToken.FUNCAO,
        "funcao": TipoToken.FUNCAO,
        "retornar": TipoToken.RETORNAR,
        "usar": TipoToken.USAR,
        "paralelo": TipoToken.PARALELO,
        "e": TipoToken.E,
        "ou": TipoToken.OU,
        "nao": TipoToken.NAO,
        "not": TipoToken.NAO,
        "é": TipoToken.IGUAL,
        "eh": TipoToken.IGUAL,
        "falar": TipoToken.FALAR,
        "mostrar": TipoToken.MOSTRAR,
        "dizer": TipoToken.DIZER,
        "escrever": TipoToken.ESCREVER,
        "ler": TipoToken.LER,
        "limpar": TipoToken.LIMPAR,
        "pausa": TipoToken.PAUSA,
        "info": TipoToken.INFO,
        "aviso": TipoToken.AVISO,
        "erro": TipoToken.ERRO,
        "tentar": TipoToken.TENTAR,
        "capturar": TipoToken.CAPTURAR,
        "corresponder": TipoToken.CORRESPONDER,
        "caso": TipoToken.CASO,
        "classe": TipoToken.CLASSE,
        "novo": TipoToken.NOVO,
        "este": TipoToken.ESTE,
        "super": TipoToken.SUPER,
        "extende": TipoToken.EXTENDE,
        "metodo": TipoToken.METODO,
        "construtor": TipoToken.CONSTRUTOR,
        "garantir": TipoToken.GARANTIR,
        "async": TipoToken.FUNCAO_ASYNC,
        "esperar": TipoToken.ESPERAR,
    }

    def __init__(self, texto, nome_arquivo="<memoria>"):
        self.texto = texto
        self.nome_arquivo = nome_arquivo
        self.pos = 0
        self.linha = 1
        self.coluna = 1

    def erro(self, mensagem):
        return ErroLexico(mensagem, linha=self.linha, coluna=self.coluna, arquivo=self.nome_arquivo)

    def tokenizar(self):
        tokens = []
        while self.pos < len(self.texto):
            c = self.texto[self.pos]
            if c in " \t\r":
                self._avancar()
            elif c == "\n":
                self._avancar()
                tokens.append(Token(TipoToken.FIM_DE_LINHA, "\\n", self.linha - 1, self.coluna))
            elif c == "#":
                self._comentario_linha()
            elif c == ";":
                self._avancar()
            elif c == '"' or c == "'":
                tok = self._string_ou_template(c)
                if isinstance(tok, list):
                    tokens.extend(tok)
                else:
                    tokens.append(tok)
            elif c.isdigit():
                tokens.append(self._numero())
            elif c == "+":
                if self._match("="):
                    tokens.append(self._cria_token(TipoToken.ADICAO_ATRIB, "+="))
                else:
                    tokens.append(self._cria_token(TipoToken.MAIS, "+"))
            elif c == "-":
                if self._match("="):
                    tokens.append(self._cria_token(TipoToken.SUB_ATRIB, "-="))
                else:
                    tokens.append(self._cria_token(TipoToken.MENOS, "-"))
            elif c == "*":
                tokens.append(self._cria_token(TipoToken.VEZES, "*"))
            elif c == "/":
                tokens.append(self._cria_token(TipoToken.DIVIDIR, "/"))
            elif c == "%":
                if self.pos + 1 < len(self.texto) and self.texto[self.pos + 1] == "%":
                    self._avancar()
                    self._avancar()
                    self._comentario_bloco()
                else:
                    tokens.append(self._cria_token(TipoToken.MOD, "%"))
            elif c == "(":
                tokens.append(self._cria_token(TipoToken.ABRE_PAREN, "("))
            elif c == ")":
                tokens.append(self._cria_token(TipoToken.FECHA_PAREN, ")"))
            elif c == "[":
                tokens.append(self._cria_token(TipoToken.ABRE_COLCHETE, "["))
            elif c == "]":
                tokens.append(self._cria_token(TipoToken.FECHA_COLCHETE, "]"))
            elif c == "{":
                tokens.append(self._cria_token(TipoToken.ABRE_CHAVE, "{"))
            elif c == "}":
                tokens.append(self._cria_token(TipoToken.FECHA_CHAVE, "}"))
            elif c == ",":
                tokens.append(self._cria_token(TipoToken.VIRGULA, ","))
            elif c == ".":
                linha_ponto = self.linha
                col_ponto = self.coluna
                self._avancar()
                if self._match("."):
                    tokens.append(Token(TipoToken.INTERVALO, "..", linha_ponto, col_ponto))
                else:
                    tokens.append(Token(TipoToken.PONTO, ".", linha_ponto, col_ponto))
            elif c == ":":
                tokens.append(self._cria_token(TipoToken.DOIS_PONTOS, ":"))
            elif c == "=":
                tokens.append(self._cria_token(TipoToken.ATRIBUICAO, "="))
            elif c == ">":
                linha_op = self.linha
                col_op = self.coluna
                self._avancar()
                if self._match("="):
                    tokens.append(Token(TipoToken.MAIOR_IGUAL, ">=", linha_op, col_op))
                else:
                    tokens.append(Token(TipoToken.MAIOR, ">", linha_op, col_op))
            elif c == "<":
                linha_op = self.linha
                col_op = self.coluna
                self._avancar()
                if self._match("="):
                    tokens.append(Token(TipoToken.MENOR_IGUAL, "<=", linha_op, col_op))
                else:
                    tokens.append(Token(TipoToken.MENOR, "<", linha_op, col_op))
            elif c == "|":
                linha_pipe = self.linha
                col_pipe = self.coluna
                self._avancar()
                if self._match(">"):
                    tokens.append(Token(TipoToken.PIPE, "|>", linha_pipe, col_pipe))
                else:
                    raise self.erro(f"Caractere inesperado: '|'")
            elif c.isalpha() or c in "_":
                tokens.append(self._identificador())
            else:
                raise self.erro(f"Caractere inesperado: {c!r}")

        tokens.append(Token(TipoToken.FIM_ARQUIVO, None, self.linha, self.coluna))
        return tokens

    def _avancar(self):
        c = self.texto[self.pos]
        self.pos += 1
        self.coluna += 1
        if c == "\n":
            self.linha += 1
            self.coluna = 1

    def _match(self, esperado):
        if self.pos < len(self.texto) and self.texto[self.pos] == esperado:
            self._avancar()
            return True
        return False

    def _cria_token(self, tipo, valor=None):
        tok = Token(tipo, valor if valor is not None else tipo.name.lower(), self.linha, self.coluna)
        self._avancar()
        return tok

    def _comentario_linha(self):
        while self.pos < len(self.texto) and self.texto[self.pos] != "\n":
            self._avancar()

    def _comentario_bloco(self):
        while self.pos + 1 < len(self.texto):
            if self.texto[self.pos] == "%" and self.texto[self.pos + 1] == "%":
                self._avancar()
                self._avancar()
                return
            self._avancar()
        raise self.erro("Comentário de bloco não fechado")

    def _string_ou_template(self, aspas):
        linha_ini = self.linha
        col_ini = self.coluna
        self._avancar()
        pos_inicio = self.pos
        partes = []
        texto_atual = []
        while self.pos < len(self.texto):
            c = self.texto[self.pos]
            if c == "\n":
                raise self.erro("String não fechada antes do final da linha")
            if c == "\\":
                self._avancar()
                if self.pos >= len(self.texto):
                    raise self.erro("String não fechada")
                prox = self.texto[self.pos]
                mapa = {"n": "\n", "t": "\t", "\\": "\\", '"': '"', "'": "'", "r": "\r"}
                texto_atual.append(mapa.get(prox, prox))
                self._avancar()
            elif c == "{" and aspas == '"':
                if texto_atual:
                    partes.append(("texto", "".join(texto_atual)))
                    texto_atual = []
                self._avancar()
                expr_texto, expr_lin, expr_col = self._extrair_expr_template()
                partes.append(("expr", expr_texto, expr_lin, expr_col))
            elif c == aspas:
                self._avancar()
                if texto_atual:
                    partes.append(("texto", "".join(texto_atual)))
                if not partes:
                    return Token(TipoToken.TEXTO, "", linha_ini, col_ini)
                if len(partes) == 1 and partes[0][0] == "texto":
                    return Token(TipoToken.TEXTO, partes[0][1], linha_ini, col_ini)
                return Token(TipoToken.TEMPLET, partes, linha_ini, col_ini)
            else:
                texto_atual.append(c)
                self._avancar()
        raise self.erro("String não fechada")

    def _extrair_expr_template(self):
        expr_lin = self.linha
        expr_col = self.coluna
        profundidade = 1
        inicio = self.pos
        while self.pos < len(self.texto) and profundidade > 0:
            c = self.texto[self.pos]
            if c == "{":
                profundidade += 1
            elif c == "}":
                profundidade -= 1
            self._avancar()
        if profundidade != 0:
            raise self.erro("Template não fechado")
        return self.texto[inicio:self.pos - 1], expr_lin, expr_col

    def _string_simples(self, aspas):
        linha_ini = self.linha
        col_ini = self.coluna
        self._avancar()
        resultado = []
        while self.pos < len(self.texto):
            c = self.texto[self.pos]
            if c == "\n":
                raise self.erro("String não fechada antes do final da linha")
            if c == "\\":
                self._avancar()
                if self.pos >= len(self.texto):
                    raise self.erro("String não fechada")
                prox = self.texto[self.pos]
                mapa = {"n": "\n", "t": "\t", "\\": "\\", '"': '"', "'": "'", "r": "\r"}
                resultado.append(mapa.get(prox, prox))
                self._avancar()
            elif c == aspas:
                self._avancar()
                return Token(TipoToken.TEXTO, "".join(resultado), linha_ini, col_ini)
            else:
                resultado.append(c)
                self._avancar()
        raise self.erro("String não fechada")

    def _numero(self):
        linha_ini = self.linha
        col_ini = self.coluna
        resultado = []
        while self.pos < len(self.texto) and self.texto[self.pos].isdigit():
            resultado.append(self.texto[self.pos])
            self._avancar()
        if (self.pos < len(self.texto) and self.texto[self.pos] == "."
                and self.pos + 1 < len(self.texto) and self.texto[self.pos + 1].isdigit()):
            resultado.append(".")
            self._avancar()
            while self.pos < len(self.texto) and self.texto[self.pos].isdigit():
                resultado.append(self.texto[self.pos])
                self._avancar()
            valor = float("".join(resultado))
            return Token(TipoToken.FLUTUANTE, valor, linha_ini, col_ini)
        valor = int("".join(resultado)) if resultado else 0
        return Token(TipoToken.INTEIRO, valor, linha_ini, col_ini)

    def _identificador(self):
        linha_ini = self.linha
        col_ini = self.coluna
        chars = []
        while self.pos < len(self.texto) and (self.texto[self.pos].isalnum() or self.texto[self.pos] == "_"):
            chars.append(self.texto[self.pos])
            self._avancar()
        palavra = "".join(chars)

        if palavra == "nao":
            pos_salva = self.pos
            linha_salva = self.linha
            col_salva = self.coluna
            espacos = 0
            while self.pos < len(self.texto) and self.texto[self.pos] in " \t":
                self.pos += 1
                self.coluna += 1
                espacos += 1
            if self.pos < len(self.texto) and self.texto[self.pos] == "é":
                self._avancar()
                return Token(TipoToken.DIFERENTE, "nao é", linha_ini, col_ini)
            resto = self.texto[self.pos:]
            if resto[:2] == "eh" and (len(resto) == 2 or not resto[2].isalnum()):
                self.pos += 2
                self.coluna += 2
                return Token(TipoToken.DIFERENTE, "nao eh", linha_ini, col_ini)
            self.pos = pos_salva
            self.linha = linha_salva
            self.coluna = col_salva
            return Token(TipoToken.NAO, "nao", linha_ini, col_ini)

        if palavra in self.PALAVRAS_RESERVADAS:
            tipo = self.PALAVRAS_RESERVADAS[palavra]
            return Token(tipo, palavra, linha_ini, col_ini)

        return Token(TipoToken.IDENTIFICADOR, palavra, linha_ini, col_ini)
