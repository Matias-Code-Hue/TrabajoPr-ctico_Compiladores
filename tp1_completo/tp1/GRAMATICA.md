# TP1 · Gramática BNF, PRIM/SGTE y verificación LL(1)

Archivo de apoyo: `gramatica.py` (calcula PRIM, SGTE, tabla LL(1) y verifica conflictos; `python3 gramatica.py`).
Los **terminales** son las categorías del analizador léxico (ver `INFORME_lexico.md`), más `EOL` (fin de línea) y `$` (fin de lote).
`<x>` es una variable sintáctica; `ε` es la cadena vacía.

## 1. Gramática de formato

Describe el archivo (sesiones y turnos). El lector `lector.py` la implementa línea a línea: cada `EOL` es un
punto de sincronización, de modo que un turno inválido se rechaza y el análisis continúa en la línea siguiente.

```
<lote> ::= <sesion> <lote_r>
<lote_r> ::= <sesion> <lote_r> | ε
<sesion> ::= KW_SESION ID_SESION EOL <turnos> KW_FIN EOL
<turnos> ::= <turno> <turnos_r>
<turnos_r> ::= <turno> <turnos_r> | ε
<turno> ::= NUM <rol> DOSPUNTOS <texto> EOL
<rol> ::= CLIENTE | AGENTE
```

Se admiten sesiones con solo `CLIENTE` (la gramática no exige alternancia de roles).
El número de turno consecutivo y la no vacuidad del texto son restricciones de contexto que verifica el lector,
porque una BNF libre de contexto no puede expresar «n+1».

## 2. Gramática lingüística (texto de un turno)

Antes del parser, el filtro de tokens elimina `RELLENO` y `SIGNO` (sin semántica) y aparta las `PALABRA`,
`TICKET_MAL`, `NUM` y `DESCONOCIDO` como **NO_INTERPRETADOS**; no se inventa valoración para ellos.

```
<texto> ::= <oracion> <texto_r>
<texto_r> ::= PUNTO <texto_rr> | ε
<texto_rr> ::= <oracion> <texto_r> | ε
<oracion> ::= <clausula> <cola>
<cola> ::= PERO <clausula> <cola> | COMA <cola_c> | ε
<cola_c> ::= PERO <clausula> <cola> | <clausula> <cola>
<clausula> ::= <ahora_op> <nucleo>
<ahora_op> ::= T_AHORA | ε
<nucleo> ::= <sujeto> <pred_s> | <pred_l> | TICKET_PAL <tk_op> | TICKET | CORTESIA
<sujeto> ::= ASP_SERV | ASP_ATEN | ASP_CLAR | AGENTE
<pred_s> ::= NEG <pred_neg> | V_COPULA <modif> | V_FUNC <modif_op> | V_SEGUIR <seg> | SE V_CORTA <frec> | <modif> | ε
<pred_l> ::= NEG <pred_neg> | V_FUNC <modif_op> | V_SEGUIR <seg> | SE V_CORTA <frec> | V_ENTENDER <obj_clar> | V_SOLICITUD <obj_router> | T_FUTURO V_COMPROMISO <ref_op> | V_COMPROMISO <ref_op>
<pred_neg> ::= V_FUNC <modif_op> | V_COPULA <modif> | V_ENTENDER <obj_clar>
<seg> ::= <modif> | NEG ASP_SERV
<modif> ::= INT <adj> | <adj>
<modif_op> ::= <modif> | ε
<adj> ::= ADJ_POS | ADJ_NEG
<frec> ::= FREC <frec> | ε
<obj_clar> ::= ASP_CLAR | ε
<obj_router> ::= ROUTER | ε
<ref_op> ::= TICKET | T_FUTURO | ε
<tk_op> ::= V_COPULA TICKET | TICKET | ε
```

### 2.1 Cobertura de los casos guía

| Frase | Derivación (resumen) |
|---|---|
| «El servicio está lento.» | `sujeto(ASP_SERV)` `pred_s → V_COPULA modif → adj(ADJ_NEG)` |
| «Ahora funciona bien.» | `ahora_op(T_AHORA)` `pred_l → V_FUNC modif_op → adj(ADJ_POS)` |
| «Me atendiste muy bien, pero sigo sin internet.» | `sujeto(ASP_ATEN)` `pred_s → modif → INT adj` · `cola → COMA cola_c → PERO clausula` · `pred_l → V_SEGUIR seg → NEG ASP_SERV` |
| «El internet sigue lento.» | `sujeto(ASP_SERV)` `pred_s → V_SEGUIR seg → modif → adj(ADJ_NEG)` |
| «El servicio se corta todos los días.» | `sujeto(ASP_SERV)` `pred_s → SE V_CORTA frec` (`FREC FREC`) |
| «Ahora funciona, pero se corta todos los días.» | `V_FUNC modif_op(ε)` · `PERO` · `pred_l → SE V_CORTA frec` (`FREC FREC`) |
| «No entendí la explicación, pero el agente fue amable.» | `pred_l → NEG pred_neg → V_ENTENDER obj_clar(ASP_CLAR)` · `sujeto(AGENTE) pred_s → V_COPULA modif` |
| «Mañana revisaremos TK-205.» | `pred_l → T_FUTURO V_COMPROMISO ref_op(TICKET)` |
| «Reinicie el router.» | `pred_l → V_SOLICITUD obj_router(ROUTER)` |
| «Gracias.» | `nucleo → CORTESIA` |

### 2.2 Cómo se llegó a la forma predictiva

La gramática de esta sección es el **resultado final** (L3) de tres transformaciones aplicadas sobre una gramática
descriptiva original: (1) eliminación de la recursión por la izquierda, (2) factorización por la izquierda y
(3) resolución de un conflicto PRIM∩SGTE con simplificación por sustitución. Los pasos intermedios, con el
diagnóstico calculado de cada gramática y la verificación de que todas generan el mismo lenguaje, están en
**`DERIVACION.md`** (`python3 derivacion.py`).

Decisión de diseño asociada: se exige `PUNTO` *entre* oraciones. Si se admitieran oraciones sin separador,
`NEG` pertenecería a PRIM(`oracion`) y a SGTE(`pred_s`) y aparecería un conflicto en `pred_s → ε`.

## 3. PRIM y SGTE

| Variable | PRIM | SGTE |
|---|---|---|
| `<lote>` | {KW_SESION} | {$} |
| `<lote_r>` | {KW_SESION, ε} | {$} |
| `<sesion>` | {KW_SESION} | {$, KW_SESION} |
| `<turnos>` | {NUM} | {KW_FIN} |
| `<turnos_r>` | {NUM, ε} | {KW_FIN} |
| `<turno>` | {NUM} | {KW_FIN, NUM} |
| `<rol>` | {AGENTE, CLIENTE} | {DOSPUNTOS} |
| `<texto>` | {AGENTE, ASP_ATEN, ASP_CLAR, ASP_SERV, CORTESIA, NEG, SE, TICKET, TICKET_PAL, T_AHORA, T_FUTURO, V_COMPROMISO, V_ENTENDER, V_FUNC, V_SEGUIR, V_SOLICITUD} | {EOL} |
| `<texto_r>` | {PUNTO, ε} | {EOL} |
| `<texto_rr>` | {AGENTE, ASP_ATEN, ASP_CLAR, ASP_SERV, CORTESIA, NEG, SE, TICKET, TICKET_PAL, T_AHORA, T_FUTURO, V_COMPROMISO, V_ENTENDER, V_FUNC, V_SEGUIR, V_SOLICITUD, ε} | {EOL} |
| `<oracion>` | {AGENTE, ASP_ATEN, ASP_CLAR, ASP_SERV, CORTESIA, NEG, SE, TICKET, TICKET_PAL, T_AHORA, T_FUTURO, V_COMPROMISO, V_ENTENDER, V_FUNC, V_SEGUIR, V_SOLICITUD} | {EOL, PUNTO} |
| `<cola>` | {COMA, PERO, ε} | {EOL, PUNTO} |
| `<cola_c>` | {AGENTE, ASP_ATEN, ASP_CLAR, ASP_SERV, CORTESIA, NEG, PERO, SE, TICKET, TICKET_PAL, T_AHORA, T_FUTURO, V_COMPROMISO, V_ENTENDER, V_FUNC, V_SEGUIR, V_SOLICITUD} | {EOL, PUNTO} |
| `<clausula>` | {AGENTE, ASP_ATEN, ASP_CLAR, ASP_SERV, CORTESIA, NEG, SE, TICKET, TICKET_PAL, T_AHORA, T_FUTURO, V_COMPROMISO, V_ENTENDER, V_FUNC, V_SEGUIR, V_SOLICITUD} | {COMA, EOL, PERO, PUNTO} |
| `<ahora_op>` | {T_AHORA, ε} | {AGENTE, ASP_ATEN, ASP_CLAR, ASP_SERV, CORTESIA, NEG, SE, TICKET, TICKET_PAL, T_FUTURO, V_COMPROMISO, V_ENTENDER, V_FUNC, V_SEGUIR, V_SOLICITUD} |
| `<nucleo>` | {AGENTE, ASP_ATEN, ASP_CLAR, ASP_SERV, CORTESIA, NEG, SE, TICKET, TICKET_PAL, T_FUTURO, V_COMPROMISO, V_ENTENDER, V_FUNC, V_SEGUIR, V_SOLICITUD} | {COMA, EOL, PERO, PUNTO} |
| `<sujeto>` | {AGENTE, ASP_ATEN, ASP_CLAR, ASP_SERV} | {ADJ_NEG, ADJ_POS, COMA, EOL, INT, NEG, PERO, PUNTO, SE, V_COPULA, V_FUNC, V_SEGUIR} |
| `<pred_s>` | {ADJ_NEG, ADJ_POS, INT, NEG, SE, V_COPULA, V_FUNC, V_SEGUIR, ε} | {COMA, EOL, PERO, PUNTO} |
| `<pred_l>` | {NEG, SE, T_FUTURO, V_COMPROMISO, V_ENTENDER, V_FUNC, V_SEGUIR, V_SOLICITUD} | {COMA, EOL, PERO, PUNTO} |
| `<pred_neg>` | {V_COPULA, V_ENTENDER, V_FUNC} | {COMA, EOL, PERO, PUNTO} |
| `<seg>` | {ADJ_NEG, ADJ_POS, INT, NEG} | {COMA, EOL, PERO, PUNTO} |
| `<modif>` | {ADJ_NEG, ADJ_POS, INT} | {COMA, EOL, PERO, PUNTO} |
| `<modif_op>` | {ADJ_NEG, ADJ_POS, INT, ε} | {COMA, EOL, PERO, PUNTO} |
| `<adj>` | {ADJ_NEG, ADJ_POS} | {COMA, EOL, PERO, PUNTO} |
| `<frec>` | {FREC, ε} | {COMA, EOL, PERO, PUNTO} |
| `<obj_clar>` | {ASP_CLAR, ε} | {COMA, EOL, PERO, PUNTO} |
| `<obj_router>` | {ROUTER, ε} | {COMA, EOL, PERO, PUNTO} |
| `<ref_op>` | {TICKET, T_FUTURO, ε} | {COMA, EOL, PERO, PUNTO} |
| `<tk_op>` | {TICKET, V_COPULA, ε} | {COMA, EOL, PERO, PUNTO} |

## 4. Verificación LL(1)

Condiciones comprobadas por `verificar_ll1()`:

1. No hay recursión por la izquierda (directa ni indirecta).
2. Para cada variable, los PRIM de sus alternativas son **disjuntos** (sin factor común directo ni indirecto).
3. Si una alternativa deriva `ε`, su SGTE es disjunto de los PRIM de las demás, y hay como máximo una alternativa anulable.

**Resultado: ningún conflicto.** La gramática es LL(1) y la tabla predictiva tiene 199 celdas sin colisiones.

### 4.1 Decisiones del parser (variables con más de una alternativa)

| Variable | Alternativa | PRIM de la alternativa (token de decisión) |
|---|---|---|
| `<lote_r>` | <sesion> <lote_r> | {KW_SESION} |
| `<lote_r>` | ε | se elige con SGTE(`<lote_r>`) = {$} |
| `<turnos_r>` | <turno> <turnos_r> | {NUM} |
| `<turnos_r>` | ε | se elige con SGTE(`<turnos_r>`) = {KW_FIN} |
| `<rol>` | CLIENTE | {CLIENTE} |
| `<rol>` | AGENTE | {AGENTE} |
| `<texto_r>` | PUNTO <texto_rr> | {PUNTO} |
| `<texto_r>` | ε | se elige con SGTE(`<texto_r>`) = {EOL} |
| `<texto_rr>` | <oracion> <texto_r> | {AGENTE, ASP_ATEN, ASP_CLAR, ASP_SERV, CORTESIA, NEG, SE, TICKET, TICKET_PAL, T_AHORA, T_FUTURO, V_COMPROMISO, V_ENTENDER, V_FUNC, V_SEGUIR, V_SOLICITUD} |
| `<texto_rr>` | ε | se elige con SGTE(`<texto_rr>`) = {EOL} |
| `<cola>` | PERO <clausula> <cola> | {PERO} |
| `<cola>` | COMA <cola_c> | {COMA} |
| `<cola>` | ε | se elige con SGTE(`<cola>`) = {EOL, PUNTO} |
| `<cola_c>` | PERO <clausula> <cola> | {PERO} |
| `<cola_c>` | <clausula> <cola> | {AGENTE, ASP_ATEN, ASP_CLAR, ASP_SERV, CORTESIA, NEG, SE, TICKET, TICKET_PAL, T_AHORA, T_FUTURO, V_COMPROMISO, V_ENTENDER, V_FUNC, V_SEGUIR, V_SOLICITUD} |
| `<ahora_op>` | T_AHORA | {T_AHORA} |
| `<ahora_op>` | ε | se elige con SGTE(`<ahora_op>`) = {AGENTE, ASP_ATEN, ASP_CLAR, ASP_SERV, CORTESIA, NEG, SE, TICKET, TICKET_PAL, T_FUTURO, V_COMPROMISO, V_ENTENDER, V_FUNC, V_SEGUIR, V_SOLICITUD} |
| `<nucleo>` | <sujeto> <pred_s> | {AGENTE, ASP_ATEN, ASP_CLAR, ASP_SERV} |
| `<nucleo>` | <pred_l> | {NEG, SE, T_FUTURO, V_COMPROMISO, V_ENTENDER, V_FUNC, V_SEGUIR, V_SOLICITUD} |
| `<nucleo>` | TICKET_PAL <tk_op> | {TICKET_PAL} |
| `<nucleo>` | TICKET | {TICKET} |
| `<nucleo>` | CORTESIA | {CORTESIA} |
| `<sujeto>` | ASP_SERV | {ASP_SERV} |
| `<sujeto>` | ASP_ATEN | {ASP_ATEN} |
| `<sujeto>` | ASP_CLAR | {ASP_CLAR} |
| `<sujeto>` | AGENTE | {AGENTE} |
| `<pred_s>` | NEG <pred_neg> | {NEG} |
| `<pred_s>` | V_COPULA <modif> | {V_COPULA} |
| `<pred_s>` | V_FUNC <modif_op> | {V_FUNC} |
| `<pred_s>` | V_SEGUIR <seg> | {V_SEGUIR} |
| `<pred_s>` | SE V_CORTA <frec> | {SE} |
| `<pred_s>` | <modif> | {ADJ_NEG, ADJ_POS, INT} |
| `<pred_s>` | ε | se elige con SGTE(`<pred_s>`) = {COMA, EOL, PERO, PUNTO} |
| `<pred_l>` | NEG <pred_neg> | {NEG} |
| `<pred_l>` | V_FUNC <modif_op> | {V_FUNC} |
| `<pred_l>` | V_SEGUIR <seg> | {V_SEGUIR} |
| `<pred_l>` | SE V_CORTA <frec> | {SE} |
| `<pred_l>` | V_ENTENDER <obj_clar> | {V_ENTENDER} |
| `<pred_l>` | V_SOLICITUD <obj_router> | {V_SOLICITUD} |
| `<pred_l>` | T_FUTURO V_COMPROMISO <ref_op> | {T_FUTURO} |
| `<pred_l>` | V_COMPROMISO <ref_op> | {V_COMPROMISO} |
| `<pred_neg>` | V_FUNC <modif_op> | {V_FUNC} |
| `<pred_neg>` | V_COPULA <modif> | {V_COPULA} |
| `<pred_neg>` | V_ENTENDER <obj_clar> | {V_ENTENDER} |
| `<seg>` | <modif> | {ADJ_NEG, ADJ_POS, INT} |
| `<seg>` | NEG ASP_SERV | {NEG} |
| `<modif>` | INT <adj> | {INT} |
| `<modif>` | <adj> | {ADJ_NEG, ADJ_POS} |
| `<modif_op>` | <modif> | {ADJ_NEG, ADJ_POS, INT} |
| `<modif_op>` | ε | se elige con SGTE(`<modif_op>`) = {COMA, EOL, PERO, PUNTO} |
| `<adj>` | ADJ_POS | {ADJ_POS} |
| `<adj>` | ADJ_NEG | {ADJ_NEG} |
| `<frec>` | FREC <frec> | {FREC} |
| `<frec>` | ε | se elige con SGTE(`<frec>`) = {COMA, EOL, PERO, PUNTO} |
| `<obj_clar>` | ASP_CLAR | {ASP_CLAR} |
| `<obj_clar>` | ε | se elige con SGTE(`<obj_clar>`) = {COMA, EOL, PERO, PUNTO} |
| `<obj_router>` | ROUTER | {ROUTER} |
| `<obj_router>` | ε | se elige con SGTE(`<obj_router>`) = {COMA, EOL, PERO, PUNTO} |
| `<ref_op>` | TICKET | {TICKET} |
| `<ref_op>` | T_FUTURO | {T_FUTURO} |
| `<ref_op>` | ε | se elige con SGTE(`<ref_op>`) = {COMA, EOL, PERO, PUNTO} |
| `<tk_op>` | V_COPULA TICKET | {V_COPULA} |
| `<tk_op>` | TICKET | {TICKET} |
| `<tk_op>` | ε | se elige con SGTE(`<tk_op>`) = {COMA, EOL, PERO, PUNTO} |

## 5. Alcance de la negación y de la intensificación (decisión de diseño)

El alcance **queda determinado por la gramática**, no por una heurística:

- `NEG` solo aparece al inicio de `pred_neg` (o en `seg → NEG ASP_SERV`). Su alcance es **exactamente** el predicado
  o el sustantivo que lo sigue dentro de la misma cláusula: «no funciona», «no está lento», «sin internet».
- `NEG` **no cruza** `PERO` ni `COMA`: cada cláusula es una derivación independiente de `clausula`, por eso
  «No entendí la explicación, pero el agente fue amable» conserva CLARIDAD negativa y ATENCION positiva por separado.
- `INT` (muy) solo aparece en `modif → INT adj`: intensifica únicamente al adjetivo inmediato.

## 6. Parser y recuperación de errores (implementado en `sintaxis.py`)

**Parser.** Descendente recursivo predictivo: un único procedimiento `parse(A)` consulta la tabla `M[A, a]`
(Clase 7, §7.5) con el token de anticipación `a`, emite la producción elegida, llama a `parse()` por cada variable
del cuerpo y a `_match()` por cada terminal (el `match()` de clase). Es el mismo algoritmo del analizador sintáctico
predictivo de la Clase 8 (§8.2): la pila explícita se reemplaza por la pila de llamadas, lo que permite devolver el
árbol de derivación sobre el que luego se evalúan las reglas semánticas (`REGLAS_SEMANTICAS.md`).
Dentro de un turno, `EOL` cumple el papel de `$`.

**Recuperación** (Clase 8, §8.5.4), con sincronización en SGTE:

| Situación | Acción de clase | En `sintaxis.py` |
|---|---|---|
| Tope terminal ≠ token | informar y desapilar el terminal esperado | `_match()` registra el error y no consume entrada |
| `M[A, a]` vacía y `a ∉ SGTE(A)` | informar y descartar el token | `parse()` descarta tokens hasta uno de PRIM(A) ∪ SGTE(A) ∪ {EOL} |
| `M[A, a]` = *sinc* (`a ∈ SGTE(A)`) | informar y desapilar `A` sin consumir | `parse()` abandona `A` (nodo `A!ERROR`) |
| Fin de entrada | terminar | `EOL` pertenece a todo conjunto de sincronización: el descarte siempre termina |

Diferencia con el pseudocódigo de clase: se informa **un** error por cada celda vacía (no uno por token descartado).
Los tokens descartados y la cláusula que contiene el error se marcan `NO_INTERPRETADO`; el resto del turno se
sigue analizando. Para ver cada decisión: `python3 main.py casos/caso_12.txt --traza S01 --detalle`.
