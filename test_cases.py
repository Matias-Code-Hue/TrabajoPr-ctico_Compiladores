CASOS_DE_PRUEBA = [
    {
        "id": "01",
        "descripcion": "Servicio lento; luego el cliente dice «Ahora funciona bien».",
        "input": "SESION S01\n1 CLIENTE: Servicio lento; luego el cliente dice Ahora funciona bien.\nFIN",
        "esperado_aspectos": {"SERVICIO": "MIXTA"},
        "esperado_estado": "RESUELTO"
    },
    {
        "id": "02",
        "descripcion": "«Me atendiste muy bien, pero sigo sin internet».",
        "input": "SESION S02\n1 CLIENTE: Me atendiste muy bien, pero sigo sin internet.\nFIN",
        "esperado_aspectos": {"ATENCION": "POSITIVA", "SERVICIO": "NEGATIVA"},
        "esperado_estado": "NO_RESUELTO"
    },
    {
        "id": "03",
        "descripcion": "«Ahora funciona, pero se corta todos los días».",
        "input": "SESION S03\n1 CLIENTE: Ahora funciona, pero se corta todos los días.\nFIN",
        "esperado_aspectos": {"SERVICIO": "MIXTA"},
        "esperado_estado": "TEMPORAL"
    },
    {
        "id": "04",
        "descripcion": "«No entendí la explicación, pero el agente fue amable».",
        "input": "SESION S04\n1 CLIENTE: No entendí la explicación, pero el agente fue amable.\nFIN",
        "esperado_aspectos": {"CLARIDAD": "NEGATIVA", "ATENCION": "POSITIVA"},
        "esperado_estado": "NO_CONFIRMADO"
    },
    {
        "id": "05",
        "descripcion": "«El internet está lentto»; se menciona TK-204.",
        "input": "SESION S05\n1 CLIENTE: El internet está lentto; se menciona TK-204.\nFIN",
        "esperado_aspectos": {"SERVICIO": "NEGATIVA"},
        "esperado_correcciones": 1,
        "esperado_entidades": ["TK-204"]
    },
    {
        "id": "06",
        "descripcion": "AGENTE: «Mañana revisaremos TK-205»; CLIENTE: «Gracias».",
        "input": "SESION S06\n1 AGENTE: Mañana revisaremos TK-205.\n2 CLIENTE: Gracias.\nFIN",
        "esperado_estado": "PENDIENTE",
        "esperado_aspectos": {"SERVICIO": "SIN_EVIDENCIA"}
    },
    {
        "id": "07",
        "descripcion": "Rol inválido SOPORTE entre dos mensajes válidos; luego otra sesión.",
        "input": "SESION S07\n1 CLIENTE: Hola\n2 SOPORTE: Rol inválido\n3 CLIENTE: Sigo con problemas.\nFIN",
        "esperado_estado_analisis": "parcial"
    },
    {
        "id": "08",
        "descripcion": "Con diccionario {lenta, lento}: CLIENTE: «lent». Empate a distancia 1.",
        "input": "SESION S08\n1 CLIENTE: lent\n2 CLIENTE: lento\nFIN",
        "esperado_empate": True
    },
    # 4 Casos propios
    {
        "id": "09",
        "descripcion": "Caso propio: Contraste y negación (servicio no malo pero cortes)",
        "input": "SESION S09\n1 CLIENTE: El servicio no es malo, pero hay cortes.\nFIN",
        "esperado_aspectos": {"SERVICIO": "MIXTA"},
        "esperado_estado": "NO_RESUELTO"
    },
    {
        "id": "10",
        "descripcion": "Caso propio: Corrección y múltiples tickets",
        "input": "SESION S10\n1 CLIENTE: Tengo un corte en TK-9999 y va lentto.\nFIN",
        "esperado_aspectos": {"SERVICIO": "NEGATIVA"},
        "esperado_entidades": ["TK-9999"]
    },
    {
        "id": "11",
        "descripcion": "Caso propio: Turnos múltiples con resolución",
        "input": "SESION S11\n1 CLIENTE: No funciona.\n2 AGENTE: Reinicie el router.\n3 CLIENTE: Ahora funciona bien.\nFIN",
        "esperado_estado": "RESUELTO"
    },
    {
        "id": "12",
        "descripcion": "Caso propio: Regresión de funcionamiento correcto",
        "input": "SESION S12\n1 CLIENTE: El servicio funciona bien.\nFIN",
        "esperado_estado": "RESUELTO"
    }
]
