"""Grafos de los autómatas del léxico (para el informe).

Construye los autómatas con el MISMO código del analizador (lexico.thompson y lexico.construir), así que lo que se
dibuja es lo que usa el programa. Por cada autómata escribe en figuras/:

  <nombre>.dot   Graphviz   (dot -Tpng figuras/afd_ticket.dot -o afd_ticket.png, o pegarlo en un visor web de Graphviz)
  <nombre>.tex   TikZ       (\\usetikzlibrary{automata,positioning}; \\input{figuras/afd_ticket.tex})
  <nombre>.png   imagen     (solo si está instalado matplotlib: pip install matplotlib)

Uso:  python3 grafos_afd.py            # todos los autómatas
      python3 grafos_afd.py --tablas   # además imprime tablas de transiciones y subconjuntos
"""
import os
import sys

import lexico as L

SALIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'figuras')
EPS_TXT = 'ε'


# ---------------------------------------------------------------- autómatas a dibujar
def patrones(*cats):
    extra = {'PALABRA': ('PALABRA', None, L.mas(L.LETRA))}
    return [p for c in cats for p in L.ESTRUCTURA if p[0] == c] + [extra[c] for c in cats if c in extra]


def afn_de(pats):
    """AFN de Thompson igual al que arma lexico.construir(): estado inicial 0 con ε a cada patrón."""
    afn = L.AFN()
    inicio = afn.nuevo()
    finales = {}
    for c, _, er in pats:
        i, f = L.thompson(afn, er)
        afn.arista(inicio, L.EPS, i)
        finales[f] = c
    aristas = [(s, a, t) for (s, a), ts in afn.mov.items() for t in ts]
    return list(range(afn.n)), aristas, inicio, finales


def afd_de(pats, minimo=False):
    afd = L.construir(pats)
    estados = sorted({0} | {e for e, _ in afd.trans} | set(afd.trans.values()))
    aristas = [(s, a, t) for (s, a), t in afd.trans.items()]
    finales = {e: afd.finales[e][0] for e in afd.finales}
    if minimo:
        estados, aristas, finales = minimizar(estados, aristas, 0, finales)
    return estados, aristas, 0, finales, afd


def minimizar(estados, aristas, inicio, finales):
    """Minimización por particiones (Clase 5): se separan los finales por token y se refinan los grupos
    hasta que todos los estados de un grupo van a los mismos grupos con cada símbolo."""
    delta = {(s, a): t for s, a, t in aristas}
    simbolos = sorted({a for _, a, _ in aristas})
    grupo = {e: finales.get(e, '') for e in estados}
    while True:
        firma = {e: (grupo[e],) + tuple(grupo.get(delta.get((e, a))) for a in simbolos) for e in estados}
        ids = {f: i for i, f in enumerate(sorted(set(firma.values()), key=str))}
        nuevo = {e: ids[firma[e]] for e in estados}
        if len(set(nuevo.values())) == len(set(grupo.values())):
            break
        grupo = nuevo
    rep = {}
    for e in estados:
        rep.setdefault(grupo[e], e)
    aristas2 = sorted({(rep[grupo[s]], a, rep[grupo[t]]) for s, a, t in aristas})
    finales2 = {rep[grupo[e]]: c for e, c in finales.items()}
    return sorted(set(rep.values())), aristas2, finales2


# ---------------------------------------------------------------- etiquetas y numeración
def etiqueta(simbolos):
    """Agrupa símbolos del alfabeto Σ: D = dígito, letra = [a-zñ]."""
    s = set(simbolos)
    partes = []
    if None in s:
        partes.append(EPS_TXT)
        s.discard(None)
    letras = s & L.LETRAS
    if letras == L.LETRAS:
        partes.append('letra')
    elif len(letras) > len(L.LETRAS) // 2:
        partes.append('letra − {' + ','.join(sorted(L.LETRAS - letras)) + '}')
    else:
        partes += sorted(letras)
    for x in sorted(s - L.LETRAS):
        partes.append({'Q': '¿?¡!'}.get(x, x))
    return ', '.join(partes)


def capas(estados, aristas, inicio):
    """Capa = camino más largo desde el inicio sin contar las aristas de retroceso (ciclos)."""
    suc = {}
    for s, _, t in aristas:
        suc.setdefault(s, []).append(t)
    orden, marca, atras = [], {}, set()

    def dfs(u):
        marca[u] = 1
        for v in sorted(set(suc.get(u, []))):
            if marca.get(v) == 1:
                atras.add((u, v))
            elif v not in marca:
                dfs(v)
        marca[u] = 2
        orden.append(u)

    sys.setrecursionlimit(10000)
    dfs(inicio)
    for e in estados:
        if e not in marca:
            dfs(e)
    capa = {e: 0 for e in estados}
    for u in reversed(orden):
        for v in suc.get(u, []):
            if (u, v) not in atras and u != v:
                capa[v] = max(capa[v], capa[u] + 1)
    return capa, orden[::-1]


def preparar(estados, aristas, inicio, finales, prefijo):
    capa, orden = capas(estados, aristas, inicio)
    pos_orden = {e: i for i, e in enumerate(orden)}
    numerados = sorted(estados, key=lambda e: (capa[e], pos_orden.get(e, 0)))
    nombre = {e: f'{prefijo}{i}' for i, e in enumerate(numerados)}
    agrup = {}
    for s, a, t in aristas:
        agrup.setdefault((s, t), []).append(a)
    arcos = [(s, t, etiqueta(v)) for (s, t), v in sorted(agrup.items(), key=lambda x: (nombre[x[0][0]], nombre[x[0][1]]))]
    return dict(estados=numerados, nombre=nombre, capa=capa, arcos=arcos, inicio=inicio, finales=finales)


# ---------------------------------------------------------------- salidas
def a_dot(g, titulo):
    n = g['nombre']
    lin = [f'digraph "{titulo}" {{', '  rankdir=LR; node [shape=circle, fontname="Helvetica"];',
           '  edge [fontname="Helvetica"]; __ini [shape=point, label=""];']
    for e in g['estados']:
        forma = 'doublecircle' if e in g['finales'] else 'circle'
        extra = f', xlabel="{g["finales"][e]}"' if e in g['finales'] else ''
        lin.append(f'  {n[e]} [shape={forma}{extra}];')
    lin.append(f'  __ini -> {n[g["inicio"]]};')
    for s, t, et in g['arcos']:
        lin.append(f'  {n[s]} -> {n[t]} [label="{et}"];')
    lin.append('}')
    return '\n'.join(lin) + '\n'


def a_tikz(g, titulo):
    """Misma disposición que el PNG (posiciones()); arcos rectos entre capas vecinas y curvos en los saltos."""
    n = g['nombre']
    tex = lambda x: x.replace('_', r'\_').replace('ε', r'$\varepsilon$').replace('−', '$-$').replace(
        '{', r'\{').replace('}', r'\}').replace('¿?¡!', r'?`?!`!').replace('ñ', r'\~n')
    esc = 1.9
    pos, cadena = posiciones(g, esc)
    lin = [f'% titulo: {titulo}',
           r'% requiere \usetikzlibrary{automata,positioning,arrows.meta}',
           r'\begin{tikzpicture}[shorten >=1pt, auto, >={Stealth[round]},',
           r'                    every state/.style={minimum size=8mm, inner sep=1pt}]']
    for e in g['estados']:
        x, y = pos[e]
        opts = ['state'] + (['initial'] if e == g['inicio'] else []) + (['accepting'] if e in g['finales'] else [])
        lin.append(f'  \\node[{",".join(opts)}] ({n[e]}) at ({x:.2f},{y:.2f}) {{${n[e][0]}_{{{n[e][1:]}}}$}};')
    lin.append(r'  \path[->]')
    for s, t, et in g['arcos']:
        (x1, y1), (x2, y2) = pos[s], pos[t]
        if s == t:
            como = 'loop above'
        elif y2 < y1 - 1.0 and x2 < x1 and s in cadena and t in cadena:      # salto de fila
            como = 'out=-90, in=90'
        elif abs(y2 - y1) > 0.01 or abs(x2 - x1) <= esc * 1.01:
            como = ''
        else:
            ang = min(50, 20 + 4 * round(abs(x2 - x1) / esc))
            como = f'bend {"right" if s not in cadena else "left"}={ang}'
        estilo = ', dashed' if et == EPS_TXT else ''
        lin.append(f'    ({n[s]}) edge[{como}{estilo}] node{{\\scriptsize {tex(et)}}} ({n[t]})')
    lin.append('  ;')
    lin.append(r'\end{tikzpicture}')
    return '\n'.join(lin) + '\n'


def posiciones(g, ancho_capa, max_por_fila=14, sep_filas=3.4):
    """Cadena principal (camino más largo desde el inicio) en una fila; el resto de cada capa, debajo.
    Si hay muchas capas, la cadena se parte en dos filas."""
    capa = g['capa']
    pred = {}
    for s, t, _ in g['arcos']:
        if s != t and capa[t] == capa[s] + 1:
            pred.setdefault(t, []).append(s)
    ultimo = max(g['estados'], key=lambda e: (capa[e], -g['estados'].index(e)))
    cadena = [ultimo]
    while cadena[-1] != g['inicio'] and pred.get(cadena[-1]):
        cadena.append(sorted(pred[cadena[-1]], key=g['estados'].index)[0])
    cadena = set(cadena)
    ncapas = max(capa.values()) + 1
    por_fila = ncapas if ncapas <= max_por_fila else -(-ncapas // 2)
    pos, abajo = {}, {}
    for e in g['estados']:
        c = capa[e]
        fila, col = divmod(c, por_fila)
        y0 = -fila * sep_filas
        if e in cadena:
            pos[e] = (col * ancho_capa, y0)
        else:
            abajo[c] = abajo.get(c, 0) + 1
            pos[e] = (col * ancho_capa, y0 - 1.7 * abajo[c])
    return pos, cadena


def a_png(g, titulo, ruta):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib.patches import Circle, FancyArrowPatch
    except ImportError:
        return False
    r = 0.32
    ancho_capa = 1.25 if len(g['estados']) > 20 else 2.0
    pos, cadena = posiciones(g, ancho_capa)
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    ymin, ymax = min(ys) - 1.0, max(ys) + 0.9
    fig, ax = plt.subplots(figsize=(max(4.0, (max(xs) - min(xs) + 2.2) * 0.8), 3), dpi=170)
    ax.set_aspect('equal')
    ax.axis('off')
    caja = dict(fc='white', ec='none', pad=0.6)
    circ = {}
    for e, (x, y) in pos.items():
        c = Circle((x, y), r, fc='white', ec='black', lw=1.3, zorder=3)
        ax.add_patch(c)
        circ[e] = c
        if e in g['finales']:
            ax.add_patch(Circle((x, y), r * 0.8, fc='none', ec='black', lw=1.1, zorder=4))
            ax.text(x, y - r - 0.12, g['finales'][e], ha='center', va='top', fontsize=6.5, color='#1f5fa8', zorder=5)
        nom = g['nombre'][e]
        ax.text(x, y, f'${nom[0]}_{{{nom[1:]}}}$', ha='center', va='center', fontsize=10, zorder=5)
    x0, y0 = pos[g['inicio']]
    ax.add_patch(FancyArrowPatch((x0 - r - 0.6, y0), (x0 - r, y0), arrowstyle='-|>', mutation_scale=11, lw=1.2))
    ax.text(x0 - r - 0.65, y0 + 0.1, 'inicio', fontsize=7, ha='left', va='bottom')
    for s, t, et in g['arcos']:
        (x1, y1), (x2, y2) = pos[s], pos[t]
        estilo = dict(arrowstyle='-|>', mutation_scale=10, lw=1.0, zorder=2, linestyle='--' if et == EPS_TXT else '-')
        if s == t:
            ax.add_patch(FancyArrowPatch((x1 - 0.17, y1 + r * 0.85), (x1 + 0.17, y1 + r * 0.85),
                                         connectionstyle='arc3,rad=-2.6', **estilo))
            ax.text(x1, y1 + r + 0.5, et, ha='center', va='bottom', fontsize=8, bbox=caja, zorder=6)
            ymax = max(ymax, y1 + r + 0.9)
            continue
        if y2 < y1 - 1.0 and x2 < x1 and s in cadena and t in cadena:      # salto de fila de la cadena
            ym = (y1 + y2) / 2 + 0.2
            ls = '--' if et == EPS_TXT else '-'
            ax.plot([x1, x1, x2, x2], [y1 - r, ym, ym, y2 + r + 0.25], color='black', lw=1.0, ls=ls, zorder=2)
            ax.add_patch(FancyArrowPatch((x2, y2 + r + 0.3), (x2, y2 + r), **estilo))
            ax.text((x1 + x2) / 2, ym, et, ha='center', va='center', fontsize=8, bbox=caja, zorder=6)
            continue
        dist = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        recto = abs(y2 - y1) > 0.01 or abs(x2 - x1) <= ancho_capa * 1.01
        if recto:
            rad = 0.0
        else:
            h = 0.4 + 0.07 * round(abs(x2 - x1) / ancho_capa)
            rad = -2 * h / dist if x2 > x1 else 2 * h / dist
            if s not in cadena:                     # fila de abajo: el arco va hacia abajo
                rad = -rad
            ymax, ymin = max(ymax, y1 + h + 0.3), min(ymin, y1 - h - 0.3)
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), patchA=circ[s], patchB=circ[t],
                                     connectionstyle=f'arc3,rad={rad}', **estilo))
        if rad:
            dx, dy = x2 - x1, y2 - y1
            lx, ly = (x1 + x2) / 2 + 0.5 * rad * dy, (y1 + y2) / 2 - 0.5 * rad * dx
        elif abs(y2 - y1) > 0.01:
            lx, ly = x1 + 0.42 * (x2 - x1), y1 + 0.42 * (y2 - y1)
        else:
            lx, ly = (x1 + x2) / 2, y1 + 0.16
        ax.text(lx, ly, et, ha='center', va='center', fontsize=8, bbox=caja, zorder=6)
    ax.set_xlim(min(xs) - 1.1, max(xs) + 0.8)
    ax.set_ylim(ymin, ymax)
    ax.set_title(titulo, fontsize=10)
    fig.set_size_inches(fig.get_size_inches()[0], max(1.8, (ymax - ymin) * 0.8 * fig.get_size_inches()[0]
                                                         / ((max(xs) - min(xs) + 1.9) * 0.8)))
    fig.savefig(ruta, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    return True


# ---------------------------------------------------------------- catálogo
def automatas():
    pats_t = patrones('TICKET')
    est, ar, ini, fin = afn_de(pats_t)
    yield 'afn_ticket', 'AFN de Thompson de TICKET = tk- D{3,6}', preparar(est, ar, ini, fin, 'n'), None
    for nombre, titulo, cats, minimo in [
        ('afd_ticket', 'AFD de TICKET (subconjuntos; ya mínimo)', ('TICKET',), False),
        ('afd_ticket_ticketmal', 'AFD combinado TICKET | TICKET_MAL (prioridad en q6-q9)', ('TICKET', 'TICKET_MAL'), False),
        ('afd_ticket_palabra', 'AFD combinado TICKET | TICKET_MAL | PALABRA (lexema más largo)',
         ('TICKET', 'TICKET_MAL', 'PALABRA'), False),
        ('afd_id_sesion', 'AFD de ID_SESION = s D D', ('ID_SESION',), False),
        ('afd_num', 'AFD de NUM = D+ (subconjuntos)', ('NUM',), False),
        ('afd_num_min', 'AFD mínimo de NUM = D+', ('NUM',), True),
    ]:
        est, ar, ini, fin, afd = afd_de(patrones(*cats), minimo)
        yield nombre, titulo, preparar(est, ar, ini, fin, 'q'), (afd, patrones(*cats))


def tabla(g):
    simb = []
    for _, _, et in g['arcos']:
        for x in et.split(', '):
            if x not in simb:
                simb.append(x)
    filas = ['| Estado | ' + ' | '.join(simb) + ' | Final |', '|' + '---|' * (len(simb) + 2)]
    for e in g['estados']:
        celdas = []
        for x in simb:
            dst = [g['nombre'][t] for s, t, et in g['arcos'] if s == e and x in et.split(', ')]
            celdas.append(','.join(dst) or '–')
        filas.append(f'| {g["nombre"][e]} | ' + ' | '.join(celdas) + f' | {g["finales"].get(e, "")} |')
    return '\n'.join(filas)


def main():
    os.makedirs(SALIDA, exist_ok=True)
    con_png = True
    afn_nombres = None
    for nombre, titulo, g, extra in automatas():
        if nombre == 'afn_ticket':
            afn_nombres = g['nombre']
        with open(os.path.join(SALIDA, nombre + '.dot'), 'w', encoding='utf-8') as f:
            f.write(a_dot(g, titulo))
        with open(os.path.join(SALIDA, nombre + '.tex'), 'w', encoding='utf-8') as f:
            f.write(a_tikz(g, titulo))
        if con_png:
            con_png = a_png(g, titulo, os.path.join(SALIDA, nombre + '.png'))
        print(f'{nombre}: {len(g["estados"])} estados, {len(g["arcos"])} arcos')
        if '--tablas' in sys.argv:
            print(tabla(g))
            if nombre == 'afd_ticket' and extra:
                afd = extra[0]
                print('Subconjuntos (estados del AFN de afn_ticket):')
                for e in g['estados']:
                    S = sorted(afd.subconj[e], key=lambda s: int(afn_nombres[s][1:]))
                    print(f'  {g["nombre"][e]} = {{{", ".join(afn_nombres[s] for s in S)}}}')
            print()
    print(f'Archivos en {SALIDA}' + ('' if con_png else '  (sin PNG: falta matplotlib)'))


if __name__ == '__main__':
    main()
