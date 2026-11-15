"""Acciones semánticas del TP1: definición dirigida por la sintaxis sobre el árbol del parser LL(1).

Cada regla está asociada a una PRODUCCIÓN (clave = (variable, texto de la producción)) y calcula
atributos sintetizados que devuelve a su padre (reglas semánticas con valores de retorno).
Resultado de cada cláusula: un "hecho" con actor, aspecto, valoración, declaración de funcionamiento
y la lista de reglas aplicadas (para la trazabilidad: turno + fragmento + regla).

El significado de cada palabra sale de su FORMA CANÓNICA: el diccionario solo guarda categoría -> forma canónica ->
formas superficiales, y la tabla SIGNIFICADO (sección 1) dice qué significa cada forma canónica (aspecto, polaridad,
declaración, clase, tiempo). Una palabra nueva se incorpora como variante de una forma canónica existente y hereda
su significado sin tocar el código.

Para modificar el comportamiento en la defensa basta con editar la tabla SIGNIFICADO (sección 1),
la regla de la producción (sección 3), la de compatibilidad (COMPAT), la decisión de estado (sección 5) o los
interruptores de la sección 0.
"""
from sintaxis import Nodo, G
from lexico import Token

# ============================================================ 0. Interruptores de política
# Precedencia entre la última declaración del CLIENTE y las promesas del AGENTE.
# True  (respuesta del profesor: «se tiene en cuenta lo último»): prevalece lo último que se dijo. Una promesa del
#        agente POSTERIOR a la última declaración del cliente (falla o confirmación) deja la sesión PENDIENTE; una
#        declaración del cliente posterior a la promesa prevalece sobre ella.
# False (lectura literal del enunciado, §5): la última declaración del cliente prevalece SIEMPRE sobre las promesas.
LO_ULTIMO_PREVALECE = True

ASPECTOS = ('SERVICIO', 'ATENCION', 'CLARIDAD')
NOMBRE_POL = {+1: 'POSITIVA', -1: 'NEGATIVA'}

# ============================================================ 1. Significado de las formas canónicas
# El diccionario (vocabulario.json y lo aprendido) solo guarda categoría -> forma canónica -> formas superficiales.
# QUÉ SIGNIFICA cada forma canónica se define aquí, en las reglas semánticas. Una forma superficial nueva hereda el
# significado de la forma canónica a la que el usuario la asigna; una forma canónica nueva con significado requiere
# agregar su línea en esta tabla. Las categorías que no figuran aquí (NEG, SIN, INT, PERO, Y, SE, V_COP, V_CONT, FREC,
# CORTESIA, RELLENO) no aportan significado por forma: su efecto lo da la producción en la que aparecen.
SIGNIFICADO = {
    'SUST': {    # clase: para la compatibilidad; asp: aspecto; pol: −1 si nombra un problema; ent: entidad
        'SERVICIO': dict(clase='SERVICIO', asp='SERVICIO', pol=0,  ent=None,     desc='el servicio'),
        'ATENCION': dict(clase='ATENCION', asp='ATENCION', pol=0,  ent=None,     desc='la atención'),
        'CLARIDAD': dict(clase='CLARIDAD', asp='CLARIDAD', pol=0,  ent=None,     desc='la explicación'),
        'ROUTER':   dict(clase='EQUIPO',   asp='SERVICIO', pol=0,  ent='EQUIPO', desc='un equipo (valora el servicio)'),
        'TICKET':   dict(clase='TICKET',   asp=None,       pol=0,  ent='TICKET', desc='un ticket o caso'),
        'CORTE':    dict(clase='PROBLEMA', asp='SERVICIO', pol=-1, ent=None,     desc='un problema del servicio'),
    },
    'ADJ': {
        'BUENO': dict(pol=+1, desc='positiva'), 'RAPIDO': dict(pol=+1, desc='positiva'),
        'ESTABLE': dict(pol=+1, desc='positiva'), 'AMABLE': dict(pol=+1, desc='positiva'),
        'CLARO': dict(pol=+1, desc='positiva'),
        'MALO': dict(pol=-1, desc='negativa'), 'LENTO': dict(pol=-1, desc='negativa'),
        'INESTABLE': dict(pol=-1, desc='negativa'), 'CONFUSO': dict(pol=-1, desc='negativa'),
    },
    'V_EST': {   # pol: el servicio anda bien (+1) o mal (−1); pron: exige «se»
        'FUNCIONAR': dict(pol=+1, pron=False, desc='el servicio anda bien'),
        'FALLAR':    dict(pol=-1, pron=False, desc='el servicio anda mal'),
        'CORTAR':    dict(pol=-1, pron=True,  desc='falla que se repite; va con «se»'),
    },
    'V_ACC': {   # clase: ENT (comprender), SOLIC (pedido), COMPR (promesa), VAL (valora un aspecto)
        'ENTENDER':  dict(clase='ENT',   asp='CLARIDAD', desc='comprender'),
        'REINICIAR': dict(clase='SOLIC', asp=None,       desc='pedido al cliente'),
        'REVISAR':   dict(clase='COMPR', asp=None,       desc='promesa a futuro'),
        'LLAMAR':    dict(clase='COMPR', asp=None,       desc='promesa a futuro'),
        'ESCALAR':   dict(clase='COMPR', asp=None,       desc='promesa a futuro'),
        'ATENDER':   dict(clase='VAL',   asp='ATENCION', desc='valora la atención'),
        'EXPLICAR':  dict(clase='VAL',   asp='CLARIDAD', desc='valora la explicación'),
    },
    'ADV_T': {
        'AHORA':  dict(t='AHORA',  desc='el momento actual'),
        'MAÑANA': dict(t='FUTURO', desc='más adelante'),
    },
}


def sig(tok):
    """Significado del token según su categoría y su forma canónica (tabla SIGNIFICADO) + el token."""
    return {**SIGNIFICADO[tok.categoria][tok.canon], 'tok': tok}


def canonicos_sin_significado(vocab):
    """Formas canónicas del vocabulario que no tienen significado definido (el vocabulario no se puede usar)."""
    return [f'{cat}/{canon}' for cat in SIGNIFICADO for canon in vocab.get(cat, {}) if canon not in SIGNIFICADO[cat]]


# Compatibilidad sujeto-predicado (el «chequeo de tipos» del análisis semántico): qué tipos de predicado (atributo k)
# admite cada clase de sujeto. Una combinación fuera de la tabla no se interpreta (R-COMPAT: abstención).
COMPAT = {
    'SERVICIO': {'COP', 'EST', 'SEG_ADJ', 'SEG_SIN', 'CORTE', 'MENCION'},
    'EQUIPO':   {'COP', 'EST', 'SEG_ADJ', 'SEG_SIN', 'CORTE', 'MENCION'},
    'ATENCION': {'COP', 'SEG_ADJ', 'MENCION', 'VAL'},       # VAL solo si el verbo valora el mismo aspecto
    'AGENTE':   {'COP', 'SEG_ADJ', 'MENCION', 'VAL'},
    'CLARIDAD': {'COP', 'SEG_ADJ', 'MENCION', 'VAL'},
    'TICKET':   {'REF', 'MENCION'},
    'PROBLEMA': {'COP', 'SEG_ADJ', 'MENCION'},
}

# ============================================================ 2. Catálogo de reglas (id -> descripción)
REGLAS = {
    'R-SUJ':    'SUST ⇒ aspecto según su forma canónica (SERVICIO, ROUTER, CORTE→SERVICIO; ATENCION→ATENCION; CLARIDAD→CLARIDAD); AGENTE→ATENCION',
    'R-COP':    'sujeto [V_COP] modif ⇒ valoración del aspecto del sujeto con la polaridad del adjetivo',
    'R-EST':    'V_EST [compl] ⇒ SERVICIO; FUNCIONAR toma la polaridad del complemento (POSITIVA si no hay), FALLAR es NEGATIVA; declaración OK/FALLA',
    'R-NEG':    'NEG invierte la polaridad del predicado que le sigue; su alcance es pred_neg y no cruza PERO, COMA ni Y',
    'R-MUY':    'INT («muy») marca intensidad ALTA del adjetivo inmediato; no cambia la polaridad',
    'R-SIN':    'SIN SUST ⇒ NEGATIVA si falta algo (sin internet); POSITIVA si lo que falta es un problema (sin cortes)',
    'R-SEG-ADJ': '[sujeto] V_CONT modif ⇒ aspecto del sujeto (SERVICIO si no hay); en SERVICIO, adjetivo negativo = FALLA y positivo = OK',
    'R-SEG-SIN': 'V_CONT SIN SUST («sigo sin internet») ⇒ aspecto del sustantivo, polaridad de R-SIN; en SERVICIO declara FALLA u OK',
    'R-CORTE':  '[sujeto] SE V_EST pronominal (CORTAR) [FREC…] ⇒ SERVICIO NEGATIVA; declaración RECUR (con o sin frecuencia)',
    'R-ENT':    '[NEG] V_ACC de comprensión (ENTENDER) [SUST] ⇒ CLARIDAD: positiva si entendió, negativa con NEG',
    'R-VAL':    'V_ACC valorativo (ATENDER, EXPLICAR) modif («me atendiste muy bien») ⇒ valoración de ATENCION / CLARIDAD',
    'R-MEN':    'sujeto o verbo valorativo sin cualidad ⇒ mención NEUTRA del aspecto (sin polaridad)',
    'R-SOLIC':  'V_ACC de pedido (REINICIAR) [SUST] ⇒ solicitud de seguimiento (no es compromiso ni valoración)',
    'R-COMPR':  '[ADV_T] V_ACC de promesa (REVISAR, LLAMAR, ESCALAR) [TICKET|plazo] ⇒ compromiso futuro',
    'R-TICKET': 'SUST TICKET [V_COP] TICKET | TICKET ⇒ referencia a un ticket (entidad)',
    'R-CORT':   'CORTESIA ⇒ sin valoración ni estado',
    'R-AHORA':  'ADV_T AHORA ⇒ la cláusula se refiere al momento actual',
    'R-POSP':   'sujeto después del verbo («no funciona el internet») ⇒ aporta el aspecto como un sujeto explícito',
    'R-COMPAT': 'sujeto y predicado incompatibles (tabla COMPAT), verbo pronominal sin «se» o no pronominal con «se», '
                'dos sujetos o V_CONT sin complemento ⇒ la cláusula no se interpreta',
    'R-PERO':   'PERO ⇒ la cláusula queda en contraste con la anterior; ambas se conservan por separado',
    'R-EST-RES':  'última declaración del CLIENTE = funciona (OK) ⇒ RESUELTO',
    'R-EST-NORES': 'última declaración del CLIENTE = la falla persiste ⇒ NO_RESUELTO',
    'R-EST-TEMP': 'el CLIENTE informa recuperación y también recurrencia ⇒ TEMPORAL',
    'R-EST-PEND': 'compromiso futuro del agente sin declaración posterior del CLIENTE ⇒ PENDIENTE',
    'R-EST-NC':   'sin evidencia suficiente ⇒ NO_CONFIRMADO',
    'R-EST-PREC': 'precedencia: prevalece lo último entre la última declaración del CLIENTE y la última promesa del agente',
}

# ============================================================ 3. Reglas semánticas por producción
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


# ---- 3.1 modificadores y complementos (los terminales con significado se leen con sig())
@acc('modif', 'ADJ')
def _modif_adj(n):
    return {'pol': sig(n.hijos[0])['pol'], 'int': None}


@acc('modif', 'INT ADJ')
def _modif_int(n):
    return {'pol': sig(n.hijos[1])['pol'], 'int': 'ALTA'}                   # R-MUY


@acc('modif_op', 'modif')
@acc('atrib', 'modif')
def _copia(n):
    return ev(n.hijos[0])


@acc('modif_op', 'ε')
@acc('compl', 'ε')
@acc('sujp', 'ε')
@acc('adv_t_op', 'ε')
def _vacio(n):
    return None


@acc('atrib', 'TICKET')
def _atrib_ticket(n):
    return {'ticket': n.hijos[0]}


@acc('compl', 'modif')
def _compl_modif(n):
    return {**ev(n.hijos[0]), 't': 'CUAL'}


@acc('compl', 'SIN SUST')
def _compl_sin(n):
    s = sig(n.hijos[1])
    return {'t': 'SIN', 'asp': s['asp'], 'pol': +1 if s['pol'] == -1 else -1, 'int': None}     # R-SIN


@acc('sujp', 'SUST')
@acc('sujeto', 'SUST')
@acc('adv_t_op', 'ADV_T')
def _sig(n):
    return sig(n.hijos[0])


@acc('sujeto', 'AGENTE')
def _sujeto_agente(n):
    return {'clase': 'AGENTE', 'asp': 'ATENCION', 'pol': 0, 'ent': None, 'tok': n.hijos[0]}   # «el agente fue amable»


@acc('obj', 'SUST')
def _obj_sust(n):
    return {'s': sig(n.hijos[0])}


@acc('obj', 'TICKET')
def _obj_ticket(n):
    return {'ticket': n.hijos[0]}


@acc('obj', 'ADV_T')
def _obj_plazo(n):
    return {'plazo': sig(n.hijos[0])['t']}


@acc('obj', 'ε')
def _obj_vacio(n):
    return {}


@acc('frec', 'FREC frec')
def _frec(n):
    return 1 + ev(n.hijos[1])


@acc('frec', 'ε')
def _frec_vacio(n):
    return 0


# ---- 3.2 predicados (atributo 'k' = tipo de predicado; 'pos' = sujeto pospuesto)
def _pos(n, i):
    return ev(n.hijos[i]) if len(n.hijos) > i else None


@acc('pred_s', 'V_COP atrib')
@acc('pred_l', 'V_COP atrib')
@acc('pred_neg', 'V_COP atrib')
def _p_cop(n):
    a = ev(n.hijos[1])
    if a.get('ticket'):
        return {'k': 'REF', 'ticket': a['ticket'], 'reglas': ['R-TICKET']}
    return {'k': 'COP', 'pol': a['pol'], 'int': a['int'], 'reglas': ['R-COP']}


@acc('pred_s', 'modif')
def _p_cop_dir(n):
    m = ev(n.hijos[0])
    return {'k': 'COP', 'pol': m['pol'], 'int': m['int'], 'reglas': ['R-COP']}


@acc('pred_s', 'TICKET')
def _p_ref(n):
    return {'k': 'REF', 'ticket': n.hijos[0], 'reglas': ['R-TICKET']}


@acc('pred_s', 'ε')
def _p_mencion(n):
    return {'k': 'MENCION', 'reglas': ['R-MEN']}


def _p_est(n, con_se):
    """V_EST compl [sujp] y SE V_EST compl [sujp]. Un verbo pronominal (CORTAR) exige «se»; los demás, no."""
    i = 1 if con_se else 0
    v, c, pos = sig(n.hijos[i]), ev(n.hijos[i + 1]), _pos(n, i + 2)
    if v['pron'] != con_se:
        return {'k': 'SE_INCOMPATIBLE', 'reglas': []}            # «el agente corta…», «se funciona»
    if v['pron']:
        return {'k': 'CORTE', 'pol': -1, 'pos': pos, 'reglas': ['R-CORTE']}
    pol = -1 if v['pol'] == -1 else (c['pol'] if c else +1)     # un verbo de falla no se vuelve positivo por el adjetivo
    return {'k': 'EST', 'pol': pol, 'int': c['int'] if c else None, 'pos': pos,
            'reglas': ['R-EST'] + (['R-SIN'] if c and c['t'] == 'SIN' else [])}


@acc('pred_s', 'V_EST compl')
@acc('pred_l', 'V_EST compl sujp')
@acc('pred_neg', 'V_EST compl sujp')
def _p_est_sin_se(n):
    return _p_est(n, False)


@acc('pred_s', 'SE V_EST compl')
@acc('pred_l', 'SE V_EST compl sujp')
@acc('pred_neg', 'SE V_EST compl sujp')
def _p_est_con_se(n):
    return _p_est(n, True)


@acc('pred_s', 'V_CONT compl')
@acc('pred_l', 'V_CONT compl')
@acc('pred_neg', 'V_CONT compl')
def _p_seguir(n):
    c = ev(n.hijos[1])
    if c is None:
        return {'k': 'INCOMPLETO', 'reglas': []}                 # «sigue» sin complemento: no se interpreta
    if c['t'] == 'SIN':
        return {'k': 'SEG_SIN', 'pol': c['pol'], 'asp': c['asp'], 'reglas': ['R-SEG-SIN', 'R-SIN']}
    return {'k': 'SEG_ADJ', 'pol': c['pol'], 'int': c['int'], 'reglas': ['R-SEG-ADJ']}


@acc('pred_s', 'V_ACC obj modif_op')
@acc('pred_l', 'V_ACC obj modif_op')
@acc('pred_neg', 'V_ACC obj modif_op')
def _p_acc(n):
    v, o, m = sig(n.hijos[0]), ev(n.hijos[1]), ev(n.hijos[2])
    if v['clase'] == 'ENT':
        return {'k': 'ENT', 'asp': v['asp'], 'pol': m['pol'] if m else +1, 'int': m['int'] if m else None, 'reglas': ['R-ENT']}
    if v['clase'] == 'VAL':
        if m is None:                                            # «me atendieron»: mención sin cualidad
            return {'k': 'MENCION', 'asp': v['asp'], 'reglas': ['R-MEN']}
        return {'k': 'VAL', 'asp': v['asp'], 'pol': m['pol'], 'int': m['int'], 'reglas': ['R-VAL']}
    if v['clase'] == 'SOLIC':
        return {'k': 'SOLIC', 'ent': o.get('s'), 'reglas': ['R-SOLIC']}
    return {'k': 'COMPR', 'ticket': o.get('ticket'), 'plazo': o.get('plazo'), 'reglas': ['R-COMPR']}


@acc('pred_s', 'NEG pred_neg')
@acc('pred_l', 'NEG pred_neg')
def _p_neg(n):
    return {**ev(n.hijos[1]), 'neg': True}                                  # R-NEG: alcance = pred_neg


# ---- 3.3 hecho de una cláusula
def _hecho(tipo, **kw):
    h = {'tipo': tipo, 'aspecto': None, 'valoracion': None, 'intensidad': None, 'negada': False,
         'declaracion': None, 'entidades': [], 'reglas': [], 'temporal': None}
    h.update(kw)
    return h


def _compatible(p, s):
    """Chequeo de compatibilidad (R-COMPAT). s = sujeto explícito o None."""
    k, pos = p['k'], p.get('pos')
    if k in ('INCOMPLETO', 'SE_INCOMPATIBLE') or (s and pos):    # «sigue» a secas, «se» mal usado, dos sujetos
        return False
    for suj in (s, pos):
        if suj is None:
            continue
        if k not in COMPAT[suj['clase']]:
            return False
        if k == 'VAL' and suj['asp'] != p['asp']:                # «la explicación me atendió bien»
            return False
    return True


def _construir(p, s):
    """Convierte los atributos de un predicado y el sujeto (o None) en un hecho."""
    if not _compatible(p, s):
        return _hecho('INCOMPATIBLE', reglas=['R-COMPAT'])
    k, pos = p['k'], p.get('pos')
    suj = s or pos
    reglas = (['R-SUJ'] if s else []) + list(p['reglas']) + (['R-POSP'] if pos else [])
    equipo = [suj['tok'].norm.upper()] if suj and suj['ent'] == 'EQUIPO' else []
    if k == 'MENCION':
        if s and s['ent'] == 'TICKET':                           # «el ticket», sin número
            return _hecho('TICKET', reglas=['R-TICKET'])
        return _hecho('MENCION', aspecto=s['asp'] if s else p.get('asp'), valoracion='NEUTRA', entidades=equipo, reglas=reglas)
    if k == 'SOLIC':
        e = p['ent']
        return _hecho('SOLICITUD', entidades=[e['tok'].norm.upper()] if e and e['ent'] == 'EQUIPO' else [], reglas=reglas)
    if k == 'COMPR':
        return _hecho('COMPROMISO', entidades=[p['ticket'].norm] if p['ticket'] else [], reglas=reglas)
    if k == 'REF':
        return _hecho('TICKET', entidades=[p['ticket'].norm], reglas=['R-TICKET'])
    if k == 'SEG_SIN':
        asp = p['asp'] or 'SERVICIO'
    else:
        asp = (suj['asp'] if suj else None) or p.get('asp') or 'SERVICIO'
    pol, neg = p['pol'], p.get('neg', False)
    if neg:
        pol, reglas = -pol, reglas + ['R-NEG']
    if p.get('int'):
        reglas.append('R-MUY')
    decl = None
    if asp == 'SERVICIO':
        if k in ('EST', 'SEG_ADJ', 'SEG_SIN'):
            decl = 'OK' if pol > 0 else 'FALLA'
        elif k == 'CORTE' and not neg:                           # «no se corta» valora, pero no declara
            decl = 'RECUR'
    tipo = 'FUNCIONAMIENTO' if decl else 'VALORACION'   # solo hay declaración de funcionamiento sobre el SERVICIO
    return _hecho(tipo, aspecto=asp, valoracion=NOMBRE_POL[pol], intensidad=p.get('int'), negada=neg,
                  declaracion=decl, entidades=equipo, reglas=reglas)


@acc('nucleo', 'sujeto pred_s')
def _n_sujeto(n):
    return _construir(ev(n.hijos[1]), ev(n.hijos[0]))


@acc('nucleo', 'pred_l')
def _n_pred(n):
    return _construir(ev(n.hijos[0]), None)


@acc('nucleo', 'TICKET')
def _n_tk(n):
    return _hecho('TICKET', entidades=[n.hijos[0].norm], reglas=['R-TICKET'])


@acc('nucleo', 'CORTESIA')
def _n_cort(n):
    return _hecho('CORTESIA', reglas=['R-CORT'])


@acc('clausula', 'adv_t_op nucleo frec')
def _clausula(n):
    t, h = ev(n.hijos[0]), ev(n.hijos[1])
    if t and t['t'] == 'AHORA' and h['tipo'] != 'INCOMPATIBLE':
        h['temporal'] = 'AHORA'
        h['reglas'].append('R-AHORA')
    return h


# ============================================================ 4. Recorrido del árbol
def clausulas(raiz):
    """Genera (nodo_clausula, conector_previo) en orden textual; conector ∈ {None, 'COMA', 'Y', 'PERO', 'PUNTO'}."""
    estado = {'sep': None}
    salida = []

    def rec(n):
        if isinstance(n, Token):
            if n.categoria in ('PERO', 'COMA', 'PUNTO', 'Y'):
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


# ============================================================ 5. Agregación por turno y sesión
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
        pos = {id(c): i for i, c in enumerate(cls)}           # orden textual (no se comparan ids como texto)
        ultima_decl = decl[-1]
        posteriores = [c for c in comps if pos[id(c)] > pos[id(ultima_decl)]]
        if LO_ULTIMO_PREVALECE and posteriores:              # R-EST-PREC: lo último es la promesa del agente
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
