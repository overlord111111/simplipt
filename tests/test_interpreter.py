import unittest
import sys
import io
from src.lexer.lexer import Lexer
from src.parser.parser import Parser
from src.interpreter.interpreter import Interpreter
from src.erros import ErroRuntime


def executa(codigo, entrada=""):
    lexer = Lexer(codigo + "\n")
    tokens = lexer.tokenizar()
    parser = Parser(tokens)
    ast = parser.programa()
    interp = Interpreter()
    old_stdin = sys.stdin
    sys.stdin = io.StringIO(entrada)
    try:
        resultado = interp.interpretar(ast)
        return resultado, interp
    finally:
        sys.stdin = old_stdin


def executa_captura(codigo, entrada=""):
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        resultado, interp = executa(codigo, entrada)
        saida = sys.stdout.getvalue()
        return saida, resultado, interp
    finally:
        sys.stdout = old_stdout


class TestInterpreter(unittest.TestCase):
    def test_atribuicao_e_variavel(self):
        _, interp = executa("x = 42")
        self.assertEqual(interp.global_env.obter("x"), 42)

    def test_falar(self):
        saida, _, _ = executa_captura('falar "teste"')
        self.assertIn("teste", saida)

    def test_mostrar_alias(self):
        saida, _, _ = executa_captura('mostrar "alias"')
        self.assertIn("alias", saida)

    def test_ler_com_prompt(self):
        saida, resultado, _ = executa_captura('ler "nome: "', entrada="Jarbs\n")
        self.assertEqual(resultado, "Jarbs")

    def test_limpar(self):
        saida, _, _ = executa_captura("limpar")
        self.assertIsNotNone(saida)

    def test_pausa(self):
        saida, _, _ = executa_captura("pausa 0.01")
        self.assertIsNotNone(saida)

    def test_se_verdadeiro(self):
        saida, _, _ = executa_captura("se verdadeiro\nfalar 1\nfim")
        self.assertIn("1", saida)

    def test_se_falso(self):
        saida, _, _ = executa_captura("se falso\nfalar 1\nsenao\nfalar 2\nfim")
        self.assertNotIn("1", saida)
        self.assertIn("2", saida)

    def test_para_ate(self):
        saida, _, _ = executa_captura("para i ate 3\nfalar i\nfim")
        for n in ["1", "2", "3"]:
            self.assertIn(n, saida)

    def test_para_em(self):
        saida, _, _ = executa_captura("para item em [10,20]\nfalar item\nfim")
        self.assertIn("10", saida)
        self.assertIn("20", saida)

    def test_enquanto(self):
        saida, _, _ = executa_captura("x = 1\nenquanto x <= 3\nfalar x\nx = x + 1\nfim")
        for n in ["1", "2", "3"]:
            self.assertIn(n, saida)

    def test_funcao_sem_retorno(self):
        _, interp = executa("funcao ola()\nfalar 1\nfim")
        fn = interp.global_env.obter("ola")
        self.assertIsNotNone(fn)

    def test_funcao_com_retorno(self):
        _, interp = executa("funcao soma(a, b)\nretornar a + b\nfim")
        fn = interp.global_env.obter("soma")
        self.assertIsNotNone(fn)

    def test_chamada_funcao(self):
        saida, _, _ = executa_captura(
            'funcao saudacao(nome)\nfalar "ola " + nome\nfim\nsaudacao("Jarbs")'
        )
        self.assertIn("ola Jarbs", saida)

    def test_retorno_valor(self):
        codigo = "funcao soma(a, b)\nretornar a + b\nfim\nresultado = soma(3, 4)"
        _, interp = executa(codigo)
        self.assertEqual(interp.global_env.obter("resultado"), 7)

    def test_operadores_aritmeticos(self):
        _, interp = executa("x = 10 + 5 * 2")
        self.assertEqual(interp.global_env.obter("x"), 20)

    def test_operador_mais_texto(self):
        _, interp = executa('x = "a" + "b"')
        self.assertEqual(interp.global_env.obter("x"), "ab")

    def test_operadores_comparacao(self):
        _, interp = executa("x = 5 é 5\ny = 5 nao é 3\nz = 5 > 3")
        self.assertTrue(interp.global_env.obter("x"))
        self.assertTrue(interp.global_env.obter("y"))
        self.assertTrue(interp.global_env.obter("z"))

    def test_operadores_logicos(self):
        _, interp = executa("x = verdadeiro e verdadeiro\ny = falso ou verdadeiro\nz = nao falso")
        self.assertTrue(interp.global_env.obter("x"))
        self.assertTrue(interp.global_env.obter("y"))
        self.assertTrue(interp.global_env.obter("z"))

    def test_lista(self):
        _, interp = executa("x = [1, 2, 3]")
        self.assertEqual(interp.global_env.obter("x"), [1, 2, 3])

    def test_dicionario(self):
        _, interp = executa('x = { nome: "Jarbs", idade: 27 }')
        d = interp.global_env.obter("x")
        self.assertEqual(d["nome"], "Jarbs")
        self.assertEqual(d["idade"], 27)

    def test_indexacao(self):
        _, interp = executa("x = [10, 20][1]")
        self.assertEqual(interp.global_env.obter("x"), 20)

    def test_membro_dict(self):
        _, interp = executa('x = { a: 1 }\ny = x.a')
        self.assertEqual(interp.global_env.obter("y"), 1)

    def test_usar_modulo(self):
        _, interp = executa("usar sistema")
        sistema = interp.global_env.obter("sistema")
        self.assertIsInstance(sistema, dict)
        self.assertIn("info", sistema)

    def test_variavel_nao_definida(self):
        with self.assertRaises(ErroRuntime):
            executa("x = y")

    def test_paralelo(self):
        saida, _, _ = executa_captura("paralelo\nfalar 1\nfalar 2\nfim")
        self.assertIn("1", saida)
        self.assertIn("2", saida)

    def test_intervalo_builtin(self):
        _, interp = executa("x = intervalo(3)")
        self.assertEqual(interp.global_env.obter("x"), [1, 2, 3])

    def test_para_em_intervalo(self):
        saida, _, _ = executa_captura("para i em intervalo(3)\nfalar i\nfim")
        for n in ["1", "2", "3"]:
            self.assertIn(n, saida)

    def test_escopo_funcao(self):
        _, interp = executa("x = 1\nfuncao teste()\nx = 2\nfim\nteste()")
        self.assertEqual(interp.global_env.obter("x"), 1)

    def test_nada(self):
        _, interp = executa("x = nada")
        self.assertIsNone(interp.global_env.obter("x"))

    def test_booleano_atribuicao(self):
        _, interp = executa("x = verdadeiro\ny = falso")
        self.assertTrue(interp.global_env.obter("x"))
        self.assertFalse(interp.global_env.obter("y"))

    def test_tentar_captura_erro(self):
        saida, _, _ = executa_captura("tentar\nfalar 1/0\ncapturar\nfalar \"erro\"\nfim")
        self.assertIn("erro", saida)

    def test_tentar_sem_erro(self):
        saida, _, _ = executa_captura("tentar\nfalar \"ok\"\ncapturar\nfalar \"erro\"\nfim")
        self.assertIn("ok", saida)
        self.assertNotIn("erro", saida)

    def test_intervalo_operator(self):
        _, interp = executa("x = 1..5")
        self.assertEqual(interp.global_env.obter("x"), [1, 2, 3, 4, 5])

    def test_para_em_intervalo_operator(self):
        saida, _, _ = executa_captura("para i em 1..3\nfalar i\nfim")
        for n in ["1", "2", "3"]:
            self.assertIn(n, saida)

    def test_info_log(self):
        saida, _, _ = executa_captura('info "teste"')
        self.assertIn("[INFO]", saida)
        self.assertIn("teste", saida)

    def test_aviso_log(self):
        saida, _, _ = executa_captura('aviso "aviso"')
        self.assertIn("[AVISO]", saida)

    def test_erro_log(self):
        saida, _, _ = executa_captura('erro "falhou"')
        self.assertIn("[ERRO]", saida)

    def test_atribuicao_membro_dict(self):
        _, interp = executa("obj = {}\nobj.chave = 42\nx = obj.chave")
        self.assertEqual(interp.global_env.obter("x"), 42)

    def test_modulo_spt(self):
        import tempfile, os
        mod = 'funcao dobra(n)\nretornar n * 2\nfim\n'
        with tempfile.NamedTemporaryFile(suffix='.spt', mode='w', delete=False, encoding='utf-8') as f:
            f.write(mod)
            mod_path = f.name
        mod_nome = os.path.splitext(os.path.basename(mod_path))[0]
        try:
            codigo = f'usar {mod_nome}\nresultado = {mod_nome}.dobra(5)\n'
            from src.lexer.lexer import Lexer
            from src.parser.parser import Parser
            lexer = Lexer(codigo + "\n")
            tokens = lexer.tokenizar()
            parser = Parser(tokens)
            ast = parser.programa()
            interp = Interpreter()
            old_cwd = os.getcwd()
            os.chdir(os.path.dirname(mod_path))
            try:
                interp.interpretar(ast)
            finally:
                os.chdir(old_cwd)
            self.assertEqual(interp.global_env.obter("resultado"), 10)
        finally:
            os.unlink(mod_path)


if __name__ == "__main__":
    unittest.main()
