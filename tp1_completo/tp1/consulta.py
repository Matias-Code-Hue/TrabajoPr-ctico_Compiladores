"""Consulta interactiva por las palabras desconocidas (corrección de Levenshtein con intervención del usuario).

Por cada palabra desconocida (token PALABRA de al menos MIN_LONG letras) se muestra el turno, los candidatos a
distancia 1 y la propuesta de la regla del enunciado, y el usuario elige:

  1..k   tomar ese candidato SOLO para esta aparición (la tabla de símbolos léxica no cambia)
  n      insertar la palabra como forma nueva en la tabla de símbolos léxica (categoría y canónico) -> se audita
  Enter  aplicar la regla del enunciado (candidato único -> se corrige; empate o ninguno -> se conserva)

La decisión se toma una vez por palabra y por ejecución. Si la entrada se termina (Ctrl-D, o stdin redirigido sin
más respuestas), el resto de las palabras se resuelve con la regla del enunciado, sin preguntar.
Los menús se escriben en stderr para no mezclarse con la vista de consola (stdout).
"""
import re
import sys

from corrector import Correccion
from tabla_lexica import FUERA_DE_GRAMATICA

PROPUESTA = {
    'CORREGIDA': lambda c: f'corregir a «{c.resultado}» (único candidato a distancia 1)',
    'EMPATE': lambda c: 'conservar la palabra y registrar el empate (NO_INTERPRETADO)',
    'SIN_CANDIDATO': lambda c: 'conservar la palabra (NO_INTERPRETADO)',
}


def categorias_insertables(vocab, terminales):
    """Categorías que puede recibir una forma nueva: los terminales de la gramática que vienen del vocabulario,
    RELLENO (sin significado) y FUERA_DE_GRAMATICA (conocida, pero sin función: no se vuelve a preguntar)."""
    return sorted(c for c in vocab if c in terminales) + ['RELLENO', FUERA_DE_GRAMATICA]


def crear_consulta(tabla, archivo, categorias, entrada=None, salida=None):
    """Devuelve decidir(token, correccion, sesion, turno) -> Correccion | None, para analizar_lote()."""
    entrada = entrada or sys.stdin
    salida = salida or sys.stderr
    decididas = {}                                   # forma -> decisión (solo esta ejecución)
    estado = {'fin': False}

    def escribir(txt=''):
        salida.write(txt + '\n')
        salida.flush()

    def leer(prompt):
        if estado['fin']:
            return None
        salida.write(prompt)
        salida.flush()
        r = entrada.readline()
        if r == '':                                  # fin de la entrada
            estado['fin'] = True
            escribir('\n(sin más respuestas: las palabras restantes se resuelven con la regla del enunciado)')
            return None
        return r.strip()

    def elegir_canonico(categoria, forma):
        existentes = tabla.canonicos(categoria)
        sugerido = forma.upper()
        if existentes:
            escribir('  Formas canónicas de ' + categoria + ':')
            for i, c in enumerate(existentes, 1):
                escribir(f'    {i:>2}) {c}')
        while True:
            r = leer(f'  Canónico [número, nombre nuevo o Enter = {sugerido}]: ')
            if r is None:
                return None
            if not r:
                return sugerido
            if r.isdigit() and existentes and 1 <= int(r) <= len(existentes):
                return existentes[int(r) - 1]
            nombre = re.sub(r'\s+', '_', r.strip()).upper()
            if re.fullmatch(r'[A-ZÑ_][A-ZÑ0-9_]*', nombre):
                return nombre
            escribir('  nombre inválido (letras, dígitos y _)')

    def insertar(tk, c, sid, turno):
        escribir('  Categoría (token) de «' + tk.norm + '»:')
        for i, cat in enumerate(categorias, 1):
            extra = (' (sin significado: artículo, preposición…)' if cat == 'RELLENO' else
                     ' (conocida, sin función en la gramática)' if cat == FUERA_DE_GRAMATICA else '')
            escribir(f'    {i:>2}) {cat}{extra}')
        while True:
            r = leer(f'  Categoría [1-{len(categorias)}, Enter = cancelar]: ')
            if not r:
                return None
            if r.isdigit() and 1 <= int(r) <= len(categorias):
                categoria = categorias[int(r) - 1]
                break
            escribir('  opción inválida')
        canonico = elegir_canonico(categoria, tk.norm)
        if canonico is None:
            return None
        origen = {'archivo': archivo, 'sesion': sid, 'turno': turno.numero, 'desp': tk.desp, 'lexema': tk.lexema,
                  'texto': turno.texto}
        decision = {'candidatos': c.candidatos, 'propuesta_enunciado': c.accion}
        if not tabla.insertar(tk.norm, categoria, canonico, origen, decision):
            escribir(f'  «{tk.norm}» ya existe en la tabla: no se inserta')
            return None
        escribir(f'  ✔ «{tk.norm}» → {categoria} / {canonico} guardada en la tabla de símbolos léxica')
        return Correccion(c.original, 'INSERTADA', tk.norm, c.candidatos, categoria, canonico)

    def decidir(tk, c, sid, turno):
        if tk.norm in decididas:
            return decididas[tk.norm]
        if estado['fin']:
            return None
        escribir(f'\nPalabra desconocida «{tk.lexema}» · sesión {sid}, turno {turno.numero}: «{turno.texto}»')
        for i, cand in enumerate(c.candidatos, 1):
            cat, canon, _ = tabla.buscar(cand)
            escribir(f'  {i:>2}) usar «{cand}» ({cat} / {canon}) solo en esta aparición')
        if not c.candidatos:
            escribir('     (sin candidatos a distancia 1)')
        escribir('   n) insertar «' + tk.norm + '» como palabra nueva en la tabla de símbolos léxica')
        escribir('   Enter) regla del enunciado: ' + PROPUESTA[c.accion](c))
        d = None
        while True:
            k = len(c.candidatos)
            r = leer(f'Opción [{"1-" + str(k) + ", " if k else ""}n, Enter]: ')
            if not r:
                break
            if r.isdigit() and 1 <= int(r) <= k:
                d = Correccion(c.original, 'CORREGIDA_USUARIO', c.candidatos[int(r) - 1], c.candidatos)
                break
            if r.lower() == 'n':
                d = insertar(tk, c, sid, turno)
                if d or estado['fin']:
                    break
                continue                             # inserción cancelada: vuelve al menú
            escribir('  opción inválida')
        decididas[tk.norm] = d
        return d

    return decidir
