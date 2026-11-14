"""Tabla de símbolos léxica: forma -> token (categoría) y forma canónica. PERSISTENTE y se ENRIQUECE.

Persistencia en tres archivos JSON (sin base de datos, solo biblioteca estándar):

  vocabulario.json                  PRECARGA manual. El programa nunca lo escribe.
  vocabulario_aprendido.json        formas que el usuario incorporó, con fecha y origen (archivo, sesión, turno).
  vocabulario_auditoria.jsonl       registro de AUDITORÍA: una línea JSON por cada cambio de la tabla.
                                    Solo se agregan líneas; nunca se modifican ni se borran.

La tabla vigente es precarga ∪ aprendido. Una forma no puede tener dos entradas (control de duplicados).
Las correcciones de una sola aparición (elegir el candidato de Levenshtein) NO cambian la tabla y no se auditan.

Es distinta de la tabla de entidades (entidades.py): esta guarda el lenguaje y persiste entre ejecuciones;
aquella guarda sesiones, participantes y tickets de cada conversación y se descarta al terminar.
"""
import getpass
import json
import os
import tempfile
from datetime import datetime

from lexico import cargar_vocabulario, plegar

FUERA_DE_GRAMATICA = 'FUERA_DE_GRAMATICA'   # forma conocida sin función en la gramática: queda NO_INTERPRETADO


def _plegar(forma):
    return ''.join(plegar(c) for c in forma)


def _ahora():
    return datetime.now().isoformat(timespec='seconds')


def _operador():
    try:
        return os.environ.get('TP1_OPERADOR') or getpass.getuser()
    except Exception:                                # sin usuario del sistema identificable
        return 'desconocido'


def rutas_por_defecto(precarga):
    """vocabulario.json -> vocabulario_aprendido.json y vocabulario_auditoria.jsonl, en la misma carpeta."""
    base, _ = os.path.splitext(precarga)
    return base + '_aprendido.json', base + '_auditoria.jsonl'


class TablaSimbolosLexica:
    def __init__(self, precarga, aprendido=None, auditoria=None):
        """precarga: ruta a vocabulario.json o un diccionario ya cargado.
        aprendido / auditoria: rutas de persistencia; con None la tabla vive solo en memoria (p. ej. el caso 08)."""
        self.precarga = cargar_vocabulario(precarga) if isinstance(precarga, str) else precarga
        self.ruta_aprendido, self.ruta_auditoria = aprendido, auditoria
        self.persistente = aprendido is not None
        self.insertadas = []                         # formas incorporadas en esta ejecución
        self._indice = {}                            # forma plegada -> (categoría, canónico, origen)
        for cat, canons in self.precarga.items():
            for canon, formas in canons.items():
                for f in formas:
                    self._indice[_plegar(f)] = (cat, canon, 'PRECARGA')
        self.aprendido = self._leer_aprendido()
        self._conciliar()
        for forma, e in self.aprendido.items():
            self._indice[forma] = (e['categoria'], e['canonico'], 'APRENDIDA')

    # ------------------------------------------------------------------ persistencia
    def _leer_aprendido(self):
        if not self.persistente or not os.path.exists(self.ruta_aprendido):
            return {}
        with open(self.ruta_aprendido, encoding='utf-8-sig') as f:
            datos = json.load(f)
        if not isinstance(datos, dict):
            raise ValueError(f'{self.ruta_aprendido}: se esperaba un objeto JSON {{forma: entrada}}')
        return datos

    def _guardar_aprendido(self):
        """Escritura atómica: archivo temporal en la misma carpeta + os.replace (no queda a medias si se interrumpe)."""
        carpeta = os.path.dirname(os.path.abspath(self.ruta_aprendido))
        fd, tmp = tempfile.mkstemp(dir=carpeta, prefix='.aprendido_', suffix='.json')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(self.aprendido, f, ensure_ascii=False, indent=2, sort_keys=True)
                f.write('\n')
            os.replace(tmp, self.ruta_aprendido)
        except BaseException:
            if os.path.exists(tmp):
                os.remove(tmp)
            raise

    def _auditar(self, operacion, forma, antes, despues, **extra):
        if not self.persistente:
            return
        linea = {'fecha': _ahora(), 'operacion': operacion, 'forma': forma, 'antes': antes, 'despues': despues,
                 'operador': _operador(), **extra}
        with open(self.ruta_auditoria, 'a', encoding='utf-8') as f:
            f.write(json.dumps(linea, ensure_ascii=False) + '\n')

    def _conciliar(self):
        """Si alguien agregó a la precarga una forma que ya estaba aprendida, gana la precarga: la entrada aprendida
        se da de baja (si no, la forma tendría dos entradas y el léxico rechazaría el vocabulario)."""
        repetidas = [f for f in self.aprendido if f in self._indice]
        for f in repetidas:
            e = self.aprendido.pop(f)
            cat, canon, _ = self._indice[f]
            self._auditar('BAJA_POR_PRECARGA', f, {'categoria': e['categoria'], 'canonico': e['canonico']},
                          {'categoria': cat, 'canonico': canon, 'origen': 'PRECARGA'})
        if repetidas and self.persistente:
            self._guardar_aprendido()

    # ------------------------------------------------------------------ operaciones
    def buscar(self, forma):
        """-> (categoría, canónico, origen) | None ; origen ∈ {PRECARGA, APRENDIDA}."""
        return self._indice.get(_plegar(forma))

    def insertar(self, forma, categoria, canonico, origen=None, decision=None):
        """Incorpora una forma nueva. Control de duplicados: devuelve False si la forma ya tiene entrada."""
        forma = _plegar(forma)
        if not forma or forma in self._indice:
            return False
        e = {'categoria': categoria, 'canonico': canonico, 'fecha': _ahora(), 'origen': origen or {}}
        self.aprendido[forma] = e
        self._indice[forma] = (categoria, canonico, 'APRENDIDA')
        self.insertadas.append(forma)
        if self.persistente:
            self._guardar_aprendido()
        self._auditar('INSERTAR', forma, None, {'categoria': categoria, 'canonico': canonico},
                      origen=origen or {}, decision=decision or {})
        return True

    def vocabulario(self):
        """Tabla vigente con el formato de vocabulario.json (categoría -> canónico -> formas), para el léxico."""
        v = {cat: {canon: list(formas) for canon, formas in canons.items()} for cat, canons in self.precarga.items()}
        for forma, e in self.aprendido.items():
            v.setdefault(e['categoria'], {}).setdefault(e['canonico'], []).append(forma)
        return v

    def canonicos(self, categoria):
        return sorted({canon for cat, canon, _ in self._indice.values() if cat == categoria})

    def resumen(self):
        n_pre = sum(1 for *_, o in self._indice.values() if o == 'PRECARGA')
        return {'precarga': n_pre, 'aprendidas': len(self.aprendido), 'insertadas_en_esta_ejecucion': list(self.insertadas)}
