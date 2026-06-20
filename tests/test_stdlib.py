import unittest
import os
import sys
import io
import tempfile
import json as py_json

from src.stdlib import sistema as mod_sistema
from src.stdlib import arquivos as mod_arquivos
from src.stdlib import json_ as mod_json


class TestSistema(unittest.TestCase):
    def test_info_tem_chaves(self):
        info = mod_sistema.MODULO["info"]()
        self.assertIn("sistema", info)
        self.assertIn("hostname", info)
        self.assertIn("python", info)

    def test_variavel_get_set(self):
        nome = "_SIMPLIPT_TEST_VAR"
        resultado = mod_sistema.MODULO["variavel"](nome, "42")
        self.assertEqual(os.environ.get(nome), "42")
        os.environ.pop(nome, None)

    def test_caminho_atual(self):
        caminho = mod_sistema.MODULO["caminho_atual"]()
        self.assertIsNotNone(caminho)
        self.assertTrue(os.path.isdir(caminho))

    def test_pasta_temp(self):
        pasta = mod_sistema.MODULO["pasta_temp"]()
        self.assertIsNotNone(pasta)


class TestArquivos(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.arquivo = os.path.join(self.temp_dir, "teste.txt")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_escrever_e_ler(self):
        mod_arquivos.MODULO["escrever"](self.arquivo, "conteudo")
        conteudo = mod_arquivos.MODULO["ler"](self.arquivo)
        self.assertEqual(conteudo, "conteudo")

    def test_adicionar(self):
        mod_arquivos.MODULO["escrever"](self.arquivo, "linha1\n")
        mod_arquivos.MODULO["adicionar"](self.arquivo, "linha2\n")
        conteudo = mod_arquivos.MODULO["ler"](self.arquivo)
        self.assertIn("linha1", conteudo)
        self.assertIn("linha2", conteudo)

    def test_existe(self):
        mod_arquivos.MODULO["escrever"](self.arquivo, "teste")
        self.assertTrue(mod_arquivos.MODULO["existe"](self.arquivo))

    def test_listar(self):
        mod_arquivos.MODULO["escrever"](self.arquivo, "teste")
        lista = mod_arquivos.MODULO["listar"](self.temp_dir)
        self.assertIn("teste.txt", lista)

    def test_eh_arquivo(self):
        mod_arquivos.MODULO["escrever"](self.arquivo, "teste")
        self.assertTrue(mod_arquivos.MODULO["eh_arquivo"](self.arquivo))

    def test_criar_pasta(self):
        nova_pasta = os.path.join(self.temp_dir, "nova")
        mod_arquivos.MODULO["criar_pasta"](nova_pasta)
        self.assertTrue(os.path.isdir(nova_pasta))

    def test_deletar_arquivo(self):
        mod_arquivos.MODULO["escrever"](self.arquivo, "teste")
        mod_arquivos.MODULO["deletar"](self.arquivo)
        self.assertFalse(os.path.exists(self.arquivo))

    def test_copiar(self):
        destino = os.path.join(self.temp_dir, "copia.txt")
        mod_arquivos.MODULO["escrever"](self.arquivo, "original")
        mod_arquivos.MODULO["copiar"](self.arquivo, destino)
        self.assertTrue(os.path.exists(destino))

    def test_tamanho(self):
        mod_arquivos.MODULO["escrever"](self.arquivo, "12345")
        self.assertEqual(mod_arquivos.MODULO["tamanho"](self.arquivo), 5)


class TestJson(unittest.TestCase):
    def test_ler_string(self):
        resultado = mod_json.MODULO["ler"]('{"nome": "Jarbs"}')
        self.assertEqual(resultado["nome"], "Jarbs")

    def test_gerar(self):
        resultado = mod_json.MODULO["gerar"]({"a": 1, "b": 2})
        self.assertIn('"a": 1', resultado)

    def test_gerar_indentado(self):
        resultado = mod_json.MODULO["gerar"]({"a": 1}, indentado=True)
        self.assertIn("\n", resultado)

    def test_arquivo_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            py_json.dump({"chave": "valor"}, f)
            caminho = f.name
        try:
            resultado = mod_json.MODULO["arquivo"](caminho)
            self.assertEqual(resultado["chave"], "valor")
        finally:
            os.unlink(caminho)

    def test_salvar_json(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            caminho = f.name
        try:
            mod_json.MODULO["salvar"](caminho, {"num": 42})
            with open(caminho, "r", encoding="utf-8") as f:
                dados = py_json.load(f)
            self.assertEqual(dados["num"], 42)
        finally:
            os.unlink(caminho)


if __name__ == "__main__":
    unittest.main()
