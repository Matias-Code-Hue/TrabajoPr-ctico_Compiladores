# Resultados de las pruebas (TP1)

Generado por `python3 pruebas.py --informe`. Para cada caso: situación, salida **esperada** (derivada del enunciado o del criterio del grupo), salida **obtenida** y las **reglas activadas** (ver catálogo en `salida.json` / `semantica.py`).

## Caso 01 — Servicio lento; luego el cliente dice «Ahora funciona bien».

- Origen: enunciado · archivo `casos/caso_01.txt`

**Sesión S01: OK**

| | Esperado | Obtenido |
|---|---|---|
| analisis | COMPLETO | COMPLETO |
| estado | RESUELTO | RESUELTO |
| SERVICIO | MIXTA | MIXTA |
| ATENCION | SIN_EVIDENCIA | SIN_EVIDENCIA |
| CLARIDAD | SIN_EVIDENCIA | SIN_EVIDENCIA |

Reglas activadas: `R-AHORA` (C3.1); `R-COP` (C1.1); `R-EST` (C3.1); `R-EST-RES` (C3.1); `R-SUJ` (C1.1)

- C1.1 (CLIENTE) «El servicio está lento» → SERVICIO NEGATIVA
- C3.1 (CLIENTE) «Ahora funciona bien» → SERVICIO POSITIVA, declaración OK
- Estado: **RESUELTO** por `R-EST-RES`

## Caso 02 — «Me atendiste muy bien, pero sigo sin internet».

- Origen: enunciado · archivo `casos/caso_02.txt`

**Sesión S01: OK**

| | Esperado | Obtenido |
|---|---|---|
| analisis | COMPLETO | COMPLETO |
| estado | NO_RESUELTO | NO_RESUELTO |
| SERVICIO | NEGATIVA | NEGATIVA |
| ATENCION | POSITIVA | POSITIVA |
| CLARIDAD | SIN_EVIDENCIA | SIN_EVIDENCIA |

Reglas activadas: `R-EST-NORES` (C1.2); `R-MUY` (C1.1); `R-PERO` (C1.2); `R-SEG-SIN` (C1.2); `R-SIN` (C1.2); `R-VAL` (C1.1)

- C1.1 (CLIENTE) «Me atendiste muy bien» → ATENCION POSITIVA
- C1.2 (CLIENTE) «sigo sin internet» → SERVICIO NEGATIVA, declaración FALLA
- Estado: **NO_RESUELTO** por `R-EST-NORES`

## Caso 03 — «Ahora funciona, pero se corta todos los días».

- Origen: enunciado · archivo `casos/caso_03.txt`

**Sesión S01: OK**

| | Esperado | Obtenido |
|---|---|---|
| analisis | COMPLETO | COMPLETO |
| estado | TEMPORAL | TEMPORAL |
| SERVICIO | MIXTA | MIXTA |
| ATENCION | SIN_EVIDENCIA | SIN_EVIDENCIA |
| CLARIDAD | SIN_EVIDENCIA | SIN_EVIDENCIA |

Reglas activadas: `R-AHORA` (C1.1); `R-CORTE` (C1.2); `R-EST` (C1.1); `R-EST-TEMP` (C1.1, C1.2); `R-PERO` (C1.2)

- C1.1 (CLIENTE) «Ahora funciona» → SERVICIO POSITIVA, declaración OK
- C1.2 (CLIENTE) «se corta todos los días» → SERVICIO NEGATIVA, declaración RECUR
- Estado: **TEMPORAL** por `R-EST-TEMP`

## Caso 04 — «No entendí la explicación, pero el agente fue amable».

- Origen: enunciado · archivo `casos/caso_04.txt`

**Sesión S01: OK**

| | Esperado | Obtenido |
|---|---|---|
| analisis | COMPLETO | COMPLETO |
| estado | NO_CONFIRMADO | NO_CONFIRMADO |
| SERVICIO | SIN_EVIDENCIA | SIN_EVIDENCIA |
| ATENCION | POSITIVA | POSITIVA |
| CLARIDAD | NEGATIVA | NEGATIVA |

Reglas activadas: `R-COP` (C1.2); `R-ENT` (C1.1); `R-EST-NC` (—); `R-NEG` (C1.1); `R-PERO` (C1.2); `R-SUJ` (C1.2)

- C1.1 (CLIENTE) «No entendí la explicación» → CLARIDAD NEGATIVA
- C1.2 (CLIENTE) «el agente fue amable» → ATENCION POSITIVA
- Estado: **NO_CONFIRMADO** por `R-EST-NC`

## Caso 05 — «El internet está lentto»; se menciona TK-204.

- Origen: enunciado · archivo `casos/caso_05.txt`

**Sesión S01: OK**

| | Esperado | Obtenido |
|---|---|---|
| analisis | COMPLETO | COMPLETO |
| estado | NO_CONFIRMADO | NO_CONFIRMADO |
| SERVICIO | NEGATIVA | NEGATIVA |
| ATENCION | SIN_EVIDENCIA | SIN_EVIDENCIA |
| CLARIDAD | SIN_EVIDENCIA | SIN_EVIDENCIA |
| correcciones | [['lentto', 'lento', 'CORREGIDA']] | [['lentto', 'lento', 'CORREGIDA']] |
| tickets | ['TK-204'] | ['TK-204'] |

Reglas activadas: `R-COP` (C1.1); `R-EST-NC` (—); `R-SUJ` (C1.1)

- C1.1 (CLIENTE) «El internet está lentto» → SERVICIO NEGATIVA
- Estado: **NO_CONFIRMADO** por `R-EST-NC`

## Caso 06 — AGENTE: «Mañana revisaremos TK-205»; CLIENTE: «Gracias».

- Origen: enunciado · archivo `casos/caso_06.txt`

**Sesión S01: OK**

| | Esperado | Obtenido |
|---|---|---|
| analisis | COMPLETO | COMPLETO |
| estado | PENDIENTE | PENDIENTE |
| SERVICIO | SIN_EVIDENCIA | SIN_EVIDENCIA |
| ATENCION | SIN_EVIDENCIA | SIN_EVIDENCIA |
| CLARIDAD | SIN_EVIDENCIA | SIN_EVIDENCIA |
| tickets | ['TK-205'] | ['TK-205'] |

Reglas activadas: `R-COMPR` (C1.1); `R-EST-PEND` (C1.1)

- C1.1 (AGENTE) «Mañana revisaremos TK-205» → COMPROMISO
- Estado: **PENDIENTE** por `R-EST-PEND`

## Caso 07 — Rol inválido SOPORTE entre dos mensajes válidos; luego otra sesión.

- Origen: enunciado · archivo `casos/caso_07.txt`

**Sesión S01: OK**

| | Esperado | Obtenido |
|---|---|---|
| analisis | PARCIAL | PARCIAL |
| estado | RESUELTO | RESUELTO |
| SERVICIO | MIXTA | MIXTA |
| ATENCION | SIN_EVIDENCIA | SIN_EVIDENCIA |
| CLARIDAD | SIN_EVIDENCIA | SIN_EVIDENCIA |
| errores | ['ROL_INVALIDO'] | ['ROL_INVALIDO'] |

Reglas activadas: `R-AHORA` (C3.1); `R-COP` (C1.1); `R-EST` (C3.1); `R-EST-RES` (C3.1); `R-SUJ` (C1.1)

- C1.1 (CLIENTE) «El servicio está lento» → SERVICIO NEGATIVA
- C3.1 (CLIENTE) «Ahora funciona bien» → SERVICIO POSITIVA, declaración OK
- Estado: **RESUELTO** por `R-EST-RES`

**Sesión S02: OK**

| | Esperado | Obtenido |
|---|---|---|
| analisis | COMPLETO | COMPLETO |
| estado | NO_RESUELTO | NO_RESUELTO |
| SERVICIO | NEGATIVA | NEGATIVA |
| ATENCION | SIN_EVIDENCIA | SIN_EVIDENCIA |
| CLARIDAD | SIN_EVIDENCIA | SIN_EVIDENCIA |

Reglas activadas: `R-EST-NORES` (C1.1); `R-SEG-SIN` (C1.1); `R-SIN` (C1.1)

- C1.1 (CLIENTE) «Sigo sin internet» → SERVICIO NEGATIVA, declaración FALLA
- Estado: **NO_RESUELTO** por `R-EST-NORES`

## Caso 08 — Con diccionario {lenta, lento}: CLIENTE «lent».

- Origen: enunciado · archivo `casos/caso_08.txt` · diccionario reducido `{"ADJ": {"LENTO": {"rasgos": {"pol": -1}, "formas": ["lenta", "lento"]}}}`

**Sesión S01: OK**

| | Esperado | Obtenido |
|---|---|---|
| analisis | COMPLETO | COMPLETO |
| estado | NO_CONFIRMADO | NO_CONFIRMADO |
| SERVICIO | SIN_EVIDENCIA | SIN_EVIDENCIA |
| ATENCION | SIN_EVIDENCIA | SIN_EVIDENCIA |
| CLARIDAD | SIN_EVIDENCIA | SIN_EVIDENCIA |
| correcciones | [['lent', 'lent', 'EMPATE']] | [['lent', 'lent', 'EMPATE']] |
| no_interpretado | ['lent'] | ['lent'] |

Reglas activadas: `R-EST-NC` (—)

- Estado: **NO_CONFIRMADO** por `R-EST-NC`

## Caso 09 — «El servicio no funciona, pero la atención fue excelente»; luego «Sigo sin internet».

- Origen: propio (negación y contraste) · archivo `casos/caso_09.txt`

**Sesión S01: OK**

| | Esperado | Obtenido |
|---|---|---|
| analisis | COMPLETO | COMPLETO |
| estado | NO_RESUELTO | NO_RESUELTO |
| SERVICIO | NEGATIVA | NEGATIVA |
| ATENCION | POSITIVA | POSITIVA |
| CLARIDAD | SIN_EVIDENCIA | SIN_EVIDENCIA |

Reglas activadas: `R-COP` (C1.2); `R-EST` (C1.1); `R-EST-NORES` (C3.1); `R-NEG` (C1.1); `R-PERO` (C1.2); `R-SEG-SIN` (C3.1); `R-SIN` (C3.1); `R-SUJ` (C1.1, C1.2)

- C1.1 (CLIENTE) «El servicio no funciona» → SERVICIO NEGATIVA, declaración FALLA
- C1.2 (CLIENTE) «la atención fue excelente» → ATENCION POSITIVA
- C3.1 (CLIENTE) «Sigo sin internet» → SERVICIO NEGATIVA, declaración FALLA
- Estado: **NO_RESUELTO** por `R-EST-NORES`

## Caso 10 — «inestabl» se corrige; el cliente confirma tras la promesa y el agente promete de nuevo: prevalece lo último (la promesa) → PENDIENTE.

- Origen: propio (corrección y precedencia) · archivo `casos/caso_10.txt`

**Sesión S01: OK**

| | Esperado | Obtenido |
|---|---|---|
| analisis | COMPLETO | COMPLETO |
| estado | PENDIENTE | PENDIENTE |
| SERVICIO | MIXTA | MIXTA |
| ATENCION | SIN_EVIDENCIA | SIN_EVIDENCIA |
| CLARIDAD | SIN_EVIDENCIA | SIN_EVIDENCIA |
| correcciones | [['inestabl', 'inestable', 'CORREGIDA']] | [['inestabl', 'inestable', 'CORREGIDA']] |
| tickets | ['TK-310'] | ['TK-310'] |

Reglas activadas: `R-AHORA` (C3.1); `R-COMPR` (C2.1, C4.1); `R-COP` (C1.1); `R-EST` (C3.1); `R-EST-PEND` (C4.1); `R-SUJ` (C1.1)

- C1.1 (CLIENTE) «La conexion esta inestabl» → SERVICIO NEGATIVA
- C2.1 (AGENTE) «Mañana revisaremos TK-310» → COMPROMISO
- C3.1 (CLIENTE) «Ahora funciona bien» → SERVICIO POSITIVA, declaración OK
- C4.1 (AGENTE) «Revisaremos TK-310» → COMPROMISO
- Estado: **PENDIENTE** por `R-EST-PEND` — R-EST-PREC: la promesa del agente (C4.1) es posterior a la última declaración del cliente (C3.1, que daba RESUELTO); prevalece lo último

## Caso 12 — Rol inválido (SOPORTE), ticket mal formado con error sintáctico y orden inconsistente (6 antes de 5): se descarta todo lo posterior; la sesión siguiente se analiza.

- Origen: propio (recuperación) · archivo `casos/caso_12.txt`

**Sesión S01: OK**

| | Esperado | Obtenido |
|---|---|---|
| analisis | PARCIAL | PARCIAL |
| estado | RESUELTO | RESUELTO |
| SERVICIO | MIXTA | MIXTA |
| ATENCION | SIN_EVIDENCIA | SIN_EVIDENCIA |
| CLARIDAD | SIN_EVIDENCIA | SIN_EVIDENCIA |
| errores | ['ORDEN_INCONSISTENTE', 'ROL_INVALIDO', 'SINTAXIS', 'TICKET_MAL_FORMADO', 'TURNO_DESCARTADO'] | ['ORDEN_INCONSISTENTE', 'ROL_INVALIDO', 'SINTAXIS', 'TICKET_MAL_FORMADO', 'TURNO_DESCARTADO'] |
| no_interpretado | ['TK-12', 'Ticket', 'respuesta', 'sin'] | ['TK-12', 'Ticket', 'respuesta', 'sin'] |

Reglas activadas: `R-AHORA` (C4.1); `R-COP` (C1.1); `R-EST` (C4.1); `R-EST-RES` (C4.1); `R-SUJ` (C1.1)

- C1.1 (CLIENTE) «El servicio está lento» → SERVICIO NEGATIVA
- C4.1 (CLIENTE) «Ahora funciona bien» → SERVICIO POSITIVA, declaración OK
- Estado: **RESUELTO** por `R-EST-RES`

**Sesión S02: OK**

| | Esperado | Obtenido |
|---|---|---|
| analisis | COMPLETO | COMPLETO |
| estado | NO_RESUELTO | NO_RESUELTO |
| SERVICIO | NEGATIVA | NEGATIVA |
| ATENCION | SIN_EVIDENCIA | SIN_EVIDENCIA |
| CLARIDAD | SIN_EVIDENCIA | SIN_EVIDENCIA |

Reglas activadas: `R-EST-NORES` (C1.1); `R-SEG-SIN` (C1.1); `R-SIN` (C1.1)

- C1.1 (CLIENTE) «Sigo sin internet» → SERVICIO NEGATIVA, declaración FALLA
- Estado: **NO_RESUELTO** por `R-EST-NORES`

## Caso 13 — «El internet sigue lento»; luego «Ahora funciona, pero el servicio se corta todos los días».

- Origen: propio (sujeto explícito + «sigue» / «se corta») · archivo `casos/caso_13.txt`

**Sesión S01: OK**

| | Esperado | Obtenido |
|---|---|---|
| analisis | COMPLETO | COMPLETO |
| estado | TEMPORAL | TEMPORAL |
| SERVICIO | MIXTA | MIXTA |
| ATENCION | SIN_EVIDENCIA | SIN_EVIDENCIA |
| CLARIDAD | SIN_EVIDENCIA | SIN_EVIDENCIA |

Reglas activadas: `R-AHORA` (C3.1); `R-CORTE` (C3.2); `R-EST` (C3.1); `R-EST-TEMP` (C3.1, C3.2); `R-PERO` (C3.2); `R-SEG-ADJ` (C1.1); `R-SUJ` (C1.1, C3.2)

- C1.1 (CLIENTE) «El internet sigue lento» → SERVICIO NEGATIVA, declaración FALLA
- C3.1 (CLIENTE) «Ahora funciona» → SERVICIO POSITIVA, declaración OK
- C3.2 (CLIENTE) «el servicio se corta todos los días» → SERVICIO NEGATIVA, declaración RECUR
- Estado: **TEMPORAL** por `R-EST-TEMP`

## Caso 14 — Salto de número (1, 3, 4): se conserva solo el 1 y se descarta todo lo posterior. Id de sesión repetido: la segunda S01 se descarta y no contamina la tabla de entidades.

- Origen: propio (recuperación de formato) · archivo `casos/caso_14.txt`

**Sesión S01: OK**

| | Esperado | Obtenido |
|---|---|---|
| analisis | PARCIAL | PARCIAL |
| estado | NO_RESUELTO | NO_RESUELTO |
| SERVICIO | NEGATIVA | NEGATIVA |
| ATENCION | SIN_EVIDENCIA | SIN_EVIDENCIA |
| CLARIDAD | SIN_EVIDENCIA | SIN_EVIDENCIA |
| errores | ['ORDEN_INCONSISTENTE', 'TURNO_DESCARTADO'] | ['ORDEN_INCONSISTENTE', 'TURNO_DESCARTADO'] |

Reglas activadas: `R-EST` (C1.1); `R-EST-NORES` (C1.1); `R-NEG` (C1.1)

- C1.1 (CLIENTE) «No funciona» → SERVICIO NEGATIVA, declaración FALLA
- Estado: **NO_RESUELTO** por `R-EST-NORES`

**Sesión S02: OK**

| | Esperado | Obtenido |
|---|---|---|
| analisis | COMPLETO | COMPLETO |
| estado | RESUELTO | RESUELTO |
| SERVICIO | POSITIVA | POSITIVA |
| ATENCION | SIN_EVIDENCIA | SIN_EVIDENCIA |
| CLARIDAD | SIN_EVIDENCIA | SIN_EVIDENCIA |

Reglas activadas: `R-EST-RES` (C1.1); `R-SEG-ADJ` (C1.1); `R-SUJ` (C1.1)

- C1.1 (CLIENTE) «El servicio sigue estable» → SERVICIO POSITIVA, declaración OK
- Estado: **RESUELTO** por `R-EST-RES`

## Caso 15 — Prevalece lo último: falla + promesa posterior → PENDIENTE; promesa + falla posterior → NO_RESUELTO; confirmación + promesa posterior → PENDIENTE.

- Origen: propio (precedencia: respuesta del profesor) · archivo `casos/caso_15.txt`

**Sesión S01: OK**

| | Esperado | Obtenido |
|---|---|---|
| analisis | COMPLETO | COMPLETO |
| estado | PENDIENTE | PENDIENTE |
| SERVICIO | NEGATIVA | NEGATIVA |
| ATENCION | SIN_EVIDENCIA | SIN_EVIDENCIA |
| CLARIDAD | SIN_EVIDENCIA | SIN_EVIDENCIA |
| tickets | ['TK-205'] | ['TK-205'] |

Reglas activadas: `R-COMPR` (C2.1); `R-EST-PEND` (C2.1); `R-SEG-SIN` (C1.1); `R-SIN` (C1.1)

- C1.1 (CLIENTE) «Sigo sin internet» → SERVICIO NEGATIVA, declaración FALLA
- C2.1 (AGENTE) «Mañana revisaremos TK-205» → COMPROMISO
- Estado: **PENDIENTE** por `R-EST-PEND` — R-EST-PREC: la promesa del agente (C2.1) es posterior a la última declaración del cliente (C1.1, que daba NO_RESUELTO); prevalece lo último

**Sesión S02: OK**

| | Esperado | Obtenido |
|---|---|---|
| analisis | COMPLETO | COMPLETO |
| estado | NO_RESUELTO | NO_RESUELTO |
| SERVICIO | NEGATIVA | NEGATIVA |
| ATENCION | SIN_EVIDENCIA | SIN_EVIDENCIA |
| CLARIDAD | SIN_EVIDENCIA | SIN_EVIDENCIA |
| tickets | ['TK-206'] | ['TK-206'] |

Reglas activadas: `R-COMPR` (C1.1); `R-EST-NORES` (C2.1); `R-SEG-SIN` (C2.1); `R-SIN` (C2.1)

- C1.1 (AGENTE) «Mañana revisaremos TK-206» → COMPROMISO
- C2.1 (CLIENTE) «Sigo sin internet» → SERVICIO NEGATIVA, declaración FALLA
- Estado: **NO_RESUELTO** por `R-EST-NORES` — R-EST-PREC: la declaración del cliente (C2.1) prevalece sobre la promesa del agente (C1.1)

**Sesión S03: OK**

| | Esperado | Obtenido |
|---|---|---|
| analisis | COMPLETO | COMPLETO |
| estado | PENDIENTE | PENDIENTE |
| SERVICIO | POSITIVA | POSITIVA |
| ATENCION | SIN_EVIDENCIA | SIN_EVIDENCIA |
| CLARIDAD | SIN_EVIDENCIA | SIN_EVIDENCIA |
| tickets | ['TK-207'] | ['TK-207'] |

Reglas activadas: `R-AHORA` (C1.1); `R-COMPR` (C2.1); `R-EST` (C1.1); `R-EST-PEND` (C2.1)

- C1.1 (CLIENTE) «Ahora funciona bien» → SERVICIO POSITIVA, declaración OK
- C2.1 (AGENTE) «Revisaremos TK-207» → COMPROMISO
- Estado: **PENDIENTE** por `R-EST-PEND` — R-EST-PREC: la promesa del agente (C2.1) es posterior a la última declaración del cliente (C1.1, que daba RESUELTO); prevalece lo último

## Caso 16 — Sujeto pospuesto, conector «y», router como sujeto, verbo de falla, negación de un verbo valorativo y «sin cortes»; en S02, sujeto y predicado incompatibles → abstención.

- Origen: propio (gramática por subcategorías) · archivo `casos/caso_16.txt`

**Sesión S01: OK**

| | Esperado | Obtenido |
|---|---|---|
| analisis | COMPLETO | COMPLETO |
| estado | RESUELTO | RESUELTO |
| SERVICIO | MIXTA | MIXTA |
| ATENCION | NEGATIVA | NEGATIVA |
| CLARIDAD | SIN_EVIDENCIA | SIN_EVIDENCIA |

Reglas activadas: `R-AHORA` (C3.2); `R-EST` (C1.1, C1.2, C3.2); `R-EST-RES` (C3.2); `R-NEG` (C1.1, C3.1); `R-PERO` (C3.2); `R-POSP` (C1.1); `R-SIN` (C3.2); `R-SUJ` (C1.2); `R-VAL` (C3.1)

- C1.1 (CLIENTE) «No funciona el internet» → SERVICIO NEGATIVA, declaración FALLA
- C1.2 (CLIENTE) «el router falla seguido» → SERVICIO NEGATIVA, declaración FALLA
- C3.1 (CLIENTE) «No me atendieron bien» → ATENCION NEGATIVA
- C3.2 (CLIENTE) «ahora funciona sin cortes» → SERVICIO POSITIVA, declaración OK
- Estado: **RESUELTO** por `R-EST-RES`

**Sesión S02: OK**

| | Esperado | Obtenido |
|---|---|---|
| analisis | COMPLETO | COMPLETO |
| estado | NO_CONFIRMADO | NO_CONFIRMADO |
| SERVICIO | SIN_EVIDENCIA | SIN_EVIDENCIA |
| ATENCION | SIN_EVIDENCIA | SIN_EVIDENCIA |
| CLARIDAD | SIN_EVIDENCIA | SIN_EVIDENCIA |
| no_interpretado | ['agente', 'bien', 'corta', 'explicación', 'funciona', 'se'] | ['agente', 'bien', 'corta', 'explicación', 'funciona', 'se'] |

Reglas activadas: `R-EST-NC` (—)

- Estado: **NO_CONFIRMADO** por `R-EST-NC`

## Caso 17 — El agente pide reiniciar el router (solicitud: no valora ni fija estado). En S01 el reinicio no resuelve: «No funciona, la conexion sigue lenta» → NO_RESUELTO; en S02 sí: «Ahora anda rapido» → RESUELTO.

- Origen: propio (alcance: lentitud y reinicio del router) · archivo `casos/caso_17.txt`

**Sesión S01: OK**

| | Esperado | Obtenido |
|---|---|---|
| analisis | COMPLETO | COMPLETO |
| estado | NO_RESUELTO | NO_RESUELTO |
| SERVICIO | NEGATIVA | NEGATIVA |
| ATENCION | SIN_EVIDENCIA | SIN_EVIDENCIA |
| CLARIDAD | SIN_EVIDENCIA | SIN_EVIDENCIA |

Reglas activadas: `R-COP` (C1.1); `R-EST` (C3.1); `R-EST-NORES` (C3.2); `R-MUY` (C1.1); `R-NEG` (C3.1); `R-SEG-ADJ` (C3.2); `R-SUJ` (C1.1, C3.2)

- C1.1 (CLIENTE) «La red esta muy lenta» → SERVICIO NEGATIVA
- C3.1 (CLIENTE) «No funciona» → SERVICIO NEGATIVA, declaración FALLA
- C3.2 (CLIENTE) «la conexion sigue lenta» → SERVICIO NEGATIVA, declaración FALLA
- Estado: **NO_RESUELTO** por `R-EST-NORES`

**Sesión S02: OK**

| | Esperado | Obtenido |
|---|---|---|
| analisis | COMPLETO | COMPLETO |
| estado | RESUELTO | RESUELTO |
| SERVICIO | MIXTA | MIXTA |
| ATENCION | SIN_EVIDENCIA | SIN_EVIDENCIA |
| CLARIDAD | SIN_EVIDENCIA | SIN_EVIDENCIA |

Reglas activadas: `R-AHORA` (C3.1); `R-EST` (C1.1, C3.1); `R-EST-RES` (C3.1); `R-SUJ` (C1.1)

- C1.1 (CLIENTE) «El modem anda lento» → SERVICIO NEGATIVA, declaración FALLA
- C3.1 (CLIENTE) «Ahora anda rapido» → SERVICIO POSITIVA, declaración OK
- Estado: **RESUELTO** por `R-EST-RES`

## Caso 18 — Cortes («se corta siempre»), ticket asignado y escalado (dos apariciones, una entrada con seguimiento COMPROMISO_FUTURO); la declaración posterior del cliente prevalece → NO_RESUELTO. S02 menciona el mismo TK-512: la tabla de entidades es por sesión (entrada propia) → PENDIENTE.

- Origen: propio (alcance: cortes y seguimiento de tickets) · archivo `casos/caso_18.txt`

**Sesión S01: OK**

| | Esperado | Obtenido |
|---|---|---|
| analisis | COMPLETO | COMPLETO |
| estado | NO_RESUELTO | NO_RESUELTO |
| SERVICIO | MIXTA | MIXTA |
| ATENCION | SIN_EVIDENCIA | SIN_EVIDENCIA |
| CLARIDAD | SIN_EVIDENCIA | SIN_EVIDENCIA |
| tickets | ['TK-512'] | ['TK-512'] |

Reglas activadas: `R-AHORA` (C4.1); `R-COMPR` (C3.1); `R-CORTE` (C1.1, C4.1); `R-EST-NORES` (C4.2); `R-NEG` (C4.1); `R-PERO` (C4.2); `R-SEG-ADJ` (C4.2); `R-SUJ` (C1.1, C4.2)

- C1.1 (CLIENTE) «El wifi se corta siempre» → SERVICIO NEGATIVA, declaración RECUR
- C3.1 (AGENTE) «Escalaremos TK-512» → COMPROMISO
- C4.1 (CLIENTE) «Ya no se corta» → SERVICIO POSITIVA
- C4.2 (CLIENTE) «la red sigue lenta» → SERVICIO NEGATIVA, declaración FALLA
- Estado: **NO_RESUELTO** por `R-EST-NORES` — R-EST-PREC: la declaración del cliente (C4.2) prevalece sobre la promesa del agente (C3.1)

**Sesión S02: OK**

| | Esperado | Obtenido |
|---|---|---|
| analisis | COMPLETO | COMPLETO |
| estado | PENDIENTE | PENDIENTE |
| SERVICIO | NEGATIVA | NEGATIVA |
| ATENCION | SIN_EVIDENCIA | SIN_EVIDENCIA |
| CLARIDAD | SIN_EVIDENCIA | SIN_EVIDENCIA |
| tickets | ['TK-512'] | ['TK-512'] |

Reglas activadas: `R-COMPR` (C2.1); `R-EST-PEND` (C2.1); `R-SEG-SIN` (C1.1); `R-SIN` (C1.1)

- C1.1 (CLIENTE) «Sigo sin conexion» → SERVICIO NEGATIVA, declaración FALLA
- C2.1 (AGENTE) «Mañana revisaremos TK-512» → COMPROMISO
- Estado: **PENDIENTE** por `R-EST-PEND` — R-EST-PREC: la promesa del agente (C2.1) es posterior a la última declaración del cliente (C1.1, que daba NO_RESUELTO); prevalece lo último

## Caso 19 — «intermitente» y «conecta» no están en el vocabulario. Se insertan como variantes de ADJ/INESTABLE y V_EST/FUNCIONAR; «conecta» se pregunta una sola vez y en el turno 3 ya se reconoce → SERVICIO MIXTA, RESUELTO. Sin consulta, las cláusulas del cliente no se interpretan.

- Origen: propio (alcance: falta de conexión; inserción en la tabla de símbolos léxica) · archivo `casos/caso_19.txt`

- Respuestas al menú (simuladas): `n #ADJ @ADJ/INESTABLE n #V_EST @V_EST/FUNCIONAR` — «intermitente»: n → ADJ → INESTABLE; «conecta»: n → V_EST → FUNCIONAR

**Sesión S01: OK**

| | Esperado | Obtenido |
|---|---|---|
| analisis | COMPLETO | COMPLETO |
| estado | RESUELTO | RESUELTO |
| SERVICIO | MIXTA | MIXTA |
| ATENCION | SIN_EVIDENCIA | SIN_EVIDENCIA |
| CLARIDAD | SIN_EVIDENCIA | SIN_EVIDENCIA |
| correcciones | [['conecta', 'conecta', 'INSERTADA'], ['intermitente', 'intermitente', 'INSERTADA']] | [['conecta', 'conecta', 'INSERTADA'], ['intermitente', 'intermitente', 'INSERTADA']] |

Reglas activadas: `R-AHORA` (C3.1); `R-COP` (C1.1); `R-EST` (C1.2, C3.1); `R-EST-RES` (C3.1); `R-NEG` (C1.2); `R-SUJ` (C1.1, C1.2)

- C1.1 (CLIENTE) «La conexion esta intermitente» → SERVICIO NEGATIVA
- C1.2 (CLIENTE) «el modem no conecta» → SERVICIO NEGATIVA, declaración FALLA
- C3.1 (CLIENTE) «Ahora conecta bien» → SERVICIO POSITIVA, declaración OK
- Estado: **RESUELTO** por `R-EST-RES`

**Consulta: OK** — se preguntó por: «intermitente», «conecta» (esperado: «intermitente», «conecta»)

**Sesión S01 sin consulta (regla del enunciado, solo precarga): OK**

| | Esperado | Obtenido |
|---|---|---|
| analisis | COMPLETO | COMPLETO |
| estado | NO_CONFIRMADO | NO_CONFIRMADO |
| SERVICIO | SIN_EVIDENCIA | SIN_EVIDENCIA |
| ATENCION | SIN_EVIDENCIA | SIN_EVIDENCIA |
| CLARIDAD | SIN_EVIDENCIA | SIN_EVIDENCIA |
| errores | ['SINTAXIS', 'SINTAXIS', 'SINTAXIS'] | ['SINTAXIS', 'SINTAXIS', 'SINTAXIS'] |
| no_interpretado | ['Ahora', 'bien', 'conecta', 'conecta', 'conexion', 'esta', 'intermitente', 'modem', 'no'] | ['Ahora', 'bien', 'conecta', 'conecta', 'conexion', 'esta', 'intermitente', 'modem', 'no'] |

## Caso 20 — «desconecta» y «verificaremos» no están en el vocabulario. Se crean las formas canónicas V_EST/DESCONECTAR (perfil RECUR, va con «se») y V_ACC/VERIFICAR (perfil COMPROMISO) → SERVICIO NEGATIVA (RECUR); la promesa sobre TK-620 es posterior → PENDIENTE. Sin consulta, el corte no se interpreta y la promesa queda como simple mención del ticket.

- Origen: propio (alcance: cortes y seguimiento de tickets; formas canónicas nuevas) · archivo `casos/caso_20.txt`

- Respuestas al menú (simuladas): `n #V_EST c desconectar %V_EST/RECUR n #V_ACC c verificar %V_ACC/COMPROMISO` — «desconecta»: n → V_EST → c (nueva) DESCONECTAR → perfil RECUR; «verificaremos»: n → V_ACC → c (nueva) VERIFICAR → perfil COMPROMISO

**Sesión S01: OK**

| | Esperado | Obtenido |
|---|---|---|
| analisis | COMPLETO | COMPLETO |
| estado | PENDIENTE | PENDIENTE |
| SERVICIO | NEGATIVA | NEGATIVA |
| ATENCION | SIN_EVIDENCIA | SIN_EVIDENCIA |
| CLARIDAD | SIN_EVIDENCIA | SIN_EVIDENCIA |
| correcciones | [['desconecta', 'desconecta', 'INSERTADA'], ['verificaremos', 'verificaremos', 'INSERTADA']] | [['desconecta', 'desconecta', 'INSERTADA'], ['verificaremos', 'verificaremos', 'INSERTADA']] |
| tickets | ['TK-620'] | ['TK-620'] |

Reglas activadas: `R-COMPR` (C3.1); `R-CORTE` (C1.1); `R-EST-PEND` (C3.1); `R-SUJ` (C1.1)

- C1.1 (CLIENTE) «El wifi se desconecta todos los dias» → SERVICIO NEGATIVA, declaración RECUR
- C3.1 (AGENTE) «Mañana verificaremos TK-620» → COMPROMISO
- Estado: **PENDIENTE** por `R-EST-PEND` — R-EST-PREC: la promesa del agente (C3.1) es posterior a la última declaración del cliente (C1.1, que daba NO_RESUELTO); prevalece lo último

**Consulta: OK** — se preguntó por: «desconecta», «verificaremos» (esperado: «desconecta», «verificaremos»)

**Sesión S01 sin consulta (regla del enunciado, solo precarga): OK**

| | Esperado | Obtenido |
|---|---|---|
| analisis | COMPLETO | COMPLETO |
| estado | NO_CONFIRMADO | NO_CONFIRMADO |
| SERVICIO | SIN_EVIDENCIA | SIN_EVIDENCIA |
| ATENCION | SIN_EVIDENCIA | SIN_EVIDENCIA |
| CLARIDAD | SIN_EVIDENCIA | SIN_EVIDENCIA |
| tickets | ['TK-620'] | ['TK-620'] |
| errores | ['SINTAXIS'] | ['SINTAXIS'] |
| no_interpretado | ['desconecta', 'dias', 'se', 'todos', 'verificaremos', 'wifi'] | ['desconecta', 'dias', 'se', 'todos', 'verificaremos', 'wifi'] |
