"""Exporta las gramáticas a LaTeX con la notación de clase: A → α | β, sin < >.

Convención (para distinguir variables de terminales sin los < >):
  variables  en cursiva          \\nt{pred\\_s}   →  pred_s
  terminales en máquina de escribir \\tm{V\\_EST}  →  V_EST
  vacío      \\varepsilon

Escribe en latex/:
  gramaticas.tex        gramática de formato y lingüística: base (F0, L0) y final LL(1) (F1, L3)
  prim_sgte.tex         tabla PRIM / SGTE de la gramática final
  tabla_m.csv           tabla predictiva M[A, a] (para abrir en una planilla)
  afd/*.tex             copia de los AFD en TikZ (los genera grafos_afd.py en figuras/)
  ejemplo.tex           documento completo que incluye todo lo anterior y los AFD

Uso:  python3 gramatica_latex.py            (luego compilar latex/ejemplo.tex, p. ej. en Overleaf)
      python3 gramatica_latex.py --texto    (imprime la gramática final en texto plano con →)
"""
import csv
import os
import shutil
import sys

import derivacion as dv
import gramatica as gr

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'latex')
MAX_ALTS_POR_LINEA = 3

MACROS = r"""\newcommand{\nt}[1]{\mathit{#1}}     % variable (no terminal)
\newcommand{\tm}[1]{\mathtt{#1}}     % terminal (categoría del léxico)
"""


def esc(s):
    return s.replace('_', r'\_').replace('$', r'\$')


def sim(s, G):
    if s in G:
        return r'\nt{' + esc(s) + '}'
    return r'\tm{' + esc(s) + '}'


def alt_tex(alt, G):
    return r'\varepsilon' if not alt else r'\;'.join(sim(s, G) for s in alt)


def gramatica_tex(G, orden=None):
    """Arreglo de tres columnas: A & → & α | β ... (corta las variables con muchas alternativas)."""
    filas = []
    for A in orden or G:
        alts = [alt_tex(a, G) for a in G[A]]
        trozos = [alts[i:i + MAX_ALTS_POR_LINEA] for i in range(0, len(alts), MAX_ALTS_POR_LINEA)]
        for k, t in enumerate(trozos):
            izq = sim(A, G) if k == 0 else ''
            flecha = r'\to' if k == 0 else r'\mid'
            filas.append(f'  {izq} & {flecha} & ' + r' \mid '.join(t) + r' \\')
    return '\\[\n\\begin{array}{rcl}\n' + '\n'.join(filas) + '\n\\end{array}\n\\]\n'


def texto_plano(G, orden=None):
    ancho = max(len(A) for A in (orden or G))
    lin = []
    for A in orden or G:
        alts = [' '.join(a) if a else 'ε' for a in G[A]]
        lin.append(f'{A:<{ancho}} → ' + ' | '.join(alts))
    return '\n'.join(lin)


def conj(c):
    return r'\{' + ', '.join(r'\varepsilon' if x == gr.EPS else r'\tm{' + esc(x) + '}' for x in sorted(c)) + r'\}'


def main():
    os.makedirs(DIR, exist_ok=True)
    form_final = {a: gr.G[a] for a in dv.FORM}
    if '--texto' in sys.argv:
        print(texto_plano(gr.G))
        return
    partes = [
        ('Gramática de formato base (F0)', dv.F0, None),
        ('Gramática lingüística base (L0)', dv.L0, None),
        ('Gramática de formato final LL(1) (F1)', dict(form_final, texto=gr.G['texto']), dv.FORM),
        ('Gramática lingüística final LL(1) (L3)', gr.G, dv.LING),
    ]
    with open(os.path.join(DIR, 'gramaticas.tex'), 'w', encoding='utf-8') as f:
        f.write('% Generado por gramatica_latex.py. Requiere las macros \\nt y \\tm (ver ejemplo.tex).\n')
        for titulo, G, orden in partes:
            # en F0 «texto» no está definida: se la marca como variable igual
            Gx = dict(G)
            for alts in G.values():
                for a in alts:
                    for s in a:
                        if s == 'texto':
                            Gx.setdefault('texto', [])
            f.write(f'\n\\paragraph{{{titulo}}}\n')
            f.write(gramatica_tex(Gx, list(orden or G)))
    P = gr.primero()
    S = gr.siguiente(P)
    with open(os.path.join(DIR, 'prim_sgte.tex'), 'w', encoding='utf-8') as f:
        f.write('% Generado por gramatica_latex.py (requiere \\usepackage{longtable})\n')
        f.write('\\begin{longtable}{>{$}l<{$} >{\\raggedright\\arraybackslash$}p{6.2cm}<{$} '
                '>{\\raggedright\\arraybackslash$}p{6.2cm}<{$}}\n')
        f.write('\\textbf{Variable} & \\textbf{PRIM} & \\textbf{SGTE} \\\\ \\hline\n\\endhead\n')
        for A in gr.G:
            f.write(f'\\nt{{{esc(A)}}} & {conj(P[A])} & {conj(S[A])} \\\\\n')
        f.write('\\end{longtable}\n')
    M = gr.tabla_ll1(P, S)
    terms = sorted({a for _, a in M})
    with open(os.path.join(DIR, 'tabla_m.csv'), 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['M[A,a]'] + terms)
        for A in gr.G:
            fila = [A]
            for a in terms:
                if (A, a) in M:
                    _, k = M[(A, a)]
                    alt = gr.G[A][k]
                    fila.append(f'{A} → ' + (' '.join(alt) if alt else 'ε'))
                else:
                    fila.append('')
            w.writerow(fila)
    origen = os.path.join(os.path.dirname(DIR), 'figuras')          # los genera grafos_afd.py
    os.makedirs(os.path.join(DIR, 'afd'), exist_ok=True)
    figuras = sorted(x[:-4] for x in os.listdir(origen) if x.endswith('.tex')) if os.path.isdir(origen) else []
    orden = ['afn_ticket', 'afd_ticket', 'afd_ticket_ticketmal', 'afd_ticket_palabra', 'afd_id_sesion', 'afd_num',
             'afd_num_min']
    figuras.sort(key=lambda x: (orden.index(x) if x in orden else len(orden), x))
    for fig in figuras:
        shutil.copyfile(os.path.join(origen, fig + '.tex'), os.path.join(DIR, 'afd', fig + '.tex'))
    with open(os.path.join(DIR, 'ejemplo.tex'), 'w', encoding='utf-8') as f:
        f.write(r"""\documentclass[11pt]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[spanish,es-noshorthands]{babel}
\usepackage[margin=2cm]{geometry}
\usepackage{amsmath,array,longtable,graphicx}
\usepackage{tikz}
\usetikzlibrary{automata,positioning,arrows.meta,babel}
""" + MACROS + r"""
\begin{document}
\section*{Gramáticas}
Las variables van en cursiva y los terminales (categorías del analizador léxico) en letra de máquina de escribir.
\input{gramaticas.tex}

\section*{PRIM y SGTE de la gramática final}
{\small \input{prim_sgte.tex}}

\section*{Autómatas del analizador léxico}
""")
        for fig in figuras:
            with open(os.path.join(origen, fig + '.tex'), encoding='utf-8') as g:
                primera = g.readline()
            tit = primera[len('% titulo: '):].strip() if primera.startswith('% titulo: ') else fig
            f.write(f'\\subsection*{{{esc(tit).replace("{", chr(92) + "{").replace("}", chr(92) + "}")}}}\n\\begin{{center}}\\resizebox{{\\linewidth}}{{!}}{{\\input{{afd/{fig}.tex}}}}\\end{{center}}\n\n')
        f.write('\\end{document}\n')
    print(f'Escrito en {DIR}: gramaticas.tex, prim_sgte.tex, tabla_m.csv, ejemplo.tex ({len(figuras)} autómatas)')


if __name__ == '__main__':
    main()
