from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Programa:
    nodes: list = field(default_factory=list)


@dataclass
class Atribuicao:
    nome: str
    valor: Any
    tipo: Optional[str] = None


@dataclass
class AtribuicaoMembro:
    objeto: Any
    nome: str
    valor: Any


@dataclass
class AtribuicaoIndexada:
    objeto: Any
    indice: Any
    valor: Any


@dataclass
class Falar:
    expressao: Any


@dataclass
class Ler:
    prompt: Optional[Any] = None


@dataclass
class Limpar:
    pass


@dataclass
class Log:
    nivel: str
    mensagem: Any


@dataclass
class Pausa:
    tempo: Any


@dataclass
class Se:
    condicao: Any
    corpo: list
    senao: Optional[list] = None


@dataclass
class ParaAte:
    var: str
    ate: Any
    corpo: list


@dataclass
class ParaEm:
    var: str
    colecao: Any
    corpo: list


@dataclass
class Enquanto:
    condicao: Any
    corpo: list


@dataclass
class Funcao:
    nome: str
    params: list
    corpo: list


@dataclass
class Chamada:
    nome: str
    argumentos: list
    argumentos_nomeados: list = field(default_factory=list)


@dataclass
class ChamadaMembro:
    objeto: Any
    nome: str
    argumentos: list
    argumentos_nomeados: list = field(default_factory=list)


@dataclass
class Retornar:
    valor: Optional[Any] = None


@dataclass
class Paralelo:
    corpo: list


@dataclass
class Tentar:
    corpo: list
    capturar: list


@dataclass
class Usar:
    modulo: str


@dataclass
class Numero:
    valor: Any


@dataclass
class Texto:
    valor: str


@dataclass
class Booleano:
    valor: bool


@dataclass
class Nada:
    pass


@dataclass
class ListaExpr:
    elementos: list


@dataclass
class ListaCompreensao:
    elemento: Any
    var: str
    colecao: Any
    filtro: Optional[Any] = None


@dataclass
class DicionarioExpr:
    pares: dict


@dataclass
class Variavel:
    nome: str


@dataclass
class Indexacao:
    objeto: Any
    indice: Any


@dataclass
class Membro:
    objeto: Any
    nome: str


@dataclass
class Binario:
    esquerda: Any
    operador: Any
    direita: Any


@dataclass
class Unario:
    operador: Any
    expressao: Any


@dataclass
class Template:
    partes: list


@dataclass
class Ternario:
    verdadeiro: Any
    condicao: Any
    falso: Any


@dataclass
class Corresponder:
    valor: Any
    casos: list


@dataclass
class Caso:
    padrao: Any
    corpo: list


@dataclass
class Classe:
    nome: str
    construtor: Optional[Any] = None
    metodos: list = field(default_factory=list)
    base: Optional[str] = None


@dataclass
class Este:
    pass


@dataclass
class Super:
    argumentos: list = field(default_factory=list)


@dataclass
class Garantir:
    condicao: Any
    mensagem: Optional[str] = None


@dataclass
class FuncaoAsync:
    nome: str
    params: list
    corpo: list


@dataclass
class Esperar:
    chamada: Any


@dataclass
class Novo:
    nome: str
    argumentos: list
