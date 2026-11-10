"""Parser LL(1) del TP1: descendente recursivo PREDICTIVO guiado por la tabla M[A, a] (gramatica.py).

Un único procedimiento parse(A) elige la producción con M[A, lookahead] (PRIM / SGTE de clase), llama
recursivamente a parse() por cada variable de la producción y a _match() por cada terminal.
Recuperación de errores: modo pánico con conjuntos de sincronización = PRIM(A) ∪ SGTE(A) ∪ {EOL}
(Aho, §4.4.5): ante M[A, a] vacía se descartan tokens hasta uno de sincronización; si es de SGTE(A)
se abandona A (nodo de error) y el análisis continúa. Una cláusula con error queda marcada y el
resto del turno se sigue analizando.
"""
from dataclasses import dataclass, field

import gramatica as gr
from lexico import Token

EPS, G = gr.EPS, gr.G
_P = gr.primero()
_S = gr.siguiente(_P)
M = gr.tabla_ll1(_P, _S)


def sincronizacion(var):
    return (_P[var] - {EPS}) | _S[var] | {'EOL'}


def _alcanzables(ini):
    vistos, pila = {ini}, [ini]
    while pila:
        for alt in G[pila.pop()]:
            for s in alt:
                if s in G and s not in vistos:
                    vistos.add(s)
                    pila.append(s)
    return vistos


VARS_TEXTO = _alcanzables('texto')
# terminales que admite la gramática lingüística (el resto de las categorías no puede formar parte de un turno)
TERMINALES_TEXTO = {s for v in VARS_TEXTO for alt in G[v] for s in alt if s not in G}


@dataclass
class Nodo:
    var: str
    prod: int                     # índice de producción en G[var]; -1 = error de sincronización
    hijos: list = field(default_factory=list)
    error: bool = False
    rango: tuple = (0, 0)         # [ini, fin) sobre la secuencia de tokens del parser

    @property
    def produccion(self):
        return (' '.join(G[self.var][self.prod]) or 'ε') if self.prod >= 0 else 'ERROR'

    def hojas(self):
        for h in self.hijos:
            if isinstance(h, Nodo):
                yield from h.hojas()
            elif h is not None:
                yield h


def arbol(n):
    """Representación compacta (los nodos ε se omiten)."""
    if isinstance(n, Token):
        return f'{n.categoria}«{n.lexema}»'
    if n.prod < 0:
        return f'{n.var}!ERROR'
    partes = [arbol(h) for h in n.hijos
              if h is not None and not (isinstance(h, Nodo) and h.prod >= 0 and not h.hijos)]
    return f'{n.var}[' + ' '.join(partes) + ']'


class AnalizadorSintactico:
    def __init__(self, tokens, eol):
        self.t = list(tokens) + [eol]
        self.i = 0
        self.n_err = 0
        self.errores, self.descartados, self.pasos = [], [], []

    @property
    def la(self):
        return self.t[self.i]

    def _error(self, var, esperado, msg):
        self.n_err += 1
        self.errores.append({'variable': var, 'token': self.la.categoria, 'lexema': self.la.lexema,
                             'desp': self.la.desp, 'esperado': sorted(esperado), 'detalle': msg})

    def parse(self, var):
        i0, e0 = self.i, self.n_err
        ent = M.get((var, self.la.categoria))
        if ent is None:                                    # celda vacía: error + modo pánico
            sinc = sincronizacion(var)
            self._error(var, {a for (v, a) in M if v == var},
                        f'token {self.la.categoria} inesperado al analizar <{var}>')
            self.pasos.append(f'ERROR M[{var}, {self.la.categoria}] vacía → se descartan tokens hasta '
                              f'{{{", ".join(sorted(sinc))}}}')
            while self.la.categoria not in sinc:
                self.descartados.append(self.la)
                self.i += 1
            ent = M.get((var, self.la.categoria))
            if ent is None:                                # el token es de SGTE(A) y A no es anulable: se abandona A
                self.pasos.append(f'  → se abandona <{var}> con lookahead {self.la.categoria}')
                return Nodo(var, -1, [], True, (i0, self.i))
        k = ent[1]
        nodo = Nodo(var, k)
        self.pasos.append(f'M[{var}, {self.la.categoria}] = {var} → {" ".join(G[var][k]) or "ε"}')
        for s in G[var][k]:
            nodo.hijos.append(self.parse(s) if s in G else self._match(s))
        nodo.rango = (i0, self.i)
        if var == 'clausula' and self.n_err > e0:
            nodo.error = True                              # la cláusula no es interpretable
        return nodo

    def _match(self, terminal):
        if self.la.categoria == terminal:
            tok = self.la
            self.i += 1
            return tok
        self._error(terminal, {terminal}, f'se esperaba {terminal} y se encontró {self.la.categoria}')
        self.pasos.append(f'ERROR se esperaba {terminal}, lookahead {self.la.categoria}')
        return None

    def analizar(self):
        raiz = self.parse('texto')
        while self.la.categoria != 'EOL':                  # defensivo: nunca debería ocurrir
            self.descartados.append(self.la)
            self.i += 1
        return raiz
