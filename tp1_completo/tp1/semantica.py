"""Acciones semánticas del TP1: definición dirigida por la sintaxis sobre el árbol del parser LL(1).

Cada regla está asociada a una PRODUCCIÓN (clave = (variable, texto de la producción)) y calcula
atributos sintetizados que devuelve a su padre (reglas semánticas con valores de retorno).
Resultado de cada cláusula: un "hecho" con actor, aspecto, valoración, declaración de funcionamiento
y la lista de reglas aplicadas (para la trazabilidad: turno + fragmento + regla).

Para modificar el comportamiento en la defensa basta con editar la regla de la producción (sección 2),
la tabla de reglas de estado (sección 4) o los interruptores de la sección 0.
"""
from sintaxis import Nodo, G
from lexico import Token

# ============================================================ 0. Interruptores de política
# False: la última declaración del CLIENTE sobre el funcionamiento prevalece SIEMPRE sobre las promesas
#        del agente (lectura literal del enunciado, §5).
# True : una promesa del agente POSTERIOR a una falla declarada por el cliente deja el estado PENDIENTE.
PROMESA_POSTERIOR_A_FALLA_ES_PENDIENTE = False

ASPECTOS = ('SERVICIO', 'ATENCION', 'CLARIDAD')
ASP_DE = {'ASP_SERV': 'SERVICIO', 'ASP_ATEN': 'ATENCION', 'ASP_CLAR': 'CLARIDAD',
          'AGENTE': 'ATENCION'}                       # «el agente fue amable» es una opinión sobre la ATENCION
POL = {'ADJ_POS': +1, 'ADJ_NEG': -1}
NOMBRE_POL = {+1: 'POSITIVA', -1: 'NEGATIVA'}

# ============================================================ 1. Catálogo de reglas (id -> descripción)
REGLAS = {
    'R-SUJ':    'sujeto ⇒ aspecto: ASP_SERV→SERVICIO, ASP_ATEN→ATENCION, ASP_CLAR→CLARIDAD, AGENTE→ATENCION',
    'R-COP':    'sujeto [V_COPULA] modif ⇒ valoración del aspecto del sujeto con la polaridad del adjetivo',
    'R-FUNC':   'V_FUNC [modif] ⇒ SERVICIO; polaridad del adjetivo (POSITIVA si no hay adjetivo); declaración OK/FALLA',
    'R-NEG':    'NEG invierte la polaridad del predicado que le sigue; su alcance es pred_neg/seg y no cruza PERO ni COMA',
    'R-MUY':    'INT («muy») marca intensidad ALTA del adjetivo inmediato; no cambia la polaridad',
    'R-SEG-ADJ': 'V_SEGUIR modif ⇒ SERVICIO; «sigue» + adjetivo negativo = FALLA, + positivo = OK',
    'R-SEG-SIN': 'V_SEGUIR NEG ASP_SERV («sigo sin internet») ⇒ SERVICIO NEGATIVA; declaración FALLA',
    'R-CORTE':  'SE V_CORTA [FREC…] ⇒ SERVICIO NEGATIVA; declaración RECUR (recurrente si hay frecuencia)',
    'R-ENT':    '[NEG] V_ENTENDER [ASP_CLAR] ⇒ CLARIDAD: positiva si entendió, negativa con NEG',
    'R-MEN':    'sujeto sin predicado ⇒ mención NEUTRA del aspecto (sin polaridad)',
    'R-SOLIC':  'V_SOLICITUD [ROUTER] ⇒ solicitud de seguimiento (no es compromiso ni valoración)',
    'R-COMPR':  '[T_FUTURO] V_COMPROMISO [TICKET|T_FUTURO] ⇒ compromiso futuro',
    'R-TICKET': 'TICKET_PAL [V_COPULA] TICKET | TICKET ⇒ referencia a un ticket (entidad)',
    'R-CORT':   'CORTESIA ⇒ sin valoración ni estado',
    'R-AHORA':  'T_AHORA ⇒ la cláusula se refiere al momento actual',
    'R-PERO':   'PERO ⇒ la cláusula queda en contraste con la anterior; ambas se conservan por separado',
    'R-EST-RES':  'última declaración del CLIENTE = funciona (OK) ⇒ RESUELTO',
    'R-EST-NORES': 'última declaración del CLIENTE = la falla persiste ⇒ NO_RESUELTO',
    'R-EST-TEMP': 'el CLIENTE informa recuperación y también recurrencia ⇒ TEMPORAL',
    'R-EST-PEND': 'sin declaración del CLIENTE y con compromiso futuro del agente ⇒ PENDIENTE',
    'R-EST-NC':   'sin evidencia suficiente ⇒ NO_CONFIRMADO',
    'R-EST-PREC': 'precedencia: la declaración explícita del CLIENTE prevalece sobre las promesas del agente',
}

# ============================================================ 2. Reglas semánticas por producción
ACC = {}


def acc(var, produccion):
    assert any((' '.join(a) or 'ε') == produccion for a in G[var]), f'{var} no tiene la producción «{produccion}»'

    def deco(f):
        ACC[(var, produccion)] = f
        return f
    return deco


def ev(n):
    """Evalúa los atributos de un nodo con la regla de su producción."""
    if not isinstance(n, Nodo):
        return None
    f = ACC.get((n.var, n.produccion))
    return f(n) if f else None


# ---- adjetivos y modificadores
@acc('adj', 'ADJ_POS')
@acc('adj', 'ADJ_NEG')
def _adj(n):
    return {'pol': POL[n.hijos[0].categoria], 'toks': [n.hijos[0]]}


@acc('modif', 'adj')
def _modif_adj(n):
    return ev(n.hijos[0])


@acc('modif', 'INT adj')
def _modif_int(n):
    a = ev(n.hijos[1])
    return {**a, 'int': 'ALTA', 'toks': [n.hijos[0]] + a['toks']}          # R-MUY


@acc('modif_op', 'modif')
def _modif_op(n):
    return ev(n.hijos[0])


@acc('modif_op', 'ε')
def _modif_op_vacio(n):
    return None


# ---- elementos opcionales
@acc('obj_clar', 'ASP_CLAR')
def _obj_clar(n):
    return n.hijos[0]


@acc('obj_clar', 'ε')
@acc('obj_router', 'ε')
@acc('ahora_op', 'ε')
def _vacio(n):
    return None


@acc('obj_router', 'ROUTER')
def _obj_router(n):
    return n.hijos[0]


@acc('ahora_op', 'T_AHORA')
def _ahora(n):
    return n.hijos[0]


@acc('frec', 'FREC frec')
def _frec(n):
    return 1 + ev(n.hijos[1])


@acc('frec', 'ε')
def _frec_vacio(n):
    return 0


@acc('ref_op', 'TICKET')
def _ref_ticket(n):
    return {'ticket': n.hijos[0]}


@acc('ref_op', 'T_FUTURO')
def _ref_plazo(n):
    return {'plazo': n.hijos[0]}


@acc('ref_op', 'ε')
def _ref_vacio(n):
    return {}


@acc('tk_op', 'V_COPULA TICKET')
def _tk1(n):
    return {'ticket': n.hijos[1]}


@acc('tk_op', 'TICKET')
def _tk2(n):
    return {'ticket': n.hijos[0]}


@acc('tk_op', 'ε')
def _tk3(n):
    return {}


# ---- sujeto
@acc('sujeto', 'ASP_SERV')
@acc('sujeto', 'ASP_ATEN')
@acc('sujeto', 'ASP_CLAR')
@acc('sujeto', 'AGENTE')
def _sujeto(n):
    return {'asp': ASP_DE[n.hijos[0].categoria], 'tok': n.hijos[0]}


# ---- predicados (atributo 'k' = tipo de predicado)
def _pred_func(v, m):
    return {'k': 'FUNC', 'pol': m['pol'] if m else +1, 'int': m.get('int') if m else None, 'reglas': ['R-FUNC']}


def _pred_cop(m):
    return {'k': 'COP', 'pol': m['pol'], 'int': m.get('int'), 'reglas': ['R-COP']}


def _pred_ent(obj):
    return {'k': 'ENT', 'pol': +1, 'obj': obj, 'reglas': ['R-ENT']}


@acc('pred_neg', 'V_FUNC modif_op')
@acc('pred_s', 'V_FUNC modif_op')
@acc('pred_l', 'V_FUNC modif_op')
def _p_func(n):
    return _pred_func(n.hijos[0], ev(n.hijos[1]))


@acc('pred_neg', 'V_COPULA modif')
@acc('pred_s', 'V_COPULA modif')
def _p_cop(n):
    return _pred_cop(ev(n.hijos[1]))


@acc('pred_s', 'modif')
def _p_cop_dir(n):
    return _pred_cop(ev(n.hijos[0]))


@acc('pred_neg', 'V_ENTENDER obj_clar')
@acc('pred_l', 'V_ENTENDER obj_clar')
def _p_ent(n):
    return _pred_ent(ev(n.hijos[1]))


@acc('pred_s', 'NEG pred_neg')
@acc('pred_l', 'NEG pred_neg')
def _p_neg(n):
    return {**ev(n.hijos[1]), 'neg': True}                                  # R-NEG: alcance = pred_neg


@acc('pred_s', 'ε')
def _p_mencion(n):
    return {'k': 'MENCION', 'reglas': ['R-MEN']}


@acc('seg', 'modif')
def _seg_adj(n):
    m = ev(n.hijos[0])
    return {'k': 'SEG_ADJ', 'pol': m['pol'], 'int': m.get('int'), 'reglas': ['R-SEG-ADJ']}


@acc('seg', 'NEG ASP_SERV')
def _seg_sin(n):
    return {'k': 'SEG_SIN', 'pol': -1, 'reglas': ['R-SEG-SIN']}


@acc('pred_l', 'V_SEGUIR seg')
def _p_seguir(n):
    return ev(n.hijos[1])


@acc('pred_l', 'SE V_CORTA frec')
def _p_corta(n):
    return {'k': 'CORTE', 'pol': -1, 'n_frec': ev(n.hijos[2]), 'reglas': ['R-CORTE']}


@acc('pred_l', 'V_SOLICITUD obj_router')
def _p_solic(n):
    return {'k': 'SOLIC', 'ent': ev(n.hijos[1]), 'reglas': ['R-SOLIC']}


@acc('pred_l', 'T_FUTURO V_COMPROMISO ref_op')
def _p_compr1(n):
    return {'k': 'COMPR', 'ref': ev(n.hijos[2]), 'reglas': ['R-COMPR']}


@acc('pred_l', 'V_COMPROMISO ref_op')
def _p_compr2(n):
    return {'k': 'COMPR', 'ref': ev(n.hijos[1]), 'reglas': ['R-COMPR']}


# ---- hecho de una cláusula
def _hecho(tipo, **kw):
    h = {'tipo': tipo, 'aspecto': None, 'valoracion': None, 'intensidad': None, 'negada': False,
         'declaracion': None, 'entidades': [], 'reglas': [], 'temporal': None}
    h.update(kw)
    return h


def _construir(p, aspecto, con_sujeto):
    """Convierte los atributos de un predicado (y el aspecto del sujeto, si lo hay) en un hecho."""
    k, reglas = p['k'], (['R-SUJ'] if con_sujeto else []) + list(p.get('reglas', []))
    if k == 'MENCION':
        return _hecho('MENCION', aspecto=aspecto, valoracion='NEUTRA', reglas=reglas)
    if k == 'SOLIC':
        ent = p['ent'].norm.upper() if p['ent'] else None
        return _hecho('SOLICITUD', entidades=[ent] if ent else [], reglas=reglas)
    if k == 'COMPR':
        tk = p['ref'].get('ticket')
        return _hecho('COMPROMISO', entidades=[tk.norm] if tk else [], reglas=reglas)
    asp = aspecto or ('CLARIDAD' if k == 'ENT' else 'SERVICIO')
    pol, neg = p['pol'], p.get('neg', False)
    if neg:
        pol, reglas = -pol, reglas + ['R-NEG']
    if p.get('int'):
        reglas.append('R-MUY')
    decl = None
    if asp == 'SERVICIO':
        if k in ('FUNC', 'SEG_ADJ'):
            decl = 'OK' if pol > 0 else 'FALLA'
        elif k == 'SEG_SIN':
            decl = 'FALLA'
        elif k == 'CORTE':
            decl = 'RECUR'
    tipo = 'VALORACION' if k in ('COP', 'ENT') else 'FUNCIONAMIENTO'
    return _hecho(tipo, aspecto=asp, valoracion=NOMBRE_POL[pol], intensidad=p.get('int'), negada=neg,
                  declaracion=decl, reglas=reglas)


@acc('nucleo', 'sujeto pred_s')
def _n_sujeto(n):
    s, p = ev(n.hijos[0]), ev(n.hijos[1])
    return _construir(p, s['asp'], True)


@acc('nucleo', 'pred_l')
def _n_pred(n):
    return _construir(ev(n.hijos[0]), None, False)


@acc('nucleo', 'TICKET_PAL tk_op')
def _n_tkpal(n):
    tk = ev(n.hijos[1]).get('ticket')
    return _hecho('TICKET', entidades=[tk.norm] if tk else [], reglas=['R-TICKET'])


@acc('nucleo', 'TICKET')
def _n_tk(n):
    return _hecho('TICKET', entidades=[n.hijos[0].norm], reglas=['R-TICKET'])


@acc('nucleo', 'CORTESIA')
def _n_cort(n):
    return _hecho('CORTESIA', reglas=['R-CORT'])


@acc('clausula', 'ahora_op nucleo')
def _clausula(n):
    ah, h = ev(n.hijos[0]), ev(n.hijos[1])
    if ah:
        h['temporal'] = 'AHORA'
        h['reglas'].append('R-AHORA')
    return h


# ============================================================ 3. Recorrido del árbol
def clausulas(raiz):
    """Genera (nodo_clausula, conector_previo) en orden textual; conector ∈ {None, 'COMA', 'PERO', 'PUNTO'}."""
    estado = {'sep': None}
    salida = []

    def rec(n):
        if isinstance(n, Token):
            if n.categoria in ('PERO', 'COMA', 'PUNTO'):
                estado['sep'] = 'PERO' if n.categoria == 'PERO' else (estado['sep'] if estado['sep'] == 'PERO' else n.categoria)
            return
        if n is None:
            return
        if n.var == 'clausula':
            salida.append((n, estado['sep']))
            estado['sep'] = None
            return
        for h in n.hijos:
            rec(h)
    rec(raiz)
    return salida


# ============================================================ 4. Agregación por turno y sesión
def combinar(valoraciones):
    s = set(valoraciones)
    if {'POSITIVA', 'NEGATIVA'} <= s:
        return 'MIXTA'                         # evidencias de ambas polaridades: no se promedian ni se cancelan
    for v in ('POSITIVA', 'NEGATIVA', 'NEUTRA'):
        if v in s:
            return v
    return 'SIN_EVIDENCIA'


def valoraciones_por_aspecto(cls):
    return {a: combinar([c['valoracion'] for c in cls if c['aspecto'] == a and c['valoracion']]) for a in ASPECTOS}


def resumen_aspectos(cls):
    """Resumen por aspecto con la evidencia del CLIENTE; las opiniones del AGENTE se conservan aparte."""
    res = {}
    for a in ASPECTOS:
        cli = [c for c in cls if c['aspecto'] == a and c['valoracion'] and c['actor'] == 'CLIENTE']
        ag = [c for c in cls if c['aspecto'] == a and c['valoracion'] and c['actor'] == 'AGENTE']
        res[a] = {'valoracion': combinar([c['valoracion'] for c in cli]),
                  'evidencias': [c['id'] for c in cli],
                  'opiniones_agente': [{'id': c['id'], 'valoracion': c['valoracion']} for c in ag]}
    return res


def decidir_estado(cls):
    """Estado conversacional de la sesión. cls = cláusulas interpretadas, en orden (turno, posición)."""
    decl = [c for c in cls if c['actor'] == 'CLIENTE' and c['declaracion']]
    comps = [c for c in cls if c['actor'] == 'AGENTE' and c['tipo'] == 'COMPROMISO']
    if decl:
        estado, regla, evid = None, None, []
        for turno in sorted({c['turno'] for c in decl}):
            ds = [c for c in decl if c['turno'] == turno]
            tipos = [c['declaracion'] for c in ds]
            if 'OK' in tipos and 'RECUR' in tipos and tipos[-1] in ('OK', 'RECUR'):
                estado, regla = 'TEMPORAL', 'R-EST-TEMP'
                evid = [c['id'] for c in ds if c['declaracion'] in ('OK', 'RECUR')]
            elif tipos[-1] == 'OK':
                estado, regla, evid = 'RESUELTO', 'R-EST-RES', [ds[-1]['id']]
            elif tipos[-1] == 'RECUR' and estado in ('RESUELTO', 'TEMPORAL'):
                estado, regla, evid = 'TEMPORAL', 'R-EST-TEMP', [ds[-1]['id']]   # recurrencia tras una recuperación
            else:                                                                 # FALLA, o RECUR sin recuperación previa
                estado, regla, evid = 'NO_RESUELTO', 'R-EST-NORES', [ds[-1]['id']]
        ultima_decl = decl[-1]
        posteriores = [c for c in comps if (c['turno'], c['id']) > (ultima_decl['turno'], ultima_decl['id'])]
        if PROMESA_POSTERIOR_A_FALLA_ES_PENDIENTE and estado == 'NO_RESUELTO' and posteriores:
            return {'valor': 'PENDIENTE', 'regla': 'R-EST-PEND', 'evidencias': [posteriores[-1]['id']],
                    'nota': 'promesa del agente posterior a la falla declarada por el cliente'}
        out = {'valor': estado, 'regla': regla, 'evidencias': evid}
        if comps:
            out['nota'] = ('R-EST-PREC: la declaración del cliente (%s) prevalece sobre la promesa del agente (%s)'
                           % (ultima_decl['id'], comps[-1]['id']))
        return out
    if comps:
        return {'valor': 'PENDIENTE', 'regla': 'R-EST-PEND', 'evidencias': [c['id'] for c in comps]}
    return {'valor': 'NO_CONFIRMADO', 'regla': 'R-EST-NC', 'evidencias': []}
