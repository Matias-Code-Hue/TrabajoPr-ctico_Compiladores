"""Tabla de símbolos (ámbito = sesión). Separada del diccionario de vocabulario.
Entradas: SESION, PARTICIPANTE (rol), TICKET. Menciones repetidas -> UNA entrada con varias apariciones.
Operaciones: insertar (con control de duplicados), buscar, actualizar. Toda operación queda en `bitacora`
(para la traza: «consulta/inserción en tabla de símbolos»).
"""
from dataclasses import dataclass, field

GLOBAL = '<global>'


@dataclass
class Aparicion:
    turno: int | None
    desp: int | None
    lexema: str


@dataclass
class Entrada:
    tipo: str
    clave: str
    sesion: str
    apariciones: list = field(default_factory=list)
    atributos: dict = field(default_factory=dict)


class TablaSimbolos:
    def __init__(self):
        self.ambitos = {}       # sesión -> {(tipo, clave): Entrada}
        self.bitacora = []

    def _get(self, sesion, tipo, clave):
        return self.ambitos.get(sesion, {}).get((tipo, clave))

    def buscar(self, sesion, tipo, clave):
        e = self._get(sesion, tipo, clave)
        self.bitacora.append(f'BUSCAR {tipo} {clave} @{sesion} -> {"ENCONTRADO" if e else "NO_EXISTE"}')
        return e

    def insertar(self, sesion, tipo, clave, aparicion=None, **atributos):
        """Devuelve (entrada, creada). Si ya existe NO duplica: enlaza la nueva aparición a la entrada única."""
        e = self._get(sesion, tipo, clave)
        creada = e is None
        if creada:
            e = Entrada(tipo, clave, sesion)
            self.ambitos.setdefault(sesion, {})[(tipo, clave)] = e
        if aparicion:
            e.apariciones.append(aparicion)
        e.atributos.update(atributos)
        self.bitacora.append(f'{"INSERTAR" if creada else "DUPLICADO->ENLAZAR"} {tipo} {clave} @{sesion}'
                             f' (apariciones={len(e.apariciones)})')
        return e, creada

    def actualizar(self, sesion, tipo, clave, **atributos):
        e = self._get(sesion, tipo, clave)
        if e is None:
            raise KeyError(f'{tipo} {clave} no existe en {sesion}')
        e.atributos.update(atributos)
        self.bitacora.append(f'ACTUALIZAR {tipo} {clave} @{sesion} {atributos}')
        return e

    def a_dict(self, sesion):
        return [{'tipo': e.tipo, 'clave': e.clave,
                 'apariciones': [{'turno': a.turno, 'desp': a.desp, 'lexema': a.lexema} for a in e.apariciones],
                 'atributos': e.atributos}
                for e in self.ambitos.get(sesion, {}).values()]


if __name__ == '__main__':
    ts = TablaSimbolos()
    ts.insertar('S01', 'PARTICIPANTE', 'CLIENTE', Aparicion(1, 2, 'CLIENTE'))
    ts.insertar('S01', 'TICKET', 'TK-204', Aparicion(2, 40, 'TK-204'))
    ts.insertar('S01', 'TICKET', 'TK-204', Aparicion(3, 12, 'tk-204'))     # mención repetida
    ts.insertar('S02', 'TICKET', 'TK-204', Aparicion(1, 5, 'TK-204'))      # otro ámbito: entrada distinta
    ts.actualizar('S01', 'TICKET', 'TK-204', estado='PENDIENTE')
    ts.buscar('S01', 'TICKET', 'TK-999')
    print('\n'.join(ts.bitacora)); print(ts.a_dict('S01'))
