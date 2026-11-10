"""Pipeline del TP1:  lector -> léxico -> corrector -> parser LL(1) -> semántica -> tabla de símbolos -> resultado.

analizar_lote(lineas, vocab) devuelve (resultado, trazas):
  · resultado: estructura serializable a JSON (un objeto por lote, con las sesiones adentro)
  · trazas[sid]: lista por turno con cada etapa (texto original → tokens → estructura → tabla de símbolos
                 → acción semántica → resultado) para la vista de consola.
"""
from lexico import Token, construir_afd
from lector import leer_lote
from corrector import indice_vocabulario, corregir_tokens
from simbolos import TablaSimbolos, Aparicion
from sintaxis import AnalizadorSintactico, TERMINALES_TEXTO, arbol
import semantica as sem

MOTIVO = {'TICKET_MAL': 'TICKET_MAL_FORMADO', 'DESCONOCIDO': 'CARACTER_INVALIDO', 'NUM': 'NUMERO_FUERA_DE_GRAMATICA'}


def _tok(t):
    d = {'categoria': t.categoria, 'lexema': t.lexema, 'normalizado': t.norm, 'canonico': t.canon, 'desp': t.desp}
    if t.corregido_de:
        d['corregido_de'] = t.corregido_de
    return d


def _fragmento(linea, completos, pos, hojas):
    """Texto de la cláusula, extendido hacia atrás sobre los RELLENO contiguos («El», «Me», «el»…)."""
    i = pos[hojas[0].desp]
    while i > 0 and completos[i - 1].categoria == 'RELLENO':
        i -= 1
    desde, hasta = completos[i].desp, hojas[-1].desp + len(hojas[-1].lexema)
    return linea[desde:hasta], desde, hasta


def _analizar_turno(sid, t, idx, ts, num_clausula_ini=0):
    tr = {'turno': t.numero, 'rol': t.rol, 'linea': t.linea, 'original': t.linea_txt}
    mark = len(ts.bitacora)

    # --- tabla de símbolos: participante
    rol_lex = t.linea_txt[t.rol_desp:t.rol_desp + len(t.rol)]
    ts.buscar(sid, 'PARTICIPANTE', t.rol)
    ts.insertar(sid, 'PARTICIPANTE', t.rol, Aparicion(t.numero, t.rol_desp, rol_lex))

    # --- corrector ortográfico (solo PALABRA)
    toks, regs = corregir_tokens(t.tokens, idx)
    por_desp = {tk.desp: c for tk, c in regs}
    correcciones, errores, no_interp, notas_corr = [], [], [], []
    for tk, c in regs:
        if c.accion in ('CORREGIDA', 'EMPATE'):
            correcciones.append({'turno': t.numero, 'desp': tk.desp, 'original': tk.lexema, 'normalizado': c.original,
                                 'resultado': c.resultado, 'accion': c.accion, 'candidatos': c.candidatos})
        notas_corr.append(f'«{tk.lexema}» → {c.accion}' + (f' candidatos={c.candidatos}' if c.candidatos else ''))

    # --- clasificación de tokens para el parser
    flujo = []
    for tk in toks:
        if tk.categoria in ('RELLENO', 'SIGNO'):
            continue
        if tk.categoria in TERMINALES_TEXTO:
            flujo.append(tk)
            continue
        motivo = MOTIVO.get(tk.categoria, 'FUERA_DE_GRAMATICA')
        if tk.categoria == 'PALABRA':
            c = por_desp.get(tk.desp)
            motivo = 'EMPATE_LEVENSHTEIN' if c and c.accion == 'EMPATE' else 'PALABRA_DESCONOCIDA'
        no_interp.append((tk, motivo))
        if tk.categoria in ('TICKET_MAL', 'DESCONOCIDO'):
            errores.append({'tipo': 'LEXICO', 'turno': t.numero, 'codigo': MOTIVO[tk.categoria], 'desp': tk.desp,
                            'detalle': f'«{tk.lexema}» no es un lexema válido'})

    # --- tabla de símbolos: tickets (todas las referencias válidas)
    for tk in toks:
        if tk.categoria == 'TICKET':
            ts.buscar(sid, 'TICKET', tk.norm)
            ts.insertar(sid, 'TICKET', tk.norm, Aparicion(t.numero, tk.desp, tk.lexema), ultima_mencion=t.numero)

    # --- parser LL(1)
    eol = Token('EOL', '', '', None, sid, t.numero, len(t.linea_txt))
    ps = AnalizadorSintactico(flujo, eol)
    raiz = ps.analizar() if flujo else None
    for e in ps.errores:
        errores.append({'tipo': 'SINTAXIS', 'turno': t.numero, 'codigo': 'SINTAXIS', 'desp': e['desp'],
                        'detalle': e['detalle']})

    # --- acciones semánticas
    pos = {tk.desp: i for i, tk in enumerate(toks)}
    cls, acciones, rangos_error = [], [], []
    if raiz is not None:
        for k, (cn, conector) in enumerate(sem.clausulas(raiz), 1):
            cid = f'C{t.numero}.{k}'
            if cn.error:
                err_toks = ps.t[cn.rango[0]:cn.rango[1]]
                rangos_error.append(cn.rango)
                for tk in err_toks:
                    no_interp.append((tk, 'FUERA_DE_GRAMATICA'))
                acciones.append(f'{cid} cláusula con error sintáctico → NO_INTERPRETADO: '
                                + ' '.join(f'«{tk.lexema}»' for tk in err_toks))
                continue
            h = sem.ev(cn)
            frag, desde, hasta = _fragmento(t.linea_txt, toks, pos, list(cn.hojas()))
            if conector == 'PERO':
                h['reglas'].append('R-PERO')
            c = {'id': cid, 'turno': t.numero, 'actor': t.rol, 'fragmento': frag, 'desde': desde, 'hasta': hasta,
                 'conector': conector, **h}
            if conector == 'PERO' and cls:
                c['en_contraste_con'] = cls[-1]['id']
            # actualización de la tabla de símbolos desde la acción semántica
            if c['tipo'] == 'COMPROMISO':
                for tk_norm in c['entidades']:
                    ts.actualizar(sid, 'TICKET', tk_norm, seguimiento='COMPROMISO_FUTURO',
                                  compromiso_turno=t.numero, compromiso_actor=t.rol)
            cls.append(c)
            res = (f'{c["aspecto"]}={c["valoracion"]}' if c['aspecto'] else c['tipo'])
            extra = f' declaración={c["declaracion"]}' if c['declaracion'] else ''
            acciones.append(f'{cid} «{frag}» → {res}{extra}  [{", ".join(c["reglas"])}]')

    # --- tokens descartados por la recuperación fuera de una cláusula con error
    dentro = {tk.desp for r in rangos_error for tk in ps.t[r[0]:r[1]]}
    for tk in ps.descartados:
        if tk.desp not in dentro:
            no_interp.append((tk, 'FUERA_DE_GRAMATICA'))
    vistos, ni = set(), []
    for tk, motivo in sorted(no_interp, key=lambda x: x[0].desp):
        if tk.categoria in ('PUNTO', 'COMA'):        # la puntuación descartada no es un fragmento fuera de la gramática
            continue
        if tk.desp not in vistos:
            vistos.add(tk.desp)
            ni.append({'turno': t.numero, 'desp': tk.desp, 'lexema': tk.lexema, 'motivo': motivo})

    val = sem.valoraciones_por_aspecto(cls)
    turno_out = {'numero': t.numero, 'rol': t.rol, 'linea': t.linea, 'texto': t.texto,
                 'tokens': [_tok(tk) for tk in toks], 'estructura': arbol(raiz) if raiz is not None else None,
                 'clausulas': cls, 'valoraciones': val, 'no_interpretado': ni}
    tr.update({'tokens': toks, 'corrector': notas_corr, 'estructura': turno_out['estructura'], 'pasos': ps.pasos,
               'tabla_simbolos': ts.bitacora[mark:], 'acciones': acciones, 'valoraciones': val, 'no_interpretado': ni,
               'sin_contenido': raiz is None})
    return turno_out, cls, correcciones, errores, ni, tr


def _err_formato(e):
    return {'tipo': 'FORMATO', 'linea': e.linea, 'codigo': e.codigo, 'detalle': e.detalle, 'contenido': e.contenido}


def _analizar_sesion(s, idx, ts):
    sid = s.id
    ts.buscar(sid, 'SESION', sid)
    ts.insertar(sid, 'SESION', sid, Aparicion(None, None, sid), linea_inicio=s.linea_ini)
    turnos, cls_all, corr_all, ni_all, trazas = [], [], [], [], []
    errores = [_err_formato(e) for e in s.errores]
    for t in s.turnos:
        turno_out, cls, corr, errs, ni, tr = _analizar_turno(sid, t, idx, ts)
        turnos.append(turno_out)
        cls_all += cls
        corr_all += corr
        errores += errs
        ni_all += ni
        trazas.append(tr)
    estado = sem.decidir_estado(cls_all)
    ts.actualizar(sid, 'SESION', sid, estado=estado['valor'], analisis='PARCIAL' if s.parcial else 'COMPLETO')
    evid = [c for c in cls_all if c['valoracion'] or c['declaracion'] or c['tipo'] == 'COMPROMISO']
    tickets = [e for e in ts.a_dict(sid) if e['tipo'] == 'TICKET']
    parts = [e for e in ts.a_dict(sid) if e['tipo'] == 'PARTICIPANTE']
    out = {'id': sid, 'analisis': 'PARCIAL' if s.parcial else 'COMPLETO', 'turnos': turnos,
           'resumen_aspectos': sem.resumen_aspectos(cls_all), 'estado': estado,
           'entidades': {'participantes': parts, 'tickets': tickets},
           'correcciones': corr_all, 'errores': errores, 'no_interpretado': ni_all, 'evidencias': evid}
    return out, trazas


def analizar_lote(lineas, vocab, archivo=''):
    afd = construir_afd(vocab)
    idx = indice_vocabulario(vocab)
    sesiones, globales = leer_lote(lineas, afd)
    ts = TablaSimbolos()
    out, trazas = [], {}
    for s in sesiones:
        o, tr = _analizar_sesion(s, idx, ts)
        out.append(o)
        trazas[s.id] = tr
    resultado = {'lote': {'archivo': archivo, 'sesiones': len(out),
                          'completas': sum(o['analisis'] == 'COMPLETO' for o in out),
                          'parciales': sum(o['analisis'] == 'PARCIAL' for o in out)},
                 'sesiones': out,
                 'errores_globales': [_err_formato(e) for e in globales],
                 'catalogo_reglas': sem.REGLAS}
    return resultado, trazas
