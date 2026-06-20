import os
import sys
import shutil
import subprocess
import tempfile


_TEMPLATE = '''import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "_simplipt"))
from src.lexer.lexer import Lexer
from src.parser.parser import Parser
from src.interpreter.interpreter import Interpreter

CODIGO = {codigo!r}

def main():
    lex = Lexer(CODIGO, {nome_arquivo!r})
    toks = lex.tokenizar()
    par = Parser(toks, {nome_arquivo!r})
    ast = par.programa()
    interp = Interpreter()
    interp.interpretar(ast)

if __name__ == "__main__":
    main()
'''


def _gerar_zipapp(caminho_spt, saida=None):
    with open(caminho_spt, "r", encoding="utf-8") as f:
        codigo = f.read()

    nome = os.path.splitext(os.path.basename(caminho_spt))[0]
    if saida is None:
        saida = nome + ".pyz"

    raiz = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.dirname(raiz)
    proj_dir = os.path.dirname(src_dir)

    with tempfile.TemporaryDirectory() as tmp:
        app_dir = os.path.join(tmp, "app")
        os.makedirs(app_dir)

        with open(os.path.join(app_dir, "__main__.py"), "w", encoding="utf-8") as f:
            f.write(_TEMPLATE.format(
                codigo=codigo,
                nome_arquivo=os.path.basename(caminho_spt),
            ))

        destino_src = os.path.join(app_dir, "_simplipt", "src")
        shutil.copytree(
            os.path.join(proj_dir, "src"),
            destino_src,
            ignore=shutil.ignore_patterns("__pycache__"),
        )

        os.chdir(tmp)
        subprocess.check_call(
            [sys.executable, "-m", "zipapp", "app", "--output", saida, "--python", "/usr/bin/env python3"]
        )

        shutil.move(saida, os.path.join(proj_dir, saida))

    print(f"ZipApp criado: {saida}")
    print(f"Execute com: python {saida}")
    return saida


def _gerar_exe(caminho_spt, saida=None):
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller nao encontrado.", file=sys.stderr)
        print("Instale com: pip install pyinstaller", file=sys.stderr)
        return None

    with open(caminho_spt, "r", encoding="utf-8") as f:
        codigo = f.read()

    nome = os.path.splitext(os.path.basename(caminho_spt))[0]
    if saida is None:
        saida = nome

    raiz = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.dirname(raiz)
    proj_dir = os.path.dirname(src_dir)

    with tempfile.TemporaryDirectory() as tmp:
        wrapper = os.path.join(tmp, "_wrapper.py")
        with open(wrapper, "w", encoding="utf-8") as f:
            f.write(_TEMPLATE.format(
                codigo=codigo,
                nome_arquivo=os.path.basename(caminho_spt),
            ))

        extras = [
            "--onefile",
            "--name", nome,
            "--distpath", os.path.join(proj_dir, "dist"),
            "--workpath", os.path.join(tmp, "build"),
            "--specpath", tmp,
            "--add-data", f"{os.path.join(proj_dir, 'src')}{os.pathsep}src",
            "--hidden-import", "src.lexer.lexer",
            "--hidden-import", "src.parser.parser",
            "--hidden-import", "src.interpreter.interpreter",
            "--hidden-import", "src.erros",
            "--hidden-import", "src.runtime.builtins",
        ]
        for mod in os.listdir(os.path.join(proj_dir, "src", "stdlib")):
            if mod.endswith(".py") and mod != "__init__.py":
                extras.append("--hidden-import")
                extras.append(f"src.stdlib.{mod[:-3]}")

        cmd = [sys.executable, "-m", "PyInstaller", wrapper] + extras
        subprocess.check_call(cmd)

        exe = os.path.join(proj_dir, "dist", f"{nome}.exe")
        print(f"Executavel criado: {exe}")
        return exe


def compilar(caminho_spt, modo="zipapp", saida=None):
    if not os.path.exists(caminho_spt):
        print(f"Arquivo nao encontrado: {caminho_spt}", file=sys.stderr)
        return None

    if modo == "exe":
        return _gerar_exe(caminho_spt, saida)
    return _gerar_zipapp(caminho_spt, saida)
