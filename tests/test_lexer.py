import unittest
from src.lexer.token import TipoToken
from src.lexer.lexer import Lexer
from src.erros import ErroLexico


class TestLexer(unittest.TestCase):
    def tokeniza(self, texto):
        lexer = Lexer(texto)
        return [t for t in lexer.tokenizar() if t.tipo != TipoToken.FIM_ARQUIVO]

    def test_numeros_inteiros(self):
        tokens = self.tokeniza("42")
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].tipo, TipoToken.INTEIRO)
        self.assertEqual(tokens[0].valor, 42)

    def test_numeros_flutuantes(self):
        tokens = self.tokeniza("3.14")
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].tipo, TipoToken.FLUTUANTE)
        self.assertEqual(tokens[0].valor, 3.14)

    def test_texto_aspas_duplas(self):
        tokens = self.tokeniza('"ola"')
        self.assertEqual(tokens[0].tipo, TipoToken.TEXTO)
        self.assertEqual(tokens[0].valor, "ola")

    def test_texto_aspas_simples(self):
        tokens = self.tokeniza("'mundo'")
        self.assertEqual(tokens[0].tipo, TipoToken.TEXTO)
        self.assertEqual(tokens[0].valor, "mundo")

    def test_texto_escapado(self):
        tokens = self.tokeniza('"linha1\\nlinha2"')
        self.assertEqual(tokens[0].valor, "linha1\nlinha2")

    def test_identificador(self):
        tokens = self.tokeniza("variavel")
        self.assertEqual(tokens[0].tipo, TipoToken.IDENTIFICADOR)
        self.assertEqual(tokens[0].valor, "variavel")

    def test_palavras_reservadas(self):
        casos = [
            ("verdadeiro", TipoToken.VERDADEIRO),
            ("falso", TipoToken.FALSO),
            ("nada", TipoToken.NADA),
            ("se", TipoToken.SE),
            ("senao", TipoToken.SENAO),
            ("para", TipoToken.PARA),
            ("ate", TipoToken.ATE),
            ("em", TipoToken.EM),
            ("enquanto", TipoToken.ENQUANTO),
            ("funcao", TipoToken.FUNCAO),
            ("retornar", TipoToken.RETORNAR),
            ("usar", TipoToken.USAR),
            ("paralelo", TipoToken.PARALELO),
            ("fim", TipoToken.FIM),
            ("e", TipoToken.E),
            ("ou", TipoToken.OU),
            ("nao", TipoToken.NAO),
            ("é", TipoToken.IGUAL),
        ]
        for texto, esperado in casos:
            tokens = self.tokeniza(texto)
            self.assertEqual(tokens[0].tipo, esperado, f"Falhou para '{texto}'")

    def test_aliases_comandos(self):
        casos = [
            ("falar", TipoToken.FALAR),
            ("mostrar", TipoToken.MOSTRAR),
            ("dizer", TipoToken.DIZER),
            ("escrever", TipoToken.ESCREVER),
            ("ler", TipoToken.LER),
            ("limpar", TipoToken.LIMPAR),
            ("pausa", TipoToken.PAUSA),
        ]
        for texto, esperado in casos:
            tokens = self.tokeniza(texto)
            self.assertEqual(tokens[0].tipo, esperado, f"Falhou para '{texto}'")

    def test_operadores(self):
        casos = [
            ("+", TipoToken.MAIS),
            ("-", TipoToken.MENOS),
            ("*", TipoToken.VEZES),
            ("/", TipoToken.DIVIDIR),
            ("%", TipoToken.MOD),
            (">", TipoToken.MAIOR),
            ("<", TipoToken.MENOR),
            ("=", TipoToken.ATRIBUICAO),
            ("(", TipoToken.ABRE_PAREN),
            (")", TipoToken.FECHA_PAREN),
            ("[", TipoToken.ABRE_COLCHETE),
            ("]", TipoToken.FECHA_COLCHETE),
            ("{", TipoToken.ABRE_CHAVE),
            ("}", TipoToken.FECHA_CHAVE),
            (",", TipoToken.VIRGULA),
            (".", TipoToken.PONTO),
            (":", TipoToken.DOIS_PONTOS),
        ]
        for texto, esperado in casos:
            tokens = self.tokeniza(texto)
            self.assertEqual(tokens[0].tipo, esperado, f"Falhou para '{texto}'")

    def test_maior_igual(self):
        tokens = self.tokeniza(">=")
        self.assertEqual(tokens[0].tipo, TipoToken.MAIOR_IGUAL)

    def test_menor_igual(self):
        tokens = self.tokeniza("<=")
        self.assertEqual(tokens[0].tipo, TipoToken.MENOR_IGUAL)

    def test_nao_e_diferente(self):
        tokens = self.tokeniza("nao é")
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].tipo, TipoToken.DIFERENTE)
        self.assertEqual(tokens[0].valor, "nao é")

    def test_nao_sozinho(self):
        tokens = self.tokeniza("nao verdadeiro")
        self.assertEqual(len(tokens), 2)
        self.assertEqual(tokens[0].tipo, TipoToken.NAO)
        self.assertEqual(tokens[1].tipo, TipoToken.VERDADEIRO)

    def test_comentario_linha(self):
        lexer = Lexer("# comentario\n42")
        tokens = [t for t in lexer.tokenizar() if t.tipo not in (TipoToken.FIM_ARQUIVO, TipoToken.FIM_DE_LINHA)]
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].tipo, TipoToken.INTEIRO)
        self.assertEqual(tokens[0].valor, 42)

    def test_comentario_bloco(self):
        tokens = self.tokeniza("%% comentario %% 42")
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].tipo, TipoToken.INTEIRO)

    def test_modulo_operador(self):
        tokens = self.tokeniza("10 % 3")
        self.assertTrue(any(t.tipo == TipoToken.MOD for t in tokens))

    def test_ponto_virgula_ignorado(self):
        tokens = self.tokeniza("a = 1;")
        self.assertTrue(any(t.tipo == TipoToken.IDENTIFICADOR for t in tokens))
        self.assertTrue(any(t.tipo == TipoToken.ATRIBUICAO for t in tokens))
        self.assertTrue(any(t.tipo == TipoToken.INTEIRO for t in tokens))

    def test_fim_de_linha(self):
        lexer = Lexer("1\n2")
        tokens = lexer.tokenizar()
        tipos = [t.tipo for t in tokens]
        self.assertIn(TipoToken.FIM_DE_LINHA, tipos)

    def test_string_nao_fechada(self):
        with self.assertRaises(ErroLexico):
            self.tokeniza('"incompleto')

    def test_caractere_invalido(self):
        with self.assertRaises(ErroLexico):
            self.tokeniza("@")

    def test_comentario_bloco_nao_fechado(self):
        with self.assertRaises(ErroLexico):
            self.tokeniza("%% sem fechar")

    def test_intervalo_operator(self):
        tokens = self.tokeniza("1..5")
        tipos = [t.tipo for t in tokens]
        self.assertEqual(tipos, [TipoToken.INTEIRO, TipoToken.INTERVALO, TipoToken.INTEIRO])

    def test_tentar(self):
        tokens = self.tokeniza("tentar")
        self.assertEqual(tokens[0].tipo, TipoToken.TENTAR)

    def test_capturar(self):
        tokens = self.tokeniza("capturar")
        self.assertEqual(tokens[0].tipo, TipoToken.CAPTURAR)

    def test_info(self):
        tokens = self.tokeniza('info "teste"')
        self.assertEqual(tokens[0].tipo, TipoToken.INFO)

    def test_aviso(self):
        tokens = self.tokeniza('aviso "teste"')
        self.assertEqual(tokens[0].tipo, TipoToken.AVISO)

    def test_erro(self):
        tokens = self.tokeniza('erro "teste"')
        self.assertEqual(tokens[0].tipo, TipoToken.ERRO)


if __name__ == "__main__":
    unittest.main()
