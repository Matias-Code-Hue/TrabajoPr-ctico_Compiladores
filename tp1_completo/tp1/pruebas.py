#!/usr/bin/env python3
"""Ejecutor de pruebas del TP1.
  python3 pruebas.py                 corre todos los casos de casos/casos.json y compara contra lo esperado
  python3 pruebas.py --regresion     además compara el JSON completo contra casos/golden/ (caso de regresión)
  python3 pruebas.py --golden        (re)genera casos/golden/ con la salida actual (revisarla antes de confirmar)
  python3 pruebas.py --informe       escribe RESULTADOS_PRUEBAS.md (esperado, obtenido y reglas activadas)

Los casos se corren SIN consulta al usuario (regla del enunciado) y con la precarga vocabulario.json, nunca con lo
aprendido: así el resultado no depende de ejecuciones interactivas anteriores. Un caso con "respuestas" (17 a 20
insertan palabras fuera del vocabulario) simula esas respuestas al menú sobre una tabla SOLO EN MEMORIA, creada desde
la precarga, y verifica además qué se preguntó ("preguntas") y el resultado sin consulta ("esperado_sin_consulta"). Aparte, `probar_tabla_lexica()`
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


def respuestas_simuladas(tabla, cats, respuestas, preguntas):
    """(entrada, salida) para crear_consulta(). respuestas: texto literal ('n', 'c', un nombre, '' = Enter),
    '#CAT' (número de esa categoría en el menú), '@CAT/CANON' (número de esa forma canónica), '%CAT/PERFIL' (número de
    ese perfil). Los números se resuelven en el momento de la pregunta, así no dependen del orden del menú.
    preguntas: lista que recibe cada palabra por la que se preguntó. Las respuestas sin usar quedan en entrada.pendientes."""
    from consulta import opciones_canonico, opciones_perfil

    class Entrada:
        pendientes = list(respuestas)

        def readline(self):
            if not self.pendientes:
                return ''
            r = self.pendientes.pop(0)
            if r.startswith('#'):
                r = str(cats.index(r[1:]) + 1)
            elif r.startswith('@'):
                c, k = r[1:].split('/')
                r = str(opciones_canonico(tabla, c).index(k) + 1)
            elif r.startswith('%'):
                c, k = r[1:].split('/')
                r = str(opciones_perfil(c).index(k) + 1)
            return r + '\n'

    class Salida(io.StringIO):
        def write(self, t):
            if t.startswith('\nPalabra desconocida'):
                preguntas.append(t.split('«')[1].split('»')[0])
            return super().write(t)

    return Entrada(), Salida()


def correr(caso, consulta=True, registro=None):
    """Corre un caso con la precarga, o con el diccionario reducido del caso ("vocab": un objeto con el formato de
    vocabulario.json, como en el caso 08, o la ruta de un archivo en casos/). Si el caso trae "respuestas" y consulta=True, las
    simula sobre una tabla de símbolos léxica solo en memoria (no se escribe ningún archivo). registro: dict que recibe
    'preguntas' y 'sin_usar'."""
    vocab_c = caso.get('vocab')
    if isinstance(vocab_c, dict):                        # diccionario reducido escrito en casos.json
        ruta = json.loads(json.dumps(vocab_c))           # copia: la tabla en memoria no modifica el caso
    else:
        ruta = os.path.join(DIR, vocab_c) if vocab_c else os.path.join(os.path.dirname(DIR), 'vocabulario.json')
    with open(os.path.join(DIR, caso['archivo']), encoding='utf-8-sig') as f:
        lineas = f.readlines()
    if not (consulta and caso.get('respuestas')):
        return analizar_lote(lineas, ruta if isinstance(ruta, dict) else cargar_vocabulario(ruta), caso['archivo'])[0]
    from consulta import categorias_insertables, crear_consulta
    from sintaxis import TERMINALES_TEXTO
    from tabla_lexica import TablaSimbolosLexica
    tabla = TablaSimbolosLexica(ruta)                    # solo en memoria: no toca vocabulario_aprendido.json
    vocab = tabla.vocabulario()
    cats = categorias_insertables(vocab, TERMINALES_TEXTO)
    preguntas = []
    entrada, salida = respuestas_simuladas(tabla, cats, caso['respuestas'], preguntas)
    r = analizar_lote(lineas, vocab, caso['archivo'], crear_consulta(tabla, cats, entrada, salida))[0]
    if registro is not None:
        registro.update(preguntas=preguntas, sin_usar=list(entrada.pendientes))
    return r


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


def comparar(caso, res, clave='esperado'):
    """Devuelve lista de (sesion, ok, esperado, obtenido). clave: 'esperado' o 'esperado_sin_consulta'."""
    out = []
    sesiones = {s['id']: s for s in res['sesiones']}
    for sid, e in caso[clave].items():
        exp = esperado_completo(e)
        obt = obtenido(sesiones[sid]) if sid in sesiones else None
        out.append((sid, obt == exp, exp, obt))
    if set(sesiones) != set(caso[clave]):
        out.append(('(sesiones)', False, sorted(caso[clave]), sorted(sesiones)))
    return out


def probar_tabla_lexica():
    """Inserción, alta de formas canónicas (con los rasgos del perfil elegido), persistencia en un solo archivo,
    validación de rasgos al cargar, reinicio, preguntas solo después del corrector, SIN_DOMINIO y control
    de duplicados, con respuestas simuladas en una carpeta temporal. Devuelve [(nombre, ok, detalle)]."""
    from consulta import categorias_insertables, crear_consulta
    from semantica import PERFILES
    from sintaxis import TERMINALES_TEXTO
    from tabla_lexica import TablaSimbolosLexica, ruta_aprendido
    base = os.path.dirname(DIR)
    tmp = tempfile.mkdtemp(prefix='tp1_tabla_')
    out = []
    try:
        pre = os.path.join(tmp, 'vocabulario.json')
        shutil.copy(os.path.join(base, 'vocabulario.json'), pre)
        huella = hashlib.sha256(open(pre, 'rb').read()).hexdigest()
        ap = ruta_aprendido(pre)

        def abrir():
            return TablaSimbolosLexica(pre, ap)

        def aprendido():
            return json.load(open(ap, encoding='utf-8')) if os.path.exists(ap) else {}

        def formas_aprendidas():
            return {f for cs in aprendido().values() for e in cs.values() for f in e.get('formas', [])}

        def correr(lote, respuestas):
            """respuestas: texto literal, '#CAT' (número de categoría), '@CAT/CANON' (número de forma canónica),
            '%CAT/PERFIL' (número de perfil)."""
            tabla = abrir()
            vocab = tabla.vocabulario()
            cats = categorias_insertables(vocab, TERMINALES_TEXTO)
            preguntas = []
            dec = crear_consulta(tabla, cats, *respuestas_simuladas(tabla, cats, respuestas, preguntas))
            r, _ = analizar_lote(lote, vocab, 'prueba.txt', dec)
            return tabla, r['sesiones'], preguntas

        def sesion(*turnos):
            return ['SESION S01\n'] + [f'{i} {t}\n' for i, t in enumerate(turnos, 1)] + ['FIN\n']

        def huella_aprendido():
            return hashlib.sha256(open(ap, 'rb').read()).hexdigest() if os.path.exists(ap) else None

        def acciones(s):
            return {c['original']: c['accion'] for c in s['correcciones']}

        # 1) solo se pregunta después del corrector: «lentto» (candidato único) se corrige sin preguntar;
        #    «fatal» (sin candidato) se pregunta y se inserta como variante de ADJ/MALO
        tabla, ss, pregs = correr(sesion('CLIENTE: El servicio anda fatal.', 'CLIENTE: El internet está lentto.'),
                                  ['n', '#ADJ', '@ADJ/MALO'])
        acc = acciones(ss[0])
        out.append(('se pregunta solo después del corrector (SIN_CANDIDATO / EMPATE)',
                    pregs == ['fatal'] and acc.get('lentto') == 'CORREGIDA', f'preguntas={pregs} acciones={acc}'))
        out.append(('inserción como variante de una forma canónica existente',
                    acc.get('fatal') == 'INSERTADA' and ss[0]['estado']['valor'] == 'NO_RESUELTO',
                    f'acciones={acc} estado={ss[0]["estado"]["valor"]}'))
        apr = aprendido()
        out.append(('lo aprendido se guarda aparte, con el formato de la precarga',
                    apr == {'ADJ': {'MALO': {'formas': ['fatal']}}}, f'{apr}'))
        # 2) EMPATE: se ofrecen los candidatos; elegir uno corrige solo esa aparición
        tabla, ss, pregs = correr(sesion('CLIENTE: El servicio está lent.'), ['2'])
        acc = acciones(ss[0])
        out.append(('EMPATE: se ofrecen los candidatos', pregs == ['lent'] and acc.get('lent') == 'CORREGIDA_USUARIO'
                    and 'lent' not in formas_aprendidas(), f'preguntas={pregs} acciones={acc}'))
        # 3) forma canónica nueva: se ofrecen primero las existentes; nombre normalizado, perfil obligatorio;
        #    lo aprendido vale para el resto de la misma entrada (turno 2)
        tabla, ss, pregs = correr(sesion('CLIENTE: El internet colapsa seguido.', 'CLIENTE: Ahora colapsa.'),
                                  ['n', '#V_EST', 'c', 'colapsár', '%V_EST/FALLA'])
        dec2 = [c['declaracion'] for t in ss[0]['turnos'] for c in t['clausulas']]
        nueva = aprendido().get('V_EST', {}).get('COLAPSAR')
        out.append(('alta de forma canónica: nombre normalizado + rasgos del perfil elegido',
                    tabla.perfil_de('V_EST', 'COLAPSAR') == 'FALLA' and tabla.canonicos_nuevos == ['V_EST/COLAPSAR']
                    and nueva == {'rasgos': PERFILES['V_EST']['FALLA']['rasgos'], 'formas': ['colapsa']}, f'{nueva}'))
        out.append(('lo aprendido vale para el resto de la misma entrada', pregs == ['colapsa'] and dec2 == ['FALLA', 'FALLA'],
                    f'preguntas={pregs} declaraciones={dec2}'))
        # 4) duplicados: forma canónica repetida en la categoría (normalizada) y forma ya existente
        dup_canon = tabla.alta_canonico('V_EST', 'Colapsar', 'FALLA')[0] is None
        dup_forma = not tabla.insertar('lento', 'ADJ', 'BUENO')
        out.append(('control de duplicados (formas y formas canónicas)', dup_canon and dup_forma, f'{dup_canon} {dup_forma}'))
        # 5) SIN_DOMINIO: «hace» y «ruidos» se reconocen pero la cláusula no se interpreta (no se pegan las palabras)
        tabla, ss, pregs = correr(sesion('CLIENTE: Mi router hace ruidos raros.'),
                                  ['n', '#V_ACC', 'c', 'hacer', '%V_ACC/SIN_DOMINIO',
                                   'n', '#SUST', 'c', 'ruido', '%SUST/SIN_DOMINIO',
                                   'n', '#ADJ', 'c', 'raro', '%ADJ/SIN_DOMINIO'])
        s = ss[0]
        out.append(('SIN_DOMINIO: la cláusula se abstiene', not s['turnos'][0]['clausulas']
                    and {n['motivo'] for n in s['no_interpretado']} == {'SIN_DOMINIO'}
                    and s['resumen_aspectos']['SERVICIO']['valoracion'] == 'SIN_EVIDENCIA',
                    f'cláusulas={s["turnos"][0]["clausulas"]} NI={s["no_interpretado"]}'))
        # 6) segunda ejecución sin respuestas: reconoce lo aprendido y no reescribe vocabulario_aprendido.json
        h = huella_aprendido()
        tabla, ss, pregs = correr(sesion('CLIENTE: El servicio anda fatal.', 'CLIENTE: El internet colapsa.'), [])
        out.append(('una ejecución posterior reconoce lo aprendido', not pregs and huella_aprendido() == h
                    and ss[0]['estado']['valor'] == 'NO_RESUELTO', f'preguntas={pregs}'))
        # 7) la precarga no se modifica
        out.append(('la precarga no se modifica', hashlib.sha256(open(pre, 'rb').read()).hexdigest() == huella,
                    'sha256 igual'))
        # 7b) menú cerrado también al cargar: rasgos que no son de ningún perfil se rechazan (precarga o aprendido)
        malo = aprendido()
        malo['V_EST']['COLAPSAR']['rasgos'] = {'pol': -1, 'decl': 'OK'}
        apr_bak = open(ap, encoding='utf-8').read()
        json.dump(malo, open(ap, 'w', encoding='utf-8'), ensure_ascii=False)
        rechazos = []
        try:
            abrir()
        except ValueError as e:
            rechazos.append(str(e))
        open(ap, 'w', encoding='utf-8').write(apr_bak)
        try:
            TablaSimbolosLexica({'ADJ': {'RARO': {'rasgos': {'pol': 2}, 'formas': ['raro']}}})
        except ValueError as e:
            rechazos.append(str(e))
        out.append(('rasgos validados al cargar contra los perfiles', len(rechazos) == 2, ' | '.join(rechazos)[:160]))
        # 8) reinicio: se borra lo aprendido y vuelve la precarga
        tabla = abrir()
        n_f, n_c = tabla.reiniciar()
        tabla = abrir()
        out.append(('reinicio de lo aprendido', n_f == 5 and n_c == 4 and tabla.buscar('fatal') is None
                    and not os.path.exists(ap), f'{n_f} formas, {n_c} canónicos'))
        # 9) conciliación: una forma aprendida que pasa a la precarga se da de baja (y se avisa)
        correr(sesion('CLIENTE: El servicio anda fatal.'), ['n', '#ADJ', '@ADJ/MALO'])
        v = json.load(open(pre, encoding='utf-8'))
        v['ADJ']['MALO']['formas'].append('fatal')
        json.dump(v, open(pre, 'w', encoding='utf-8'), ensure_ascii=False)
        tabla = abrir()
        out.append(('baja por precarga (gana la precarga, se avisa)', 'fatal' not in formas_aprendidas()
                    and tabla.buscar('fatal')[2] == 'PRECARGA' and tabla.bajas == ['«fatal» (ADJ/MALO)'], f'{tabla.bajas}'))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out


def comparaciones(caso, res, registro):
    """Comparación principal y, en los casos con "respuestas", las preguntas hechas (y que no sobren respuestas) y
    el resultado sin consulta (regla del enunciado). Filas: (etiqueta, ok, esperado, obtenido)."""
    out = comparar(caso, res)
    if caso.get('respuestas'):
        obt = registro.get('preguntas', [])
        out.append(('consulta', obt == caso.get('preguntas', []) and not registro.get('sin_usar'),
                    caso.get('preguntas', []), obt + ([f'(sin usar: {registro["sin_usar"]})'] if registro.get('sin_usar') else [])))
    if caso.get('esperado_sin_consulta'):
        out += [(f'{sid}·sc', ok, exp, obt) for sid, ok, exp, obt in
                comparar(caso, correr(caso, consulta=False), 'esperado_sin_consulta')]
    return out


def informe(casos, resultados, registros=None):
    L = ['# Resultados de las pruebas (TP1)', '',
         'Generado por `python3 pruebas.py --informe`. Para cada caso: situación, salida **esperada** (derivada del enunciado '
         'o del criterio del grupo), salida **obtenida** y las **reglas activadas** (ver catálogo en `salida.json` / `semantica.py`).', '']
    registros = registros or [{} for _ in casos]
    for caso, res, reg in zip(casos, resultados, registros):
        L += [f'## Caso {caso["caso"]} — {caso["situacion"]}', '', f'- Origen: {caso["origen"]} · archivo `casos/{caso["archivo"]}`'
              + (f' · diccionario reducido `{json.dumps(caso["vocab"], ensure_ascii=False)}`' if isinstance(caso.get('vocab'), dict)
                 else f' · diccionario `casos/{caso["vocab"]}`' if caso.get('vocab') else ''), '']
        if caso.get('respuestas'):
            L += [f'- Respuestas al menú (simuladas): `{" ".join(r if r else "⏎" for r in caso["respuestas"])}`'
                  + (f' — {caso["menu"]}' if caso.get('menu') else ''), '']
        for sid, ok, exp, obt in comparaciones(caso, res, reg):
            if sid == 'consulta':
                L += [f'**Consulta: {"OK" if ok else "FALLA"}** — se preguntó por: {", ".join(f"«{p}»" for p in obt) or "nada"}'
                      f' (esperado: {", ".join(f"«{p}»" for p in exp) or "nada"})', '']
                continue
            sc = sid.endswith('·sc')
            titulo = f'Sesión {sid[:-3]} sin consulta (regla del enunciado, solo precarga)' if sc else f'Sesión {sid}'
            L += [f'**{titulo}: {"OK" if ok else "FALLA"}**', '', '| | Esperado | Obtenido |', '|---|---|---|']
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
            s = None if sc else next((x for x in res['sesiones'] if x['id'] == sid), None)
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
    registros = [{} for _ in casos]
    resultados = [correr(c, registro=g) for c, g in zip(casos, registros)]
    if '--golden' in args:
        os.makedirs(os.path.join(DIR, 'golden'), exist_ok=True)
        for c, r in zip(casos, resultados):
            with open(os.path.join(DIR, 'golden', f'caso_{c["caso"]}.json'), 'w', encoding='utf-8') as f:
                json.dump(r, f, ensure_ascii=False, indent=2, sort_keys=True)
        print(f'golden generado en casos/golden/ ({len(casos)} archivos)')
        return 0
    fallas = 0
    print(f'{"caso":<5}{"sesión":<10}{"resultado":<10}detalle')
    for c, r, g in zip(casos, resultados, registros):
        for sid, ok, exp, obt in comparaciones(c, r, g):
            fallas += not ok
            det = ''
            if not ok:
                det = f'esperado={exp}\n{"":25}obtenido={obt}'
            elif isinstance(obt, dict):
                det = f'{obt["estado"]:<15}' + ' '.join(f'{a[:3]}={v}' for a, v in obt['aspectos'].items() if v != 'SIN_EVIDENCIA')
            elif isinstance(obt, list):
                det = 'preguntas: ' + ', '.join(obt)
            print(f'{c["caso"]:<5}{sid:<10}{"OK" if ok else "FALLA":<10}{det}')
    print('\nTabla de símbolos léxica (consulta simulada, persistencia, reinicio, SIN_DOMINIO):')
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
            f.write(informe(casos, resultados, registros))
        print('\nRESULTADOS_PRUEBAS.md escrito')
    print(f'\n{"TODAS LAS PRUEBAS PASAN" if not fallas else f"{fallas} FALLA(S)"}')
    return 1 if fallas else 0


if __name__ == '__main__':
    sys.exit(main())
