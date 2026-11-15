#!/usr/bin/env python3
"""Ejecutor de pruebas del TP1.
  python3 pruebas.py                 corre todos los casos de casos/casos.json y compara contra lo esperado
  python3 pruebas.py --regresion     además compara el JSON completo contra casos/golden/ (caso de regresión)
  python3 pruebas.py --golden        (re)genera casos/golden/ con la salida actual (revisarla antes de confirmar)
  python3 pruebas.py --informe       escribe RESULTADOS_PRUEBAS.md (esperado, obtenido y reglas activadas)

Los casos se corren SIN consulta al usuario (regla del enunciado) y con la precarga vocabulario.json, nunca con lo
aprendido: así el resultado no depende de ejecuciones interactivas anteriores. Aparte, `probar_tabla_lexica()`
verifica la tabla de símbolos léxica persistente con respuestas simuladas, en una carpeta temporal.
"""
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile

from analizador import analizar_lote
from lexico import cargar_vocabulario

ASPECTOS = ('SERVICIO', 'ATENCION', 'CLARIDAD')
DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'casos')


def correr(caso):
    vocab_f = caso.get('vocab')
    vocab = cargar_vocabulario(os.path.join(DIR, vocab_f)) if vocab_f else cargar_vocabulario(
        os.path.join(os.path.dirname(DIR), 'vocabulario.json'))
    with open(os.path.join(DIR, caso['archivo']), encoding='utf-8-sig') as f:
        return analizar_lote(f.readlines(), vocab, caso['archivo'])[0]


def obtenido(s):
    return {'analisis': s['analisis'],
            'aspectos': {a: s['resumen_aspectos'][a]['valoracion'] for a in ASPECTOS},
            'estado': s['estado']['valor'],
            'correcciones': sorted([c['original'], c['resultado'], c['accion']] for c in s['correcciones']),
            'tickets': sorted(t['clave'] for t in s['entidades']['tickets']),
            'errores': sorted(e['codigo'] for e in s['errores']),
            'no_interpretado': sorted(n['lexema'] for n in s['no_interpretado'])}


def esperado_completo(e):
    return {'analisis': e['analisis'],
            'aspectos': {a: e['aspectos'].get(a, 'SIN_EVIDENCIA') for a in ASPECTOS},
            'estado': e['estado'],
            'correcciones': sorted(e.get('correcciones', [])), 'tickets': sorted(e.get('tickets', [])),
            'errores': sorted(e.get('errores', [])), 'no_interpretado': sorted(e.get('no_interpretado', []))}


def comparar(caso, res):
    """Devuelve lista de (sesion, ok, esperado, obtenido)."""
    out = []
    sesiones = {s['id']: s for s in res['sesiones']}
    for sid, e in caso['esperado'].items():
        exp = esperado_completo(e)
        obt = obtenido(sesiones[sid]) if sid in sesiones else None
        out.append((sid, obt == exp, exp, obt))
    if set(sesiones) != set(caso['esperado']):
        out.append(('(sesiones)', False, sorted(caso['esperado']), sorted(sesiones)))
    return out


def probar_tabla_lexica():
    """Inserción, persistencia, auditoría, corrección de una sola aparición y control de duplicados.
    Devuelve [(nombre, ok, detalle)]."""
    from consulta import categorias_insertables, crear_consulta, opciones_canonico
    from sintaxis import TERMINALES_TEXTO
    from tabla_lexica import TablaSimbolosLexica, rutas_por_defecto
    base = os.path.dirname(DIR)
    tmp = tempfile.mkdtemp(prefix='tp1_tabla_')
    out = []
    try:
        pre = os.path.join(tmp, 'vocabulario.json')
        shutil.copy(os.path.join(base, 'vocabulario.json'), pre)
        huella = hashlib.sha256(open(pre, 'rb').read()).hexdigest()
        ap, aud = rutas_por_defecto(pre)
        lote = ['SESION S01\n', '1 CLIENTE: El servicio anda fatal.\n', '2 CLIENTE: El internet está lentto.\n', 'FIN\n']

        def correr(respuestas):
            tabla = TablaSimbolosLexica(pre, ap, aud)
            vocab = tabla.vocabulario()
            cats = categorias_insertables(vocab, TERMINALES_TEXTO)
            resp = [str(cats.index(r[1:]) + 1) if r.startswith('#') else
                    str(opciones_canonico(tabla, r[1:].split('/')[0]).index(r[1:].split('/')[1]) + 1) if r.startswith('@') else r
                    for r in respuestas]
            dec = crear_consulta(tabla, 'prueba.txt', cats, io.StringIO(''.join(x + '\n' for x in resp)), io.StringIO())
            r, _ = analizar_lote(lote, vocab, 'prueba.txt', dec)
            return tabla, r['sesiones'][0]

        def lineas_auditoria():
            return [json.loads(x) for x in open(aud, encoding='utf-8')] if os.path.exists(aud) else []

        # ejecución 1: «fatal» -> insertar como variante de ADJ/MALO; «lentto» -> elegir el candidato 1 (solo esa aparición)
        tabla, s = correr(['n', '#ADJ', '@ADJ/MALO', '1'])
        acc = {c['original']: c['accion'] for c in s['correcciones']}
        out.append(('inserción interactiva', acc.get('fatal') == 'INSERTADA' and s['estado']['valor'] == 'NO_RESUELTO',
                    f'acciones={acc} estado={s["estado"]["valor"]}'))
        aprendido = json.load(open(ap, encoding='utf-8'))
        out.append(('persistencia en vocabulario_aprendido.json',
                    set(aprendido) == {'fatal'} and aprendido['fatal']['categoria'] == 'ADJ' and aprendido['fatal']['canonico'] == 'MALO', f'{sorted(aprendido)}'))
        aud1 = lineas_auditoria()
        out.append(('auditoría: una línea INSERTAR con origen', len(aud1) == 1 and aud1[0]['operacion'] == 'INSERTAR'
                    and aud1[0]['origen'].get('turno') == 1, f'{[(a["operacion"], a["forma"]) for a in aud1]}'))
        out.append(('corrección de una sola aparición no cambia la tabla',
                    acc.get('lentto') == 'CORREGIDA_USUARIO' and 'lentto' not in aprendido, f'acciones={acc}'))
        # ejecución 2: sin respuestas -> «fatal» ya está en la tabla; no hay cambios ni líneas nuevas de auditoría
        tabla, s = correr([])
        cat = next(t['categoria'] for t in s['turnos'][0]['tokens'] if t['normalizado'] == 'fatal')
        out.append(('segunda ejecución reconoce lo aprendido', cat == 'ADJ' and s['estado']['valor'] == 'NO_RESUELTO'
                    and len(lineas_auditoria()) == 1, f'categoría={cat} estado={s["estado"]["valor"]}'))
        out.append(('control de duplicados', not tabla.insertar('fatal', 'ADJ', 'BUENO') and not tabla.insertar('lento', 'ADJ', 'BUENO'),
                    'insertar(fatal) e insertar(lento) rechazados'))
        out.append(('la precarga no se modifica', hashlib.sha256(open(pre, 'rb').read()).hexdigest() == huella, 'sha256 igual'))
        # conciliación: la forma pasa a la precarga -> la entrada aprendida se da de baja y se audita
        v = json.load(open(pre, encoding='utf-8'))
        v['ADJ']['MALO'].append('fatal')
        json.dump(v, open(pre, 'w', encoding='utf-8'), ensure_ascii=False)
        tabla = TablaSimbolosLexica(pre, ap, aud)
        out.append(('baja por precarga auditada', 'fatal' not in tabla.aprendido
                    and lineas_auditoria()[-1]['operacion'] == 'BAJA_POR_PRECARGA', f'{lineas_auditoria()[-1]["operacion"]}'))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out


def informe(casos, resultados):
    L = ['# Resultados de las pruebas (TP1)', '',
         'Generado por `python3 pruebas.py --informe`. Para cada caso: situación, salida **esperada** (derivada del enunciado '
         'o del criterio del grupo), salida **obtenida** y las **reglas activadas** (ver catálogo en `salida.json` / `semantica.py`).', '']
    for caso, res in zip(casos, resultados):
        L += [f'## Caso {caso["caso"]} — {caso["situacion"]}', '', f'- Origen: {caso["origen"]} · archivo `casos/{caso["archivo"]}`'
              + (f' · diccionario `casos/{caso["vocab"]}`' if caso.get('vocab') else ''), '']
        for sid, ok, exp, obt in comparar(caso, res):
            L += [f'**Sesión {sid}: {"OK" if ok else "FALLA"}**', '', '| | Esperado | Obtenido |', '|---|---|---|']
            if obt is None:
                L += ['| sesión | presente | **no existe en la salida** |', '']
                continue
            if isinstance(exp, dict):
                for k in ('analisis', 'estado'):
                    L.append(f'| {k} | {exp[k]} | {obt[k]} |')
                for a in ASPECTOS:
                    L.append(f'| {a} | {exp["aspectos"][a]} | {obt["aspectos"][a]} |')
                for k in ('correcciones', 'tickets', 'errores', 'no_interpretado'):
                    if exp[k] or obt[k]:
                        L.append(f'| {k} | {exp[k]} | {obt[k]} |')
            L.append('')
            s = next((x for x in res['sesiones'] if x['id'] == sid), None)
            if s:
                reglas = {}
                for c in s['evidencias']:
                    for r in c['reglas']:
                        reglas.setdefault(r, []).append(c['id'])
                reglas[s['estado']['regla']] = s['estado']['evidencias'] or ['—']
                L.append('Reglas activadas: ' + '; '.join(f'`{r}` ({", ".join(ids)})' for r, ids in sorted(reglas.items())))
                L.append('')
                for c in s['evidencias']:
                    L.append(f'- {c["id"]} ({c["actor"]}) «{c["fragmento"]}» → '
                             + (f'{c["aspecto"]} {c["valoracion"]}' if c['aspecto'] else c['tipo'])
                             + (f', declaración {c["declaracion"]}' if c['declaracion'] else ''))
                L.append(f'- Estado: **{s["estado"]["valor"]}** por `{s["estado"]["regla"]}`'
                         + (f' — {s["estado"]["nota"]}' if s['estado'].get('nota') else ''))
                L.append('')
    return '\n'.join(L)


def main():
    args = sys.argv[1:]
    with open(os.path.join(DIR, 'casos.json'), encoding='utf-8') as f:
        casos = json.load(f)
    resultados = [correr(c) for c in casos]
    if '--golden' in args:
        os.makedirs(os.path.join(DIR, 'golden'), exist_ok=True)
        for c, r in zip(casos, resultados):
            with open(os.path.join(DIR, 'golden', f'caso_{c["caso"]}.json'), 'w', encoding='utf-8') as f:
                json.dump(r, f, ensure_ascii=False, indent=2, sort_keys=True)
        print(f'golden generado en casos/golden/ ({len(casos)} archivos)')
        return 0
    fallas = 0
    print(f'{"caso":<5}{"sesión":<8}{"resultado":<10}detalle')
    for c, r in zip(casos, resultados):
        for sid, ok, exp, obt in comparar(c, r):
            fallas += not ok
            det = ''
            if not ok:
                det = f'esperado={exp}\n{"":23}obtenido={obt}'
            elif isinstance(obt, dict):
                det = f'{obt["estado"]:<15}' + ' '.join(f'{a[:3]}={v}' for a, v in obt['aspectos'].items() if v != 'SIN_EVIDENCIA')
            print(f'{c["caso"]:<5}{sid:<8}{"OK" if ok else "FALLA":<10}{det}')
    print('\nTabla de símbolos léxica (persistencia, auditoría, consulta simulada):')
    for nombre, ok, det in probar_tabla_lexica():
        fallas += not ok
        print(f'  {"OK" if ok else "FALLA":<6}{nombre}' + ('' if ok else f'  → {det}'))
    if '--regresion' in args:
        print('\nRegresión contra casos/golden/:')
        for c, r in zip(casos, resultados):
            ruta = os.path.join(DIR, 'golden', f'caso_{c["caso"]}.json')
            if not os.path.exists(ruta):
                print(f'  caso {c["caso"]}: SIN GOLDEN (ejecute --golden)')
                fallas += 1
                continue
            with open(ruta, encoding='utf-8') as f:
                g = json.load(f)
            igual = json.dumps(g, sort_keys=True, ensure_ascii=False) == json.dumps(r, sort_keys=True, ensure_ascii=False)
            fallas += not igual
            print(f'  caso {c["caso"]}: {"IGUAL" if igual else "DIFERENTE"}')
    if '--informe' in args:
        with open(os.path.join(os.path.dirname(DIR), 'RESULTADOS_PRUEBAS.md'), 'w', encoding='utf-8') as f:
            f.write(informe(casos, resultados))
        print('\nRESULTADOS_PRUEBAS.md escrito')
    print(f'\n{"TODAS LAS PRUEBAS PASAN" if not fallas else f"{fallas} FALLA(S)"}')
    return 1 if fallas else 0


if __name__ == '__main__':
    sys.exit(main())
