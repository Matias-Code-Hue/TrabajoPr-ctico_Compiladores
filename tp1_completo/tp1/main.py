#!/usr/bin/env python3
"""Speech Analytics · TP1 Diseño de Compiladores (FPUNA 2026).

Uso:
  python3 main.py ENTRADA.txt                       vista de consola + JSON (salida.json); consulta por cada palabra desconocida
  python3 main.py ENTRADA.txt < /dev/null           sin respuestas: las palabras desconocidas siguen la regla del enunciado
  python3 main.py ENTRADA.txt --traza S01           traza completa de una sesión (o --traza todas)
  python3 main.py ENTRADA.txt --traza S01 --detalle además muestra cada decisión de la tabla LL(1)
  python3 main.py ENTRADA.txt --dic lenta,lento     usa un diccionario reducido (caso 08)
  python3 main.py ENTRADA.txt --vocab otro.json --json resultado.json --quiet
  python3 main.py --reiniciar-aprendido             vuelve a la precarga: borra lo aprendido
  python3 main.py --tabla [CAT]                     tabla de símbolos léxica vigente (precarga + aprendido, «+» = aprendido)
  python3 main.py ENTRADA.txt --tabla [CAT]         analiza la entrada y después muestra la tabla ya enriquecida
  python3 main.py --tabla-inicial [CAT]             tabla inicial: solo la precarga (vocabulario.json)

Tabla de símbolos léxica (persistente):
  precarga (nunca se escribe):  vocabulario.json   categoría -> forma canónica -> {rasgos, formas superficiales}
  lo aprendido:                 vocabulario_aprendido.json (mismo formato; una escritura atómica por cambio)
Ver tabla_lexica.py. Las pruebas (pruebas.py) no preguntan y usan solo la precarga.
"""
import argparse
import json
import os
import sys

from analizador import analizar_lote
from consulta import categorias_insertables, crear_consulta
from sintaxis import TERMINALES_TEXTO
from tabla_lexica import TablaSimbolosLexica, ruta_aprendido

ASPECTOS = ('SERVICIO', 'ATENCION', 'CLARIDAD')
VOCAB_POR_DEFECTO = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vocabulario.json')


def _vista_sesion(s):
    L = []
    L.append(f'══ SESION {s["id"]} · análisis {s["analisis"]} ' + '═' * 40)
    for t in s['turnos']:
        v = ' | '.join(f'{a}: {t["valoraciones"][a]}' for a in ASPECTOS if t['valoraciones'][a] != 'SIN_EVIDENCIA')
        L.append(f'  T{t["numero"]} {t["rol"]:<7} «{t["texto"]}»')
        L.append(f'       ⇒ {v or "SIN_EVIDENCIA en los tres aspectos"}')
    L.append('  Resumen por aspecto (evidencia del CLIENTE):')
    for a in ASPECTOS:
        r = s['resumen_aspectos'][a]
        ag = f'  · opiniones del AGENTE: {r["opiniones_agente"]}' if r['opiniones_agente'] else ''
        L.append(f'     {a:<9} {r["valoracion"]:<14} {", ".join(r["evidencias"])}{ag}')
    e = s['estado']
    L.append(f'  Estado: {e["valor"]}  [{e["regla"]}]  evidencias: {", ".join(e["evidencias"]) or "—"}')
    if e.get('nota'):
        L.append(f'          nota: {e["nota"]}')
    tk = ', '.join(f'{x["clave"]} (×{len(x["apariciones"])})' for x in s['entidades']['tickets']) or '—'
    L.append(f'  Entidades: tickets={tk}; participantes={", ".join(p["clave"] for p in s["entidades"]["participantes"]) or "—"}')
    if s['correcciones']:
        for c in s['correcciones']:
            L.append(f'  Corrección: T{c["turno"]} «{c["original"]}» → {c["resultado"]} [{c["accion"]}'
                     + (f', candidatos {c["candidatos"]}' if c['accion'] == 'EMPATE' else '') + ']')
    for er in s['errores']:
        loc = f'línea {er["linea"]}' if 'linea' in er else f'T{er["turno"]}@{er["desp"]}'
        L.append(f'  Error {er["tipo"]}/{er["codigo"]} ({loc}): {er["detalle"]}')
    for n in s['no_interpretado']:
        L.append(f'  NO_INTERPRETADO: T{n["turno"]}@{n["desp"]} «{n["lexema"]}» ({n["motivo"]})')
    return '\n'.join(L)


def _traza_sesion(sid, trazas, detalle):
    L = [f'┌── TRAZA DE LA SESIÓN {sid} ' + '─' * 40]
    for tr in trazas[sid]:
        L.append(f'│ Turno {tr["turno"]} · {tr["rol"]} · línea {tr["linea"]}')
        L.append(f'│  [1] Texto original : {tr["original"]}')
        toks = '  '.join(f'{t.categoria}«{t.lexema}»@{t.desp}' + (f'→{t.norm}(corr.)' if t.corregido_de else '')
                         + (f'={t.canon}' if t.canon else '') for t in tr['tokens'])
        L.append(f'│  [2] Tokens         : {toks}')
        for n in tr['corrector']:
            L.append(f'│      corrector      : {n}')
        L.append(f'│  [3] Estructura     : {tr["estructura"] or "(sin contenido interpretable: no se invoca al parser)"}')
        if detalle:
            for p in tr['pasos']:
                L.append(f'│        · {p}')
        L.append('│  [4] Tabla entidades:')
        for b in tr['tabla_entidades']:
            L.append(f'│        {b}')
        L.append('│  [5] Acción semántica:' + ('' if tr['acciones'] else ' (ninguna cláusula interpretada)'))
        for a in tr['acciones']:
            L.append(f'│        {a}')
        for n in tr['no_interpretado']:
            L.append(f'│        NO_INTERPRETADO «{n["lexema"]}» ({n["motivo"]})')
        v = ' | '.join(f'{a}: {tr["valoraciones"][a]}' for a in ASPECTOS)
        L.append(f'│  [6] Resultado      : {v}')
        L.append('│')
    L.append('└' + '─' * 60)
    return '\n'.join(L)


def _ver_tabla(tabla, categoria):
    """Tabla de símbolos léxica vigente (precarga + aprendido), para --tabla."""
    fuente = (f'precarga + {os.path.basename(tabla.ruta_aprendido)}' if tabla.persistente
              else 'solo en memoria: diccionario reducido --dic')
    return '\n'.join([f'Tabla de símbolos léxica VIGENTE ({fuente})', '', tabla.mostrar(categoria=categoria or None)])


def _abrir_tabla(vocab):
    """Tabla persistente (precarga + vocabulario_aprendido.json). Avisa si algo aprendido pasó a la precarga."""
    tabla = TablaSimbolosLexica(vocab, ruta_aprendido(vocab))
    if tabla.bajas:
        print('Aviso: ya están en la precarga y se quitaron de lo aprendido: ' + ', '.join(tabla.bajas), file=sys.stderr)
    return tabla


def main(argv=None):
    ap = argparse.ArgumentParser(description='Speech Analytics (TP1 Diseño de Compiladores)')
    ap.add_argument('entrada', nargs='?')
    ap.add_argument('--vocab', default=VOCAB_POR_DEFECTO)
    ap.add_argument('--dic', help='diccionario reducido «forma1,forma2,…» (todas bajo ADJ/LENTO, pol −1); para el caso 08')
    ap.add_argument('--json', default='salida.json')
    ap.add_argument('--traza', metavar='SID|todas')
    ap.add_argument('--detalle', action='store_true')
    ap.add_argument('--quiet', action='store_true', help='no imprimir la vista legible')
    ap.add_argument('--reiniciar-aprendido', action='store_true',
                    help='borra lo aprendido (formas y formas canónicas) y vuelve a la precarga')
    ap.add_argument('--tabla', nargs='?', const='', metavar='CAT',
                    help='muestra la tabla de símbolos léxica vigente (precarga + aprendido, «+» = aprendido); '
                         'con ENTRADA, después de analizarla. CAT: solo esa categoría')
    ap.add_argument('--tabla-inicial', nargs='?', const='', metavar='CAT',
                    help='muestra la tabla inicial (solo la precarga, vocabulario.json). CAT: solo esa categoría')
    a = ap.parse_args(argv)

    if a.reiniciar_aprendido:
        try:
            tabla = _abrir_tabla(a.vocab)
        except (OSError, ValueError) as e:
            print(f'No se pudo abrir la tabla de símbolos léxica: {e}', file=sys.stderr)
            return 2
        n_formas, n_canon = tabla.reiniciar()
        print(f'Tabla de símbolos léxica reiniciada: se quitaron {n_formas} formas y {n_canon} formas canónicas '
              f'aprendidas ({os.path.basename(tabla.ruta_aprendido)} borrado).')
        if not a.entrada:
            return 0
    if a.tabla_inicial is not None or (a.tabla is not None and not a.entrada):
        try:
            tabla = _abrir_tabla(a.vocab)
        except (OSError, ValueError) as e:
            print(f'No se pudo abrir la tabla de símbolos léxica: {e}', file=sys.stderr)
            return 2
        if a.tabla_inicial is not None:
            print(f'Tabla de símbolos léxica INICIAL (precarga: {os.path.basename(a.vocab)})\n')
            print(tabla.mostrar(inicial=True, categoria=a.tabla_inicial or None))
        if a.tabla is not None and not a.entrada:
            print(_ver_tabla(tabla, a.tabla))
        if not a.entrada:
            return 0
    if not a.entrada:
        ap.error('falta el archivo de entrada')

    try:
        if a.dic:                                              # diccionario reducido (caso 08): solo en memoria
            tabla = TablaSimbolosLexica({'ADJ': {'LENTO': {'rasgos': {'pol': -1},
                                                           'formas': [x.strip() for x in a.dic.split(',')]}}})
        else:
            tabla = _abrir_tabla(a.vocab)
        vocab = tabla.vocabulario()                            # precarga + lo aprendido (objeto vivo)
        with open(a.entrada, encoding='utf-8-sig') as f:       # utf-8-sig: tolera el BOM de los editores de Windows
            lineas = f.readlines()
        decidir = crear_consulta(tabla, categorias_insertables(vocab, TERMINALES_TEXTO))
        resultado, trazas = analizar_lote(lineas, vocab, a.entrada, decidir)
    except (OSError, UnicodeDecodeError) as e:                 # archivo inexistente o que no es UTF-8
        print(f'No se pudo leer la entrada o el vocabulario: {e}', file=sys.stderr)
        return 2
    except ValueError as e:                                    # JSON inválido, forma duplicada o rasgos sin perfil
        print(f'Vocabulario inválido: {e}', file=sys.stderr)
        return 2
    with open(a.json, 'w', encoding='utf-8') as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    if not a.quiet:
        for s in resultado['sesiones']:
            print(_vista_sesion(s))
            print()
        for e in resultado['errores_globales']:
            print(f'Error global línea {e["linea"]}: {e["codigo"]} – {e["detalle"]}')
        l = resultado['lote']
        print(f'Lote: {l["sesiones"]} sesiones ({l["completas"]} completas, {l["parciales"]} parciales) → {a.json}')
    r = tabla.resumen()
    if r['insertadas_en_esta_ejecucion'] or r['canonicos_nuevos_en_esta_ejecucion']:
        destino = (f'guardado en {os.path.basename(tabla.ruta_aprendido)}'
                   if tabla.persistente else 'solo en memoria (diccionario reducido --dic: no se guarda)')
        print(f'Tabla de símbolos léxica: {len(r["insertadas_en_esta_ejecucion"])} formas nuevas '
              f'({", ".join(r["insertadas_en_esta_ejecucion"]) or "—"}) y {len(r["canonicos_nuevos_en_esta_ejecucion"])} '
              f'formas canónicas nuevas ({", ".join(r["canonicos_nuevos_en_esta_ejecucion"]) or "—"}); {destino}')
    if a.traza:
        ids = list(trazas) if a.traza.lower() == 'todas' else [a.traza.upper()]
        for sid in ids:
            if sid not in trazas:
                print(f'La sesión {sid} no existe en el lote', file=sys.stderr)
                return 1
            print('\n' + _traza_sesion(sid, trazas, a.detalle))
    if a.tabla is not None:                                    # la tabla ya enriquecida con lo de esta ejecución
        print('\n' + _ver_tabla(tabla, a.tabla))
    return 0


if __name__ == '__main__':
    sys.exit(main())
