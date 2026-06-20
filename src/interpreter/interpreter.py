import concurrent.futures
import datetime
import threading
import traceback

from src.erros import ErroRuntime
from src.interpreter.environment import Environment
from src.parser.ast import *
from src.runtime.builtins import REGISTRY_BUILTINS


class Interpreter:
    def __init__(self, debugger=None, perfil=False):
        self.global_env = Environment()
        self.modulos = {}
        self._este_atual = None
        self._classes = {}
        self.debugger = debugger
        self.perfil = None
        if perfil:
            from src.profile import ativar
            self.perfil = ativar()
        self._init_globais()

    def _init_globais(self):
        for nome, fn in REGISTRY_BUILTINS.items():
            self.global_env.definir(nome, fn)

    def interpretar(self, node):
        resultado = self._executar(node, self.global_env)
        if isinstance(resultado, _Retorno):
            return resultado.valor
        return resultado

    def _executar(self, node, env):
        if self.debugger:
            self.debugger._notify(node, env, self)
        if isinstance(node, Programa):
            return self._executar_programa(node, env)
        if isinstance(node, Atribuicao):
            return self._executar_atribuicao(node, env)
        if isinstance(node, AtribuicaoMembro):
            return self._executar_atribuicao_membro(node, env)
        if isinstance(node, AtribuicaoIndexada):
            return self._executar_atribuicao_indexada(node, env)
        if isinstance(node, Falar):
            return self._executar_falar(node, env)
        if isinstance(node, Ler):
            return self._executar_ler(node, env)
        if isinstance(node, Limpar):
            return self._executar_limpar(node, env)
        if isinstance(node, Log):
            return self._executar_log(node, env)
        if isinstance(node, Pausa):
            return self._executar_pausa(node, env)
        if isinstance(node, Se):
            return self._executar_se(node, env)
        if isinstance(node, ParaAte):
            return self._executar_para_ate(node, env)
        if isinstance(node, ParaEm):
            return self._executar_para_em(node, env)
        if isinstance(node, Enquanto):
            return self._executar_enquanto(node, env)
        if isinstance(node, Funcao):
            return self._executar_funcao_def(node, env)
        if isinstance(node, Chamada):
            return self._executar_chamada(node, env)
        if isinstance(node, ChamadaMembro):
            return self._executar_chamada_membro(node, env)
        if isinstance(node, Retornar):
            return self._executar_retornar(node, env)
        if isinstance(node, Paralelo):
            return self._executar_paralelo(node, env)
        if isinstance(node, Tentar):
            return self._executar_tentar(node, env)
        if isinstance(node, Usar):
            return self._executar_usar(node, env)
        if isinstance(node, Classe):
            return self._executar_classe(node, env)
        if isinstance(node, Novo):
            return self._executar_novo(node, env)
        if isinstance(node, Corresponder):
            return self._executar_corresponder(node, env)
        if isinstance(node, Garantir):
            cond = self._avaliar(node.condicao, env)
            if not _e_verdadeiro(cond):
                msg = node.mensagem or _para_texto(node.condicao)
                raise ErroRuntime(f"Garantia falhou: {msg}")
            return None
        if isinstance(node, FuncaoAsync):
            return self._executar_funcao_async(node, env)
        if isinstance(node, Esperar):
            return self._executar_esperar(node, env)
        if isinstance(node, (Numero, Texto, Booleano, Nada, ListaExpr, ListaCompreensao, DicionarioExpr)):
            return self._avaliar(node, env)
        if isinstance(node, (Variavel, Binario, Unario, Indexacao, Membro, Template, Este, Super)):
            return self._avaliar(node, env)
        if node is None:
            return None
        raise ErroRuntime(f"Tipo de nó desconhecido: {type(node).__name__}")

    def _executar_programa(self, node, env):
        resultado = None
        for n in node.nodes:
            resultado = self._executar(n, env)
        return resultado

    def _executar_atribuicao(self, node, env):
        valor = self._avaliar(node.valor, env)
        if node.tipo:
            self._validar_tipo(node.tipo, valor, node.nome, node.linha if hasattr(node, 'linha') else None)
        env.definir(node.nome, valor)
        return valor

    def _validar_tipo(self, tipo, valor, nome, linha=None):
        tipo = tipo.lower()
        mapa = {
            "texto": str,
            "inteiro": int,
            "numero": (int, float),
            "booleano": bool,
            "nada": type(None),
            "lista": list,
            "dicionario": dict,
        }
        esperado = mapa.get(tipo)
        if esperado and not isinstance(valor, esperado):
            raise ErroRuntime(f"Tipo incompatível: '{nome}' esperado {tipo}, recebeu {type(valor).__name__}")

    def _executar_atribuicao_membro(self, node, env):
        obj = self._avaliar(node.objeto, env)
        valor = self._avaliar(node.valor, env)
        if isinstance(obj, dict):
            obj[node.nome] = valor
        elif isinstance(obj, _Instancia):
            obj.atributos[node.nome] = valor
        elif hasattr(obj, node.nome):
            setattr(obj, node.nome, valor)
        else:
            obj[node.nome] = valor
        return valor

    def _executar_atribuicao_indexada(self, node, env):
        obj = self._avaliar(node.objeto, env)
        indice = self._avaliar(node.indice, env)
        valor = self._avaliar(node.valor, env)
        obj[indice] = valor
        return valor

    def _executar_falar(self, node, env):
        valor = self._avaliar(node.expressao, env)
        print(_para_texto(valor))

    def _executar_ler(self, node, env):
        if node.prompt is not None:
            prompt = _para_texto(self._avaliar(node.prompt, env))
            return input(prompt)
        return input()

    def _executar_limpar(self, node, env):
        import os
        os.system("cls" if os.name == "nt" else "clear")

    def _executar_log(self, node, env):
        agora = datetime.datetime.now().strftime("%H:%M:%S")
        msg = _para_texto(self._avaliar(node.mensagem, env))
        prefixo = {"info": "INFO", "aviso": "AVISO", "erro": "ERRO"}.get(node.nivel, "LOG")
        print(f"[{agora}] [{prefixo}] {msg}")

    def _executar_pausa(self, node, env):
        import time
        tempo = float(self._avaliar(node.tempo, env))
        time.sleep(tempo)

    def _executar_se(self, node, env):
        condicao = self._avaliar(node.condicao, env)
        if _e_verdadeiro(condicao):
            return self._executar_bloco(node.corpo, env)
        elif node.senao is not None:
            return self._executar_bloco(node.senao, env)
        return None

    def _executar_para_ate(self, node, env):
        ate = int(self._avaliar(node.ate, env))
        for i in range(1, ate + 1):
            env.definir(node.var, i)
            for n in node.corpo:
                resultado = self._executar(n, env)
                if isinstance(resultado, _Retorno):
                    return resultado
        return None

    def _executar_para_em(self, node, env):
        colecao = self._avaliar(node.colecao, env)
        for item in colecao:
            env.definir(node.var, item)
            for n in node.corpo:
                resultado = self._executar(n, env)
                if isinstance(resultado, _Retorno):
                    return resultado
        return None

    def _executar_enquanto(self, node, env):
        while _e_verdadeiro(self._avaliar(node.condicao, env)):
            for n in node.corpo:
                resultado = self._executar(n, env)
                if isinstance(resultado, _Retorno):
                    return resultado
        return None

    def _executar_funcao_def(self, node, env):
        funcao = _FuncaoUsuario(node, env, self)
        env.definir(node.nome, funcao)
        return funcao

    def _executar_funcao_async(self, node, env):
        import asyncio
        async def _coro_wrapper(*args):
            func_env = Environment(env)
            for i, param in enumerate(node.params):
                func_env.definir(param, args[i] if i < len(args) else None)
            resultado = None
            for n in node.corpo:
                resultado = self._executar(n, func_env)
                if isinstance(resultado, _Retorno):
                    return resultado.valor
            return resultado
        env.definir(node.nome, _coro_wrapper)
        return _coro_wrapper

    def _executar_esperar(self, node, env):
        import asyncio
        chamada = self._avaliar(node.chamada, env)
        if callable(chamada):
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                        fut = pool.submit(asyncio.run, chamada())
                        return fut.result()
                return asyncio.run(chamada())
            except RuntimeError:
                return asyncio.run(chamada())
        return chamada

    def _executar_chamada(self, node, env):
        obj = env.obter(node.nome)
        args = [self._avaliar(arg, env) for arg in node.argumentos]
        named = {nome: self._avaliar(valor, env) for nome, valor in node.argumentos_nomeados}
        if isinstance(obj, _FuncaoUsuario):
            return self._executar_funcao_usuario(obj, args, env, named)
        if isinstance(obj, _ClasseUsuario):
            return self._executar_chamada_classe(obj, node.argumentos, env, named)
        if callable(obj):
            if named:
                return obj(*args, **named)
            return obj(*args)
        if isinstance(obj, type):
            return obj()
        raise ErroRuntime(f"'{node.nome}' não é uma função chamável")

    def _executar_funcao_usuario(self, fn, args, env, named_args=None):
        if self.perfil:
            self.perfil.entrar(fn.node.nome)
        func_env = Environment(fn.closure)
        if self._este_atual is not None:
            func_env.definir("este", self._este_atual)
        for i, param in enumerate(fn.node.params):
            func_env.definir(param, args[i] if i < len(args) else None)
        if named_args:
            for nome, valor in named_args.items():
                func_env.definir(nome, valor)
        resultado = None
        for n in fn.node.corpo:
            resultado = self._executar(n, func_env)
            if isinstance(resultado, _Retorno):
                if self.perfil:
                    self.perfil.sair()
                return resultado.valor
        if self.perfil:
            self.perfil.sair()
        return resultado

    ALIASES_METODOS = {
        "adicionar": "append",
        "remover": "remove",
        "inserir": "insert",
        "contar": "count",
        "ordenar": "sort",
        "inverter": "reverse",
        "pegar": "get",
    }

    def _executar_chamada_membro(self, node, env):
        obj = self._avaliar(node.objeto, env)
        args = [self._avaliar(arg, env) for arg in node.argumentos]
        named = {nome: self._avaliar(valor, env) for nome, valor in node.argumentos_nomeados}

        if isinstance(obj, _Instancia):
            metodo = obj._classe._buscar_metodo(node.nome)
            if metodo:
                antigo = self._este_atual
                self._este_atual = obj
                try:
                    return self._executar_funcao_usuario(metodo, args, env, named)
                finally:
                    self._este_atual = antigo
            raise ErroRuntime(f"'{obj._classe.nome}' não tem método '{node.nome}'")

        if isinstance(obj, _SuperProxy):
            metodo = obj._classe._buscar_metodo(node.nome)
            if metodo:
                antigo = self._este_atual
                self._este_atual = obj._instancia
                try:
                    return self._executar_funcao_usuario(metodo, args, env, named)
                finally:
                    self._este_atual = antigo
            raise ErroRuntime(f"Classe base não tem método '{node.nome}'")

        if isinstance(obj, dict) and node.nome in obj:
            fn = obj[node.nome]
            if isinstance(fn, _FuncaoUsuario):
                return self._executar_funcao_usuario(fn, args, env, named)
            if callable(fn):
                return fn(*args, **named) if named else fn(*args)

        nome_metodo = self.ALIASES_METODOS.get(node.nome, node.nome)
        if hasattr(obj, nome_metodo):
            fn = getattr(obj, nome_metodo)
            if isinstance(fn, _FuncaoUsuario):
                return self._executar_funcao_usuario(fn, args, env, named)
            if callable(fn):
                return fn(*args, **named) if named else fn(*args)

        raise ErroRuntime(f"'{type(obj).__name__}' não tem método '{node.nome}'")

    def _executar_retornar(self, node, env):
        if node.valor is not None:
            valor = self._avaliar(node.valor, env)
            return _Retorno(valor)
        return _Retorno(None)

    def _executar_paralelo(self, node, env):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            for n in node.corpo:
                if n is None:
                    continue
                copia_env = self._prepara_paralelo(env)
                futures.append(executor.submit(self._executar_linha_isolada, n, copia_env))
            for f in concurrent.futures.as_completed(futures):
                f.result()

    def _prepara_paralelo(self, env):
        novo = Environment()
        novo.values = env.values.copy()
        return novo

    def _executar_linha_isolada(self, node, env):
        try:
            return self._executar(node, env)
        except Exception as e:
            print(f"[paralelo] Erro: {e}")

    def _executar_tentar(self, node, env):
        try:
            return self._executar_bloco(node.corpo, env)
        except Exception:
            return self._executar_bloco(node.capturar, env)

    def _executar_usar(self, node, env):
        nome = node.modulo
        if nome in self.modulos:
            modulo = self.modulos[nome]
        else:
            modulo = self._carregar_modulo(nome)
            self.modulos[nome] = modulo
        env.definir(nome, modulo)
        return modulo

    def _carregar_modulo(self, nome):
        import importlib
        ALIASES = {"json": "json_"}
        nome_real = ALIASES.get(nome, nome)
        try:
            modulo_py = importlib.import_module(f"src.stdlib.{nome_real}")
            return modulo_py.MODULO
        except ImportError:
            pass
        import os
        caminhos = [f"{nome}.spt", os.path.join("modulos", f"{nome}.spt")]
        for caminho in caminhos:
            if os.path.exists(caminho):
                return self._executar_modulo_spt(caminho)
        raise ErroRuntime(f"Módulo '{nome}' não encontrado")

    def _executar_modulo_spt(self, caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            texto = f.read()
        from src.lexer.lexer import Lexer
        from src.parser.parser import Parser
        lexer = Lexer(texto, caminho)
        tokens = lexer.tokenizar()
        parser = Parser(tokens, caminho)
        ast = parser.programa()
        env_mod = Environment()
        for nome_b, fn in REGISTRY_BUILTINS.items():
            env_mod.definir(nome_b, fn)
        self._executar(ast, env_mod)
        return env_mod.values.copy()

    def _executar_bloco(self, nodes, env):
        resultado = None
        for n in nodes:
            if n is None:
                continue
            resultado = self._executar(n, env)
            if isinstance(resultado, _Retorno):
                return resultado
        return resultado

    def _executar_classe(self, node, env):
        metodos = {}
        if node.construtor:
            metodos["_init"] = _FuncaoUsuario(node.construtor, env, self)
        for m in node.metodos:
            metodos[m.nome] = _FuncaoUsuario(m, env, self)
        cls = _ClasseUsuario(node.nome, metodos, node.base, self)
        self._classes[node.nome] = cls
        env.definir(node.nome, cls)
        return cls

    def _executar_novo(self, node, env):
        cls = self._classes.get(node.nome)
        if not cls:
            raise ErroRuntime(f"Classe '{node.nome}' não definida")
        instancia = _Instancia(cls)
        args = [self._avaliar(arg, env) for arg in node.argumentos]
        construtor = cls._buscar_metodo("_init")
        if construtor:
            antigo = self._este_atual
            self._este_atual = instancia
            try:
                self._executar_funcao_usuario(construtor, args, env)
            finally:
                self._este_atual = antigo
        return instancia

    def _executar_chamada_classe(self, cls, argumentos, env, named_args=None):
        instancia = _Instancia(cls)
        args = [self._avaliar(arg, env) for arg in argumentos]
        construtor = cls._buscar_metodo("_init")
        if construtor:
            antigo = self._este_atual
            self._este_atual = instancia
            try:
                self._executar_funcao_usuario(construtor, args, env, named_args)
            finally:
                self._este_atual = antigo
        return instancia

    def _executar_corresponder(self, node, env):
        valor = self._avaliar(node.valor, env)
        for caso in node.casos:
            padrao = self._avaliar(caso.padrao, env)
            if valor == padrao:
                return self._executar_bloco(caso.corpo, env)
        return None

    def _avaliar(self, node, env):
        if isinstance(node, Numero):
            return node.valor
        if isinstance(node, Texto):
            return node.valor
        if isinstance(node, Booleano):
            return node.valor
        if isinstance(node, Nada):
            return None
        if isinstance(node, ListaExpr):
            return [self._avaliar(e, env) for e in node.elementos]
        if isinstance(node, ListaCompreensao):
            return self._avaliar_compreensao(node, env)
        if isinstance(node, DicionarioExpr):
            return {chave: self._avaliar(valor, env) for chave, valor in node.pares.items()}
        if isinstance(node, Variavel):
            return env.obter(node.nome)
        if isinstance(node, Binario):
            return self._avaliar_binario(node, env)
        if isinstance(node, Unario):
            return self._avaliar_unario(node, env)
        if isinstance(node, Indexacao):
            return self._avaliar_indexacao(node, env)
        if isinstance(node, Membro):
            return self._avaliar_membro(node, env)
        if isinstance(node, Template):
            return self._avaliar_template(node, env)
        if isinstance(node, Este):
            if self._este_atual is None:
                raise ErroRuntime("'este' usado fora de método")
            return self._este_atual
        if isinstance(node, Super):
            return self._avaliar_super(node, env)
        if isinstance(node, Funcao):
            return _FuncaoUsuario(node, env, self)
        if isinstance(node, Chamada):
            return self._executar_chamada(node, env)
        if isinstance(node, ChamadaMembro):
            return self._executar_chamada_membro(node, env)
        if isinstance(node, Novo):
            return self._executar_novo(node, env)
        if isinstance(node, Ternario):
            cond = self._avaliar(node.condicao, env)
            if _e_verdadeiro(cond):
                return self._avaliar(node.verdadeiro, env)
            return self._avaliar(node.falso, env)
        raise ErroRuntime(f"Não é possível avaliar: {type(node).__name__}")

    def _avaliar_compreensao(self, node, env):
        colecao = self._avaliar(node.colecao, env)
        resultados = []
        for item in colecao:
            env.definir(node.var, item)
            if node.filtro:
                cond = self._avaliar(node.filtro, env)
                if not _e_verdadeiro(cond):
                    continue
            resultados.append(self._avaliar(node.elemento, env))
        return resultados

    def _avaliar_template(self, node, env):
        partes = []
        for parte in node.partes:
            if isinstance(parte, Texto):
                partes.append(parte.valor)
            else:
                valor = self._avaliar(parte, env)
                partes.append(_para_texto(valor))
        return "".join(partes)

    def _avaliar_super(self, node, env):
        if self._este_atual is None:
            raise ErroRuntime("'super' usado fora de método")
        cls = self._este_atual._classe
        if not cls.base:
            raise ErroRuntime(f"Classe '{cls.nome}' não tem classe base")
        base_cls = self._classes.get(cls.base)
        if not base_cls:
            raise ErroRuntime(f"Classe base '{cls.base}' não encontrada")
        return _SuperProxy(base_cls, self._este_atual, self)

    def _avaliar_binario(self, node, env):
        from src.lexer.token import TipoToken

        if node.operador == TipoToken.PIPE:
            esq = self._avaliar(node.esquerda, env)
            if isinstance(node.direita, Variavel):
                fn = env.obter(node.direita.nome)
                if isinstance(fn, _FuncaoUsuario):
                    return self._executar_funcao_usuario(fn, [esq], env)
                if callable(fn):
                    return fn(esq)
                raise ErroRuntime(f"'{node.direita.nome}' não é uma função")
            raise ErroRuntime("Pipe requer uma função à direita")

        esq = self._avaliar(node.esquerda, env)
        dir = self._avaliar(node.direita, env)
        op = node.operador

        if op == TipoToken.MAIS:
            if isinstance(esq, str) or isinstance(dir, str):
                return _para_texto(esq) + _para_texto(dir)
            return esq + dir
        if op == TipoToken.MENOS:
            return esq - dir
        if op == TipoToken.VEZES:
            return esq * dir
        if op == TipoToken.DIVIDIR:
            return esq / dir
        if op == TipoToken.MOD:
            return esq % dir

        if op == TipoToken.IGUAL:
            return esq == dir
        if op == TipoToken.DIFERENTE:
            return esq != dir
        if op == TipoToken.MAIOR:
            return esq > dir
        if op == TipoToken.MENOR:
            return esq < dir
        if op == TipoToken.MAIOR_IGUAL:
            return esq >= dir
        if op == TipoToken.MENOR_IGUAL:
            return esq <= dir

        if op == TipoToken.E:
            return _e_verdadeiro(esq) and _e_verdadeiro(dir)
        if op == TipoToken.OU:
            return _e_verdadeiro(esq) or _e_verdadeiro(dir)

        if op == TipoToken.INTERVALO:
            return list(range(int(esq), int(dir) + 1))

        raise ErroRuntime(f"Operador desconhecido: {op}")

    def _avaliar_unario(self, node, env):
        from src.lexer.token import TipoToken
        valor = self._avaliar(node.expressao, env)
        if node.operador == TipoToken.NAO:
            return not _e_verdadeiro(valor)
        if node.operador == TipoToken.MENOS:
            return -valor
        raise ErroRuntime(f"Operador unário desconhecido: {node.operador}")

    def _avaliar_indexacao(self, node, env):
        objeto = self._avaliar(node.objeto, env)
        indice = self._avaliar(node.indice, env)
        if isinstance(objeto, (list, str)):
            return objeto[int(indice)]
        if isinstance(objeto, dict):
            return objeto[indice]
        if isinstance(objeto, _Instancia):
            return objeto.atributos[indice]
        raise ErroRuntime(f"Tipo não suporta indexação: {type(objeto).__name__}")

    def _avaliar_membro(self, node, env):
        objeto = self._avaliar(node.objeto, env)

        if isinstance(objeto, _Instancia):
            if node.nome in objeto.atributos:
                return objeto.atributos[node.nome]
            metodo = objeto._classe._buscar_metodo(node.nome)
            if metodo:
                return _MetodoVinculado(objeto, metodo, self)
            raise ErroRuntime(f"'{objeto._classe.nome}' não tem atributo ou método '{node.nome}'")

        if isinstance(objeto, _SuperProxy):
            metodo = objeto._classe._buscar_metodo(node.nome)
            if metodo:
                return _MetodoVinculado(objeto._instancia, metodo, self)
            raise ErroRuntime(f"Classe base não tem método '{node.nome}'")

        if isinstance(objeto, dict):
            if node.nome in objeto:
                return objeto[node.nome]
            return None
        nome_metodo = self.ALIASES_METODOS.get(node.nome, node.nome)
        if hasattr(objeto, nome_metodo):
            attr = getattr(objeto, nome_metodo)
            if callable(attr):
                return attr
            return attr
        raise ErroRuntime(f"'{type(objeto).__name__}' não tem membro '{node.nome}'")


class _Retorno:
    def __init__(self, valor):
        self.valor = valor


class _FuncaoUsuario:
    def __init__(self, node, closure, interpreter=None):
        self.node = node
        self.closure = closure
        self._interp = interpreter

    def __call__(self, *args):
        if self._interp is None:
            raise ErroRuntime("Funcao nao pode ser chamada fora do interpretador")
        return self._interp._executar_funcao_usuario(self, list(args), self.closure)

    def __repr__(self):
        nome = self.node.nome if self.node.nome else "(anonima)"
        return f"<funcao {nome}>"


class _ClasseUsuario:
    def __init__(self, nome, metodos, base=None, interp=None):
        self.nome = nome
        self.metodos = metodos
        self.base = base
        self._interp = interp

    def _buscar_metodo(self, nome):
        if nome in self.metodos:
            return self.metodos[nome]
        if self.base and self._interp:
            base_cls = self._interp._classes.get(self.base)
            if base_cls:
                return base_cls._buscar_metodo(nome)
        return None

    def __repr__(self):
        return f"<classe {self.nome}>"


class _Instancia:
    def __init__(self, classe, atributos=None):
        self._classe = classe
        self.atributos = atributos or {}

    def __repr__(self):
        return f"<{self._classe.nome} instancia>"

    def __getitem__(self, key):
        return self.atributos[key]

    def __contains__(self, key):
        return key in self.atributos


class _MetodoVinculado:
    def __init__(self, instancia, metodo, interpreter):
        self._instancia = instancia
        self._metodo = metodo
        self._interp = interpreter

    def __call__(self, *args):
        antigo = self._interp._este_atual
        self._interp._este_atual = self._instancia
        try:
            return self._interp._executar_funcao_usuario(self._metodo, list(args), self._metodo.closure)
        finally:
            self._interp._este_atual = antigo

    def __repr__(self):
        return f"<metodo {self._metodo.node.nome}>"


class _SuperProxy:
    def __init__(self, classe, instancia, interpreter):
        self._classe = classe
        self._instancia = instancia
        self._interp = interpreter

    def __repr__(self):
        return f"<super {self._classe.nome}>"


def _e_verdadeiro(valor):
    if valor is None:
        return False
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, (int, float)):
        return valor != 0
    if isinstance(valor, str):
        return len(valor) > 0
    if isinstance(valor, (list, dict)):
        return len(valor) > 0
    return True


def _para_texto(valor):
    if valor is None:
        return "nada"
    if isinstance(valor, bool):
        return "verdadeiro" if valor else "falso"
    if isinstance(valor, float):
        return str(valor)
    if isinstance(valor, list):
        itens = ", ".join(_para_texto(v) for v in valor)
        return f"[{itens}]"
    if isinstance(valor, dict):
        itens = ", ".join(f"{_para_texto(k)}: {_para_texto(v)}" for k, v in valor.items())
        return f"{{{itens}}}"
    return str(valor)
