import unittest
from src.lexer.lexer import Lexer
from src.lexer.token import TipoToken
from src.parser.parser import Parser
from src.parser.ast import *
from src.erros import ErroSintaxe


def parse(texto):
    lexer = Lexer(texto + "\n")
    tokens = lexer.tokenizar()
    parser = Parser(tokens)
    return parser.programa()


class TestParser(unittest.TestCase):
    def test_programa_vazio(self):
        ast = parse("")
        self.assertIsInstance(ast, Programa)
        self.assertEqual(len(ast.nodes), 0)

    def test_atribuicao_numero(self):
        ast = parse("x = 42")
        self.assertIsInstance(ast.nodes[0], Atribuicao)
        self.assertEqual(ast.nodes[0].nome, "x")
        self.assertIsInstance(ast.nodes[0].valor, Numero)
        self.assertEqual(ast.nodes[0].valor.valor, 42)

    def test_atribuicao_texto(self):
        ast = parse('nome = "Jarbs"')
        self.assertIsInstance(ast.nodes[0].valor, Texto)
        self.assertEqual(ast.nodes[0].valor.valor, "Jarbs")

    def test_falar(self):
        ast = parse('falar "oi"')
        self.assertIsInstance(ast.nodes[0], Falar)
        self.assertIsInstance(ast.nodes[0].expressao, Texto)

    def test_mostrar_alias(self):
        ast = parse('mostrar "oi"')
        self.assertIsInstance(ast.nodes[0], Falar)

    def test_ler_sem_prompt(self):
        ast = parse("ler")
        self.assertIsInstance(ast.nodes[0], Ler)
        self.assertIsNone(ast.nodes[0].prompt)

    def test_ler_com_prompt(self):
        ast = parse('ler "nome: "')
        self.assertIsInstance(ast.nodes[0], Ler)
        self.assertIsNotNone(ast.nodes[0].prompt)

    def test_limpar(self):
        ast = parse("limpar")
        self.assertIsInstance(ast.nodes[0], Limpar)

    def test_pausa(self):
        ast = parse("pausa 5")
        self.assertIsInstance(ast.nodes[0], Pausa)
        self.assertIsInstance(ast.nodes[0].tempo, Numero)

    def test_se_sem_senao(self):
        ast = parse("se verdadeiro\nfalar 1\nfim")
        self.assertIsInstance(ast.nodes[0], Se)
        self.assertIsNone(ast.nodes[0].senao)

    def test_se_com_senao(self):
        ast = parse("se falso\nfalar 1\nsenao\nfalar 2\nfim")
        self.assertIsInstance(ast.nodes[0], Se)
        self.assertIsNotNone(ast.nodes[0].senao)

    def test_para_ate(self):
        ast = parse("para i ate 10\nfalar i\nfim")
        self.assertIsInstance(ast.nodes[0], ParaAte)
        self.assertEqual(ast.nodes[0].var, "i")
        self.assertIsInstance(ast.nodes[0].ate, Numero)

    def test_para_em(self):
        ast = parse("para item em [1,2]\nfalar item\nfim")
        self.assertIsInstance(ast.nodes[0], ParaEm)
        self.assertEqual(ast.nodes[0].var, "item")

    def test_enquanto(self):
        ast = parse("enquanto verdadeiro\npausa 1\nfim")
        self.assertIsInstance(ast.nodes[0], Enquanto)

    def test_funcao_sem_params(self):
        ast = parse("funcao ola()\nfalar 1\nfim")
        self.assertIsInstance(ast.nodes[0], Funcao)
        self.assertEqual(ast.nodes[0].nome, "ola")
        self.assertEqual(ast.nodes[0].params, [])

    def test_funcao_com_params(self):
        ast = parse("funcao soma(a, b)\nretornar a + b\nfim")
        self.assertIsInstance(ast.nodes[0], Funcao)
        self.assertEqual(ast.nodes[0].nome, "soma")
        self.assertEqual(ast.nodes[0].params, ["a", "b"])

    def test_chamada_funcao(self):
        ast = parse('saudacao("Jarbs")')
        self.assertIsInstance(ast.nodes[0], Chamada)
        self.assertEqual(ast.nodes[0].nome, "saudacao")
        self.assertEqual(len(ast.nodes[0].argumentos), 1)

    def test_chamada_membro(self):
        ast = parse("sistema.info()")
        self.assertIsInstance(ast.nodes[0], ChamadaMembro)
        self.assertEqual(ast.nodes[0].nome, "info")

    def test_retornar_sem_valor(self):
        ast = parse("retornar")
        self.assertIsInstance(ast.nodes[0], Retornar)
        self.assertIsNone(ast.nodes[0].valor)

    def test_retornar_com_valor(self):
        ast = parse("retornar 42")
        self.assertIsInstance(ast.nodes[0], Retornar)
        self.assertIsInstance(ast.nodes[0].valor, Numero)

    def test_paralelo(self):
        ast = parse("paralelo\nfalar 1\nfalar 2\nfim")
        self.assertIsInstance(ast.nodes[0], Paralelo)
        self.assertEqual(len(ast.nodes[0].corpo), 2)

    def test_usar(self):
        ast = parse("usar json")
        self.assertIsInstance(ast.nodes[0], Usar)
        self.assertEqual(ast.nodes[0].modulo, "json")

    def test_expressao_binaria(self):
        ast = parse("x = 1 + 2")
        expr = ast.nodes[0].valor
        self.assertIsInstance(expr, Binario)
        self.assertEqual(expr.operador, TipoToken.MAIS)

    def test_expressao_comparacao(self):
        ast = parse("x = a é b")
        expr = ast.nodes[0].valor
        self.assertIsInstance(expr, Binario)
        self.assertEqual(expr.operador, TipoToken.IGUAL)

    def test_expressao_logica(self):
        ast = parse("x = a e b")
        expr = ast.nodes[0].valor
        self.assertIsInstance(expr, Binario)
        self.assertEqual(expr.operador, TipoToken.E)

    def test_expressao_unaria(self):
        ast = parse("x = nao verdadeiro")
        expr = ast.nodes[0].valor
        self.assertIsInstance(expr, Unario)
        self.assertEqual(expr.operador, TipoToken.NAO)

    def test_lista(self):
        ast = parse("x = [1, 2, 3]")
        expr = ast.nodes[0].valor
        self.assertIsInstance(expr, ListaExpr)
        self.assertEqual(len(expr.elementos), 3)

    def test_dicionario(self):
        ast = parse('x = { nome: "Jarbs" }')
        expr = ast.nodes[0].valor
        self.assertIsInstance(expr, DicionarioExpr)
        self.assertIn("nome", expr.pares)

    def test_indexacao(self):
        ast = parse("x = lista[0]")
        expr = ast.nodes[0].valor
        self.assertIsInstance(expr, Indexacao)

    def test_membro(self):
        ast = parse("x = pessoa.nome")
        expr = ast.nodes[0].valor
        self.assertIsInstance(expr, Membro)
        self.assertEqual(expr.nome, "nome")

    def test_parenteses(self):
        ast = parse("x = (1 + 2) * 3")
        expr = ast.nodes[0].valor
        self.assertIsInstance(expr, Binario)
        self.assertEqual(expr.operador, TipoToken.VEZES)

    def test_nada(self):
        ast = parse("x = nada")
        self.assertIsInstance(ast.nodes[0].valor, Nada)

    def test_booleano(self):
        ast = parse("x = verdadeiro\ny = falso")
        self.assertIsInstance(ast.nodes[0].valor, Booleano)
        self.assertTrue(ast.nodes[0].valor.valor)
        self.assertIsInstance(ast.nodes[1].valor, Booleano)
        self.assertFalse(ast.nodes[1].valor.valor)

    def test_ler_em_atribuicao(self):
        ast = parse('nome = ler "nome: "')
        self.assertIsInstance(ast.nodes[0], Atribuicao)
        expr = ast.nodes[0].valor
        self.assertIsInstance(expr, Chamada)
        self.assertEqual(expr.nome, "ler")

    def test_erro_sintatico(self):
        with self.assertRaises(ErroSintaxe):
            parse("se erro")

    def test_tentar_capturar(self):
        ast = parse("tentar\nfalar 1\ncapturar\nfalar 2\nfim")
        self.assertIsInstance(ast.nodes[0], Tentar)
        self.assertEqual(len(ast.nodes[0].corpo), 1)
        self.assertEqual(len(ast.nodes[0].capturar), 1)

    def test_log_info(self):
        ast = parse('info "msg"')
        self.assertIsInstance(ast.nodes[0], Log)
        self.assertEqual(ast.nodes[0].nivel, "info")

    def test_log_aviso(self):
        ast = parse('aviso "msg"')
        self.assertIsInstance(ast.nodes[0], Log)
        self.assertEqual(ast.nodes[0].nivel, "aviso")

    def test_log_erro(self):
        ast = parse('erro "msg"')
        self.assertIsInstance(ast.nodes[0], Log)
        self.assertEqual(ast.nodes[0].nivel, "erro")

    def test_atribuicao_membro(self):
        ast = parse('config.chave = "valor"')
        self.assertIsInstance(ast.nodes[0], AtribuicaoMembro)
        self.assertEqual(ast.nodes[0].nome, "chave")
        self.assertIsInstance(ast.nodes[0].valor, Texto)

    def test_intervalo_operator(self):
        ast = parse("x = 1..5")
        expr = ast.nodes[0].valor
        self.assertIsInstance(expr, Binario)
        self.assertEqual(expr.operador, TipoToken.INTERVALO)

    def test_para_em_intervalo(self):
        ast = parse("para i em 1..5\nfalar i\nfim")
        self.assertIsInstance(ast.nodes[0], ParaEm)

    def test_chamada_membro_com_info(self):
        ast = parse("sistema.info()")
        self.assertIsInstance(ast.nodes[0], ChamadaMembro)


if __name__ == "__main__":
    unittest.main()
