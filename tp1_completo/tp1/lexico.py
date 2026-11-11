"""Analizador léxico del TP1 (Speech Analytics).
Procedimiento de clase: ER -> AFN (Thompson) -> AFD (subconjuntos) -> mover() + lexema más largo
+ prioridad para resolver ambigüedad léxica.  Sin usar el módulo `re`.
"""
import json
import unicodedata
from dataclasses import dataclass

EPS = None  # transición vacía

# ---------------------------------------------------------------- 1. Normalización y alfabeto
LETRAS = frozenset('abcdefghijklmnopqrstuvwxyzñ')


def plegar(ch):
    """minúscula + sin tilde, carácter a carácter (longitud preservada => offsets válidos). Conserva ñ."""
    if ch in 'ñÑ':
        return 'ñ'
    base = unicodedata.normalize('NFD', ch)[0].lower()
    return base if len(base) == 1 else ch


def simbolo(c):
    """Clase de símbolo del alfabeto Σ para un carácter ya plegado."""
    if c in LETRAS:
        return c
    if '0' <= c <= '9':
        return 'D'
    if c in '-:.,':
        return c
    if c in '¿?¡!':
        return 'Q'
    if c in ' \t':
        return ' '
    return '?'            # fuera de Σ => error léxico


ALFABETO = LETRAS | frozenset('D-:.,Q')

# ---------------------------------------------------------------- 2. ER como árbol + Thompson
def sim(conj): return ('sim', frozenset(conj))
def lit(txt):  return ('cat', [sim(simbolo(c)) for c in txt])
def cat(*xs):  return ('cat', list(xs))
def mas(x):    return ('plus', x)
def est(x):    return ('star', x)

DIG, LETRA = sim('D'), sim(LETRAS)


def rep(x, n, m):
    """x{n,m} = x^n (x(x(x)?)?)?  (la notación de potencia vista en clase)"""
    interno = None
    for _ in range(m - n):
        interno = ('opt', cat(x, interno) if interno else x)
    return cat(*([x] * n + ([interno] if interno else [])))


class AFN:
    def __init__(self):
        self.n, self.mov = 0, {}

    def nuevo(self):
        self.n += 1
        return self.n - 1

    def arista(self, i, a, j):
        self.mov.setdefault((i, a), set()).add(j)


def thompson(afn, r):
    t = r[0]
    if t == 'sim':
        i, f = afn.nuevo(), afn.nuevo()
        for s in r[1]:
            afn.arista(i, s, f)
        return i, f
    if t == 'cat':
        i, f = thompson(afn, r[1][0])
        for x in r[1][1:]:
            i2, f2 = thompson(afn, x)
            afn.arista(f, EPS, i2)
            f = f2
        return i, f
    if t == 'alt':
        i, f = afn.nuevo(), afn.nuevo()
        for x in r[1]:
            i2, f2 = thompson(afn, x)
            afn.arista(i, EPS, i2); afn.arista(f2, EPS, f)
        return i, f
    if t == 'star':
        i, f = afn.nuevo(), afn.nuevo()
        i2, f2 = thompson(afn, r[1])
        afn.arista(i, EPS, i2); afn.arista(i, EPS, f)
        afn.arista(f2, EPS, i2); afn.arista(f2, EPS, f)
        return i, f
    if t == 'plus':                      # r+ = r r*
        return thompson(afn, cat(r[1], est(r[1])))
    if t == 'opt':                       # r? = r | ε
        i, f = afn.nuevo(), afn.nuevo()
        i2, f2 = thompson(afn, r[1])
        afn.arista(i, EPS, i2); afn.arista(i, EPS, f); afn.arista(f2, EPS, f)
        return i, f
    raise ValueError(t)

# ---------------------------------------------------------------- 3. Subconjuntos
def cierre(afn, S):
    res, pila = set(S), list(S)
    while pila:
        for t in afn.mov.get((pila.pop(), EPS), ()):
            if t not in res:
                res.add(t); pila.append(t)
    return frozenset(res)


def mover_afn(afn, T, a):
    return {t for s in T for t in afn.mov.get((s, a), ())}


@dataclass
class AFD:
    trans: dict        # (estado, símbolo) -> estado
    finales: dict      # estado -> (categoría, canónico)
    ambiguos: dict     # estado -> [categorías en conflicto resueltas por prioridad]
    subconj: dict      # estado -> conjunto de estados del AFN (para explicar en el informe)


def construir(patrones, alfabeto=ALFABETO):
    """patrones: lista ordenada por PRIORIDAD (índice menor = más prioridad) de (categoría, canónico, ER)."""
    afn = AFN()
    inicio = afn.nuevo()
    fin_afn = {}
    for prio, (c, canon, er) in enumerate(patrones):
        i, f = thompson(afn, er)
        afn.arista(inicio, EPS, i)
        fin_afn[f] = (prio, c, canon)
    A = cierre(afn, {inicio})
    ids, pend, trans = {A: 0}, [A], {}
    while pend:
        T = pend.pop()
        for a in sorted(alfabeto):
            U = cierre(afn, mover_afn(afn, T, a))
            if not U:
                continue
            if U not in ids:
                ids[U] = len(ids); pend.append(U)
            trans[(ids[T], a)] = ids[U]
    finales, ambiguos = {}, {}
    for S, e in ids.items():
        fs = sorted(fin_afn[s] for s in S if s in fin_afn)
        if fs:
            finales[e] = (fs[0][1], fs[0][2])            # gana la prioridad más alta
            if len({x[1] for x in fs}) > 1:
                ambiguos[e] = [x[1] for x in fs]
    return AFD(trans, finales, ambiguos, {e: S for S, e in ids.items()})

# ---------------------------------------------------------------- 4. Patrones del TP
ESTRUCTURA = [  # (categoría, canónico, ER)   -- orden = prioridad
    ('KW_SESION', 'SESION', lit('sesion')),
    ('KW_FIN', 'FIN', lit('fin')),
    ('CLIENTE', 'CLIENTE', lit('cliente')),
    ('AGENTE', 'AGENTE', lit('agente')),
    ('ID_SESION', None, cat(lit('s'), DIG, DIG)),
    ('NUM', None, mas(DIG)),
    ('DOSPUNTOS', None, lit(':')),
    ('PUNTO', None, lit('.')),
    ('COMA', None, lit(',')),
    ('SIGNO', None, sim('Q')),
    ('TICKET', None, cat(lit('tk-'), rep(DIG, 3, 6))),       # TK- y 3 a 6 dígitos
    ('TICKET_MAL', None, cat(lit('tk-'), est(DIG))),         # TK- con <3 ó >6 dígitos: error léxico específico
]


def cargar_vocabulario(ruta):
    with open(ruta, encoding='utf-8-sig') as f:        # utf-8-sig: tolera el BOM de los editores de Windows
        return json.load(f)


def patrones_vocabulario(vocab):
    """Control de duplicados: una forma superficial no puede tener dos categorías/canónicos."""
    vistos, pats = {}, []
    for categoria, canonicos in vocab.items():
        for canon, formas in canonicos.items():
            for forma in formas:
                forma = ''.join(plegar(c) for c in forma)
                if forma in vistos:
                    raise ValueError(f'forma duplicada {forma!r}: {vistos[forma]} vs {(categoria, canon)}')
                vistos[forma] = (categoria, canon)
                pats.append((categoria, canon, lit(forma)))
    return pats


def construir_afd(vocab):
    pats = ESTRUCTURA + patrones_vocabulario(vocab) + [('PALABRA', None, mas(LETRA))]  # PALABRA: prioridad mínima
    return construir(pats)

# ---------------------------------------------------------------- 5. Scanner (lexema más largo)
@dataclass
class Token:
    categoria: str
    lexema: str          # original
    norm: str            # normalizado (minúsculas, sin tildes; TICKET en mayúsculas)
    canon: str | None    # forma canónica del vocabulario
    sesion: str | None
    turno: int | None
    desp: int            # desplazamiento (0-based) dentro de la línea
    corregido_de: str | None = None   # forma normalizada original si el corrector la cambió


def escanear(texto, afd, sesion=None, turno=None, base=0):
    plegado = ''.join(plegar(c) for c in texto)
    toks, i, n = [], 0, len(texto)
    while i < n:
        if simbolo(plegado[i]) == ' ':
            i += 1
            continue
        estado, j, ultimo = 0, i, None
        while j < n:
            nxt = afd.trans.get((estado, simbolo(plegado[j])))
            if nxt is None:
                break
            estado, j = nxt, j + 1
            if estado in afd.finales:
                ultimo = (j, afd.finales[estado])
        if ultimo is None:                                     # ningún patrón: error léxico
            fin, (cat_, canon) = i + 1, ('DESCONOCIDO', None)
        else:
            fin, (cat_, canon) = ultimo
        norm = plegado[i:fin].upper() if cat_ == 'TICKET' else plegado[i:fin]
        toks.append(Token(cat_, texto[i:fin], norm, canon, sesion, turno, base + i))
        i = fin
    return toks


if __name__ == '__main__':
    import sys
    afd = construir_afd(cargar_vocabulario('vocabulario.json'))
    print(f'AFD: {len({e for e, _ in afd.trans} | set(afd.trans.values()))} estados, '
          f'{len(afd.ambiguos)} estados con ambigüedad léxica resuelta por prioridad')
    for linea in sys.argv[1:] or ['2 CLIENTE: El internet está lentto. Ver TK-204, TK-12 y TK-1234567 ¡Gracias!']:
        for t in escanear(linea, afd, 'S01', 2):
            print(f'{t.desp:>3} {t.categoria:<11} {t.lexema!r:<14} norm={t.norm!r:<12} canon={t.canon}')
