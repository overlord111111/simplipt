import unittest
import sys
import os

from src.interpreter.interpreter import Interpreter
from src.lexer.lexer import Lexer
from src.parser.parser import Parser


def executa(codigo):
    interp = Interpreter()
    lex = Lexer(codigo)
    toks = lex.tokenizar()
    par = Parser(toks)
    ast = par.programa()
    return interp.interpretar(ast)


class TestTemplate(unittest.TestCase):
    def test_template_simples(self):
        executa('nome = "Jarbs"')
        r = executa('nome = "Jarbs"\nmsg = "ola {nome}"\nretornar msg\n')
        self.assertEqual(r, "ola Jarbs")

    def test_template_multiplo(self):
        r = executa('a = "x"; b = "y"\nmsg = "{a} e {b}"\nretornar msg\n')
        self.assertEqual(r, "x e y")

    def test_template_sem_interpolacao(self):
        r = executa('msg = "ola mundo"\nretornar msg\n')
        self.assertEqual(r, "ola mundo")

    def test_template_expressao(self):
        r = executa('msg = "resultado: {2 + 3}"\nretornar msg\n')
        self.assertEqual(r, "resultado: 5")


class TestPipe(unittest.TestCase):
    def test_pipe_funcao_usuario(self):
        r = executa('''
dobro = funcao(x)
    retornar x * 2
fim
r = 5 |> dobro
retornar r
''')
        self.assertEqual(r, 10)

    def test_pipe_encadeado(self):
        r = executa('''
dobro = funcao(x)
    retornar x * 2
fim
mais3 = funcao(x)
    retornar x + 3
fim
r = 5 |> dobro |> mais3
retornar r
''')
        self.assertEqual(r, 13)


class TestListCompreensao(unittest.TestCase):
    def test_simples(self):
        r = executa('nums = [x * 2 para x em [1, 2, 3]]\nretornar nums\n')
        self.assertEqual(r, [2, 4, 6])

    def test_com_filtro(self):
        r = executa('nums = [x para x em [1, 2, 3, 4, 5] se x > 3]\nretornar nums\n')
        self.assertEqual(r, [4, 5])

    def test_vazia(self):
        r = executa('nums = []\nretornar nums\n')
        self.assertEqual(r, [])


class TestCorresponder(unittest.TestCase):
    def test_caso_match(self):
        r = executa('''
valor = 2
corresponder valor
    caso 1
        retornar "um"
    caso 2
        retornar "dois"
fim
''')
        self.assertEqual(r, "dois")

    def test_sem_match(self):
        r = executa('''
valor = 99
corresponder valor
    caso 1
        retornar "um"
    caso 2
        retornar "dois"
fim
retornar "nada"
''')
        self.assertEqual(r, "nada")

    def test_caso_texto(self):
        r = executa('''
valor = "foo"
corresponder valor
    caso "bar"
        retornar "bar"
    caso "foo"
        retornar "foo encontrado"
fim
''')
        self.assertEqual(r, "foo encontrado")


class TestClasses(unittest.TestCase):
    def test_classe_simples(self):
        r = executa('''
classe Animal
    construtor(nome)
        este.nome = nome
    fim
    metodo falar()
        retornar "Oi, sou " + este.nome
    fim
fim
gato = novo Animal("Jarbs")
retornar gato.falar()
''')
        self.assertEqual(r, "Oi, sou Jarbs")

    def test_atributo_instancia(self):
        r = executa('''
classe Cachorro
    construtor(nome)
        este.nome = nome
    fim
fim
dog = novo Cachorro("Rex")
retornar dog.nome
''')
        self.assertEqual(r, "Rex")

    def test_heranca(self):
        r = executa('''
classe Animal
    construtor(nome)
        este.nome = nome
    fim
    metodo falar()
        retornar "Oi, sou " + este.nome
    fim
fim
classe Cachorro extende Animal
    construtor(nome, raca)
        super(nome)
        este.raca = raca
    fim
    metodo falar()
        retornar "Au au, sou " + este.nome + " da raca " + este.raca
    fim
fim
dog = novo Cachorro("Rex", "Vira-lata")
retornar dog.falar()
''')
        self.assertEqual(r, "Au au, sou Rex da raca Vira-lata")
