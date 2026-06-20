from enum import Enum, auto


class TipoToken(Enum):
    INTEIRO = auto()
    FLUTUANTE = auto()
    TEXTO = auto()
    VERDADEIRO = auto()
    FALSO = auto()
    NADA = auto()
    IDENTIFICADOR = auto()

    MAIS = auto()
    MENOS = auto()
    VEZES = auto()
    DIVIDIR = auto()
    MOD = auto()
    PIPE = auto()

    IGUAL = auto()
    DIFERENTE = auto()
    MAIOR = auto()
    MENOR = auto()
    MAIOR_IGUAL = auto()
    MENOR_IGUAL = auto()

    E = auto()
    OU = auto()
    NAO = auto()

    ATRIBUICAO = auto()
    ADICAO_ATRIB = auto()
    SUB_ATRIB = auto()

    ABRE_PAREN = auto()
    FECHA_PAREN = auto()
    ABRE_COLCHETE = auto()
    FECHA_COLCHETE = auto()
    ABRE_CHAVE = auto()
    FECHA_CHAVE = auto()
    VIRGULA = auto()
    PONTO = auto()
    DOIS_PONTOS = auto()
    INTERVALO = auto()

    FIM = auto()
    SE = auto()
    SENAO = auto()
    PARA = auto()
    ATE = auto()
    EM = auto()
    ENQUANTO = auto()
    FUNCAO = auto()
    RETORNAR = auto()
    USAR = auto()
    PARALELO = auto()

    FALAR = auto()
    MOSTRAR = auto()
    DIZER = auto()
    ESCREVER = auto()
    LER = auto()
    LIMPAR = auto()
    PAUSA = auto()
    INFO = auto()
    AVISO = auto()
    ERRO = auto()
    TENTAR = auto()
    CAPTURAR = auto()

    CORRESPONDER = auto()
    CASO = auto()
    GARANTIR = auto()
    FUNCAO_ASYNC = auto()
    ESPERAR = auto()
    CLASSE = auto()
    NOVO = auto()
    ESTE = auto()
    SUPER = auto()
    EXTENDE = auto()
    METODO = auto()
    CONSTRUTOR = auto()
    TEMPLET = auto()

    FIM_DE_LINHA = auto()
    FIM_ARQUIVO = auto()


class Token:
    __slots__ = ("tipo", "valor", "linha", "coluna")

    def __init__(self, tipo, valor, linha, coluna):
        self.tipo = tipo
        self.valor = valor
        self.linha = linha
        self.coluna = coluna

    def __repr__(self):
        return f"Token({self.tipo.name}, {self.valor!r}, L{self.linha}:C{self.coluna})"
