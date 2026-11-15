"""Acciones semánticas del TP1: definición dirigida por la sintaxis sobre el árbol del parser LL(1).

Cada regla está asociada a una PRODUCCIÓN (clave = (variable, texto de la producción)) y calcula
atributos sintetizados que devuelve a su padre (reglas semánticas con valores de retorno).
Resultado de cada cláusula: un "hecho" con actor, aspecto, valoración, declaración de funcionamiento
y la lista de reglas aplicadas (para la trazabilidad: turno + fragmento + regla).

El significado de cada palabra sale de los RASGOS de su forma canónica, guardados en la propia tabla de símbolos
léxica (vocabulario.json + lo aprendido): categoría -> forma canónica -> {rasgos, formas superficiales}. PERFILES
(sección 1) es el catálogo cerrado de combinaciones de rasgos válidas por categoría (aspecto, polaridad, declaración,
clase, tiempo). Una palabra nueva se incorpora como variante de una forma canónica, o como forma canónica nueva con los
rasgos de un perfil existente, sin tocar el código.

Para modificar el comportamiento en la defensa basta con editar los rasgos en vocabulario.json o PERFILES (sección 1),
la regla de la producción (sección 3), la de compatibilidad (COMPAT), la decisión de estado (sección 5) o los
interruptores de la sección 0.
"""
import json

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

# ============================================================ 1. Rasgos y perfiles
# La tabla de símbolos léxica (vocabulario.json + lo aprendido) guarda, para cada forma canónica, sus RASGOS y sus
# formas superficiales:   {categoría: {forma canónica: {"rasgos": {...}, "formas": [...]}}}
# Las reglas semánticas leen los rasgos con sig(). Los rasgos posibles NO son libres: PERFILES es el catálogo
# CERRADO de combinaciones válidas por categoría (una plantilla por perfil). Al cargar la tabla, los rasgos de cada
# forma canónica tienen que coincidir exactamente con una plantilla de su categoría (errores_de_rasgos); al crear una
# forma canónica desde el menú, el programa copia los rasgos de la plantilla elegida (el usuario no los escribe).
# Solo un significado realmente nuevo (una plantilla nueva) requiere tocar el código.
#
# Rasgos:  aspecto (SERVICIO | ATENCION | CLARIDAD)   entidad (EQUIPO | TICKET)   pol (+1 | −1)
#          decl (OK | FALLA | RECUR: declaración de funcionamiento)   pronominal (va con «se»)
#          clase (COMPRENSION | SOLICITUD | COMPROMISO | VALORABLE)   tiempo (AHORA | FUTURO)
#          sin_dominio (la gramática la reconoce, pero no tiene significado para el dominio: R-SINDOM)
def _p(desc, **rasgos):
    return {'rasgos': rasgos, 'desc': desc}


PERFILES = {
    'SUST': {
        'SERVICIO':    _p('habla del servicio (internet, conexión)', aspecto='SERVICIO'),
        'ATENCION':    _p('habla de la atención (trato)', aspecto='ATENCION'),
        'CLARIDAD':    _p('habla de la explicación (indicaciones)', aspecto='CLARIDAD'),
        'EQUIPO':      _p('un equipo; valora el servicio (router, módem)', aspecto='SERVICIO', entidad='EQUIPO'),
        'TICKET':      _p('un ticket o caso', entidad='TICKET'),
        'PROBLEMA':    _p('un problema del servicio (corte)', aspecto='SERVICIO', pol=-1),
        'SIN_DOMINIO': _p('sin significado para el dominio (ruido, técnico)', sin_dominio=True),
    },
    'ADJ': {
        'POSITIVO':    _p('cualidad buena (bien, rápido, amable)', pol=+1),
        'NEGATIVO':    _p('cualidad mala (mal, lento, confuso)', pol=-1),
        'SIN_DOMINIO': _p('cualidad sin valor para el dominio (raro)', sin_dominio=True),
    },
    'V_EST': {
        'OK':          _p('el servicio anda bien (funciona, anda)', pol=+1, decl='OK'),
        'FALLA':       _p('el servicio anda mal (falla)', pol=-1, decl='FALLA'),
        'RECUR':       _p('falla que se repite; va con «se» (se corta)', pol=-1, decl='RECUR', pronominal=True),
    },
    'V_ACC': {
        'COMPRENSION': _p('comprender (entendí)', clase='COMPRENSION', aspecto='CLARIDAD'),
        'SOLICITUD':   _p('pedido al cliente (reinicie)', clase='SOLICITUD'),
        'COMPROMISO':  _p('promesa a futuro (revisaremos)', clase='COMPROMISO'),
        'VAL_ATEN':    _p('valora la atención (atendiste)', clase='VALORABLE', aspecto='ATENCION'),
        'VAL_CLAR':    _p('valora la explicación (explicaste)', clase='VALORABLE', aspecto='CLARIDAD'),
        'SIN_DOMINIO': _p('acción sin significado para el dominio (hace, tiene)', sin_dominio=True),
    },
    'ADV_T': {
        'AHORA':       _p('el momento actual (ahora, ya)', tiempo='AHORA'),
        'FUTURO':      _p('más adelante (mañana, luego)', tiempo='FUTURO'),
    },
    # categorías cuyo efecto lo da la producción en la que aparecen: un único perfil, sin rasgos
    'V_COP':    {'COPULA':          _p('ser o estar')},
    'V_CONT':   {'CONTINUIDAD':     _p('seguir')},
    'NEG':      {'NEGACION':        _p('niega el predicado que sigue')},
    'SIN':      {'PRIVACION':       _p('«sin» + sustantivo')},
    'INT':      {'INTENSIFICADOR':  _p('intensifica el adjetivo (muy)')},
    'PERO':     {'CONTRASTE':       _p('contraste entre cláusulas')},
    'Y':        {'UNION':           _p('une cláusulas')},
    'SE':       {'PRONOMINAL':      _p('marca de verbo pronominal')},
    'FREC':     {'FRECUENCIA':      _p('frecuencia (siempre, todos los días)')},
    'CORTESIA': {'CORTESIA':        _p('cortesía (gracias, hola)')},
    'RELLENO':  {'SIN_SIGNIFICADO': _p('artículo, clítico o preposición; se filtra antes del parser')},
    'FUERA_DE_GRAMATICA': {'FUERA': _p('conocida, sin función en la gramática; queda NO_INTERPRETADO')},
}

# clase de V_ACC (rasgo) -> tipo de predicado que usan las reglas de la sección 3
_TIPO_ACC = {'COMPRENSION': 'ENT', 'SOLICITUD': 'SOLIC', 'COMPROMISO': 'COMPR', 'VALORABLE': 'VAL'}


def perfil_de_rasgos(categoria, rasgos):
    """Nombre de la plantilla de PERFILES cuyos rasgos son exactamente `rasgos`; None si ninguna coincide."""
    for nombre, p in PERFILES.get(categoria, {}).items():
        if p['rasgos'] == rasgos:
            return nombre
    return None


def errores_de_rasgos(vocab):
    """Entradas de la tabla de símbolos léxica que no se pueden usar: categoría desconocida, entrada sin «rasgos» o
    sin «formas», o rasgos que no coinciden con ninguna plantilla de la categoría."""
    errs = []
    for cat, canons in vocab.items():
        if cat not in PERFILES:
            errs.append(f'categoría {cat} desconocida (no es terminal de la gramática ni RELLENO/FUERA_DE_GRAMATICA)')
            continue
        for canon, e in canons.items():
            if not isinstance(e, dict) or not isinstance(e.get('rasgos'), dict) or not isinstance(e.get('formas'), list):
                errs.append(f'{cat}/{canon}: se esperaba {{"rasgos": {{...}}, "formas": [...]}}')
            elif perfil_de_rasgos(cat, e['rasgos']) is None:
                errs.append(f'{cat}/{canon}: rasgos {json.dumps(e["rasgos"], ensure_ascii=False)} no coinciden con '
                            f'ningún perfil de {cat} ({", ".join(PERFILES[cat])})')
    return errs


# Tabla de símbolos léxica vigente. La fija analizar_lote() con usar_vocabulario(); es el mismo objeto que mantiene
# TablaSimbolosLexica, así que una forma canónica creada durante la ejecución vale para el resto de la entrada.
VOCAB = {}


def usar_vocabulario(vocab):
    global VOCAB
    VOCAB = vocab


def rasgos(tok):
    return VOCAB[tok.categoria][tok.canon]['rasgos']


def sig(tok):
    """Atributos semánticos del token, calculados a partir de los rasgos de su forma canónica:
    asp (aspecto), pol (polaridad, 0 si no tiene), ent (entidad), pron (pronominal), t (tiempo) y clase:
    en SUST, el perfil (SERVICIO, EQUIPO, PROBLEMA…, la usa COMPAT); en V_ACC, el tipo de predicado (ENT, SOLIC, COMPR,
    VAL). Con sin_dominio, clase = SIN_DOMINIO."""
    r = rasgos(tok)
    a = {'asp': r.get('aspecto'), 'pol': r.get('pol', 0), 'ent': r.get('entidad'), 'pron': r.get('pronominal', False),
         't': r.get('tiempo'), 'decl': r.get('decl'), 'tok': tok}
    if r.get('sin_dominio'):
        a['clase'] = 'SIN_DOMINIO'
    elif tok.categoria == 'SUST':
        a['clase'] = perfil_de_rasgos('SUST', r)
    elif tok.categoria == 'V_ACC':
        a['clase'] = _TIPO_ACC[r['clase']]
    return a


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
    'R-SUJ':    'SUST ⇒ aspecto = rasgo «aspecto» de su forma canónica (perfiles SERVICIO, EQUIPO, PROBLEMA→SERVICIO; ATENCION; CLARIDAD); AGENTE→ATENCION',
    'R-COP':    'sujeto [V_COP] modif ⇒ valoración del aspecto del sujeto con la polaridad del adjetivo',
    'R-EST':    'V_EST [compl] ⇒ SERVICIO; con pol +1 (perfil OK) toma la polaridad del complemento (POSITIVA si no hay), con pol −1 (perfil FALLA) es NEGATIVA; declaración OK/FALLA',
    'R-NEG':    'NEG invierte la polaridad del predicado que le sigue; su alcance es pred_neg y no cruza PERO, COMA ni Y',
    'R-MUY':    'INT («muy») marca intensidad ALTA del adjetivo inmediato; no cambia la polaridad',
    'R-SIN':    'SIN SUST ⇒ NEGATIVA si falta algo (sin internet); POSITIVA si lo que falta es un problema (sin cortes)',
    'R-SEG-ADJ': '[sujeto] V_CONT modif ⇒ aspecto del sujeto (SERVICIO si no hay); en SERVICIO, adjetivo negativo = FALLA y positivo = OK',
    'R-SEG-SIN': 'V_CONT SIN SUST («sigo sin internet») ⇒ aspecto del sustantivo, polaridad de R-SIN; en SERVICIO declara FALLA u OK',
    'R-CORTE':  '[sujeto] SE V_EST pronominal (perfil RECUR, «se corta») [FREC…] ⇒ SERVICIO NEGATIVA; declaración RECUR (con o sin frecuencia)',
    'R-ENT':    '[NEG] V_ACC de clase COMPRENSION [SUST] ⇒ CLARIDAD: positiva si entendió, negativa con NEG',
    'R-VAL':    'V_ACC de clase VALORABLE + modif («me atendiste muy bien») ⇒ valoración del rasgo «aspecto» del verbo (ATENCION / CLARIDAD)',
    'R-MEN':    'sujeto o verbo valorativo sin cualidad ⇒ mención NEUTRA del aspecto (sin polaridad)',
    'R-SOLIC':  'V_ACC de clase SOLICITUD [SUST] ⇒ solicitud de seguimiento (no es compromiso ni valoración)',
    'R-COMPR':  '[ADV_T] V_ACC de clase COMPROMISO [TICKET|plazo] ⇒ compromiso futuro',
    'R-TICKET': 'SUST con entidad TICKET [V_COP] TICKET | TICKET ⇒ referencia a un ticket (entidad)',
    'R-CORT':   'CORTESIA ⇒ sin valoración ni estado',
    'R-AHORA':  'ADV_T con tiempo AHORA ⇒ la cláusula se refiere al momento actual',
    'R-POSP':   'sujeto después del verbo («no funciona el internet») ⇒ aporta el aspecto como un sujeto explícito',
    'R-COMPAT': 'sujeto y predicado incompatibles (tabla COMPAT), verbo pronominal sin «se» o no pronominal con «se», '
                'dos sujetos o V_CONT sin complemento ⇒ la cláusula no se interpreta',
    'R-SINDOM': 'la cláusula contiene una palabra con el rasgo sin_dominio ⇒ se reconoce pero no se interpreta (abstención)',
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
    """V_EST compl [sujp] y SE V_EST compl [sujp]. Un verbo con el rasgo pronominal (perfil RECUR) exige «se»; los demás, no."""
    i = 1 if con_se else 0
    v, c, pos = sig(n.hijos[i]), ev(n.hijos[i + 1]), _pos(n, i + 2)
    if v['pron'] != con_se:
        return {'k': 'SE_INCOMPATIBLE', 'reglas': []}            # «el servicio corta…», «se funciona»
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
    # R-SINDOM: si alguna palabra de la cláusula tiene el rasgo sin_dominio, se reconoce pero no se interpreta. Se revisa
    # ANTES de evaluar el núcleo: la palabra ocupa su lugar en el árbol, así que no se «pegan» las palabras restantes.
    if any(tk.categoria in PERFILES and rasgos(tk).get('sin_dominio') for tk in n.hojas()):
        return _hecho('SIN_DOMINIO', reglas=['R-SINDOM'])
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
