from symbol_table import TablaSimbolos

class AnalizadorSemantico:
    def __init__(self, tabla_simbolos: TablaSimbolos):
        self.tabla_simbolos = tabla_simbolos

    def analizar_sesion(self, sesion):
        evaluaciones_turnos = []
        evidencias_aspectos = {
            "SERVICIO": [],
            "ATENCION": [],
            "CLARIDAD": []
        }
        
        entidades = []
        correcciones = []
        errores = list(sesion.errores)
        trazas = []

        for turno in sesion.turnos:
            if turno.rechazado:
                trazas.append({
                    "turno": turno.turno_num,
                    "original": turno.texto,
                    "tokens": [],
                    "estructura": "Rechazado (Rol inválido u orden inconsistente)",
                    "operacion_simbolos": "Ninguna",
                    "semantica": "Turno rechazado",
                    "resultado": "RECHAZADO"
                })
                continue

            tokens_dict = []
            for t in turno.tokens:
                tokens_dict.append(t.a_diccionario())
                if t.tipo == "TICKET":
                    self.tabla_simbolos.insertar(sesion.sesion_id, t.lexema_original, "TICKET", turno.turno_num, t.desplazamiento)
                    entidades.append({"tipo": "TICKET", "valor": t.lexema_original.upper(), "turno": turno.turno_num})
                if t.corregido:
                    correcciones.append({"original": t.lexema_original, "corregido": t.lexema_norm, "turno": turno.turno_num})
                elif t.empate:
                    correcciones.append({"original": t.lexema_original, "corregido": None, "empate": True, "turno": turno.turno_num})

            valoracion_turno = self.evaluar_turno(turno)
            evaluaciones_turnos.append({
                "turno": turno.turno_num,
                "rol": turno.rol,
                "texto": turno.texto,
                "valoraciones": valoracion_turno
            })

            for aspecto, val in valoracion_turno.items():
                if val != "SIN_EVIDENCIA":
                    evidencias_aspectos[aspecto].append({
                        "turno": turno.turno_num,
                        "rol": turno.rol,
                        "valoracion": val,
                        "texto": turno.texto
                    })

            trazas.append({
                "turno": turno.turno_num,
                "original": turno.texto,
                "tokens": [t.lexema_original for t in turno.tokens],
                "estructura": f"Turno {turno.turno_num} ({turno.rol}): Cláusula reconocida",
                "operacion_simbolos": f"Inserción/Consulta de tickets en sesión {sesion.sesion_id}",
                "semantica": f"Valoraciones: {valoracion_turno}",
                "resultado": "OK"
            })

        resumen_aspectos = {}
        for aspecto, lista_ev in evidencias_aspectos.items():
            vals = [e["valoracion"] for e in lista_ev if e["rol"] == "CLIENTE"]
            pos_cant = vals.count("POSITIVA")
            neg_cant = vals.count("NEGATIVA")
            neut_cant = vals.count("NEUTRA")

            if pos_cant > 0 and neg_cant > 0:
                resumen_aspectos[aspecto] = "MIXTA"
            elif pos_cant > 0:
                resumen_aspectos[aspecto] = "POSITIVA"
            elif neg_cant > 0:
                resumen_aspectos[aspecto] = "NEGATIVA"
            elif neut_cant > 0:
                resumen_aspectos[aspecto] = "NEUTRA"
            else:
                vals_agente = [e["valoracion"] for e in lista_ev if e["rol"] == "AGENTE"]
                if "POSITIVA" in vals_agente:
                    resumen_aspectos[aspecto] = "POSITIVA"
                elif "NEGATIVA" in vals_agente:
                    resumen_aspectos[aspecto] = "NEGATIVA"
                else:
                    resumen_aspectos[aspecto] = "SIN_EVIDENCIA"

        estado = self.inferir_estado(sesion, evidencias_aspectos, evaluaciones_turnos)
        simbolos_sesion = [sim.a_diccionario() for sim in self.tabla_simbolos.obtener_simbolos_sesion(sesion.sesion_id)]

        return {
            "id": sesion.sesion_id,
            "estado_analisis": sesion.estado_analisis,
            "evaluaciones_turnos": evaluaciones_turnos,
            "resumen_aspectos": resumen_aspectos,
            "estado": estado,
            "entidades": entidades,
            "correcciones": correcciones,
            "errores": errores,
            "tabla_simbolos": simbolos_sesion,
            "traza": trazas
        }

    def evaluar_turno(self, turno):
        texto_min = turno.texto.lower()
        normas = [t.lexema_norm for t in turno.tokens]
        
        val_servicio = "SIN_EVIDENCIA"
        val_atencion = "SIN_EVIDENCIA"
        val_claridad = "SIN_EVIDENCIA"

        tiene_no = "no" in normas
        tiene_pero = "pero" in normas

        if "lento" in normas or "lentitud" in normas or "corte" in normas or "cortes" in normas or "sigue" in normas and "lento" in normas:
            if tiene_no and ("funcionar" in normas or "bien" in normas):
                val_servicio = "POSITIVA"
            else:
                val_servicio = "NEGATIVA"
        elif "funcionar" in normas or "bien" in normas:
            if tiene_no:
                val_servicio = "NEGATIVA"
            else:
                val_servicio = "POSITIVA"
        elif "mal" in normas:
            val_servicio = "NEGATIVA"

        if "amable" in normas or "bien" in normas and turno.rol == "AGENTE" or "atencion" in normas or "atendiste" in texto_min:
            if tiene_no:
                val_atencion = "NEGATIVA"
            else:
                val_atencion = "POSITIVA"

        if "explicacion" in normas or "claridad" in normas or "entendi" in texto_min or "entender" in normas:
            if tiene_no:
                val_claridad = "NEGATIVA"
            else:
                val_claridad = "POSITIVA"

        return {
            "SERVICIO": val_servicio,
            "ATENCION": val_atencion,
            "CLARIDAD": val_claridad
        }

    def inferir_estado(self, sesion, evidencias_aspectos, evaluaciones_turnos):
        turnos_cliente = [t for t in sesion.turnos if t.rol == "CLIENTE" and not t.rechazado]
        
        if not turnos_cliente:
            return "NO_CONFIRMADO"

        ultimo_texto_cliente = turnos_cliente[-1].texto.lower()
        ultimas_normas_cliente = [t.lexema_norm for t in turnos_cliente[-1].tokens]

        tiene_pendiente = any("revisar" in [t.lexema_norm for t in t.tokens] or "mañana" in [t.lexema_norm for t in t.tokens] for t in sesion.turnos)
        tiene_confirmacion_posterior = len(turnos_cliente) > 1 and ("gracias" in [t.lexema_norm for t in turnos_cliente[-1].tokens]) and any("revisar" in [t.lexema_norm for t in t.tokens] for t in sesion.turnos[:-1])
        
        if tiene_pendiente and not any("funcionar" in [t.lexema_norm for t in t.tokens] for t in turnos_cliente):
            if len(turnos_cliente) == 1 and turnos_cliente[0].rol == "CLIENTE":
                return "PENDIENTE"
            if tiene_confirmacion_posterior or ("gracias" in ultimas_normas_cliente and len(sesion.turnos) >= 2 and sesion.turnos[-2].rol == "AGENTE"):
                return "PENDIENTE"

        if "pero" in ultimo_texto_cliente or ("funcionar" in ultimas_normas_cliente and ("corte" in ultimas_normas_cliente or "lento" in ultimas_normas_cliente or "todos" in ultimas_normas_cliente)) or ("funcionar" in ultimas_normas_cliente and ("pero" in ultimo_texto_cliente or "sigue" in ultimo_texto_cliente)):
            return "TEMPORAL"

        if ("funcionar" in ultimas_normas_cliente or "bien" in ultimas_normas_cliente) and "no" not in ultimas_normas_cliente and "pero" not in ultimo_texto_cliente:
            return "RESUELTO"

        if "no" in ultimas_normas_cliente or "lento" in ultimas_normas_cliente or "corte" in ultimas_normas_cliente or "mal" in ultimas_normas_cliente or "sin" in ultimo_texto_cliente:
            if "funcionar" not in ultimas_normas_cliente:
                return "NO_RESUELTO"

        return "NO_CONFIRMADO"
