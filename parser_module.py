import re
from lexer import tokenizar_texto

class Turno:
    def __init__(self, turno_num, rol, texto):
        self.turno_num = turno_num
        self.rol = rol # "CLIENTE" o "AGENTE"
        self.texto = texto
        self.tokens = []
        self.clausulas = []
        self.rechazado = False

    def a_diccionario(self):
        return {
            "turno_num": self.turno_num,
            "rol": self.rol,
            "texto": self.texto,
            "tokens": [t.a_diccionario() for t in self.tokens],
            "clausulas": self.clausulas,
            "rechazado": self.rechazado
        }

class Sesion:
    def __init__(self, sesion_id):
        self.sesion_id = sesion_id
        self.turnos = []
        self.errores = []
        self.estado_analisis = "completo" # o "parcial"

    def a_diccionario(self):
        return {
            "id": self.sesion_id,
            "estado_analisis": self.estado_analisis,
            "turnos": [t.a_diccionario() for t in self.turnos],
            "errores": self.errores
        }

def analizar_archivo_entrada(contenido):
    sesiones = []
    lineas = contenido.strip().splitlines()
    sesion_actual = None
    procesando_sesion = False
    
    indice_linea = 0
    while indice_linea < len(lineas):
        linea = lineas[indice_linea].strip()
        if not linea:
            indice_linea += 1
            continue
            
        if linea.upper().startswith("SESION "):
            partes = linea.split()
            ses_id = partes[1] if len(partes) > 1 else "S01"
            sesion_actual = Sesion(ses_id)
            procesando_sesion = True
            indice_linea += 1
            continue
            
        if linea.upper() == "FIN":
            if sesion_actual:
                sesiones.append(sesion_actual)
                sesion_actual = None
            procesando_sesion = False
            indice_linea += 1
            continue
            
        if procesando_sesion and sesion_actual:
            coincidencia_turno = validar_turno(linea)
            if coincidencia_turno:
                t_num, rol, texto = coincidencia_turno
                turno = Turno(t_num, rol, texto)
                tokens = tokenizar_texto(texto, sesion_actual.sesion_id, t_num)
                turno.tokens = tokens
                sesion_actual.turnos.append(turno)
            else:
                sesion_actual.estado_analisis = "parcial"
                sesion_actual.errores.append(f"Turno rechazado o formato inválido en línea: {linea}")
                turno = Turno(0, "INVALIDO", linea)
                turno.rechazado = True
                sesion_actual.turnos.append(turno)
        indice_linea += 1
        
    return sesiones

def validar_turno(linea):
    coincidencia = re.match(r'^(\d+)\s+(CLIENTE|AGENTE)\s*:\s*(.+)$', linea, re.IGNORECASE)
    if coincidencia:
        return int(coincidencia.group(1)), coincidencia.group(2).upper(), coincidencia.group(3)
    return None
