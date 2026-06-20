# SimpliPT

Linguagem de programação em português para scripts, automação e produtividade.

```spt
usar sistema
usar arquivos

falar "=== GERADOR DE SENHA ==="
tamanho = sistema.ler("Tamanho: ").inteiro()

caracteres = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%&*"
senha = ""
para i em 1...tamanho
    senha = senha + caracteres[matematica.aleatorio(0, caracteres.tamanho() - 1)]
fim

falar "Senha gerada: " + senha
arquivos.escrever("senha.txt", senha)
falar "Salvo em senha.txt"
```

## Instalação

```bash
# Via PyPI (recomendado)
pip install simplipt

# Ou via repositório (modo desenvolvimento)
git clone https://github.com/overlord111111/simplipt
cd simplipt
pip install -e .

# Ou diretamente sem instalação
python -m src.cli arquivo.spt
```

Requer **Python 3.12+**. Zero dependências externas (pacote opcional `colorama` para cores no terminal).

## Uso

### CLI (linha de comando)

```bash
simplipt                     # REPL interativo
simplipt arquivo.spt         # Executar script
simplipt formatar <arquivo>  # Formatador de código
simplipt transpilar <arq>    # Transpilar SimpliPT → Python
simplipt build <arquivo>     # Compilar para .pyz (zipapp)
simplipt build --exe <arq>   # Compilar para .exe (requer PyInstaller)
simplipt dashboard [dir]     # IDE web / admin dashboard
simplipt lsp                 # Servidor LSP (autocomplete em editores)
simplipt install <pacote>    # Instalar pacote do repositório
simplipt new <nome>          # Criar novo projeto (scaffold)
simplipt test [dir]          # Rodar test runner
simplipt debug [dir]         # Debugger web interativo
simplipt modulo install <pkg>  # Instalar módulo Python externo
simplipt modulo listar         # Listar módulos externos
```

Opções: `--debug`, `-b/--breakpoint`, `-w/--watch`, `--strict`, `--hot`, `--json`, `--profile`

## Características

- Comandos em português natural (`falar`, `se`, `para`, `enquanto`, `tentar`)
- 18 módulos embutidos (sistema, arquivos, json, http, servidor, banco, template, etc.)
- Ternário em qualquer expressão: `status = "ok" se resposta eh 200 senao "erro"`
- Template engine: `{{ var }}`, `{% se %}`, `{% para %}`, `{% incluir %}`
- List comprehension: `[x*2 para x em lista se x > 5]`
- Orientação a objetos: `classe`, `novo`, `este`, `super`, `extende`
- Servidor web embutido com rotas, sessões, arquivos estáticos, templates
- SQLite, cache com TTL, fila de tarefas com workers
- Tipagem opcional: `nome: texto = "João"`
- Zero dependências externas
