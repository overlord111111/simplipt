import os
import tempfile
import unittest
import json


class _Helper:
    def __init__(self):
        self.interp = None


def _executa(codigo, helper=None):
    from src.lexer.lexer import Lexer
    from src.parser.parser import Parser
    from src.interpreter.interpreter import Interpreter
    lex = Lexer(codigo)
    toks = lex.tokenizar()
    par = Parser(toks)
    ast = par.programa()
    interp = Interpreter()
    resultado = interp.interpretar(ast)
    if helper:
        helper.interp = interp
    return resultado


class TestTernario(unittest.TestCase):
    def test_verdadeiro(self):
        self.assertEqual(_executa("x = 1 se verdadeiro senao 2\nretornar x\n"), 1)

    def test_falso(self):
        self.assertEqual(_executa("x = 1 se falso senao 2\nretornar x\n"), 2)

    def test_membro_existe(self):
        r = _executa("d = {\"a\": 10}\nx = d.a se d.a senao 0\nretornar x\n")
        self.assertEqual(r, 10)

    def test_membro_ausente(self):
        r = _executa("d = {}\nx = d.a se d.a senao 99\nretornar x\n")
        self.assertEqual(r, 99)

    def test_em_retorno(self):
        self.assertEqual(_executa("retornar 1 se 5 > 3 senao 0\n"), 1)

    def test_em_falar(self):
        import io, sys
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            _executa("falar 1 se verdadeiro senao 2\n")
        finally:
            sys.stdout = old
        self.assertIn("1", buf.getvalue())

    def test_em_atribuicao(self):
        self.assertEqual(_executa("x = 10 se 5 > 3 senao 0\nretornar x\n"), 10)

    def test_em_chamada(self):
        r = _executa("fn dobro(n)\n    retornar n * 2\nfim\n"
                      "x = dobro(5 se verdadeiro senao 0)\nretornar x\n")
        self.assertEqual(r, 10)

    def test_em_lista(self):
        r = _executa("x = [1 se falso senao 2, 3 se verdadeiro senao 4]\nretornar x\n")
        self.assertEqual(r, [2, 3])

    def test_em_listcomp(self):
        r = _executa("x = [n se n > 1 senao 0 para n em [0,1,2,3]]\nretornar x\n")
        self.assertEqual(r, [0, 0, 2, 3])

    def test_aninhado(self):
        r = _executa("x = 1 se 5 > 3 se 2 > 1 senao 0 senao 0\nretornar x\n")
        self.assertEqual(r, 1)

    def test_em_dicionario(self):
        r = _executa("x = {\"v\": 10 se verdadeiro senao 0}\nretornar x.v\n")
        self.assertEqual(r, 10)


class TestTemplate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp()
        from src.stdlib.template import MODULO as tmpl
        tmpl.diretorio(cls.tmpdir)

    def _criar(self, nome, conteudo):
        with open(os.path.join(self.tmpdir, nome), "w", encoding="utf-8") as f:
            f.write(conteudo)

    def test_simples(self):
        self._criar("t.html", "<h1>{{ titulo }}</h1>")
        from src.stdlib.template import MODULO as tmpl
        self.assertEqual(tmpl.renderizar("t.html", {"titulo": "Ola"}), "<h1>Ola</h1>")

    def test_multi(self):
        self._criar("t2.html", "{{a}} {{b}}")
        from src.stdlib.template import MODULO as tmpl
        self.assertEqual(tmpl.renderizar("t2.html", {"a": "x", "b": "y"}), "x y")

    def test_se_true(self):
        self._criar("t3.html", "{% se ativo %}ON{% fim %}")
        from src.stdlib.template import MODULO as tmpl
        self.assertEqual(tmpl.renderizar("t3.html", {"ativo": True}), "ON")

    def test_se_false(self):
        self._criar("t4.html", "{% se ativo %}ON{% fim %}")
        from src.stdlib.template import MODULO as tmpl
        self.assertEqual(tmpl.renderizar("t4.html", {"ativo": False}), "")

    def test_se_senao(self):
        self._criar("t5.html", "{% se ok %}SIM{% senao %}NAO{% fim %}")
        from src.stdlib.template import MODULO as tmpl
        self.assertEqual(tmpl.renderizar("t5.html", {"ok": True}), "SIM")
        self.assertEqual(tmpl.renderizar("t5.html", {"ok": False}), "NAO")

    def test_para(self):
        self._criar("t6.html", "{% para x em itens %}({{ x }}){% fim %}")
        from src.stdlib.template import MODULO as tmpl
        self.assertEqual(tmpl.renderizar("t6.html", {"itens": ["A", "B"]}), "(A)(B)")

    def test_dict_acesso(self):
        self._criar("t7.html", "{{ u.nome }}")
        from src.stdlib.template import MODULO as tmpl
        self.assertEqual(tmpl.renderizar("t7.html", {"u": {"nome": "J"}}), "J")

    def test_var_ausente(self):
        self._criar("t8.html", "{% se xyz %}X{% fim %}")
        from src.stdlib.template import MODULO as tmpl
        self.assertEqual(tmpl.renderizar("t8.html", {}), "")

    def test_aninhado(self):
        self._criar("t9.html", (
            "{% se items %}"
            "{% para i em items %}"
            "{% se i.a %}{{ i.n }}{% fim %}"
            "{% fim %}"
            "{% fim %}"
        ))
        from src.stdlib.template import MODULO as tmpl
        html = tmpl.renderizar("t9.html", {
            "items": [{"n": "A", "a": True}, {"n": "B", "a": False}, {"n": "C", "a": True}]
        })
        self.assertEqual(html, "AC")


class TestServidorExpandido(unittest.TestCase):
    def _setup_servidor(self, port, codigo_pre):
        codigo = "usar servidor\nservidor.limpar()\n" + codigo_pre + f"falar servidor.iniciar({port})\n"
        h = _Helper()
        _executa(codigo, h)
        return h

    def test_rota_html(self):
        import time, urllib.request
        tmp = tempfile.mkdtemp()
        modelos = os.path.join(tmp, "m")
        os.makedirs(modelos)
        with open(os.path.join(modelos, "idx.html"), "w") as f:
            f.write("<p>{{ msg }}</p>")

        h = self._setup_servidor(19876,
            "servidor.modelos(" + repr(modelos) + ")\n"
            "servidor.rota(\"GET\", \"/\", fn(req)\n"
            "    retornar servidor.html(\"idx.html\", {\"msg\": \"ok\"})\n"
            "fim)\n"
        )
        time.sleep(0.3)

        res = urllib.request.urlopen("http://localhost:19876/")
        self.assertEqual(res.status, 200)
        self.assertIn(b"ok", res.read())
        h.interp.global_env.obter("servidor").parar()

    def test_rota_estatico(self):
        import time, urllib.request
        tmp = tempfile.mkdtemp()
        pub = os.path.join(tmp, "pub")
        os.makedirs(pub)
        with open(os.path.join(pub, "f.txt"), "w") as f:
            f.write("static ok")

        h = self._setup_servidor(19877,
            "servidor.estatico(\"/static\", " + repr(pub) + ")\n"
            "servidor.rota(\"GET\", \"/static2\", fn(req)\n"
            "    retornar \"ok\"\n"
            "fim)\n"
        )
        time.sleep(0.3)

        res = urllib.request.urlopen("http://localhost:19877/static/f.txt")
        self.assertEqual(res.status, 200)
        self.assertEqual(res.read().decode(), "static ok")
        h.interp.global_env.obter("servidor").parar()

    def test_sessao(self):
        import time, http.cookiejar, urllib.request

        h = self._setup_servidor(19878,
            "servidor.rota(\"GET\", \"/\", fn(req)\n"
            "    s = servidor.sessao(req)\n"
            "    s.c = s.c + 1 se s.c senao 1\n"
            "    retornar {\"c\": s.c}\n"
            "fim)\n"
        )
        time.sleep(0.3)

        cj = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
        r1 = json.loads(opener.open("http://localhost:19878/").read())
        self.assertEqual(r1["c"], 1)
        r2 = json.loads(opener.open("http://localhost:19878/").read())
        self.assertEqual(r2["c"], 2)
        r3 = json.loads(opener.open("http://localhost:19878/").read())
        self.assertEqual(r3["c"], 3)
        h.interp.global_env.obter("servidor").parar()


class TestNovasFeatures(unittest.TestCase):
    def test_eh_alias(self):
        self.assertEqual(_executa("retornar 5 eh 5\n"), True)

    def test_nao_eh_diferente(self):
        self.assertEqual(_executa("retornar 5 nao eh 3\n"), True)

    def test_nao_eh_diferente_falso(self):
        self.assertEqual(_executa("retornar 5 nao eh 5\n"), False)

    def test_senao_se_simples(self):
        r = _executa("x = 2\nv = ''\nse x eh 1\n    v = 'um'\nsenao se x eh 2\n    v = 'dois'\nsenao\n    v = 'outro'\nfim\nretornar v\n")
        self.assertEqual(r, "dois")

    def test_senao_se_primeiro(self):
        r = _executa("x = 1\nv = ''\nse x eh 1\n    v = 'um'\nsenao se x eh 2\n    v = 'dois'\nsenao\n    v = 'outro'\nfim\nretornar v\n")
        self.assertEqual(r, "um")

    def test_senao_se_tres_cadeia(self):
        r = _executa("x = 3\nv = ''\nse x eh 1\n    v = 'um'\nsenao se x eh 2\n    v = 'dois'\nsenao se x eh 3\n    v = 'tres'\nsenao\n    v = 'outro'\nfim\nretornar v\n")
        self.assertEqual(r, "tres")

    def test_senao_se_sem_else(self):
        r = _executa("x = 2\nv = ''\nse x eh 1\n    v = 'um'\nsenao se x eh 2\n    v = 'dois'\nfim\nretornar v\n")
        self.assertEqual(r, "dois")

    def test_senao_se_nenhum(self):
        r = _executa("x = 9\nv = ''\nse x eh 1\n    v = 'um'\nsenao se x eh 2\n    v = 'dois'\nfim\nretornar v\n")
        self.assertEqual(r, "")

    def test_multi_line_lista(self):
        r = _executa("x = [\n    1,\n    2,\n    3\n]\nretornar x\n")
        self.assertEqual(r, [1, 2, 3])

    def test_multi_line_dict(self):
        r = _executa("x = {\n    'a': 1,\n    'b': 2\n}\nretornar x['a']\n")
        self.assertEqual(r, 1)

    def test_multi_line_dict_uma_linha(self):
        r = _executa("x = {'a': 1, 'b': 2}\nretornar x['b']\n")
        self.assertEqual(r, 2)

    def test_template_recarregar(self):
        import tempfile, os
        tmp = tempfile.mkdtemp()
        m_dir = os.path.join(tmp, "m")
        os.makedirs(m_dir)
        with open(os.path.join(m_dir, "t.html"), "w", encoding="utf-8") as f:
            f.write("{{ msg }}")
        r = _executa(
            "usar template\n"
            "template.recarregar()\n"
            "template.diretorio(" + repr(m_dir) + ")\n"
            "x = template.renderizar(\"t.html\", {\"msg\": \"ok\"})\n"
            "template.recarregar()\n"
            "retornar x\n"
        )
        self.assertEqual(r, "ok")

    def test_recarregar_arquivo_novo(self):
        import tempfile, os
        tmp = tempfile.mkdtemp()
        m_dir = os.path.join(tmp, "m")
        os.makedirs(m_dir)
        with open(os.path.join(m_dir, "t.html"), "w", encoding="utf-8") as f:
            f.write("v1 {{ msg }}")
        r = _executa(
            "usar template\n"
            "template.recarregar()\n"
            "template.diretorio(" + repr(m_dir) + ")\n"
            "retornar template.renderizar(\"t.html\", {\"msg\": \"a\"})\n"
        )
        self.assertEqual(r, "v1 a")
        with open(os.path.join(m_dir, "t.html"), "w", encoding="utf-8") as f:
            f.write("v2 {{ msg }}")
        r = _executa(
            "usar template\n"
            "template.recarregar()\n"
            "template.diretorio(" + repr(m_dir) + ")\n"
            "template.recarregar()\n"
            "retornar template.renderizar(\"t.html\", {\"msg\": \"b\"})\n"
        )
        self.assertEqual(r, "v2 b")


class TestTipagem(unittest.TestCase):
    def test_tipo_texto_valido(self):
        r = _executa("nome: texto = 'joao'\nretornar nome\n")
        self.assertEqual(r, "joao")

    def test_tipo_inteiro_valido(self):
        r = _executa("x: inteiro = 42\nretornar x\n")
        self.assertEqual(r, 42)

    def test_tipo_numero_valido(self):
        r = _executa("x: numero = 3.14\nretornar x\n")
        self.assertEqual(r, 3.14)

    def test_tipo_booleano_valido(self):
        r = _executa("x: booleano = verdadeiro\nretornar x\n")
        self.assertEqual(r, True)

    def test_tipo_incompativel(self):
        from src.erros import ErroRuntime
        with self.assertRaises(ErroRuntime):
            _executa("x: texto = 42\n")

    def test_tipo_inteiro_incompativel(self):
        from src.erros import ErroRuntime
        with self.assertRaises(ErroRuntime):
            _executa("x: inteiro = 'texto'\n")

    def test_tipo_sem_anotacao(self):
        r = _executa("x = 42\nretornar x\n")
        self.assertEqual(r, 42)
