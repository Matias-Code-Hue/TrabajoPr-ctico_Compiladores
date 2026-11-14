"""Lector de formato del TP1.

Implementa, línea a línea, la gramática de formato (ver GRAMATICA.md):
    lote -> sesion lote'   sesion -> SESION Sxx EOL turnos FIN EOL   turno -> NUM rol ':' texto EOL
Cada EOL es un punto de sincronización: ante un error de formato la línea se rechaza, se registra
el error y el análisis continúa en la línea SIGUIENTE (recuperación en modo pánico por línea).
Excepción (respuesta del profesor): un número de turno fuera de orden descarta TODO el resto de la sesión hasta su FIN
(ORDEN_INCONSISTENTE y luego TURNO_DESCARTADO por cada turno siguiente); la sesión siguiente se analiza normalmente.
"""
import unicodedata
from dataclasses import dataclass, field
from lexico import escanear, Token


@dataclass
class Turno:
    numero: int
    rol: str                 # CLIENTE | AGENTE
    texto: str
    linea: int
    tokens: list             # tokens del texto (con posición sesión/turno/desplazamiento)
    rol_desp: int = 0        # desplazamiento (0-based, dentro de la línea) del token de rol
    linea_txt: str = ''      # línea original completa (para extraer fragmentos por desplazamiento)


@dataclass
class ErrorFormato:
    sesion: str | None
    linea: int
    codigo: str
    detalle: str
    contenido: str


@dataclass
class Sesion:
    id: str
    linea_ini: int
    turnos: list = field(default_factory=list)
    errores: list = field(default_factory=list)
    cerrada: bool = False

    @property
    def parcial(self):       # análisis parcial: hubo rechazos o falta FIN
        return bool(self.errores) or not self.cerrada


def leer_lote(lineas, afd):
    sesiones, globales = [], []
    ses, esperado, descarte = None, 1, False
    truncada = False         # True tras un orden inconsistente: se descartan los turnos restantes de la sesión
    ids = set()              # control de duplicados: el id de sesión es el ámbito de la tabla de entidades

    def err(codigo, detalle, n, contenido):
        (ses.errores if ses else globales).append(
            ErrorFormato(ses.id if ses else None, n, codigo, detalle, contenido))

    for n, crudo in enumerate(lineas, 1):
        # NFC: «á» escrita como a + tilde combinante (NFD, típico de macOS) pasa a un solo carácter; BOM fuera
        linea = unicodedata.normalize('NFC', crudo.rstrip('\r\n')).lstrip('\ufeff')
        if not linea.strip():
            if not descarte:
                err('LINEA_EN_BLANCO', 'no se admiten líneas en blanco', n, linea)
            continue
        toks = escanear(linea, afd, ses.id if ses else None)
        c0 = toks[0].categoria

        if c0 == 'SESION':
            if ses and not ses.cerrada:
                err('SESION_SIN_FIN', f'{ses.id} no cerró con FIN antes de la línea {n}', n, linea)
            sid = toks[1].norm.upper() if len(toks) == 2 and toks[1].categoria == 'ID_SESION' else None
            if sid in ids:                          # id repetido: se rechaza la sesión completa (hasta su FIN)
                ses, descarte = None, True
                err('SESION_DUPLICADA', f'el id {sid} ya fue usado en este lote; la sesión se descarta', n, linea)
            elif sid:
                ids.add(sid)
                ses, esperado, truncada, descarte = Sesion(sid, n), 1, False, False
                sesiones.append(ses)
            else:                                   # encabezado inválido: se descarta hasta el próximo SESION/FIN
                ses, descarte = None, True
                err('SESION_MAL_FORMADA', 'se esperaba «SESION Sxx»', n, linea)

        elif c0 == 'FIN':
            if descarte:
                descarte = False
            elif ses is None:
                err('FIN_SIN_SESION', 'FIN fuera de una sesión', n, linea)
            else:
                if len(toks) != 1:
                    err('FIN_MAL_FORMADO', 'FIN no admite texto adicional', n, linea)
                ses.cerrada, ses = True, None

        elif descarte:
            continue

        elif c0 == 'NUM':
            if ses is None:
                err('TURNO_FUERA_DE_SESION', 'turno fuera de una sesión', n, linea)
                continue
            num = int(toks[0].norm)
            # Respuesta del profesor: ante un orden inconsistente se conserva lo anterior y se descarta TODO lo que
            # sigue en la sesión («1, 3, 4» -> solo el 1). La sesión queda PARCIAL y las siguientes no se afectan.
            if truncada:
                err('TURNO_DESCARTADO', f'turno {num} posterior a un orden inconsistente', n, linea)
                continue
            if num != esperado:
                truncada = True
                err('ORDEN_INCONSISTENTE', f'turno {num}, se esperaba {esperado}; se descarta el resto de la sesión',
                    n, linea)
                continue
            esperado = num + 1                      # un turno rechazado por rol/formato consume igualmente su número
            if len(toks) < 2 or toks[1].categoria not in ('CLIENTE', 'AGENTE'):
                rol = toks[1].lexema if len(toks) > 1 else ''
                err('ROL_INVALIDO', f'rol {rol!r}: debe ser CLIENTE o AGENTE', n, linea)
            elif len(toks) < 3 or toks[2].categoria != 'DOSPUNTOS':
                err('FALTA_DOSPUNTOS', 'se esperaba «:» después del rol', n, linea)
            elif len(toks) == 3:
                err('TEXTO_VACIO', 'el turno no tiene texto', n, linea)
            else:
                texto_toks = toks[3:]
                for t in texto_toks:
                    t.turno = num
                ses.turnos.append(Turno(num, toks[1].norm.upper(), linea[toks[2].desp + 1:].strip(),
                                        n, texto_toks, toks[1].desp, linea))
        else:
            err('LINEA_NO_RECONOCIDA', 'se esperaba SESION, FIN o un turno', n, linea)

    if ses and not ses.cerrada:
        err('SESION_SIN_FIN', f'{ses.id} no cerró con FIN antes del fin de archivo', len(lineas), '')
    if not sesiones:                                # <lote> ::= <sesion> <lote_r>: al menos una sesión
        globales.append(ErrorFormato(None, len(lineas), 'LOTE_VACIO', 'el archivo no contiene ninguna sesión', ''))
    return sesiones, globales


if __name__ == '__main__':
    import sys
    from lexico import construir_afd, cargar_vocabulario
    afd = construir_afd(cargar_vocabulario('vocabulario.json'))
    with open(sys.argv[1] if len(sys.argv) > 1 else 'casos_guia.txt', encoding='utf-8') as f:
        sesiones, globales = leer_lote(f.readlines(), afd)
    for s in sesiones:
        print(f'{s.id}: {"PARCIAL" if s.parcial else "COMPLETA"}  turnos aceptados={[t.numero for t in s.turnos]}')
        for e in s.errores:
            print(f'    ✗ línea {e.linea} {e.codigo}: {e.detalle}')
    for e in globales:
        print(f'global ✗ línea {e.linea} {e.codigo}: {e.detalle}')
