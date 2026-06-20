import sqlite3


class _Banco:
    def __init__(self):
        self._conexao = None

    def _checar(self):
        if not self._conexao:
            raise RuntimeError("Banco nao conectado. Use banco.conectar() primeiro")

    def conectar(self, caminho):
        self._conexao = sqlite3.connect(str(caminho))
        self._conexao.row_factory = sqlite3.Row
        self._conexao.isolation_level = None
        return True

    def fechar(self):
        if self._conexao:
            self._conexao.close()
            self._conexao = None
        return True

    def executar(self, sql, params=None):
        self._checar()
        if params is None:
            self._conexao.execute(sql)
        else:
            self._conexao.execute(sql, params)
        if self._conexao.isolation_level is None:
            self._conexao.commit()
        return self._conexao.total_changes

    def buscar(self, sql, params=None):
        self._checar()
        if params is None:
            cursor = self._conexao.execute(sql)
        else:
            cursor = self._conexao.execute(sql, params)
        return [dict(linha) for linha in cursor.fetchall()]

    def buscar_um(self, sql, params=None):
        self._checar()
        if params is None:
            cursor = self._conexao.execute(sql)
        else:
            cursor = self._conexao.execute(sql, params)
        linha = cursor.fetchone()
        return dict(linha) if linha else None

    def criar_tabela(self, sql):
        return self.executar(sql)

    def inserir(self, tabela, dados):
        colunas = ", ".join(dados.keys())
        placeholders = ", ".join("?" for _ in dados)
        sql = f"INSERT INTO {tabela} ({colunas}) VALUES ({placeholders})"
        return self.executar(sql, list(dados.values()))

    def atualizar(self, tabela, dados, onde, params_onde=None):
        set_clause = ", ".join(f"{k} = ?" for k in dados)
        sql = f"UPDATE {tabela} SET {set_clause} WHERE {onde}"
        params = list(dados.values()) + (list(params_onde) if params_onde else [])
        return self.executar(sql, params)

    def deletar(self, tabela, onde, params_onde=None):
        sql = f"DELETE FROM {tabela} WHERE {onde}"
        return self.executar(sql, params_onde)

    def ultimo_id(self):
        self._checar()
        return self._conexao.execute("SELECT last_insert_rowid()").fetchone()[0]

    def contar(self, tabela, onde=None, params_onde=None):
        sql = f"SELECT COUNT(*) as total FROM {tabela}"
        if onde:
            sql += f" WHERE {onde}"
        return self.buscar_um(sql, params_onde)["total"]

    def tabelas(self):
        return [
            r["name"]
            for r in self.buscar(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
        ]

    def iniciar_transacao(self):
        self._checar()
        self._conexao.isolation_level = "DEFERRED"
        self._conexao.execute("BEGIN")
        return True

    def confirmar(self):
        self._checar()
        self._conexao.commit()
        self._conexao.isolation_level = None
        return True

    def desfazer(self):
        self._checar()
        self._conexao.rollback()
        self._conexao.isolation_level = None
        return True

    def migrar(self, versoes):
        for versao in versoes:
            sql = versao.get("sql")
            params = versao.get("params")
            self.executar(sql, params)
        return True


    def modelo(self, nome_tabela, esquema):
        colunas = []
        for campo, tipo in esquema.items():
            m = {"texto": "TEXT", "inteiro": "INTEGER", "real": "REAL", "booleano": "INTEGER", "binario": "BLOB"}
            sql_tipo = m.get(tipo.lower() if isinstance(tipo, str) else "texto", "TEXT")
            colunas.append(f"{campo} {sql_tipo}")
        if "id" not in {k.lower() for k in esquema}:
            colunas.insert(0, "id INTEGER PRIMARY KEY AUTOINCREMENT")
        sql = f"CREATE TABLE IF NOT EXISTS {nome_tabela} ({', '.join(colunas)})"
        self.executar(sql)

        class Modelo:
            def __init__(self, banco, tabela, esquema):
                self._banco = banco
                self._tabela = tabela
                self._esquema = esquema

            def criar(self, **dados):
                self._banco.inserir(self._tabela, dados)
                return self._banco.ultimo_id()

            def buscar(self, id_valor):
                return self._banco.buscar_um(f"SELECT * FROM {self._tabela} WHERE id = ?", [id_valor])

            def atualizar(self, id_valor, **dados):
                return self._banco.atualizar(self._tabela, dados, "id = ?", [id_valor]) if dados else 0

            def deletar(self, id_valor):
                return self._banco.deletar(self._tabela, "id = ?", [id_valor])

            def todos(self, ordem="id ASC"):
                return self._banco.buscar(f"SELECT * FROM {self._tabela} ORDER BY {ordem}")

            def contar(self, onde=None, params=None):
                return self._banco.contar(self._tabela, onde, params)

            def onde(self, clausula, *params):
                return self._banco.buscar(f"SELECT * FROM {self._tabela} WHERE {clausula}", list(params) if params else None)

        return Modelo(self, nome_tabela, esquema)


MODULO = _Banco()
