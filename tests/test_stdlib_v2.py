import unittest
import os
import sys
import io
import tempfile
import json

from src.stdlib import config as mod_config
from src.stdlib import data as mod_data
from src.stdlib import matematica as mod_matematica
from src.stdlib import regex as mod_regex
from src.stdlib import hashes as mod_hashes


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.old_appdata = os.environ.get("APPDATA")
        self.temp_dir = tempfile.mkdtemp()
        os.environ["APPDATA"] = self.temp_dir
        import importlib
        importlib.reload(mod_config)

    def tearDown(self):
        if self.old_appdata:
            os.environ["APPDATA"] = self.old_appdata
        else:
            del os.environ["APPDATA"]
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_set_and_get(self):
        cfg = mod_config.MODULO
        cfg.api_key = "sk-test"
        self.assertEqual(cfg.api_key, "sk-test")

    def test_persistencia(self):
        cfg = mod_config.MODULO
        cfg.minha_chave = "valor_salvo"
        import importlib
        importlib.reload(mod_config)
        cfg2 = mod_config.MODULO
        self.assertEqual(cfg2.minha_chave, "valor_salvo")

    def test_chave_inexistente(self):
        cfg = mod_config.MODULO
        self.assertEqual(cfg.chave_que_nao_existe, "")


class TestData(unittest.TestCase):
    def test_agora_retorna_string(self):
        resultado = mod_data.MODULO["agora"]()
        self.assertIsInstance(resultado, str)
        self.assertIn(":", resultado)

    def test_hoje_formato(self):
        resultado = mod_data.MODULO["hoje"]()
        self.assertIsInstance(resultado, str)
        self.assertEqual(len(resultado), 10)

    def test_hora(self):
        resultado = mod_data.MODULO["hora"]()
        self.assertIsInstance(resultado, str)

    def test_timestamp(self):
        resultado = mod_data.MODULO["timestamp"]()
        self.assertGreater(resultado, 1_500_000_000)

    def test_ano(self):
        self.assertGreater(mod_data.MODULO["ano"](), 2020)

    def test_mes(self):
        self.assertGreaterEqual(mod_data.MODULO["mes"](), 1)
        self.assertLessEqual(mod_data.MODULO["mes"](), 12)

    def test_dia(self):
        self.assertGreaterEqual(mod_data.MODULO["dia"](), 1)
        self.assertLessEqual(mod_data.MODULO["dia"](), 31)

    def test_formatar(self):
        resultado = mod_data.MODULO["formatar"]("%Y")
        self.assertIsInstance(resultado, str)

    def test_diferenca_dias(self):
        diff = mod_data.MODULO["diferenca_dias"]("2024-01-01", "2024-01-10")
        self.assertEqual(diff, 9)


class TestMatematica(unittest.TestCase):
    def test_arredondar(self):
        self.assertEqual(mod_matematica.MODULO["arredondar"](3.14159, 2), 3.14)

    def test_abs(self):
        self.assertEqual(mod_matematica.MODULO["abs"](-5), 5)

    def test_max(self):
        self.assertEqual(mod_matematica.MODULO["max"](1, 3, 2), 3)

    def test_min(self):
        self.assertEqual(mod_matematica.MODULO["min"](1, 3, 2), 1)

    def test_sqrt(self):
        self.assertEqual(mod_matematica.MODULO["sqrt"](9), 3)

    def test_pi(self):
        self.assertAlmostEqual(mod_matematica.MODULO["pi"](), 3.14159, places=4)

    def test_aleatorio_int(self):
        resultado = mod_matematica.MODULO["aleatorio_int"](1, 10)
        self.assertGreaterEqual(resultado, 1)
        self.assertLessEqual(resultado, 10)

    def test_aleatorio(self):
        resultado = mod_matematica.MODULO["aleatorio"](0, 1)
        self.assertGreaterEqual(resultado, 0)
        self.assertLessEqual(resultado, 1)


class TestRegex(unittest.TestCase):
    def test_buscar(self):
        resultado = mod_regex.MODULO["buscar"]("\\d+", "abc123def")
        self.assertEqual(resultado, "123")

    def test_encontrar(self):
        resultado = mod_regex.MODULO["encontrar"]("\\d+", "a1b2c3")
        self.assertEqual(resultado, ["1", "2", "3"])

    def test_testar(self):
        self.assertTrue(mod_regex.MODULO["testar"]("\\d", "abc1"))
        self.assertFalse(mod_regex.MODULO["testar"]("\\d", "abc"))

    def test_substituir(self):
        resultado = mod_regex.MODULO["substituir"]("mundo", "Jarbs", "ola mundo")
        self.assertEqual(resultado, "ola Jarbs")

    def test_dividir(self):
        resultado = mod_regex.MODULO["dividir"](",", "a,b,c")
        self.assertEqual(resultado, ["a", "b", "c"])

    def test_grupos(self):
        resultado = mod_regex.MODULO["grupos"]("(\\d+)-(\\w+)", "123-abc")
        self.assertEqual(resultado, ["123", "abc"])

    def test_buscar_sem_match(self):
        resultado = mod_regex.MODULO["buscar"]("\\d+", "abc")
        self.assertEqual(resultado, "")


class TestHashes(unittest.TestCase):
    def test_md5(self):
        resultado = mod_hashes.MODULO["md5"]("teste")
        self.assertEqual(len(resultado), 32)

    def test_sha1(self):
        resultado = mod_hashes.MODULO["sha1"]("teste")
        self.assertEqual(len(resultado), 40)

    def test_sha256(self):
        resultado = mod_hashes.MODULO["sha256"]("teste")
        self.assertEqual(len(resultado), 64)

    def test_md5_consistente(self):
        h1 = mod_hashes.MODULO["md5"]("teste")
        h2 = mod_hashes.MODULO["md5"]("teste")
        self.assertEqual(h1, h2)


if __name__ == "__main__":
    unittest.main()
