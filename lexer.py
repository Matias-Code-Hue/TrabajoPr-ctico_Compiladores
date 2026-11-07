import re

def distancia_levenshtein(s1, s2):
    if len(s1) < len(s2):
        return distancia_levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)
    fila_anterior = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        fila_actual = [i + 1]
        for j, c2 in enumerate(s2):
            inserciones = fila_anterior[j + 1] + 1
            eliminaciones = fila_actual[j] + 1
            sustituciones = fila_anterior[j] + (c1 != c2)
            fila_actual.append(min(inserciones, eliminaciones, sustituciones))
        fila_anterior = fila_actual
    return fila_anterior[-1]

# Diccionario de vocabulario con palabras canónicas y sinónimos
VOCABULARIO = {
    "servicio": "servicio",
    "internet": "servicio",
    "conexion": "servicio",
    "atencion": "atencion",
    "explicacion": "clara",
    "claridad": "claridad",
    "lento": "lento",
    "lenta": "lento",
    "lentitud": "lento",
    "funciona": "funcionar",
    "funciono": "funcionar",
    "funcionamiento": "funcionar",
    "bien": "bien",
    "mal": "mal",
    "cortes": "corte",
    "corta": "corte",
    "corte": "corte",
    "router": "router",
    "reinicio": "reiniciar",
    "reinicie": "reiniciar",
    "reiniciar": "reiniciar",
    "gracias": "agradecimiento",
    "amable": "amable",
    "atento": "amable",
    "revisaremos": "revisar",
    "revision": "revisar",
    "mañana": "mañana",
    "ticket": "ticket",
    "no": "no",
    "pero": "pero",
    "muy": "muy",
}

class Token:
    def __init__(self, tipo, lexema_original, lexema_norm, sesion_id, turno_num, desplazamiento):
        self.tipo = tipo
        self.lexema_original = lexema_original
        self.lexema_norm = lexema_norm
        self.sesion_id = sesion_id
        self.turno_num = turno_num
        self.desplazamiento = desplazamiento
        self.corregido = False
        self.empate = False

    def a_diccionario(self):
        return {
            "tipo": self.tipo,
            "lexema_original": self.lexema_original,
            "lexema_norm": self.lexema_norm,
            "sesion": self.sesion_id,
            "turno": self.turno_num,
            "desplazamiento": self.desplazamiento,
            "corregido": self.corregido,
            "empate": self.empate
        }

def corregir_palabra(palabra, diccionario):
    palabra_min = palabra.lower()
    if palabra_min in diccionario or palabra_min.startswith("tk-") or palabra_min.isdigit() or palabra_min in ["no", "pero"]:
        return palabra_min, False, False

    # Verificar distancia de Levenshtein <= 1
    candidatos = {}
    for canon in diccionario.keys():
        dist = distancia_levenshtein(palabra_min, canon)
        if dist <= 1:
            if dist not in candidatos:
                candidatos[dist] = []
            candidatos[dist].append(diccionario[canon])

    if 1 in candidatos:
        coincidencias_unicas = list(set(candidatos[1]))
        if len(coincidencias_unicas) == 1:
            return coincidencias_unicas[0], True, False
        else:
            # Empate
            return palabra_min, False, True

    return palabra_min, False, False

def tokenizar_texto(texto, sesion_id, turno_num):
    patron_token = re.compile(r'(TK-\d{3,6}|\b\w+\b|[.,;])', re.UNICODE)
    coincidencias = patron_token.finditer(texto)
    tokens = []
    
    for coincidencia in coincidencias:
        lexema = coincidencia.group(1)
        desplazamiento = coincidencia.start()
        
        if lexema.lower() in ["no", "pero"] or lexema.isdigit() or lexema.upper().startswith("TK-"):
            tipo = "TICKET" if lexema.upper().startswith("TK-") else ("NEGACION" if lexema.lower() == "no" else ("CONTRASTE" if lexema.lower() == "pero" else "PALABRA"))
            norm = lexema.lower()
            tokens.append(Token(tipo, lexema, norm, sesion_id, turno_num, desplazamiento))
        elif re.match(r'^[.,;]$', lexema):
            tokens.append(Token("PUNCT", lexema, lexema, sesion_id, turno_num, desplazamiento))
        else:
            norm, corregido, empate = corregir_palabra(lexema, VOCABULARIO)
            tipo = "PALABRA"
            tok = Token(tipo, lexema, norm, sesion_id, turno_num, desplazamiento)
            tok.corregido = corregido
            tok.empate = empate
            tokens.append(tok)
            
    return tokens
