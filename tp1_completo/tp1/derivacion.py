"""Derivación paso a paso: gramática descriptiva (original) -> gramática predictiva LL(1).
Cada gramática intermedia se diagnostica con los mismos algoritmos de clase (PRIM, SGTE) y se comprueba
por enumeración que todas generan el MISMO lenguaje (hasta una longitud acotada).
    python3 derivacion.py
"""
import gramatica as gr
EPS = gr.EPS


def gram(texto):
    """Mini-DSL:  'A -> alt1 | alt2'  (una línea por variable; 'ε' = vacío)."""
    G = {}
    for linea in texto.strip().splitlines():
        a, alts = linea.split('->')
        G[a.strip()] = [[] if x.strip() == EPS else x.split() for x in alts.split('|')]
    return G


# ===================================================================== FORMATO
F0 = gram("""
lote -> lote sesion | sesion
sesion -> SESION ID_SESION EOL turnos FIN EOL
turnos -> turnos turno | turno
turno -> NUM rol DOSPUNTOS texto EOL
rol -> CLIENTE | AGENTE
""")
F1 = gram("""
lote -> sesion lote_r
lote_r -> sesion lote_r | ε
sesion -> SESION ID_SESION EOL turnos FIN EOL
turnos -> turno turnos_r
turnos_r -> turno turnos_r | ε
turno -> NUM rol DOSPUNTOS texto EOL
rol -> CLIENTE | AGENTE
""")

# ===================================================================== LINGÜÍSTICA
# L0: gramática DESCRIPTIVA: describe el lenguaje sin preocuparse por la predictividad
L0 = gram("""
texto -> lista | lista PUNTO
lista -> lista PUNTO oracion | oracion
oracion -> oracion sep clausula | clausula
sep -> PERO | COMA | COMA PERO | Y
clausula -> nucleo | ADV_T nucleo | nucleo frec | ADV_T nucleo frec
nucleo -> sujeto | sujeto V_COP atrib | sujeto modif | sujeto TICKET | sujeto est | sujeto SE est | sujeto V_CONT | sujeto V_CONT compl | sujeto acc | sujeto NEG pred_neg | pred_l | TICKET | CORTESIA
pred_l -> NEG pred_neg | V_COP atrib | est | est SUST | SE est | SE est SUST | V_CONT | V_CONT compl | acc
pred_neg -> V_COP atrib | est | est SUST | SE est | SE est SUST | V_CONT | V_CONT compl | acc
est -> V_EST | V_EST compl
acc -> V_ACC | V_ACC obj | V_ACC modif | V_ACC obj modif
compl -> modif | SIN SUST
obj -> SUST | TICKET | ADV_T
sujeto -> SUST | AGENTE
atrib -> modif | TICKET
modif -> INT ADJ | ADJ
frec -> frec FREC | FREC
""")

# L1: PASO 1 — eliminación de la recursión por la izquierda  (A -> Aα | β  ≡  A -> βR ; R -> αR | ε)
L1 = gram("""
texto -> lista | lista PUNTO
lista -> oracion lista_r
lista_r -> PUNTO oracion lista_r | ε
oracion -> clausula oracion_r
oracion_r -> sep clausula oracion_r | ε
sep -> PERO | COMA | COMA PERO | Y
clausula -> nucleo | ADV_T nucleo | nucleo frec | ADV_T nucleo frec
nucleo -> sujeto | sujeto V_COP atrib | sujeto modif | sujeto TICKET | sujeto est | sujeto SE est | sujeto V_CONT | sujeto V_CONT compl | sujeto acc | sujeto NEG pred_neg | pred_l | TICKET | CORTESIA
pred_l -> NEG pred_neg | V_COP atrib | est | est SUST | SE est | SE est SUST | V_CONT | V_CONT compl | acc
pred_neg -> V_COP atrib | est | est SUST | SE est | SE est SUST | V_CONT | V_CONT compl | acc
est -> V_EST | V_EST compl
acc -> V_ACC | V_ACC obj | V_ACC modif | V_ACC obj modif
compl -> modif | SIN SUST
obj -> SUST | TICKET | ADV_T
sujeto -> SUST | AGENTE
atrib -> modif | TICKET
modif -> INT ADJ | ADJ
frec -> FREC frec_r
frec_r -> FREC frec_r | ε
""")

# L2: PASO 2 — factorización por la izquierda (factor común directo, A -> αβ1 | αβ2  ≡  A -> αR ; R -> β1 | β2)
L2 = gram("""
texto -> lista texto_p
texto_p -> PUNTO | ε
lista -> oracion lista_r
lista_r -> PUNTO oracion lista_r | ε
oracion -> clausula oracion_r
oracion_r -> sep clausula oracion_r | ε
sep -> PERO | COMA sep_c | Y
sep_c -> PERO | ε
clausula -> ADV_T nucleo frec_op | nucleo frec_op
frec_op -> FREC frec_r | ε
frec_r -> FREC frec_r | ε
nucleo -> sujeto pred_s | pred_l | TICKET | CORTESIA
pred_s -> NEG pred_neg | V_COP atrib | V_EST compl | SE V_EST compl | V_CONT compl | V_ACC obj modif_op | modif | TICKET | ε
pred_l -> NEG pred_neg | V_COP atrib | V_EST compl sujp | SE V_EST compl sujp | V_CONT compl | V_ACC obj modif_op
pred_neg -> V_COP atrib | V_EST compl sujp | SE V_EST compl sujp | V_CONT compl | V_ACC obj modif_op
compl -> modif | SIN SUST | ε
sujp -> SUST | ε
obj -> SUST | TICKET | ADV_T | ε
modif_op -> modif | ε
sujeto -> SUST | AGENTE
atrib -> modif | TICKET
modif -> INT ADJ | ADJ
""")

# L3: PASO 3 — resolución del conflicto PRIM/SGTE en lista_r y simplificación por sustitución = gramática final
LING = ['texto', 'texto_r', 'texto_rr', 'oracion', 'cola', 'cola_c', 'clausula', 'adv_t_op', 'nucleo', 'sujeto',
        'pred_s', 'pred_l', 'pred_neg', 'atrib', 'compl', 'sujp', 'obj', 'modif', 'modif_op', 'frec']
FORM = ['lote', 'lote_r', 'sesion', 'turnos', 'turnos_r', 'turno', 'rol']
L3 = {a: gr.G[a] for a in LING}
F2 = {a: gr.G[a] for a in FORM if a != 'texto'}


# ===================================================================== diagnóstico y equivalencia
def diagnostico(G, inicio):
    gr.G, gr.INICIO = G, inicio
    P = gr.primero(); S = gr.siguiente(P)
    rec, pp, ps = set(), {}, {}
    for A, i, j, tipo, conj in gr.verificar_ll1(P, S):
        if tipo == 'recursión por la izquierda':
            rec.add(A)
        elif tipo == 'PRIM∩PRIM':
            pp.setdefault(A, set()).update(conj)
        elif tipo == 'PRIM∩SGTE':
            ps.setdefault(A, set()).update(conj)
    return {'recursion': sorted(rec), 'prim_prim': pp, 'prim_sgte': ps}


def lenguaje(G, inicio, N):
    L = {A: set() for A in G}
    cambio = True
    while cambio:
        cambio = False
        for A, alts in G.items():
            for alt in alts:
                cur = {()}
                for s in alt:
                    opts = L[s] if s in G else {(s,)}
                    cur = {x + y for x in cur for y in opts if len(x) + len(y) <= N}
                    if not cur:
                        break
                nuevo = cur - L[A]
                if nuevo:
                    L[A] |= nuevo
                    cambio = True
    return L[inicio]


PASOS_L = [('L0 (original)', L0), ('L1 (sin rec. izq.)', L1), ('L2 (factorizada)', L2), ('L3 (final LL(1))', L3)]
PASOS_F = [('F0 (original)', F0), ('F1 (final LL(1))', F2)]

if __name__ == '__main__':
    import sys
    NL = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    for titulo, pasos, ini, N in (('FORMATO', PASOS_F, 'lote', 21), ('LINGÜÍSTICA', PASOS_L, 'texto', NL)):
        print(f'== {titulo}')
        ref = None
        for nombre, G in pasos:
            d = diagnostico(G, ini)
            lang = lenguaje(G, ini, N)
            ref = lang if ref is None else ref
            print(f'{nombre:22} rec.izq={d["recursion"]}  PRIM∩PRIM={ {k: sorted(v) for k, v in d["prim_prim"].items()} }'
                  f'  PRIM∩SGTE={ {k: sorted(v) for k, v in d["prim_sgte"].items()} }')
            print(f'{"":22} |L(≤{N})|={len(lang)}  igual al original: {lang == ref}')
