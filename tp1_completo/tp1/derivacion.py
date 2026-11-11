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
sesion -> KW_SESION ID_SESION EOL turnos KW_FIN EOL
turnos -> turnos turno | turno
turno -> NUM rol DOSPUNTOS texto EOL
rol -> CLIENTE | AGENTE
""")
F1 = gram("""
lote -> sesion lote_r
lote_r -> sesion lote_r | ε
sesion -> KW_SESION ID_SESION EOL turnos KW_FIN EOL
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
sep -> PERO | COMA | COMA PERO
clausula -> T_AHORA nucleo | nucleo
nucleo -> sujeto | sujeto V_COPULA modif | sujeto modif | sujeto V_FUNC | sujeto V_FUNC modif | sujeto V_SEGUIR seg | sujeto SE V_CORTA | sujeto SE V_CORTA frec | sujeto NEG pred_neg | pred_l | TICKET_PAL | TICKET_PAL TICKET | TICKET_PAL V_COPULA TICKET | TICKET | CORTESIA
sujeto -> ASP_SERV | ASP_ATEN | ASP_CLAR | AGENTE
pred_l -> NEG pred_neg | V_FUNC | V_FUNC modif | V_SEGUIR seg | SE V_CORTA | SE V_CORTA frec | V_ENTENDER | V_ENTENDER ASP_CLAR | V_SOLICITUD | V_SOLICITUD ROUTER | T_FUTURO V_COMPROMISO | T_FUTURO V_COMPROMISO TICKET | T_FUTURO V_COMPROMISO T_FUTURO | V_COMPROMISO | V_COMPROMISO TICKET | V_COMPROMISO T_FUTURO
pred_neg -> V_FUNC | V_FUNC modif | V_COPULA modif | V_ENTENDER | V_ENTENDER ASP_CLAR
seg -> modif | NEG ASP_SERV
modif -> INT adj | adj
adj -> ADJ_POS | ADJ_NEG
frec -> frec FREC | FREC
""")

# L1: PASO 1 — eliminación de la recursión por la izquierda  (A -> Aα | β  ≡  A -> βR ; R -> αR | ε)
L1 = gram("""
texto -> lista | lista PUNTO
lista -> oracion lista_r
lista_r -> PUNTO oracion lista_r | ε
oracion -> clausula oracion_r
oracion_r -> sep clausula oracion_r | ε
sep -> PERO | COMA | COMA PERO
clausula -> T_AHORA nucleo | nucleo
nucleo -> sujeto | sujeto V_COPULA modif | sujeto modif | sujeto V_FUNC | sujeto V_FUNC modif | sujeto V_SEGUIR seg | sujeto SE V_CORTA | sujeto SE V_CORTA frec | sujeto NEG pred_neg | pred_l | TICKET_PAL | TICKET_PAL TICKET | TICKET_PAL V_COPULA TICKET | TICKET | CORTESIA
sujeto -> ASP_SERV | ASP_ATEN | ASP_CLAR | AGENTE
pred_l -> NEG pred_neg | V_FUNC | V_FUNC modif | V_SEGUIR seg | SE V_CORTA | SE V_CORTA frec | V_ENTENDER | V_ENTENDER ASP_CLAR | V_SOLICITUD | V_SOLICITUD ROUTER | T_FUTURO V_COMPROMISO | T_FUTURO V_COMPROMISO TICKET | T_FUTURO V_COMPROMISO T_FUTURO | V_COMPROMISO | V_COMPROMISO TICKET | V_COMPROMISO T_FUTURO
pred_neg -> V_FUNC | V_FUNC modif | V_COPULA modif | V_ENTENDER | V_ENTENDER ASP_CLAR
seg -> modif | NEG ASP_SERV
modif -> INT adj | adj
adj -> ADJ_POS | ADJ_NEG
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
sep -> PERO | COMA sep_c
sep_c -> PERO | ε
clausula -> T_AHORA nucleo | nucleo
nucleo -> sujeto pred_s | pred_l | TICKET_PAL tk_op | TICKET | CORTESIA
sujeto -> ASP_SERV | ASP_ATEN | ASP_CLAR | AGENTE
pred_s -> NEG pred_neg | V_COPULA modif | V_FUNC modif_op | V_SEGUIR seg | SE V_CORTA frec_op | modif | ε
pred_l -> NEG pred_neg | V_FUNC modif_op | V_SEGUIR seg | SE V_CORTA frec_op | V_ENTENDER obj_clar | V_SOLICITUD obj_router | T_FUTURO V_COMPROMISO ref_op | V_COMPROMISO ref_op
pred_neg -> V_FUNC modif_op | V_COPULA modif | V_ENTENDER obj_clar
seg -> modif | NEG ASP_SERV
modif -> INT adj | adj
modif_op -> modif | ε
adj -> ADJ_POS | ADJ_NEG
frec_op -> FREC frec_r | ε
frec_r -> FREC frec_r | ε
obj_clar -> ASP_CLAR | ε
obj_router -> ROUTER | ε
ref_op -> TICKET | T_FUTURO | ε
tk_op -> V_COPULA TICKET | TICKET | ε
""")

# L3: PASO 3 — resolución del conflicto PRIM/SGTE en lista_r y simplificación por sustitución = gramática final
LING = ['texto', 'texto_r', 'texto_rr', 'oracion', 'cola', 'cola_c', 'clausula', 'ahora_op', 'nucleo', 'sujeto',
        'pred_s', 'pred_l', 'pred_neg', 'seg', 'modif', 'modif_op', 'adj', 'frec', 'obj_clar', 'obj_router',
        'ref_op', 'tk_op']
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
