import webbrowser
import urllib.request
import urllib.error
import re


def _abrir(url):
    webbrowser.open(url)
    return True


def _html(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SimpliPT/0.1"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Erro HTTP {e.code} ao acessar {url}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Erro de conexão ao acessar {url}: {e.reason}")
    except Exception as e:
        raise RuntimeError(f"Erro ao acessar {url}: {e}")


def _titulo(html):
    match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else ""


def _texto(html):
    texto = re.sub(r"<[^>]+>", " ", html)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


MODULO = {
    "abrir": _abrir,
    "html": _html,
    "titulo": _titulo,
    "texto": _texto,
}
