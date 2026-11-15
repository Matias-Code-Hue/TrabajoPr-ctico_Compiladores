"""Tabla de símbolos léxica: PERSISTENTE y se ENRIQUECE con las respuestas del usuario.

Es UNA sola estructura, con el mismo formato en la precarga y en lo aprendido:

    {categoría: {forma canónica: {"rasgos": {...}, "formas": [formas superficiales]}}}

  precarga   vocabulario.json            escrita a mano; el programa nunca la modifica.
  aprendido  vocabulario_aprendido.json  mismo formato. Una forma canónica de la precarga aparece solo con "formas" (las
                                         variantes aprendidas heredan sus rasgos); una forma canónica NUEVA aparece con
                                         "rasgos" (copiados del perfil elegido en el menú) y "formas".

Vigente = precarga + aprendido. Cada cambio se guarda con UNA escritura atómica de vocabulario_aprendido.json, así que
el archivo nunca queda con una forma que apunte a una forma canónica sin rasgos.

Los rasgos no son libres: semantica.PERFILES es el catálogo cerrado de combinaciones válidas por categoría. Al cargar se
valida que los rasgos de cada forma canónica coincidan con un perfil; desde el menú no se escriben rasgos, se elige un
perfil y el programa copia sus rasgos.
Es distinta de la tabla de entidades (entidades.py), que guarda sesiones, participantes y tickets y no persiste.
"""
import json
import os
import re
import tempfile

from lexico import cargar_vocabulario, plegar
from semantica import PERFILES, errores_de_rasgos, perfil_de_rasgos

FUERA_DE_GRAMATICA = 'FUERA_DE_GRAMATICA'   # forma conocida sin función en la gramática: queda NO_INTERPRETADO


def _plegar(texto):
    return ''.join(plegar(c) for c in texto)


def normalizar_canonico(nombre):
    """Nombre de forma canónica: sin tildes (conserva Ñ), en mayúsculas, espacios y guiones como «_».
    Devuelve None si no es un nombre válido (debe empezar con letra; solo letras, dígitos y «_»)."""
    n = re.sub(r'[\s\-]+', '_', _plegar(nombre.strip())).upper()
    return n if re.fullmatch(r'[A-ZÑ][A-ZÑ0-9_]*', n) else None


def ruta_aprendido(precarga):
    """vocabulario.json -> vocabulario_aprendido.json (en la misma carpeta)."""
    base, _ = os.path.splitext(precarga)
    return base + '_aprendido.json'


def _leer_json(ruta, vacio):
    if not ruta or not os.path.exists(ruta):
        return vacio
    with open(ruta, encoding='utf-8-sig') as f:
        datos = json.load(f)
    if not isinstance(datos, dict):
        raise ValueError(f'{ruta}: se esperaba un objeto JSON')
    return datos


def _escribir_json(ruta, datos):
    """Escritura atómica: archivo temporal en la misma carpeta + os.replace (no queda a medias si se interrumpe)."""
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(ruta)), prefix='.tmp_', suffix='.json')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(datos, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write('\n')
        os.replace(tmp, ruta)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


class TablaSimbolosLexica:
    def __init__(self, precarga, aprendido=None):
        """precarga: ruta a vocabulario.json o un diccionario ya cargado (mismo formato).
        aprendido: ruta de persistencia (vocabulario_aprendido.json); con None la tabla vive solo en memoria (modo de
        pruebas, o el diccionario reducido del caso 08)."""
        self.precarga = cargar_vocabulario(precarga) if isinstance(precarga, str) else precarga
        errs = errores_de_rasgos(self.precarga)
        if errs:
            raise ValueError('vocabulario (precarga) inválido: ' + '; '.join(errs))
        self.ruta_aprendido = aprendido
        self.persistente = aprendido is not None
        self.insertadas, self.canonicos_nuevos = [], []      # cambios de esta ejecución
        self.bajas = []                                      # lo aprendido que pasó a la precarga (aviso al abrir)
        self.aprendido = _leer_json(aprendido, {}) if self.persistente else {}
        self._validar_aprendido()
        self._vigente = {}                                   # objeto vivo: lo usan el corrector y la semántica
        self._conciliar()
        self._reconstruir()

    # ------------------------------------------------------------------ estado en memoria
    def _validar_aprendido(self):
        errs = []
        for cat, canons in self.aprendido.items():
            if cat not in PERFILES or not isinstance(canons, dict):
                errs.append(f'categoría {cat} desconocida')
                continue
            for canon, e in canons.items():
                if not isinstance(e, dict) or not isinstance(e.get('formas', []), list):
                    errs.append(f'{cat}/{canon}: entrada mal formada')
                elif canon not in self.precarga.get(cat, {}) and (
                        not isinstance(e.get('rasgos'), dict) or perfil_de_rasgos(cat, e['rasgos']) is None):
                    errs.append(f'{cat}/{canon}: forma canónica nueva sin rasgos de un perfil existente')
        if errs:
            raise ValueError(f'{self.ruta_aprendido} inválido ({"; ".join(errs)}); se puede volver a la precarga '
                             'con --reiniciar-aprendido')

    def _reconstruir(self):
        """Vigente = precarga + aprendido. Se actualiza EN EL LUGAR: el mismo objeto sigue siendo válido."""
        self._vigente.clear()
        self._indice = {}                                    # forma plegada -> (categoría, canónico, origen)
        for cat, canons in self.precarga.items():
            self._vigente[cat] = {c: {'rasgos': dict(e['rasgos']), 'formas': list(e['formas'])} for c, e in canons.items()}
            for c, e in canons.items():
                for f in e['formas']:
                    self._indice[_plegar(f)] = (cat, c, 'PRECARGA')
        for cat, canons in self.aprendido.items():
            for c, e in canons.items():
                v = self._vigente.setdefault(cat, {}).setdefault(c, {'rasgos': dict(e.get('rasgos', {})), 'formas': []})
                for f in e.get('formas', []):
                    v['formas'].append(f)
                    self._indice.setdefault(f, (cat, c, 'APRENDIDA'))

    def _guardar(self):
        if self.persistente:
            _escribir_json(self.ruta_aprendido, self.aprendido)

    def _conciliar(self):
        """Si alguien agregó a la precarga algo que ya estaba aprendido, gana la precarga y lo aprendido se da de baja
        (si no, una forma o una forma canónica tendría dos entradas). Cada baja queda en self.bajas (main.py avisa)."""
        en_precarga = {_plegar(f): (cat, c) for cat, cs in self.precarga.items() for c, e in cs.items() for f in e['formas']}
        cambio = False
        for cat in list(self.aprendido):
            for canon in list(self.aprendido[cat]):
                e = self.aprendido[cat][canon]
                pre = self.precarga.get(cat, {}).get(canon)
                if pre is not None and 'rasgos' in e:        # la forma canónica pasó a la precarga
                    e.pop('rasgos')
                    self.bajas.append(f'{cat}/{canon} (forma canónica)')
                    cambio = True
                for f in [f for f in e.get('formas', []) if f in en_precarga]:   # la forma pasó a la precarga
                    e['formas'].remove(f)
                    self.bajas.append(f'«{f}» ({cat}/{canon})')
                    cambio = True
                if not e.get('formas') and 'rasgos' not in e:
                    del self.aprendido[cat][canon]
            if not self.aprendido[cat]:
                del self.aprendido[cat]
        if cambio:
            self._guardar()

    # ------------------------------------------------------------------ consultas
    def buscar(self, forma):
        """-> (categoría, canónico, origen) | None ; origen ∈ {PRECARGA, APRENDIDA}."""
        return self._indice.get(_plegar(forma))

    def canonicos(self, categoria):
        """Formas canónicas existentes de una categoría (precarga y aprendidas), en orden."""
        return sorted(self._vigente.get(categoria, {}))

    def rasgos_de(self, categoria, canonico):
        return self._vigente[categoria][canonico]['rasgos']

    def perfil_de(self, categoria, canonico):
        """Perfil de semantica.PERFILES cuyos rasgos coinciden con los de la forma canónica."""
        return perfil_de_rasgos(categoria, self.rasgos_de(categoria, canonico))

    def vocabulario(self):
        """Tabla vigente, con el formato de vocabulario.json. Es un objeto VIVO: las altas e inserciones de esta
        ejecución se reflejan en él, así que valen para el resto de la misma entrada (corrector y semántica)."""
        return self._vigente

    # ------------------------------------------------------------------ altas
    def alta_canonico(self, categoria, nombre, perfil):
        """Crea una forma canónica nueva con los rasgos de un perfil EXISTENTE de la categoría.
        Devuelve (canónico normalizado, None) o (None, motivo del rechazo)."""
        canon = normalizar_canonico(nombre)
        if canon is None:
            return None, 'nombre inválido (debe empezar con letra; letras, dígitos y «_»)'
        if categoria not in PERFILES or perfil not in PERFILES[categoria]:
            return None, f'el perfil {perfil} no existe para {categoria}'
        if canon in self._vigente.get(categoria, {}):
            return None, f'{categoria}/{canon} ya existe: elegila como forma canónica de la que la palabra es variante'
        rasgos = dict(PERFILES[categoria][perfil]['rasgos'])
        self.aprendido.setdefault(categoria, {})[canon] = {'rasgos': rasgos, 'formas': []}
        self._vigente.setdefault(categoria, {})[canon] = {'rasgos': dict(rasgos), 'formas': []}
        self.canonicos_nuevos.append(f'{categoria}/{canon}')
        self._guardar()
        return canon, None

    def insertar(self, forma, categoria, canonico):
        """Incorpora una forma superficial como variante de una forma canónica existente (hereda sus rasgos).
        Control de duplicados: devuelve False si la forma ya tiene entrada o si la forma canónica no existe."""
        forma = _plegar(forma.strip())
        if not forma or forma in self._indice or canonico not in self._vigente.get(categoria, {}):
            return False
        self.aprendido.setdefault(categoria, {}).setdefault(canonico, {}).setdefault('formas', []).append(forma)
        self._vigente[categoria][canonico]['formas'].append(forma)
        self._indice[forma] = (categoria, canonico, 'APRENDIDA')
        self.insertadas.append(forma)
        self._guardar()
        return True

    # ------------------------------------------------------------------ reinicio
    def _contar(self):
        formas = sum(len(e.get('formas', [])) for cs in self.aprendido.values() for e in cs.values())
        canon = sum('rasgos' in e for cs in self.aprendido.values() for e in cs.values())
        return formas, canon

    def reiniciar(self):
        """Vuelve a la precarga: borra lo aprendido (formas y formas canónicas). Devuelve (formas, canónicos) quitados."""
        n_formas, n_canon = self._contar()
        if self.ruta_aprendido and os.path.exists(self.ruta_aprendido):
            os.remove(self.ruta_aprendido)
        self.aprendido = {}
        self._reconstruir()
        return n_formas, n_canon

    # ------------------------------------------------------------------ vista para la CLI (main.py --tabla)
    def mostrar(self, inicial=False, categoria=None):
        """Texto de la tabla, una fila por forma canónica: categoría, forma canónica, perfil, rasgos y formas.
        inicial=True: solo la precarga (vocabulario.json). Si no, la tabla vigente (precarga + aprendido), con «+» en
        las formas y formas canónicas aprendidas. categoria: mostrar solo esa categoría."""
        datos = self.precarga if inicial else self._vigente
        if categoria is not None and categoria not in datos:
            return f'La categoría {categoria} no existe. Categorías: {", ".join(datos)}'
        filas = []
        for cat, canons in datos.items():
            if categoria not in (None, cat):
                continue
            pre = self.precarga.get(cat, {})
            for canon, e in canons.items():
                nuevo = not inicial and canon not in pre
                formas = [f if inicial or f in [_plegar(x) for x in pre.get(canon, {}).get('formas', [])] else f'+{f}'
                          for f in e['formas']]
                filas.append((cat, ('+' if nuevo else '') + canon, perfil_de_rasgos(cat, e['rasgos']) or '¿?',
                              json.dumps(e['rasgos'], ensure_ascii=False) if e['rasgos'] else '—',
                              ', '.join(formas) or '(sin formas)'))
        cab = ('categoría', 'forma canónica', 'perfil', 'rasgos', 'formas superficiales')
        anchos = [max(len(x[i]) for x in filas + [cab]) for i in range(4)]
        linea = lambda x: '  '.join(v.ljust(anchos[i]) if i < 4 else v for i, v in enumerate(x)).rstrip()
        L = [linea(cab), '  '.join('─' * a for a in anchos) + '  ' + '─' * 20]
        anterior = None
        for x in filas:
            L.append(linea((x[0] if x[0] != anterior else '',) + x[1:]))
            anterior = x[0]
        n_can = len(filas)
        n_formas = sum(len(e['formas']) for cat, cs in datos.items() if categoria in (None, cat) for e in cs.values())
        n = lambda k, sing, plur: f'{k} {sing if k == 1 else plur}'
        if inicial:
            L += ['', f'{n(n_can, "forma canónica", "formas canónicas")} y '
                      f'{n(n_formas, "forma superficial", "formas superficiales")} en la precarga.']
        else:
            n_ap = sum(f.startswith('+') for x in filas for f in x[4].split(', '))
            n_nuevos = sum(x[1].startswith('+') for x in filas)
            L += ['', f'{n(n_can, "forma canónica", "formas canónicas")} ({n(n_nuevos, "aprendida", "aprendidas")}) y '
                      f'{n(n_formas, "forma superficial", "formas superficiales")} ({n(n_ap, "aprendida", "aprendidas")}). '
                      '«+» = aprendido.']
        return '\n'.join(L)

    def resumen(self):
        n_pre = sum(1 for *_, o in self._indice.values() if o == 'PRECARGA')
        n_formas, n_canon = self._contar()
        return {'precarga': n_pre, 'aprendidas': n_formas, 'canonicos_aprendidos': n_canon,
                'insertadas_en_esta_ejecucion': list(self.insertadas),
                'canonicos_nuevos_en_esta_ejecucion': list(self.canonicos_nuevos)}
