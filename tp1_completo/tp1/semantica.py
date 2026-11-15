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
LO_ULTIMO_PREVALECE = True

ASPECTOS = ('SERVICIO', 'ATENCION', 'CLARIDAD')
ASP_DE = {
    'SUST_SERV': 'SERVICIO',
    'SUST_ATEN': 'ATENCION',
    'SUST_CLAR': 'CLARIDAD',
    'SUST_EQUIPO': 'SERVICIO',
    'SUST_TICKET': None,
    'SUST_PROB': 'SERVICIO',
    'AGENTE': 'ATENCION'
}
POL = {'ADJ_POS': +1, 'ADJ_NEG': -1, 'V_EST_OK': +1, 'V_EST_FALLA': -1}
NOMBRE_POL = {+1: 'POSITIVA', -1: 'NEGATIVA'}

# ============================================================ 1. Catálogo de reglas (id -> descripción)
REGLAS = {
    'R-SUJ':    'sujeto ⇒ aspecto',
    'R-COP':    'sujeto [V_COPULA] atrib ⇒ valoración del aspecto del sujeto con la polaridad del atributo',
    'R-EST':    'v_est compl ⇒ declaración OK/FALLA del servicio',
    'R-NEG':    'NEG invierte la polaridad del predicado que le sigue',
    'R-MUY':    'INT («muy») marca intensidad ALTA del adjetivo inmediato',
    'R-SEG-ADJ': 'V_CONT compl ⇒ seguimiento con adjetivo o estado',
    'R-SEG-SIN': 'V_CONT SIN sust ⇒ seguimiento negativo',
    'R-CORTE':  'SE V_EST_RECUR ⇒ SERVICIO NEGATIVA; declaración RECUR',
    'R-VAL':    'v_acc obj modif_op ⇒ valoración de atención o claridad',
    'R-SOLIC':  'v_acc obj ⇒ solicitud de seguimiento',
    'R-COMPR':  'v_acc obj ⇒ compromiso futuro',
    'R-TICKET': 'TICKET o SUST_TICKET ⇒ referencia a un ticket',
    'R-CORT':   'CORTESIA ⇒ sin valoración ni estado',
    'R-AHORA':  'T_AHORA ⇒ la cláusula se refiere al momento actual',
    'R-PERO':   'PERO ⇒ la cláusula queda en contraste con la anterior',
    'R-EST-RES':  'última declaración del CLIENTE = funciona (OK) ⇒ RESUELTO',
    'R-EST-NORES': 'última declaración del CLIENTE = la falla persiste ⇒ NO_RESUELTO',
    'R-EST-TEMP': 'el CLIENTE informa recuperación y también recurrencia ⇒ TEMPORAL',
    'R-EST-PEND': 'compromiso futuro del agente sin declaración posterior del CLIENTE ⇒ PENDIENTE',
    'R-EST-NC':   'sin evidencia suficiente ⇒ NO_CONFIRMADO',
    'R-EST-PREC': 'precedencia: prevalece lo último entre la última declaración del CLIENTE y la última promesa del agente',
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
    if not isinstance(n, Nodo):
        return None
    f = ACC.get((n.var, n.produccion))
    return f(n) if f else None


# ---- sustantivos y sujetos
@acc('sust', 'SUST_SERV')
def _sust_serv(n):
    return {'asp': 'SERVICIO', 'pol': 0, 'ent': None, 'tok': n.hijos[0]}

@acc('sust', 'SUST_ATEN')
def _sust_aten(n):
    return {'asp': 'ATENCION', 'pol': 0, 'ent': None, 'tok': n.hijos[0]}

@acc('sust', 'SUST_CLAR')
def _sust_clar(n):
    return {'asp': 'CLARIDAD', 'pol': 0, 'ent': None, 'tok': n.hijos[0]}

@acc('sust', 'SUST_EQUIPO')
def _sust_eq(n):
    return {'asp': 'SERVICIO', 'pol': 0, 'ent': 'ROUTER', 'tok': n.hijos[0]}

@acc('sust', 'SUST_TICKET')
def _sust_tk(n):
    return {'asp': None, 'pol': 0, 'ent': 'TICKET', 'tok': n.hijos[0]}

@acc('sust', 'SUST_PROB')
def _sust_prob(n):
    return {'asp': 'SERVICIO', 'pol': -1, 'ent': None, 'tok': n.hijos[0]}


@acc('sujeto', 'sust')
def _suj_sust(n):
    s = ev(n.hijos[0])
    return {'asp': s['asp'], 'ent': s['ent'], 'tok': s['tok'], 's': s}

@acc('sujeto', 'AGENTE')
def _suj_agente(n):
    return {'asp': 'ATENCION', 'ent': None, 'tok': n.hijos[0]}


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
    return {**a, 'int': 'ALTA', 'toks': [n.hijos[0]] + a['toks']}


@acc('modif_op', 'modif')
def _modif_op(n):
    return ev(n.hijos[0])


@acc('modif_op', 'ε')
def _modif_op_vacio(n):
    return None


@acc('frec', 'FREC frec')
def _frec(n):
    return 1 + ev(n.hijos[1])


@acc('frec', 'ε')
def _frec_vacio(n):
    return 0


@acc('adv_t', 'T_AHORA')
def _adv_ahora(n):
    return {'t': 'AHORA', 'tok': n.hijos[0]}


@acc('adv_t', 'T_FUTURO')
def _adv_futuro(n):
    return {'t': 'FUTURO', 'tok': n.hijos[0]}


@acc('adv_t_op', 'adv_t')
def _adv_t_op(n):
    return ev(n.hijos[0])


@acc('adv_t_op', 'ε')
def _adv_t_op_vacio(n):
    return None


@acc('ref_op', 'TICKET')
def _ref_ticket(n):
    return {'ticket': n.hijos[0]}


@acc('ref_op', 'T_FUTURO')
def _ref_plazo(n):
    return {'plazo': n.hijos[0]}


@acc('ref_op', 'ε')
def _ref_vacio(n):
    return {}


@acc('atrib', 'modif')
def _atrib_modif(n):
    m = ev(n.hijos[0])
    return {'k': 'COP', 'pol': m['pol'], 'int': m.get('int'), 'reglas': ['R-COP']}


@acc('atrib', 'TICKET')
def _atrib_ticket(n):
    return {'k': 'REF', 'ticket': n.hijos[0], 'reglas': ['R-TICKET']}


@acc('compl', 'modif')
def _compl_modif(n):
    return ev(n.hijos[0])


@acc('compl', 'SIN sust')
def _compl_sin(n):
    s = ev(n.hijos[1])
    pol = +1 if s['pol'] == -1 else -1
    return {'pol': pol, 'asp': s['asp'], 'tipo_compl': 'SIN', 'reglas': ['R-SIN']}


@acc('compl', 'ε')
def _compl_vacio(n):
    return None


@acc('obj', 'sust')
def _obj_sust(n):
    return {'sust': ev(n.hijos[0])}


@acc('obj', 'TICKET')
def _obj_ticket(n):
    return {'ticket': n.hijos[0]}


@acc('obj', 'adv_t')
def _obj_adv(n):
    return {'adv': ev(n.hijos[0])}


@acc('obj', 'ε')
def _obj_vacio(n):
    return {}


@acc('obj_clar', 'SUST_CLAR')
def _obj_clar(n):
    return ev(n.hijos[0])


@acc('obj_clar', 'ε')
def _obj_clar_v(n):
    return None


@acc('obj_router', 'SUST_EQUIPO')
def _obj_router(n):
    return ev(n.hijos[0])


@acc('obj_router', 'ε')
def _obj_router_v(n):
    return None


# ---- verbos y predicados
@acc('v_est', 'V_EST_OK')
def _v_est_ok(n):
    return {'pol': +1, 'tok': n.hijos[0]}


@acc('v_est', 'V_EST_FALLA')
def _v_est_fall(n):
    return {'pol': -1, 'tok': n.hijos[0]}


@acc('pred_s', 'V_COP atrib')
@acc('pred_l', 'V_COP atrib')
def _p_cop(n):
    return ev(n.hijos[1])


@acc('pred_s', 'v_est compl')
@acc('pred_l', 'v_est compl')
@acc('pred_neg', 'v_est compl')
def _p_est(n):
    v = ev(n.hijos[0])
    c = ev(n.hijos[1])
    pol = v['pol']
    asp = None
    if c and c.get('tipo_compl') == 'SIN':
        pol = c['pol']
        asp = c['asp']
    elif c and 'pol' in c:
        pol = c['pol']
    return {'k': 'EST', 'pol': pol, 'asp': asp, 'int': c.get('int') if c else None, 'reglas': ['R-EST']}


@acc('pred_s', 'SE V_EST_RECUR')
@acc('pred_l', 'SE V_EST_RECUR')
def _p_recur(n):
    return {'k': 'CORTE', 'pol': -1, 'reglas': ['R-CORTE']}


@acc('pred_s', 'V_CONT compl')
@acc('pred_l', 'V_CONT compl')
def _p_cont(n):
    c = ev(n.hijos[1])
    if c and c.get('tipo_compl') == 'SIN':
        return {'k': 'SEG_SIN', 'pol': c['pol'], 'asp': c['asp'], 'reglas': ['R-SEG-SIN']}
    m = c or {'pol': +1}
    return {'k': 'SEG_ADJ', 'pol': m['pol'], 'int': m.get('int'), 'reglas': ['R-SEG-ADJ']}


@acc('v_acc', 'V_ENTENDER')
def _va_ent(n):
    return {'clase': 'ENT', 'asp': 'CLARIDAD'}


@acc('v_acc', 'V_SOLICITUD')
def _va_sol(n):
    return {'clase': 'SOLIC', 'asp': None}


@acc('v_acc', 'V_COMPROMISO')
def _va_comp(n):
    return {'clase': 'COMPR', 'asp': None}


@acc('v_acc', 'V_VAL_ATEN')
def _va_vaten(n):
    return {'clase': 'VAL', 'asp': 'ATENCION'}


@acc('v_acc', 'V_VAL_CLAR')
def _va_vclar(n):
    return {'clase': 'VAL', 'asp': 'CLARIDAD'}


@acc('pred_s', 'v_acc obj modif_op')
@acc('pred_l', 'v_acc obj modif_op')
@acc('pred_neg', 'v_acc obj modif_op')
def _p_acc(n):
    va = ev(n.hijos[0])
    obj = ev(n.hijos[1])
    mo = ev(n.hijos[2])
    clase = va['clase']
    if clase == 'ENT':
        pol = mo['pol'] if mo else +1
        return {'k': 'ENT', 'pol': pol, 'reglas': ['R-ENT']}
    if clase == 'VAL':
        pol = mo['pol'] if mo else +1
        return {'k': 'VAL', 'asp': va['asp'], 'pol': pol, 'int': mo.get('int') if mo else None, 'reglas': ['R-VAL']}
    if clase == 'SOLIC':
        ent = obj.get('sust', {}).get('ent') or (obj.get('ticket').norm if obj.get('ticket') else None)
        return {'k': 'SOLIC', 'ent': ent, 'reglas': ['R-SOLIC']}
    if clase == 'COMPR':
        tk = obj.get('ticket')
        plazo = obj.get('adv')
        return {'k': 'COMPR', 'ref': {'ticket': tk, 'plazo': plazo}, 'reglas': ['R-COMPR']}
    return {'k': 'MENCION', 'reglas': ['R-MEN']}


@acc('pred_s', 'atrib')
def _p_atrib(n):
    return ev(n.hijos[0])


@acc('pred_s', 'NEG pred_neg')
@acc('pred_l', 'NEG pred_neg')
def _p_neg(n):
    return {**ev(n.hijos[1]), 'neg': True}


@acc('pred_s', 'ε')
def _p_vacio(n):
    return {'k': 'MENCION', 'reglas': ['R-MEN']}


# ---- hecho de una cláusula
def _hecho(tipo, **kw):
    h = {'tipo': tipo, 'aspecto': None, 'valoracion': None, 'intensidad': None, 'negada': False,
         'declaracion': None, 'entidades': [], 'reglas': [], 'temporal': None}
    h.update(kw)
    return h


def _construir(p, aspecto, con_sujeto):
    k, reglas = p['k'], (['R-SUJ'] if con_sujeto else []) + list(p.get('reglas', []))
    if k == 'MENCION':
        return _hecho('MENCION', aspecto=aspecto or 'SERVICIO', valoracion='NEUTRA', reglas=reglas)
    if k == 'REF':
        tk = p.get('ticket')
        return _hecho('TICKET', entidades=[tk.norm] if tk else [], reglas=reglas)
    if k == 'SOLIC':
        ent = p.get('ent')
        return _hecho('SOLICITUD', entidades=[ent] if ent else [], reglas=reglas)
    if k == 'COMPR':
        ref = p.get('ref', {})
        tk = ref.get('ticket')
        return _hecho('COMPROMISO', entidades=[tk.norm] if tk else [], reglas=reglas)
    asp = p.get('asp') or aspecto or ('CLARIDAD' if k == 'ENT' else 'SERVICIO')
    pol, neg = p['pol'], p.get('neg', False)
    if neg:
        pol, reglas = -pol, reglas + ['R-NEG']
    if p.get('int'):
        reglas.append('R-MUY')
    decl = None
    if asp == 'SERVICIO':
        if k in ('EST', 'SEG_ADJ'):
            decl = 'OK' if pol > 0 else 'FALLA'
        elif k == 'SEG_SIN':
            decl = 'FALLA'
        elif k == 'CORTE':
            decl = 'RECUR'
    tipo = 'FUNCIONAMIENTO' if decl else 'VALORACION'
    return _hecho(tipo, aspecto=asp, valoracion=NOMBRE_POL[pol], intensidad=p.get('int'), negada=neg,
                  declaracion=decl, reglas=reglas)


@acc('nucleo', 'sujeto pred_s')
def _n_sujeto(n):
    s, p = ev(n.hijos[0]), ev(n.hijos[1])
    return _construir(p, s['asp'], True)


@acc('nucleo', 'pred_l')
def _n_pred(n):
    return _construir(ev(n.hijos[0]), None, False)


@acc('nucleo', 'TICKET')
def _n_tk(n):
    return _hecho('TICKET', entidades=[n.hijos[0].norm], reglas=['R-TICKET'])


@acc('nucleo', 'CORTESIA')
def _n_cort(n):
    return _hecho('CORTESIA', reglas=['R-CORT'])


@acc('clausula', 'adv_t_op nucleo frec')
def _clausula(n):
    ah, h = ev(n.hijos[0]), ev(n.hijos[1])
    if ah and ah.get('t') == 'AHORA':
        h['temporal'] = 'AHORA'
        h['reglas'].append('R-AHORA')
    return h


# ============================================================ 3. Recorrido del árbol
def clausulas(raiz):
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
        return 'MIXTA'
    for v in ('POSITIVA', 'NEGATIVA', 'NEUTRA'):
        if v in s:
            return v
    return 'SIN_EVIDENCIA'


def valoraciones_por_aspecto(cls):
    return {a: combinar([c['valoracion'] for c in cls if c['aspecto'] == a and c['valoracion']]) for a in ASPECTOS}


def resumen_aspectos(cls):
    res = {}
    for a in ASPECTOS:
        cli = [c for c in cls if c['aspecto'] == a and c['valoracion'] and c['actor'] == 'CLIENTE']
        ag = [c for c in cls if c['aspecto'] == a and c['valoracion'] and c['actor'] == 'AGENTE']
        res[a] = {'valoracion': combinar([c['valoracion'] for c in cli]),
                  'evidencias': [c['id'] for c in cli],
                  'opiniones_agente': [{'id': c['id'], 'valoracion': c['valoracion']} for c in ag]}
    return res


def decidir_estado(cls):
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
                estado, regla, evid = 'TEMPORAL', 'R-EST-TEMP', [ds[-1]['id']]
            else:
                estado, regla, evid = 'NO_RESUELTO', 'R-EST-NORES', [ds[-1]['id']]
        pos = {id(c): i for i, c in enumerate(cls)}
        ultima_decl = decl[-1]
        posteriores = [c for c in comps if pos[id(c)] > pos[id(ultima_decl)]]
        if LO_ULTIMO_PREVALECE and posteriores:
            return {'valor': 'PENDIENTE', 'regla': 'R-EST-PEND', 'evidencias': [posteriores[-1]['id']],
                    'nota': ('R-EST-PREC: la promesa del agente (%s) es posterior a la última declaración del cliente '
                             '(%s, que daba %s); prevalece lo último' % (posteriores[-1]['id'], ultima_decl['id'], estado))}
        out = {'valor': estado, 'regla': regla, 'evidencias': evid}
        if comps:
            out['nota'] = ('R-EST-PREC: la declaración del cliente (%s) prevalece sobre la promesa del agente (%s)'
                           % (ultima_decl['id'], comps[-1]['id']))
        return out
    if comps:
        return {'valor': 'PENDIENTE', 'regla': 'R-EST-PEND', 'evidencias': [c['id'] for c in comps]}
    return {'valor': 'NO_CONFIRMADO', 'regla': 'R-EST-NC', 'evidencias': []}
