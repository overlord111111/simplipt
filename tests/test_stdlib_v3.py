import unittest
import os
import sys
import json
import tempfile
import threading
import time

from src.stdlib import servidor as mod_servidor
from src.stdlib import banco as mod_banco
from src.stdlib import cache as mod_cache
from src.stdlib import fila as mod_fila


class TestServidor(unittest.TestCase):
    def setUp(self):
        self.srv = mod_servidor.MODULO
        self.srv.parar()
        self.srv.rotas.clear()

    def tearDown(self):
        self.srv.parar()
        self.srv.rotas.clear()

    def test_rota_exata(self):
        capturado = {}
        def handler(req):
            capturado["req"] = req
            return {"status": "ok"}
        self.srv.rota("GET", "/teste", handler)
        self.srv.iniciar(0)
        porta = self.srv._httpd.server_port
        import urllib.request
        resp = urllib.request.urlopen(f"http://localhost:{porta}/teste", timeout=3)
        self.assertEqual(json.loads(resp.read()), {"status": "ok"})
        self.assertEqual(capturado["req"]["metodo"], "GET")
        self.assertEqual(capturado["req"]["caminho"], "/teste")

    def test_rota_path_params(self):
        capturado = {}
        def handler(req):
            capturado["req"] = req
            return {"id": req["params"]["id"]}
        self.srv.rota("GET", "/usuarios/:id", handler)
        self.srv.iniciar(0)
        porta = self.srv._httpd.server_port
        import urllib.request
        resp = urllib.request.urlopen(f"http://localhost:{porta}/usuarios/42", timeout=3)
        self.assertEqual(json.loads(resp.read()), {"id": "42"})

    def test_rota_404(self):
        self.srv.rota("GET", "/ok", lambda req: {"ok": True})
        self.srv.iniciar(0)
        porta = self.srv._httpd.server_port
        import urllib.request
        try:
            urllib.request.urlopen(f"http://localhost:{porta}/nao-existe", timeout=3)
            self.fail("Deveria ter lançado 404")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 404)

    def test_post_json_body(self):
        capturado = {}
        def handler(req):
            capturado["req"] = req
            return {"eco": req["corpo"]}
        self.srv.rota("POST", "/eco", handler)
        self.srv.iniciar(0)
        porta = self.srv._httpd.server_port
        import urllib.request
        dados = json.dumps({"msg": "ola"}).encode("utf-8")
        req = urllib.request.Request(
            f"http://localhost:{porta}/eco",
            data=dados,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        resp = urllib.request.urlopen(req, timeout=3)
        self.assertEqual(json.loads(resp.read()), {"eco": {"msg": "ola"}})

    def test_rodando(self):
        self.assertFalse(self.srv.rodando())
        self.srv.iniciar(0)
        self.assertTrue(self.srv.rodando())
        self.srv.parar()
        self.assertFalse(self.srv.rodando())


class TestBanco(unittest.TestCase):
    def setUp(self):
        self.banco = mod_banco.MODULO
        self.banco.conectar(":memory:")
        self.banco.criar_tabela(
            "CREATE TABLE teste (id INTEGER PRIMARY KEY, nome TEXT, idade INTEGER)"
        )

    def tearDown(self):
        self.banco.fechar()

    def test_inserir_e_buscar(self):
        self.banco.inserir("teste", {"nome": "Jarbs", "idade": 30})
        resultados = self.banco.buscar("SELECT * FROM teste")
        self.assertEqual(len(resultados), 1)
        self.assertEqual(resultados[0]["nome"], "Jarbs")

    def test_buscar_um(self):
        self.banco.inserir("teste", {"nome": "Over", "idade": 25})
        r = self.banco.buscar_um("SELECT * FROM teste WHERE nome = ?", ["Over"])
        self.assertIsNotNone(r)
        self.assertEqual(r["nome"], "Over")

    def test_atualizar(self):
        self.banco.inserir("teste", {"nome": "Jarbs", "idade": 30})
        self.banco.atualizar("teste", {"idade": 31}, "nome = ?", ["Jarbs"])
        r = self.banco.buscar_um("SELECT * FROM teste")
        self.assertEqual(r["idade"], 31)

    def test_deletar(self):
        self.banco.inserir("teste", {"nome": "Jarbs", "idade": 30})
        self.banco.deletar("teste", "nome = ?", ["Jarbs"])
        self.assertEqual(self.banco.contar("teste"), 0)

    def test_contar(self):
        self.banco.inserir("teste", {"nome": "A", "idade": 1})
        self.banco.inserir("teste", {"nome": "B", "idade": 2})
        self.assertEqual(self.banco.contar("teste"), 2)

    def test_tabelas(self):
        tabelas = self.banco.tabelas()
        self.assertIn("teste", tabelas)

    def test_transacao_confirmar(self):
        self.banco.iniciar_transacao()
        self.banco.inserir("teste", {"nome": "Trans", "idade": 99})
        self.banco.confirmar()
        self.assertEqual(self.banco.contar("teste"), 1)

    def test_transacao_desfazer(self):
        self.banco.inserir("teste", {"nome": "Antes", "idade": 1})
        self.banco.iniciar_transacao()
        self.banco.inserir("teste", {"nome": "Depois", "idade": 2})
        self.banco.desfazer()
        self.assertEqual(self.banco.contar("teste"), 1)

    def test_ultimo_id(self):
        id1 = self.banco.inserir("teste", {"nome": "A", "idade": 1})
        id2 = self.banco.ultimo_id()
        self.assertEqual(id2, 1)
        self.banco.inserir("teste", {"nome": "B", "idade": 2})
        self.assertEqual(self.banco.ultimo_id(), 2)


class TestCache(unittest.TestCase):
    def setUp(self):
        self.cache = mod_cache.MODULO
        self.cache.limpar()

    def test_set_get(self):
        self.cache.definir("chave", 42)
        self.assertEqual(self.cache.obter("chave"), 42)

    def test_padrao(self):
        self.assertEqual(self.cache.obter("inexistente", "padrao"), "padrao")

    def test_existe(self):
        self.cache.definir("chave", "valor")
        self.assertTrue(self.cache.existe("chave"))
        self.assertFalse(self.cache.existe("outra"))

    def test_remover(self):
        self.cache.definir("chave", "valor")
        self.assertTrue(self.cache.remover("chave"))
        self.assertFalse(self.cache.existe("chave"))

    def test_ttl(self):
        self.cache.definir("chave", "valor", 0.1)
        self.assertTrue(self.cache.existe("chave"))
        time.sleep(0.15)
        self.assertFalse(self.cache.existe("chave"))

    def test_tamanho(self):
        self.cache.definir("a", 1)
        self.cache.definir("b", 2)
        self.assertEqual(self.cache.tamanho(), 2)

    def test_limpar(self):
        self.cache.definir("a", 1)
        self.cache.limpar()
        self.assertEqual(self.cache.tamanho(), 0)


class TestFila(unittest.TestCase):
    def setUp(self):
        self.fila = mod_fila.MODULO
        self.fila.limpar()

    def test_adicionar_retirar(self):
        self.fila.adicionar("item1")
        self.fila.adicionar("item2")
        self.assertEqual(self.fila.retirar(), "item1")
        self.assertEqual(self.fila.retirar(), "item2")

    def test_tamanho(self):
        self.assertEqual(self.fila.tamanho(), 0)
        self.fila.adicionar("a")
        self.fila.adicionar("b")
        self.assertEqual(self.fila.tamanho(), 2)

    def test_vazia(self):
        self.assertTrue(self.fila.vazia())
        self.fila.adicionar("a")
        self.assertFalse(self.fila.vazia())

    def test_pegar_todos(self):
        self.fila.adicionar("a")
        self.fila.adicionar("b")
        self.assertEqual(self.fila.pegar_todos(), ["a", "b"])
        self.assertTrue(self.fila.vazia())

    def test_salvar_carregar(self):
        self.fila.adicionar("x")
        self.fila.adicionar("y")
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            path = f.name
        try:
            self.fila.salvar(path)
            self.fila.limpar()
            self.assertTrue(self.fila.vazia())
            qtd = self.fila.carregar(path)
            self.assertEqual(qtd, 2)
            self.assertEqual(self.fila.tamanho(), 2)
        finally:
            os.unlink(path)

    def test_retirar_timeout(self):
        self.assertIsNone(self.fila.retirar(timeout=0.1))
