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

Reglas activadas: `R-AHORA` (C3.1); `R-COP` (C1.1); `R-EST-RES` (C3.1); `R-FUNC` (C3.1); `R-SUJ` (C1.1)

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

Reglas activadas: `R-COP` (C1.1); `R-EST-NORES` (C1.2); `R-MUY` (C1.1); `R-PERO` (C1.2); `R-SEG-SIN` (C1.2); `R-SUJ` (C1.1)

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

Reglas activadas: `R-AHORA` (C1.1); `R-CORTE` (C1.2); `R-EST-TEMP` (C1.1, C1.2); `R-FUNC` (C1.1); `R-PERO` (C1.2)

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

Reglas activadas: `R-AHORA` (C3.1); `R-COP` (C1.1); `R-EST-RES` (C3.1); `R-FUNC` (C3.1); `R-SUJ` (C1.1)

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

Reglas activadas: `R-EST-NORES` (C1.1); `R-SEG-SIN` (C1.1)

- C1.1 (CLIENTE) «Sigo sin internet» → SERVICIO NEGATIVA, declaración FALLA
- Estado: **NO_RESUELTO** por `R-EST-NORES`

## Caso 08 — Con diccionario {lenta, lento}: CLIENTE «lent».

- Origen: enunciado · archivo `casos/caso_08.txt` · diccionario `casos/caso_08.vocab.json`

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

Reglas activadas: `R-COP` (C1.2); `R-EST-NORES` (C3.1); `R-FUNC` (C1.1); `R-NEG` (C1.1); `R-PERO` (C1.2); `R-SEG-SIN` (C3.1); `R-SUJ` (C1.1, C1.2)

- C1.1 (CLIENTE) «El servicio no funciona» → SERVICIO NEGATIVA, declaración FALLA
- C1.2 (CLIENTE) «la atención fue excelente» → ATENCION POSITIVA
- C3.1 (CLIENTE) «Sigo sin internet» → SERVICIO NEGATIVA, declaración FALLA
- Estado: **NO_RESUELTO** por `R-EST-NORES`

## Caso 10 — «inestabl» se corrige; el cliente confirma tras la promesa y el agente promete de nuevo.

- Origen: propio (corrección y precedencia) · archivo `casos/caso_10.txt`

**Sesión S01: OK**

| | Esperado | Obtenido |
|---|---|---|
| analisis | COMPLETO | COMPLETO |
| estado | RESUELTO | RESUELTO |
| SERVICIO | MIXTA | MIXTA |
| ATENCION | SIN_EVIDENCIA | SIN_EVIDENCIA |
| CLARIDAD | SIN_EVIDENCIA | SIN_EVIDENCIA |
| correcciones | [['inestabl', 'inestable', 'CORREGIDA']] | [['inestabl', 'inestable', 'CORREGIDA']] |
| tickets | ['TK-310'] | ['TK-310'] |

Reglas activadas: `R-AHORA` (C3.1); `R-COMPR` (C2.1, C4.1); `R-COP` (C1.1); `R-EST-RES` (C3.1); `R-FUNC` (C3.1); `R-SUJ` (C1.1)

- C1.1 (CLIENTE) «La conexion esta inestabl» → SERVICIO NEGATIVA
- C2.1 (AGENTE) «Mañana revisaremos TK-310» → COMPROMISO
- C3.1 (CLIENTE) «Ahora funciona bien» → SERVICIO POSITIVA, declaración OK
- C4.1 (AGENTE) «Revisaremos TK-310» → COMPROMISO
- Estado: **RESUELTO** por `R-EST-RES` — R-EST-PREC: la declaración del cliente (C3.1) prevalece sobre la promesa del agente (C4.1)

## Caso 11 — Palabras y fragmentos fuera de la gramática: no se inventa valoración.

- Origen: propio (abstención) · archivo `casos/caso_11.txt`

**Sesión S01: OK**

| | Esperado | Obtenido |
|---|---|---|
| analisis | COMPLETO | COMPLETO |
| estado | NO_CONFIRMADO | NO_CONFIRMADO |
| SERVICIO | SIN_EVIDENCIA | SIN_EVIDENCIA |
| ATENCION | SIN_EVIDENCIA | SIN_EVIDENCIA |
| CLARIDAD | SIN_EVIDENCIA | SIN_EVIDENCIA |
| errores | ['SINTAXIS'] | ['SINTAXIS'] |
| no_interpretado | ['Muchas', 'hace', 'raros', 'router', 'ruidos'] | ['Muchas', 'hace', 'raros', 'router', 'ruidos'] |

Reglas activadas: `R-EST-NC` (—)

- Estado: **NO_CONFIRMADO** por `R-EST-NC`

## Caso 12 — Orden inconsistente, rol inválido, ticket mal formado y error sintáctico; la sesión siguiente se analiza.

- Origen: propio (recuperación) · archivo `casos/caso_12.txt`

**Sesión S01: OK**

| | Esperado | Obtenido |
|---|---|---|
| analisis | PARCIAL | PARCIAL |
| estado | RESUELTO | RESUELTO |
| SERVICIO | POSITIVA | POSITIVA |
| ATENCION | SIN_EVIDENCIA | SIN_EVIDENCIA |
| CLARIDAD | SIN_EVIDENCIA | SIN_EVIDENCIA |
| errores | ['ORDEN_INCONSISTENTE', 'ROL_INVALIDO', 'SINTAXIS', 'TICKET_MAL_FORMADO'] | ['ORDEN_INCONSISTENTE', 'ROL_INVALIDO', 'SINTAXIS', 'TICKET_MAL_FORMADO'] |
| no_interpretado | ['TK-12', 'Ticket', 'respuesta', 'sin'] | ['TK-12', 'Ticket', 'respuesta', 'sin'] |

Reglas activadas: `R-AHORA` (C3.1); `R-EST-RES` (C3.1); `R-FUNC` (C3.1)

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

Reglas activadas: `R-EST-NORES` (C1.1); `R-SEG-SIN` (C1.1)

- C1.1 (CLIENTE) «Sigo sin internet» → SERVICIO NEGATIVA, declaración FALLA
- Estado: **NO_RESUELTO** por `R-EST-NORES`
