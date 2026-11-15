"""Consulta interactiva por las palabras desconocidas, DESPUÉS del corrector de Levenshtein.

Solo se pregunta cuando la regla del enunciado no resuelve la palabra (token PALABRA de al menos MIN_LONG letras):
  · SIN_CANDIDATO  -> se ofrece insertarla en la tabla de símbolos léxica
  · EMPATE         -> se ofrecen los candidatos (corrección de esa aparición) o insertarla
  (un candidato único se corrige sin preguntar, como pide el enunciado)

  1..k   tomar ese candidato del empate SOLO para esta aparición (la tabla de símbolos léxica no cambia)
  n      insertar la palabra en la tabla de símbolos léxica (menú cerrado):
           1) categoría (token): solo las existentes
           2) forma canónica de la que es variante (hereda sus rasgos): se ofrecen primero las existentes de esa
              categoría, con sus rasgos; también se puede crear una nueva -> nombre normalizado, sin duplicados en la
              categoría, y un PERFIL obligatorio elegido entre los existentes de la categoría: el programa copia sus
              rasgos en la entrada nueva (el usuario no escribe rasgos).
  Enter  mantener la regla del enunciado (empate o sin candidato -> la palabra queda NO_INTERPRETADA)

La decisión se toma una vez por palabra y por ejecución, y lo aprendido vale para el resto de la misma entrada. Si la
entrada se termina (Ctrl-D, o stdin redirigido sin más respuestas), el resto se resuelve con la regla del enunciado.
Los menús se escriben en stderr para no mezclarse con la vista de consola (stdout).
"""
import json
import sys

from corrector import Correccion
from semantica import PERFILES
from tabla_lexica import FUERA_DE_GRAMATICA, normalizar_canonico

PROPUESTA = {
    'EMPATE': lambda c: 'conservar la palabra y registrar el empate (NO_INTERPRETADO)',
    'SIN_CANDIDATO': lambda c: 'conservar la palabra (NO_INTERPRETADO)',
}

# Menú de categorías (cerrado): las categorías léxicas agrupadas por tipo de palabra, con una descripción.
MENU = [
    ('Cosa, cualidad o momento', [
        ('SUST', 'sustantivo: internet, atención, explicación, router, ticket, corte'),
        ('ADJ', 'cualidad: bien, lento, amable, confuso'),
        ('ADV_T', 'momento: ahora, mañana')]),
    ('Acción o estado (verbo)', [
        ('V_EST', 'estado del servicio: funciona, falla, se corta'),
        ('V_ACC', 'acción: entender, reiniciar, revisar, atender, explicar'),
        ('V_COP', 'ser o estar: es, está, fue'),
        ('V_CONT', 'seguir: sigue, sigo')]),
    ('Palabra gramatical', [
        ('NEG', 'negación: no, nunca'),
        ('SIN', 'sin'),
        ('INT', 'intensificador: muy, bastante'),
        ('PERO', 'contraste: pero'),
        ('Y', 'unión de cláusulas: y'),
        ('SE', 'se'),
        ('FREC', 'frecuencia: siempre, todos los días'),
        ('CORTESIA', 'cortesía: gracias, hola')]),
    ('Sin efecto en el análisis', [
        ('RELLENO', 'sin significado: artículo, preposición… (se filtra antes del parser)'),
        (FUERA_DE_GRAMATICA, 'conocida, sin función en la gramática: no se vuelve a preguntar')]),
]
GRUPO = {cat: titulo for titulo, cats in MENU for cat, _ in cats}
DESCRIPCION = {cat: d for _, cats in MENU for cat, d in cats}


def categorias_insertables(vocab, terminales):
    """Categorías que puede recibir una forma nueva, en el orden del menú: las categorías léxicas que son terminales
    de la gramática, RELLENO y FUERA_DE_GRAMATICA. (vocab se conserva por compatibilidad; no se usa.)"""
    return [cat for _, cats in MENU for cat, _ in cats if cat in terminales or cat in ('RELLENO', FUERA_DE_GRAMATICA)]


def opciones_canonico(tabla, categoria):
    """Formas canónicas existentes de una categoría (precarga y aprendidas), en el orden en que se ofrecen."""
    return tabla.canonicos(categoria)


def opciones_perfil(categoria):
    """Perfiles existentes de una categoría (semantica.PERFILES), en el orden en que se ofrecen."""
    return list(PERFILES[categoria])


def _ver_rasgos(rasgos):
    return json.dumps(rasgos, ensure_ascii=False) if rasgos else 'sin rasgos'


def crear_consulta(tabla, categorias, entrada=None, salida=None):
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

    def elegir_numero(prompt, n):
        """Número entre 1 y n; None si se cancela (Enter) o se termina la entrada."""
        while True:
            r = leer(prompt)
            if not r:
                return None
            if r.isdigit() and 1 <= int(r) <= n:
                return int(r) - 1
            escribir('  opción inválida')

    def elegir_categoria(forma):
        escribir(f'  1) ¿Qué tipo de palabra es «{forma}»? (categoría léxica)')
        grupo = None
        for i, cat in enumerate(categorias, 1):
            if GRUPO.get(cat) != grupo:
                grupo = GRUPO.get(cat)
                escribir(f'    {grupo}:')
            escribir(f'      {i:>2}) {cat:<9} {DESCRIPCION.get(cat, "")}')
        k = elegir_numero(f'  Categoría [1-{len(categorias)}, Enter = cancelar]: ', len(categorias))
        return None if k is None else categorias[k]

    def elegir_perfil(categoria):
        perfiles = opciones_perfil(categoria)
        if len(perfiles) == 1:
            escribir(f'     perfil: {perfiles[0]} (único perfil de {categoria}; {_ver_rasgos(PERFILES[categoria][perfiles[0]]["rasgos"])})')
            return perfiles[0]
        escribir(f'  3) ¿Qué significa? (perfil de {categoria}; solo los existentes)')
        for i, p in enumerate(perfiles, 1):
            escribir(f'    {i:>2}) {p:<12} {PERFILES[categoria][p]["desc"]}; rasgos {_ver_rasgos(PERFILES[categoria][p]["rasgos"])}')
        k = elegir_numero(f'  Perfil [1-{len(perfiles)}, Enter = cancelar]: ', len(perfiles))
        return None if k is None else perfiles[k]

    def elegir_canonico(categoria, forma):
        """Forma canónica existente (la palabra será su variante) o una nueva de un perfil existente."""
        while True:
            existentes = opciones_canonico(tabla, categoria)
            escribir(f'  2) ¿De qué forma canónica de {categoria} es variante «{forma}»?')
            for i, c in enumerate(existentes, 1):
                p = tabla.perfil_de(categoria, c)
                escribir(f'    {i:>2}) {c:<12} {_ver_rasgos(tabla.rasgos_de(categoria, c))} (perfil {p}: '
                         f'{PERFILES[categoria][p]["desc"]})')
            escribir('     c) crear una forma canónica nueva')
            r = leer(f'  Forma canónica [{"1-" + str(len(existentes)) + ", " if existentes else ""}c, Enter = cancelar]: ')
            if not r:
                return None
            if r.isdigit() and 1 <= int(r) <= len(existentes):
                return existentes[int(r) - 1]
            if r.lower() != 'c':
                escribir('  opción inválida')
                continue
            sugerido = normalizar_canonico(forma) or ''
            nombre = leer(f'  Nombre de la forma canónica nueva [Enter = {sugerido}]: ')
            if nombre is None:
                return None
            nombre = nombre or sugerido
            canon = normalizar_canonico(nombre)
            if canon is None:
                escribir('  nombre inválido: debe empezar con letra; letras, dígitos y «_»')
                continue
            if canon in existentes:                  # duplicado dentro de la categoría: se ofrece usar la existente
                escribir(f'  {categoria}/{canon} ya existe: elegila de la lista como variante')
                continue
            p = elegir_perfil(categoria)
            if p is None:
                return None
            canon, motivo = tabla.alta_canonico(categoria, nombre, p)
            if canon is None:
                escribir(f'  no se pudo crear: {motivo}')
                continue
            escribir(f'  ✔ forma canónica nueva {categoria}/{canon} (perfil {p}, rasgos {_ver_rasgos(tabla.rasgos_de(categoria, canon))})')
            return canon

    def insertar(tk, c, sid, turno):
        categoria = elegir_categoria(tk.norm)
        if categoria is None:
            return None
        canonico = elegir_canonico(categoria, tk.norm)
        if canonico is None:
            return None
        if not tabla.insertar(tk.norm, categoria, canonico):
            escribir(f'  «{tk.norm}» ya existe en la tabla: no se inserta')
            return None
        escribir(f'  ✔ «{tk.norm}» → {categoria} / {canonico} (rasgos {_ver_rasgos(tabla.rasgos_de(categoria, canonico))}) '
                 'guardada en la tabla de símbolos léxica')
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
        escribir('   n) insertar «' + tk.norm + '» en la tabla de símbolos léxica')
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
