"""Corrección ortográfica acotada (Levenshtein).
Regla del enunciado: se corrige automáticamente SOLO si existe un único candidato a distancia 1.
  · 0 candidatos  -> SIN_CANDIDATO (queda PALABRA; el parser la marcará NO_INTERPRETADO)
  · ≥2 candidatos -> EMPATE (se conserva la palabra y se registra el empate)
Solo se evalúan tokens PALABRA (no `no`, ni números, ni TK-xxx, que ya tienen otra categoría).

Con una función `decidir` (main.py la conecta a la terminal) se consulta al usuario DESPUÉS del corrector, solo
cuando la regla no resuelve la palabra: SIN_CANDIDATO y EMPATE. Con un candidato único se corrige sin preguntar; las
palabras de menos de MIN_LONG letras no se consultan.
  · CORREGIDA_USUARIO -> se toma uno de los candidatos del EMPATE, SOLO para esa aparición (la tabla no cambia)
  · INSERTADA         -> la palabra se incorpora a la tabla de símbolos léxica (categoría y forma canónica)
  · None              -> se mantiene la regla del enunciado (la respuesta por defecto)
"""
from dataclasses import dataclass, replace
from lexico import plegar

MIN_LONG = 4     # decisión de diseño: no se corrigen palabras de menos de 4 letras (evita «mas» -> «mal»)


def levenshtein(a, b):
    ant = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        act = [i]
        for j, cb in enumerate(b, 1):
            act.append(min(ant[j] + 1,                 # borrado
                           act[j - 1] + 1,             # inserción
                           ant[j - 1] + (ca != cb)))   # sustitución
        ant = act
    return ant[-1]


def indice_vocabulario(vocab):
    """forma plegada -> (categoría, canónico). Las formas superficiales se conservan sin lematizar."""
    return {''.join(plegar(c) for c in f): (cat, canon)
            for cat, canons in vocab.items() for canon, e in canons.items() for f in e['formas']}


@dataclass
class Correccion:
    original: str
    accion: str            # CORREGIDA | EMPATE | SIN_CANDIDATO | OMITIDA_CORTA | CORREGIDA_USUARIO | INSERTADA | APRENDIDA
    resultado: str         # forma final (igual al original si no se corrigió)
    candidatos: list
    categoria: str | None = None     # solo INSERTADA: token elegido por el usuario
    canonico: str | None = None


def evaluar(norm, indice, min_long=MIN_LONG):
    if len(norm) < min_long:
        return Correccion(norm, 'OMITIDA_CORTA', norm, [])
    cands = sorted(f for f in indice if abs(len(f) - len(norm)) <= 1 and levenshtein(norm, f) == 1)
    if len(cands) == 1:
        return Correccion(norm, 'CORREGIDA', cands[0], cands)
    if len(cands) > 1:
        return Correccion(norm, 'EMPATE', norm, cands)
    return Correccion(norm, 'SIN_CANDIDATO', norm, [])


def corregir_tokens(tokens, indice, min_long=MIN_LONG, decidir=None):
    """Devuelve (tokens_nuevos, correcciones). El lexema original se conserva; el token corregido
    se re-categoriza con la categoría de la forma corregida.
    decidir(token, correccion_propuesta) -> Correccion | None : consulta al usuario (None = regla del enunciado).
    Una forma INSERTADA se agrega a `indice`, así sus otras apariciones en el mismo lote ya se reconocen."""
    salida, regs = [], []
    for t in tokens:
        if t.categoria != 'PALABRA':
            salida.append(t)
            continue
        if t.norm in indice:                         # incorporada a la tabla en esta misma ejecución
            cat, canon = indice[t.norm]
            regs.append((t, Correccion(t.norm, 'APRENDIDA', t.norm, [])))
            salida.append(replace(t, categoria=cat, canon=canon))
            continue
        c = evaluar(t.norm, indice, min_long)
        if decidir is not None and c.accion in ('SIN_CANDIDATO', 'EMPATE'):
            c = decidir(t, c) or c
        regs.append((t, c))
        if c.accion in ('CORREGIDA', 'CORREGIDA_USUARIO'):
            cat, canon = indice[c.resultado]
            t = replace(t, categoria=cat, canon=canon, norm=c.resultado, corregido_de=c.original)
        elif c.accion == 'INSERTADA':
            indice[t.norm] = (c.categoria, c.canonico)
            t = replace(t, categoria=c.categoria, canon=c.canonico)
        salida.append(t)
    return salida, regs


if __name__ == '__main__':
    from lexico import construir_afd, cargar_vocabulario, escanear
    voc = cargar_vocabulario('vocabulario.json')
    idx = indice_vocabulario(voc)
    afd = construir_afd(voc)
    for frase in ['El internet está lentto', 'lent', 'mas rapido', 'sin conexionn']:
        _, regs = corregir_tokens(escanear(frase, afd), idx)
        print(frase, '->', [(t.lexema, c.accion, c.resultado, c.candidatos) for t, c in regs])
    # caso 08: diccionario reducido {lenta, lento}
    red = {'ADJ': {'LENTO': {'rasgos': {'pol': -1}, 'formas': ['lenta', 'lento']}}}
    print('caso 08:', evaluar('lent', indice_vocabulario(red)))
