"""Gramática del TP1 (formato + construcciones lingüísticas) y verificación LL(1).
Calcula PRIM (primero) y SGTE (siguiente) con los algoritmos de clase y verifica la condición LL(1).
Terminales = categorías del lexer (más EOL y $).  Nodo vacío = [].
"""
EPS, FIN = 'ε', '$'

_PROD = [
    # ---------------- formato (una línea = un EOL) ----------------
    ('lote',      ['sesion lote_r']),
    ('lote_r',    ['sesion lote_r', 'ε']),
    ('sesion',    ['SESION ID_SESION EOL turnos FIN EOL']),
    ('turnos',    ['turno turnos_r']),
    ('turnos_r',  ['turno turnos_r', 'ε']),
    ('turno',     ['NUM rol DOSPUNTOS texto EOL']),
    ('rol',       ['CLIENTE', 'AGENTE']),
    # ---------------- texto del turno ----------------
    ('texto',     ['oracion texto_r']),
    ('texto_r',   ['PUNTO texto_rr', 'ε']),
    ('texto_rr',  ['oracion texto_r', 'ε']),
    ('oracion',   ['clausula cola']),
    ('cola',      ['PERO clausula cola', 'COMA cola_c', 'ε']),
    ('cola_c',    ['PERO clausula cola', 'clausula cola']),
    ('clausula',  ['adv_t_op nucleo frec']),
    ('adv_t_op',  ['adv_t', 'ε']),
    ('adv_t',     ['T_AHORA', 'T_FUTURO']),
    ('nucleo',    ['sujeto pred_s', 'pred_l', 'TICKET', 'CORTESIA']),
    ('sujeto',    ['sust', 'AGENTE']),
    ('sust',      ['SUST_SERV', 'SUST_ATEN', 'SUST_CLAR', 'SUST_EQUIPO', 'SUST_TICKET', 'SUST_PROB']),
    ('pred_s',    ['NEG pred_neg', 'V_COP atrib', 'v_est compl', 'SE V_EST_RECUR', 'V_CONT compl',
                   'v_acc obj modif_op', 'atrib', 'ε']),
    ('pred_l',    ['NEG pred_neg', 'V_COP atrib', 'v_est compl', 'SE V_EST_RECUR', 'V_CONT compl',
                   'v_acc obj modif_op']),
    ('pred_neg',  ['v_est compl', 'V_COP atrib', 'v_acc obj modif_op']),
    ('v_est',     ['V_EST_OK', 'V_EST_FALLA']),
    ('v_acc',     ['V_ENTENDER', 'V_SOLICITUD', 'V_COMPROMISO', 'V_VAL_ATEN', 'V_VAL_CLAR']),
    ('compl',     ['modif', 'SIN sust', 'ε']),
    ('atrib',     ['modif', 'TICKET']),
    ('modif',     ['INT adj', 'adj']),
    ('modif_op',  ['modif', 'ε']),
    ('adj',       ['ADJ_POS', 'ADJ_NEG']),
    ('frec',      ['FREC frec', 'ε']),
    ('obj',       ['sust', 'TICKET', 'adv_t', 'ε']),
    ('obj_clar',  ['SUST_CLAR', 'ε']),
    ('obj_router', ['SUST_EQUIPO', 'ε']),
    ('ref_op',    ['TICKET', 'T_FUTURO', 'ε']),
]
G = {a: [[] if x == EPS else x.split() for x in alts] for a, alts in _PROD}
INICIO = 'lote'


def prim_cadena(cad, P):
    r = set()
    for s in cad:
        if s not in G:
            r.add(s)
            return r
        r |= P[s] - {EPS}
        if EPS not in P[s]:
            return r
    r.add(EPS)
    return r


def primero():
    P = {A: set() for A in G}
    cambio = True
    while cambio:
        cambio = False
        for A, alts in G.items():
            for alt in alts:
                f = prim_cadena(alt, P)
                if not f <= P[A]:
                    P[A] |= f
                    cambio = True
    return P


def siguiente(P):
    S = {A: set() for A in G}
    S[INICIO].add(FIN)
    cambio = True
    while cambio:
        cambio = False
        for A, alts in G.items():
            for alt in alts:
                for i, B in enumerate(alt):
                    if B not in G:
                        continue
                    f = prim_cadena(alt[i + 1:], P)
                    nuevo = f - {EPS}
                    if EPS in f:
                        nuevo |= S[A]
                    if not nuevo <= S[B]:
                        S[B] |= nuevo
                        cambio = True
    return S


def verificar_ll1(P, S):
    """Devuelve la lista de conflictos (vacía => la gramática es LL(1))."""
    conflictos = []
    for A, alts in G.items():
        prims = [prim_cadena(a, P) for a in alts]
        for i in range(len(alts)):
            for j in range(i + 1, len(alts)):
                inter = (prims[i] - {EPS}) & (prims[j] - {EPS})
                if inter:
                    conflictos.append((A, i, j, 'PRIM INTERSECCION PRIM', inter))
            if EPS in prims[i]:
                for j in range(len(alts)):
                    if j != i and (prims[j] - {EPS}) & S[A]:
                        conflictos.append((A, i, j, 'PRIM INTERSECCION SGTE', (prims[j] - {EPS}) & S[A]))
        if sum(EPS in p for p in prims) > 1:
            conflictos.append((A, -1, -1, 'dos alternativas anulables', set()))
    # no recursión por la izquierda: ningún A deriva A como primer símbolo (directo o indirecto)
    for A in G:
        vistos, pila = set(), [A]
        while pila:
            X = pila.pop()
            for alt in G[X]:
                for s in alt:
                    if s == A:
                        conflictos.append((A, -1, -1, 'recursion por la izquierda', {A}))
                    if s in G and s not in vistos:
                        vistos.add(s); pila.append(s)
                    if s not in G or EPS not in P[s]:
                        break
    return conflictos


def tabla_ll1(P, S):
    """M[A, a] = producción a aplicar (análisis predictivo)."""
    M = {}
    for A, alts in G.items():
        for k, alt in enumerate(alts):
            f = prim_cadena(alt, P)
            for a in f - {EPS}:
                M[(A, a)] = (A, k)
            if EPS in f:
                for b in S[A]:
                    M[(A, b)] = (A, k)
    return M


def fmt(conj):
    return '{' + ', '.join(sorted(conj)) + '}'


if __name__ == '__main__':
    P = primero(); S = siguiente(P)
    print('Terminales:', sorted({s for alts in G.values() for alt in alts for s in alt if s not in G}))
    c = verificar_ll1(P, S)
    print('Conflictos LL(1):', c if c else 'NINGUNO -> la gramatica es LL(1)')
    print('Celdas de la tabla:', len(tabla_ll1(P, S)))
