from src.erros import ErroSintaxe
from src.lexer.token import TipoToken
from src.parser.ast import *


class Parser:
    def __init__(self, tokens, nome_arquivo="<memoria>"):
        self.tokens = tokens
        self.nome_arquivo = nome_arquivo
        self.atual = 0

    def erro(self, mensagem):
        tok = self.token_atual()
        return ErroSintaxe(mensagem, linha=tok.linha, coluna=tok.coluna, arquivo=self.nome_arquivo)

    def token_atual(self):
        return self.tokens[self.atual]

    def anterior(self):
        return self.tokens[self.atual - 1]

    def verifica(self, *tipos):
        return self.token_atual().tipo in tipos

    def consome(self, tipo, mensagem):
        if self.verifica(tipo):
            tok = self.token_atual()
            self.atual += 1
            return tok
        raise self.erro(mensagem)

    def avanca(self):
        tok = self.token_atual()
        self.atual += 1
        return tok

    def pula_linhas(self):
        while self.verifica(TipoToken.FIM_DE_LINHA):
            self.avanca()

    def programa(self):
        nodes = []
        while not self.verifica(TipoToken.FIM_ARQUIVO):
            self.pula_linhas()
            if self.verifica(TipoToken.FIM_ARQUIVO):
                break
            nodes.append(self.linha())
            self.pula_linhas()
        return Programa(nodes)

    def linha(self):
        if self.verifica(TipoToken.SE):
            return self.condicional()
        if self.verifica(TipoToken.PARA):
            return self.loop_para()
        if self.verifica(TipoToken.ENQUANTO):
            return self.loop_enquanto()
        if self.verifica(TipoToken.FUNCAO):
            return self.funcao_def()
        if self.verifica(TipoToken.PARALELO):
            return self.paralelo()
        if self.verifica(TipoToken.TENTAR):
            return self.tentar()
        if self.verifica(TipoToken.USAR):
            return self.usar()
        if self.verifica(TipoToken.RETORNAR):
            return self.retorno()
        if self.verifica(TipoToken.CORRESPONDER):
            return self.corresponder_stmt()
        if self.verifica(TipoToken.CLASSE):
            return self.classe_stmt()
        if self.verifica(TipoToken.METODO):
            return self.metodo_stmt()
        if self.verifica(TipoToken.CONSTRUTOR):
            return self.construtor_stmt()
        if self.verifica(TipoToken.FALAR, TipoToken.MOSTRAR, TipoToken.DIZER, TipoToken.ESCREVER):
            return self.comando_falar()
        if self.verifica(TipoToken.LER):
            return self.comando_ler()
        if self.verifica(TipoToken.LIMPAR):
            return self.comando_limpar()
        if self.verifica(TipoToken.PAUSA):
            return self.comando_pausa()
        if self.verifica(TipoToken.GARANTIR):
            return self.comando_garantir()
        if self.verifica(TipoToken.FUNCAO_ASYNC):
            return self.funcao_async_stmt()
        if self.verifica(TipoToken.ESPERAR):
            return self.comando_esperar()
        if self.verifica(TipoToken.INFO, TipoToken.AVISO, TipoToken.ERRO):
            peek = self.tokens[self.atual + 1] if self.atual + 1 < len(self.tokens) else None
            if peek and peek.tipo in (TipoToken.ATRIBUICAO, TipoToken.ADICAO_ATRIB, TipoToken.SUB_ATRIB):
                return self.statement_expressao()
            return self.comando_log()
        if self.verifica(TipoToken.IDENTIFICADOR, TipoToken.ESTE, TipoToken.SUPER, TipoToken.NOVO):
            return self.statement_expressao()
        if self.verifica(TipoToken.FIM_DE_LINHA):
            self.avanca()
            return None
        raise self.erro(f"Instrução inválida: {self.token_atual().valor!r}")

    def statement_expressao(self):
        tok = self.token_atual()
        peek = self.tokens[self.atual + 1] if self.atual + 1 < len(self.tokens) else None
        if peek and peek.tipo == TipoToken.DOIS_PONTOS:
            self.avanca()
            self.avanca()
            tipo_tok = self.consome(TipoToken.IDENTIFICADOR, "Esperado tipo após ':'")
            self.consome(TipoToken.ATRIBUICAO, "Esperado '=' após tipo")
            valor = self.expressao()
            return Atribuicao(tok.valor, valor, tipo_tok.valor)
        if peek and peek.tipo == TipoToken.ATRIBUICAO:
            self.avanca()
            self.avanca()
            valor = self.expressao()
            return Atribuicao(tok.valor, valor)
        if peek and peek.tipo in (TipoToken.ADICAO_ATRIB, TipoToken.SUB_ATRIB):
            self.avanca()
            op = self.avanca().tipo
            valor = self.expressao()
            var = Variavel(tok.valor)
            expr = Binario(var, TipoToken.MAIS if op == TipoToken.ADICAO_ATRIB else TipoToken.MENOS, valor)
            return Atribuicao(tok.valor, expr)
        expr = self.expressao()
        if self.verifica(TipoToken.ATRIBUICAO) and isinstance(expr, Membro):
            self.avanca()
            valor = self.expressao()
            return AtribuicaoMembro(expr.objeto, expr.nome, valor)
        if self.verifica(TipoToken.ATRIBUICAO) and isinstance(expr, Indexacao):
            self.avanca()
            valor = self.expressao()
            return AtribuicaoIndexada(expr.objeto, expr.indice, valor)
        return expr

    def comando_garantir(self):
        self.avanca()
        cond = self.expressao()
        msg = None
        if self.verifica(TipoToken.VIRGULA):
            self.avanca()
            msg_tok = self.consome(TipoToken.TEXTO, "Esperado mensagem de texto")
            msg = msg_tok.valor
        return Garantir(cond, msg)

    def comando_falar(self):
        self.avanca()
        expr = self.expressao()
        return Falar(expr)

    def comando_ler(self):
        self.avanca()
        if not self.verifica(TipoToken.FIM_DE_LINHA, TipoToken.FIM_ARQUIVO):
            prompt = self.expressao()
            return Ler(prompt)
        return Ler()

    def comando_limpar(self):
        self.avanca()
        return Limpar()

    def comando_pausa(self):
        self.avanca()
        tempo = self.expressao()
        return Pausa(tempo)

    def comando_log(self):
        tok = self.avanca()
        nivel = tok.valor
        msg = self.expressao()
        return Log(nivel, msg)

    def condicional(self):
        self.consome(TipoToken.SE, "Esperado 'se'")
        condicao = self.expressao()
        self.consome(TipoToken.FIM_DE_LINHA, "Esperado nova linha após condição do se")
        corpo = self.corpo()
        senao = self._parse_elif_chain() if self.verifica(TipoToken.SENAO) else None
        self.consome(TipoToken.FIM, "Esperado 'fim' para fechar se")
        return Se(condicao, corpo, senao)

    def _parse_elif_chain(self):
        self.consome(TipoToken.SENAO, "Esperado 'senao'")
        if self.verifica(TipoToken.SE):
            self.avanca()
            cond = self.expressao()
            self.consome(TipoToken.FIM_DE_LINHA, "Esperado nova linha após condição")
            corpo = self.corpo()
            resto = self._parse_elif_chain() if self.verifica(TipoToken.SENAO) else None
            return [Se(cond, corpo, resto)]
        self.consome(TipoToken.FIM_DE_LINHA, "Esperado nova linha após 'senao'")
        return self.corpo()

    def loop_para(self):
        self.consome(TipoToken.PARA, "Esperado 'para'")
        var_tok = self.consome(TipoToken.IDENTIFICADOR, "Esperado nome da variável após 'para'")
        var = var_tok.valor
        if self.verifica(TipoToken.ATE):
            self.avanca()
            ate = self.expressao()
            self.consome(TipoToken.FIM_DE_LINHA, "Esperado nova linha após expressão do para")
            corpo = self.corpo()
            self.consome(TipoToken.FIM, "Esperado 'fim' para fechar para")
            return ParaAte(var, ate, corpo)
        if self.verifica(TipoToken.EM):
            self.avanca()
            colecao = self.expressao()
            self.consome(TipoToken.FIM_DE_LINHA, "Esperado nova linha após expressão do para")
            corpo = self.corpo()
            self.consome(TipoToken.FIM, "Esperado 'fim' para fechar para")
            return ParaEm(var, colecao, corpo)
        raise self.erro("Esperado 'ate' ou 'em' após variável do para")

    def loop_enquanto(self):
        self.consome(TipoToken.ENQUANTO, "Esperado 'enquanto'")
        condicao = self.expressao()
        self.consome(TipoToken.FIM_DE_LINHA, "Esperado nova linha após condição do enquanto")
        corpo = self.corpo()
        self.consome(TipoToken.FIM, "Esperado 'fim' para fechar enquanto")
        return Enquanto(condicao, corpo)

    def _parse_params_e_corpo(self):
        self.consome(TipoToken.ABRE_PAREN, "Esperado '('")
        params = []
        if not self.verifica(TipoToken.FECHA_PAREN):
            params.append(self.consome(TipoToken.IDENTIFICADOR, "Esperado nome do parâmetro").valor)
            while self.verifica(TipoToken.VIRGULA):
                self.avanca()
                params.append(self.consome(TipoToken.IDENTIFICADOR, "Esperado nome do parâmetro").valor)
        self.consome(TipoToken.FECHA_PAREN, "Esperado ')'")
        self.consome(TipoToken.FIM_DE_LINHA, "Esperado nova linha após declaração da função")
        corpo = self.corpo()
        self.consome(TipoToken.FIM, "Esperado 'fim' para fechar função")
        return params, corpo

    def funcao_def(self):
        self.consome(TipoToken.FUNCAO, "Esperado 'funcao'")
        nome = self._consome_nome_membro()
        params, corpo = self._parse_params_e_corpo()
        return Funcao(nome, params, corpo)

    def funcao_async_stmt(self):
        self.consome(TipoToken.FUNCAO_ASYNC, "Esperado 'async'")
        nome = self._consome_nome_membro()
        params, corpo = self._parse_params_e_corpo()
        return FuncaoAsync(nome, params, corpo)

    def comando_esperar(self):
        self.consome(TipoToken.ESPERAR, "Esperado 'esperar'")
        chamada = self.expressao()
        return Esperar(chamada)

    def funcao_anonima(self):
        self.consome(TipoToken.FUNCAO, "Esperado 'funcao'")
        nome = ""
        params, corpo = self._parse_params_e_corpo()
        return Funcao(nome, params, corpo)

    def paralelo(self):
        self.consome(TipoToken.PARALELO, "Esperado 'paralelo'")
        self.consome(TipoToken.FIM_DE_LINHA, "Esperado nova linha após 'paralelo'")
        corpo = self.corpo()
        self.consome(TipoToken.FIM, "Esperado 'fim' para fechar paralelo")
        return Paralelo(corpo)

    def tentar(self):
        self.consome(TipoToken.TENTAR, "Esperado 'tentar'")
        self.consome(TipoToken.FIM_DE_LINHA, "Esperado nova linha após 'tentar'")
        corpo = self.corpo()
        self.consome(TipoToken.CAPTURAR, "Esperado 'capturar'")
        self.consome(TipoToken.FIM_DE_LINHA, "Esperado nova linha após 'capturar'")
        capturar = self.corpo()
        self.consome(TipoToken.FIM, "Esperado 'fim' para fechar tentar")
        return Tentar(corpo, capturar)

    def usar(self):
        self.consome(TipoToken.USAR, "Esperado 'usar'")
        nome_tok = self.consome(TipoToken.IDENTIFICADOR, "Esperado nome do módulo")
        return Usar(nome_tok.valor)

    def retorno(self):
        self.consome(TipoToken.RETORNAR, "Esperado 'retornar'")
        if not self.verifica(TipoToken.FIM_DE_LINHA, TipoToken.FIM_ARQUIVO):
            valor = self.expressao()
            return Retornar(valor)
        return Retornar()

    def corpo(self):
        instrucoes = []
        self.pula_linhas()
        while not self.verifica(TipoToken.FIM, TipoToken.SENAO, TipoToken.CAPTURAR, TipoToken.FIM_ARQUIVO):
            if self.verifica(TipoToken.FIM_DE_LINHA):
                self.avanca()
                continue
            instrucoes.append(self.linha())
            self.pula_linhas()
        return instrucoes

    def expressao(self):
        expr = self.logica()
        if self.verifica(TipoToken.SE):
            self.avanca()
            condicao = self.expressao()
            self.consome(TipoToken.SENAO, "Esperado 'senao' no ternário")
            falso = self.expressao()
            return Ternario(expr, condicao, falso)
        return expr

    def logica(self):
        expr = self.comparacao()
        while self.verifica(TipoToken.E, TipoToken.OU):
            operador = self.avanca().tipo
            direita = self.comparacao()
            expr = Binario(expr, operador, direita)
        return expr

    def comparacao(self):
        expr = self.pipe()
        while self.verifica(TipoToken.IGUAL, TipoToken.DIFERENTE, TipoToken.MAIOR,
                           TipoToken.MENOR, TipoToken.MAIOR_IGUAL, TipoToken.MENOR_IGUAL,
                           TipoToken.INTERVALO):
            operador = self.avanca().tipo
            direita = self.pipe()
            expr = Binario(expr, operador, direita)
        return expr

    def pipe(self):
        expr = self.adicao()
        while self.verifica(TipoToken.PIPE):
            self.avanca()
            direita = self.unaria()
            expr = Binario(expr, TipoToken.PIPE, direita)
        return expr

    def adicao(self):
        expr = self.multiplicacao()
        while self.verifica(TipoToken.MAIS, TipoToken.MENOS):
            operador = self.avanca().tipo
            direita = self.multiplicacao()
            expr = Binario(expr, operador, direita)
        return expr

    def multiplicacao(self):
        expr = self.unaria()
        while self.verifica(TipoToken.VEZES, TipoToken.DIVIDIR, TipoToken.MOD):
            operador = self.avanca().tipo
            direita = self.unaria()
            expr = Binario(expr, operador, direita)
        return expr

    def unaria(self):
        if self.verifica(TipoToken.NAO):
            operador = self.avanca().tipo
            expr = self.unaria()
            return Unario(operador, expr)
        if self.verifica(TipoToken.MENOS):
            operador = self.avanca().tipo
            expr = self.unaria()
            return Unario(operador, expr)
        return self.chamada()

    def chamada(self):
        expr = self.primario()
        while True:
            if self.verifica(TipoToken.ABRE_PAREN):
                self.avanca()
                argumentos = []
                argumentos_nomeados = []
                if not self.verifica(TipoToken.FECHA_PAREN):
                    self._parse_um_arg(argumentos, argumentos_nomeados)
                    while self.verifica(TipoToken.VIRGULA):
                        self.avanca()
                        if self.verifica(TipoToken.FECHA_PAREN):
                            break
                        self._parse_um_arg(argumentos, argumentos_nomeados)
                self.consome(TipoToken.FECHA_PAREN, "Esperado ')' após argumentos")
                if isinstance(expr, Variavel):
                    expr = Chamada(expr.nome, argumentos, argumentos_nomeados)
                elif isinstance(expr, Membro):
                    expr = ChamadaMembro(expr.objeto, expr.nome, argumentos, argumentos_nomeados)
                elif isinstance(expr, Super):
                    expr = ChamadaMembro(expr, "_init", argumentos, argumentos_nomeados)
                else:
                    raise self.erro("Apenas funções nomeadas podem ser chamadas")
            elif self.verifica(TipoToken.ABRE_COLCHETE):
                self.avanca()
                indice = self.expressao()
                self.consome(TipoToken.FECHA_COLCHETE, "Esperado ']'")
                expr = Indexacao(expr, indice)
            elif self.verifica(TipoToken.PONTO):
                self.avanca()
                nome = self._consome_nome_membro()
                expr = Membro(expr, nome)
            else:
                break
        return expr

    def _parse_um_arg(self, argumentos, argumentos_nomeados):
        if self.verifica(TipoToken.IDENTIFICADOR):
            peek = self.tokens[self.atual + 1] if self.atual + 1 < len(self.tokens) else None
            if peek and peek.tipo == TipoToken.ATRIBUICAO:
                nome_tok = self.avanca()
                self.avanca()
                valor = self.expressao()
                argumentos_nomeados.append((nome_tok.valor, valor))
                return
        argumentos.append(self.expressao())

    def primario(self):
        if self.verifica(TipoToken.FUNCAO):
            return self.funcao_anonima()
        if self.verifica(TipoToken.NOVO):
            return self.novo_expr()
        if self.verifica(TipoToken.ESTE):
            self.avanca()
            return Este()
        if self.verifica(TipoToken.SUPER):
            self.avanca()
            return Super()
        if self.verifica(TipoToken.INTEIRO, TipoToken.FLUTUANTE):
            tok = self.avanca()
            return Numero(tok.valor)
        if self.verifica(TipoToken.TEXTO):
            tok = self.avanca()
            return Texto(tok.valor)
        if self.verifica(TipoToken.TEMPLET):
            tok = self.avanca()
            return self._montar_template(tok)
        if self.verifica(TipoToken.VERDADEIRO):
            self.avanca()
            return Booleano(True)
        if self.verifica(TipoToken.FALSO):
            self.avanca()
            return Booleano(False)
        if self.verifica(TipoToken.NADA):
            self.avanca()
            return Nada()
        if self.verifica(TipoToken.IDENTIFICADOR,
            TipoToken.INFO, TipoToken.AVISO, TipoToken.ERRO):
            tok = self.avanca()
            return Variavel(tok.valor)
        if self.verifica(TipoToken.ABRE_PAREN):
            self.avanca()
            expr = self.expressao()
            self.consome(TipoToken.FECHA_PAREN, "Esperado ')'")
            return expr
        if self.verifica(TipoToken.ABRE_COLCHETE):
            return self.lista()
        if self.verifica(TipoToken.ABRE_CHAVE):
            return self.dicionario()
        if self.verifica(TipoToken.LER):
            self.avanca()
            if not self.verifica(TipoToken.FIM_DE_LINHA, TipoToken.FIM_ARQUIVO, TipoToken.FECHA_PAREN):
                prompt = self.expressao()
                return Chamada("ler", [prompt])
            return Chamada("ler", [])
        raise self.erro(f"Expressão inválida: {self.token_atual().valor!r}")

    def novo_expr(self):
        self.consome(TipoToken.NOVO, "Esperado 'novo'")
        nome_tok = self.consome(TipoToken.IDENTIFICADOR, "Esperado nome da classe")
        self.consome(TipoToken.ABRE_PAREN, "Esperado '('")
        argumentos = []
        if not self.verifica(TipoToken.FECHA_PAREN):
            argumentos.append(self.expressao())
            while self.verifica(TipoToken.VIRGULA):
                self.avanca()
                argumentos.append(self.expressao())
        self.consome(TipoToken.FECHA_PAREN, "Esperado ')'")
        return Novo(nome_tok.valor, argumentos)

    def _montar_template(self, tok):
        partes = []
        for parte in tok.valor:
            if parte[0] == "texto":
                partes.append(Texto(parte[1]))
            else:
                _, expr_texto, expr_lin, expr_col = parte
                from src.lexer.lexer import Lexer
                sub_lexer = Lexer(expr_texto, self.nome_arquivo)
                sub_lexer.linha = expr_lin
                sub_lexer.coluna = expr_col
                sub_tokens = sub_lexer.tokenizar()
                sub_parser = Parser(sub_tokens, self.nome_arquivo)
                expr_node = sub_parser.expressao()
                partes.append(expr_node)
        if len(partes) == 1 and isinstance(partes[0], Texto):
            return partes[0]
        return Template(partes)

    def lista(self):
        self.consome(TipoToken.ABRE_COLCHETE, "Esperado '['")
        self.pula_linhas()
        if self.verifica(TipoToken.FECHA_COLCHETE):
            self.avanca()
            return ListaExpr([])
        primeiro = self.expressao()
        self.pula_linhas()
        if self.verifica(TipoToken.PARA):
            self.avanca()
            var_tok = self.consome(TipoToken.IDENTIFICADOR, "Esperado nome da variável")
            self.consome(TipoToken.EM, "Esperado 'em'")
            colecao = self.comparacao()
            filtro = None
            if self.verifica(TipoToken.SE):
                self.avanca()
                filtro = self.expressao()
            self.consome(TipoToken.FECHA_COLCHETE, "Esperado ']'")
            return ListaCompreensao(primeiro, var_tok.valor, colecao, filtro)
        elementos = [primeiro]
        while self.verifica(TipoToken.VIRGULA) or self.verifica(TipoToken.FIM_DE_LINHA):
            self.pula_linhas()
            if not self.verifica(TipoToken.VIRGULA):
                break
            self.avanca()
            self.pula_linhas()
            if self.verifica(TipoToken.FECHA_COLCHETE):
                break
            elementos.append(self.expressao())
            self.pula_linhas()
        self.pula_linhas()
        self.consome(TipoToken.FECHA_COLCHETE, "Esperado ']'")
        return ListaExpr(elementos)

    def dicionario(self):
        self.consome(TipoToken.ABRE_CHAVE, "Esperado '{'")
        self.pula_linhas()
        pares = {}
        if not self.verifica(TipoToken.FECHA_CHAVE):
            chave = self.chave_dicionario()
            self.consome(TipoToken.DOIS_PONTOS, "Esperado ':' após chave do dicionário")
            self.pula_linhas()
            valor = self.expressao()
            pares[chave] = valor
            self.pula_linhas()
            while self.verifica(TipoToken.VIRGULA):
                self.avanca()
                self.pula_linhas()
                if self.verifica(TipoToken.FECHA_CHAVE):
                    break
                chave = self.chave_dicionario()
                self.consome(TipoToken.DOIS_PONTOS, "Esperado ':' após chave do dicionário")
                self.pula_linhas()
                valor = self.expressao()
                pares[chave] = valor
                self.pula_linhas()
        self.pula_linhas()
        self.consome(TipoToken.FECHA_CHAVE, "Esperado '}'")
        return DicionarioExpr(pares)

    def _consome_nome_membro(self):
        if self.verifica(TipoToken.IDENTIFICADOR,
            TipoToken.FALAR, TipoToken.MOSTRAR, TipoToken.DIZER, TipoToken.ESCREVER,
            TipoToken.LER, TipoToken.LIMPAR, TipoToken.PAUSA,
            TipoToken.INFO, TipoToken.AVISO, TipoToken.ERRO,
            TipoToken.VERDADEIRO, TipoToken.FALSO, TipoToken.NADA,
            TipoToken.NOVO, TipoToken.ESTE, TipoToken.SUPER,
            TipoToken.METODO, TipoToken.CONSTRUTOR,
            TipoToken.RETORNAR, TipoToken.USAR, TipoToken.PARALELO,
            TipoToken.TENTAR, TipoToken.CAPTURAR,
            TipoToken.CORRESPONDER, TipoToken.CASO,
            TipoToken.CLASSE, TipoToken.EXTENDE,
            TipoToken.FUNCAO, TipoToken.FUNCAO_ASYNC, TipoToken.ESPERAR,
            TipoToken.GARANTIR,
            TipoToken.ENQUANTO,
            TipoToken.PARA, TipoToken.ATE, TipoToken.EM,
            TipoToken.SE, TipoToken.SENAO):
            return self.avanca().valor
        raise self.erro("Esperado nome do membro")

    def chave_dicionario(self):
        if self.verifica(TipoToken.TEXTO):
            return self.avanca().valor
        if self.verifica(TipoToken.IDENTIFICADOR,
            TipoToken.FALAR, TipoToken.MOSTRAR, TipoToken.DIZER, TipoToken.ESCREVER,
            TipoToken.LER, TipoToken.LIMPAR, TipoToken.PAUSA,
            TipoToken.INFO, TipoToken.AVISO, TipoToken.ERRO,
            TipoToken.VERDADEIRO, TipoToken.FALSO, TipoToken.NADA,
            TipoToken.NOVO, TipoToken.ESTE, TipoToken.SUPER,
            TipoToken.METODO, TipoToken.CONSTRUTOR,
            TipoToken.RETORNAR, TipoToken.USAR, TipoToken.PARALELO,
            TipoToken.TENTAR, TipoToken.CAPTURAR,
            TipoToken.CORRESPONDER, TipoToken.CASO,
            TipoToken.CLASSE, TipoToken.EXTENDE,
            TipoToken.FUNCAO, TipoToken.FUNCAO_ASYNC, TipoToken.ESPERAR,
            TipoToken.GARANTIR,
            TipoToken.ENQUANTO,
            TipoToken.PARA, TipoToken.ATE, TipoToken.EM,
            TipoToken.SE, TipoToken.SENAO):
            return self.avanca().valor
        raise self.erro("Esperado chave do dicionário (texto ou identificador)")

    def corresponder_stmt(self):
        self.consome(TipoToken.CORRESPONDER, "Esperado 'corresponder'")
        valor = self.expressao()
        self.consome(TipoToken.FIM_DE_LINHA, "Esperado nova linha após 'corresponder'")
        casos = []
        while not self.verifica(TipoToken.FIM, TipoToken.FIM_ARQUIVO):
            self.pula_linhas()
            if self.verifica(TipoToken.FIM, TipoToken.FIM_ARQUIVO):
                break
            self.consome(TipoToken.CASO, "Esperado 'caso' dentro de corresponder")
            padrao = self.expressao()
            self.consome(TipoToken.FIM_DE_LINHA, "Esperado nova linha após padrão do caso")
            corpo = []
            self.pula_linhas()
            while not self.verifica(TipoToken.CASO, TipoToken.FIM, TipoToken.FIM_ARQUIVO):
                if self.verifica(TipoToken.FIM_DE_LINHA):
                    self.avanca()
                    continue
                corpo.append(self.linha())
                self.pula_linhas()
            casos.append(Caso(padrao, corpo))
        self.consome(TipoToken.FIM, "Esperado 'fim' para fechar corresponder")
        return Corresponder(valor, casos)

    def classe_stmt(self):
        self.consome(TipoToken.CLASSE, "Esperado 'classe'")
        nome_tok = self.consome(TipoToken.IDENTIFICADOR, "Esperado nome da classe")
        nome = nome_tok.valor
        base = None
        if self.verifica(TipoToken.EXTENDE):
            self.avanca()
            base_tok = self.consome(TipoToken.IDENTIFICADOR, "Esperado nome da classe base")
            base = base_tok.valor
        self.consome(TipoToken.FIM_DE_LINHA, "Esperado nova linha após declaração da classe")
        construtor = None
        metodos = []
        while not self.verifica(TipoToken.FIM, TipoToken.FIM_ARQUIVO):
            self.pula_linhas()
            if self.verifica(TipoToken.FIM, TipoToken.FIM_ARQUIVO):
                break
            if self.verifica(TipoToken.CONSTRUTOR):
                self.avanca()
                params, corpo = self._parse_params_e_corpo()
                construtor = Funcao("_init", params, corpo)
            elif self.verifica(TipoToken.METODO):
                self.avanca()
                nome_m = self._consome_nome_membro()
                params, corpo = self._parse_params_e_corpo()
                metodos.append(Funcao(nome_m, params, corpo))
            else:
                break
        self.consome(TipoToken.FIM, "Esperado 'fim' para fechar classe")
        return Classe(nome, construtor, metodos, base)

    def metodo_stmt(self):
        self.consome(TipoToken.METODO, "Esperado 'metodo'")
        nome_m = self._consome_nome_membro()
        params, corpo = self._parse_params_e_corpo()
        return Funcao(nome_m, params, corpo)

    def construtor_stmt(self):
        self.consome(TipoToken.CONSTRUTOR, "Esperado 'construtor'")
        params, corpo = self._parse_params_e_corpo()
        return Funcao("_init", params, corpo)
