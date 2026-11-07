class EntradaTablaSimbolos:
    def __init__(self, nombre, tipo_simbolo, sesion_id):
        self.nombre = nombre
        self.tipo_simbolo = tipo_simbolo # "TICKET" o "PARTICIPANTE"
        self.sesion_id = sesion_id
        self.apariciones = [] # lista de (turno_num, desplazamiento)

    def agregar_aparicion(self, turno_num, desplazamiento):
        aparicion = (turno_num, desplazamiento)
        if aparicion not in self.apariciones:
            self.apariciones.append(aparicion)

    def a_diccionario(self):
        return {
            "nombre": self.nombre,
            "tipo": self.tipo_simbolo,
            "sesion": self.sesion_id,
            "apariciones": self.apariciones
        }

class TablaSimbolos:
    def __init__(self):
        self.tablas = {} # sesion_id -> {nombre_simbolo: EntradaTablaSimbolos}

    def insertar(self, sesion_id, nombre, tipo_simbolo, turno_num, desplazamiento):
        if sesion_id not in self.tablas:
            self.tablas[sesion_id] = {}
        
        clave = nombre.upper() if tipo_simbolo == "TICKET" else nombre
        if clave in self.tablas[sesion_id]:
            self.tablas[sesion_id][clave].agregar_aparicion(turno_num, desplazamiento)
        else:
            entrada = EntradaTablaSimbolos(nombre, tipo_simbolo, sesion_id)
            entrada.agregar_aparicion(turno_num, desplazamiento)
            self.tablas[sesion_id][clave] = entrada

    def buscar(self, sesion_id, nombre):
        if sesion_id in self.tablas:
            clave = nombre.upper()
            return self.tablas[sesion_id].get(clave, None)
        return None

    def obtener_simbolos_sesion(self, sesion_id):
        if sesion_id in self.tablas:
            return list(self.tablas[sesion_id].values())
        return []

    def a_diccionario(self):
        resultado = {}
        for sesion, simbolos in self.tablas.items():
            resultado[sesion] = [sim.a_diccionario() for sim in simbolos.values()]
        return resultado
