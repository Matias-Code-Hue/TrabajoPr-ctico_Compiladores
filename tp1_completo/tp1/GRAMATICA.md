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
<sesion> ::= SESION ID_SESION EOL <turnos> FIN EOL
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
`TICKET_MAL`, `NUM`, `DESCONOCIDO` y `FUERA_DE_GRAMATICA` como **NO_INTERPRETADOS**; no se inventa valoración para ellos.

```
<texto> ::= <oracion> <texto_r>
<texto_r> ::= PUNTO <texto_rr> | ε
<texto_rr> ::= <oracion> <texto_r> | ε
<oracion> ::= <clausula> <cola>
<cola> ::= PERO <clausula> <cola> | COMA <cola_c> | Y <clausula> <cola> | ε
<cola_c> ::= PERO <clausula> <cola> | <clausula> <cola>
<clausula> ::= <adv_t_op> <nucleo> <frec>
<adv_t_op> ::= ADV_T | ε
<nucleo> ::= <sujeto> <pred_s> | <pred_l> | TICKET | CORTESIA
<sujeto> ::= SUST | AGENTE
<pred_s> ::= NEG <pred_neg> | V_COP <atrib> | V_EST <compl> | SE V_EST <compl> | V_CONT <compl> | V_ACC <obj> <modif_op> | <modif> | TICKET | ε
<pred_l> ::= NEG <pred_neg> | V_COP <atrib> | V_EST <compl> <sujp> | SE V_EST <compl> <sujp> | V_CONT <compl> | V_ACC <obj> <modif_op>
<pred_neg> ::= V_COP <atrib> | V_EST <compl> <sujp> | SE V_EST <compl> <sujp> | V_CONT <compl> | V_ACC <obj> <modif_op>
<atrib> ::= <modif> | TICKET
<compl> ::= <modif> | SIN SUST | ε
<sujp> ::= SUST | ε
<obj> ::= SUST | TICKET | ADV_T | ε
<modif> ::= INT ADJ | ADJ
<modif_op> ::= <modif> | ε
<frec> ::= FREC <frec> | ε
```

La gramática describe **construcciones** con categorías léxicas generales (`SUST`, `ADJ`, `V_EST`, `V_ACC`, `ADV_T`…).
No distingue qué significa cada palabra: eso lo dice el **perfil** de su forma canónica, que las reglas semánticas
consultan (ver `REGLAS_SEMANTICAS.md` §3). Por eso una palabra nueva solo necesita su categoría y su forma canónica
(existente, o nueva de un perfil existente): la tabla de símbolos léxica se enriquece sin tocar la gramática.

### 2.1 Qué significa cada no terminal

| No terminal | Significado |
|---|---|
| `texto` / `texto_r` / `texto_rr` | texto de un turno / resto después de una oración / resto después de un `PUNTO` |
| `oracion` / `cola` / `cola_c` | oración: cláusulas unidas por `COMA`, `PERO` o `Y` / resto de la oración / resto después de una `COMA` |
| `clausula` | unidad mínima que se interpreta: marca temporal opcional, núcleo y frecuencia opcional |
| `adv_t_op` | marca temporal opcional al inicio («ahora», «mañana») |
| `nucleo` | contenido de la cláusula: sujeto y predicado, predicado solo, un ticket o una cortesía |
| `sujeto` | de qué se habla: un sustantivo o «el agente» |
| `pred_s` | predicado que **sigue a un sujeto explícito** |
| `pred_l` | predicado **sin sujeto delante** (sujeto tácito o pospuesto) |
| `pred_neg` | predicado dentro del alcance de `NEG` |
| `atrib` | lo que sigue a una cópula: una cualidad o un ticket («es TK-204») |
| `compl` | complemento de un verbo de estado o de «seguir»: una cualidad, «sin» + sustantivo, o nada |
| `sujp` | sujeto después del verbo («no funciona **el internet**») |
| `obj` | objeto de un verbo de acción: sustantivo, ticket, plazo, o nada |
| `modif` / `modif_op` | cualidad con o sin intensificador / opcional |
| `frec` | expresión de frecuencia («todos los días») |
Los verbos se agrupan por **cómo se construyen**, no por palabra: `V_COP` (ser/estar + cualidad), `V_EST` (solo o con
complemento, y con o sin «se»), `V_CONT` (seguir + complemento) y `V_ACC` (con objeto). Que «corta» exija «se» y
«funciona» no lo admita depende del perfil (RECUR frente a OK y FALLA), así que lo verifica la semántica (R-COMPAT).

### 2.2 Cobertura de los casos guía y de las construcciones nuevas

| Frase | Derivación (resumen) |
|---|---|
| «El servicio está lento.» | `sujeto → SUST«servicio»` · `pred_s → V_COP atrib → modif → ADJ«lento»` |
| «Ahora funciona bien.» | `adv_t_op → ADV_T«ahora»` · `pred_l → V_EST«funciona» compl(modif) sujp(ε)` |
| «Me atendiste muy bien, pero sigo sin internet.» | `pred_l → V_ACC«atendiste» obj(ε) modif_op(INT ADJ)` · `cola → COMA cola_c → PERO clausula` · `pred_l → V_CONT compl → SIN SUST` |
| «Ahora funciona, pero se corta todos los días.» | `V_EST compl(ε)` · `PERO` · `pred_l → SE V_EST«corta» compl(ε) sujp(ε)` · `frec → FREC FREC` |
| «No entendí la explicación, pero el agente fue amable.» | `pred_l → NEG pred_neg → V_ACC«entendí» obj(SUST)` · `sujeto(AGENTE) pred_s → V_COP atrib` |
| «Su ticket es TK-204.» | `sujeto → SUST«ticket»` · `pred_s → V_COP atrib → TICKET` |
| «Mañana revisaremos TK-205.» | `adv_t_op → ADV_T«mañana»` · `pred_l → V_ACC«revisaremos» obj(TICKET)` |
| «Reinicie el router.» | `pred_l → V_ACC«reinicie» obj(SUST«router»)` |
| «El internet sigue lento.» | `sujeto(SUST)` · `pred_s → V_CONT compl → modif` |
| «No funciona el internet.» | `pred_l → NEG pred_neg → V_EST compl(ε) sujp(SUST)` |
| «El router no anda.» | `sujeto → SUST«router»` · `pred_s → NEG pred_neg → V_EST` |
| «El internet falla seguido.» | `pred_s → V_EST«falla» compl(ε)` · `frec → FREC` |
| «No me atendieron bien.» | `pred_l → NEG pred_neg → V_ACC«atendieron» obj(ε) modif_op` |
| «Funciona sin cortes.» | `pred_l → V_EST compl → SIN SUST«cortes»` |
| «El servicio está lento y se corta.» | `cola → Y clausula cola` |
| «Gracias.» | `nucleo → CORTESIA` |

### 2.3 Cómo se llegó a la forma predictiva

La gramática de esta sección es el **resultado final** (L3) de tres transformaciones aplicadas sobre una gramática
descriptiva original: (1) eliminación de la recursión por la izquierda, (2) factorización por la izquierda y
(3) resolución de un conflicto PRIM∩SGTE con simplificación por sustitución. Los pasos intermedios, con el
diagnóstico calculado de cada gramática y la verificación de que todas generan el mismo lenguaje, están en
**`DERIVACION.md`** (`python3 derivacion.py`).

Decisiones de diseño asociadas:

- Se exige `PUNTO` *entre* oraciones. Si se admitieran oraciones sin separador, `NEG` pertenecería a PRIM(`oracion`)
  y a SGTE(`pred_s`) y aparecería un conflicto en `pred_s → ε`.
- «se» precede a un verbo de estado (`SE V_EST compl`). La gramática acepta «corta» sin «se» y «se funciona»; los
  descarta la semántica: el perfil RECUR exige «se» y los perfiles OK y FALLA no lo admiten. Así «el agente corta la
  llamada» (lectura transitiva) queda en abstención.
- `SIN` es una categoría distinta de `NEG`: «sin» precede a un sustantivo y «no» a un predicado.
- La gramática acepta combinaciones que no tienen sentido («el agente se corta», «el servicio corta»). Las descarta
  el análisis semántico (R-COMPAT), como el chequeo de tipos de un compilador.

## 3. PRIM y SGTE

| Variable | PRIM | SGTE |
|---|---|---|
| `<lote>` | {SESION} | {$} |
| `<lote_r>` | {SESION, ε} | {$} |
| `<sesion>` | {SESION} | {$, SESION} |
| `<turnos>` | {NUM} | {FIN} |
| `<turnos_r>` | {NUM, ε} | {FIN} |
| `<turno>` | {NUM} | {FIN, NUM} |
| `<rol>` | {AGENTE, CLIENTE} | {DOSPUNTOS} |
| `<texto>` | {ADV_T, AGENTE, CORTESIA, NEG, SE, SUST, TICKET, V_ACC, V_CONT, V_COP, V_EST} | {EOL} |
| `<texto_r>` | {PUNTO, ε} | {EOL} |
| `<texto_rr>` | {ADV_T, AGENTE, CORTESIA, NEG, SE, SUST, TICKET, V_ACC, V_CONT, V_COP, V_EST, ε} | {EOL} |
| `<oracion>` | {ADV_T, AGENTE, CORTESIA, NEG, SE, SUST, TICKET, V_ACC, V_CONT, V_COP, V_EST} | {EOL, PUNTO} |
| `<cola>` | {COMA, PERO, Y, ε} | {EOL, PUNTO} |
| `<cola_c>` | {ADV_T, AGENTE, CORTESIA, NEG, PERO, SE, SUST, TICKET, V_ACC, V_CONT, V_COP, V_EST} | {EOL, PUNTO} |
| `<clausula>` | {ADV_T, AGENTE, CORTESIA, NEG, SE, SUST, TICKET, V_ACC, V_CONT, V_COP, V_EST} | {COMA, EOL, PERO, PUNTO, Y} |
| `<adv_t_op>` | {ADV_T, ε} | {AGENTE, CORTESIA, NEG, SE, SUST, TICKET, V_ACC, V_CONT, V_COP, V_EST} |
| `<nucleo>` | {AGENTE, CORTESIA, NEG, SE, SUST, TICKET, V_ACC, V_CONT, V_COP, V_EST} | {COMA, EOL, FREC, PERO, PUNTO, Y} |
| `<sujeto>` | {AGENTE, SUST} | {ADJ, COMA, EOL, FREC, INT, NEG, PERO, PUNTO, SE, TICKET, V_ACC, V_CONT, V_COP, V_EST, Y} |
| `<pred_s>` | {ADJ, INT, NEG, SE, TICKET, V_ACC, V_CONT, V_COP, V_EST, ε} | {COMA, EOL, FREC, PERO, PUNTO, Y} |
| `<pred_l>` | {NEG, SE, V_ACC, V_CONT, V_COP, V_EST} | {COMA, EOL, FREC, PERO, PUNTO, Y} |
| `<pred_neg>` | {SE, V_ACC, V_CONT, V_COP, V_EST} | {COMA, EOL, FREC, PERO, PUNTO, Y} |
| `<atrib>` | {ADJ, INT, TICKET} | {COMA, EOL, FREC, PERO, PUNTO, Y} |
| `<compl>` | {ADJ, INT, SIN, ε} | {COMA, EOL, FREC, PERO, PUNTO, SUST, Y} |
| `<sujp>` | {SUST, ε} | {COMA, EOL, FREC, PERO, PUNTO, Y} |
| `<obj>` | {ADV_T, SUST, TICKET, ε} | {ADJ, COMA, EOL, FREC, INT, PERO, PUNTO, Y} |
| `<modif>` | {ADJ, INT} | {COMA, EOL, FREC, PERO, PUNTO, SUST, Y} |
| `<modif_op>` | {ADJ, INT, ε} | {COMA, EOL, FREC, PERO, PUNTO, Y} |
| `<frec>` | {FREC, ε} | {COMA, EOL, PERO, PUNTO, Y} |

## 4. Verificación LL(1)

Condiciones comprobadas por `verificar_ll1()`:

1. No hay recursión por la izquierda (directa ni indirecta).
2. Para cada variable, los PRIM de sus alternativas son **disjuntos** (sin factor común directo ni indirecto).
3. Si una alternativa deriva `ε`, su SGTE es disjunto de los PRIM de las demás, y hay como máximo una alternativa anulable.

**Resultado: ningún conflicto.** La gramática es LL(1) y la tabla predictiva tiene 170 celdas sin colisiones.

### 4.1 Decisiones del parser (variables con más de una alternativa)

| Variable | Alternativa | PRIM de la alternativa (token de decisión) |
|---|---|---|
| `<lote_r>` | <sesion> <lote_r> | {SESION} |
| `<lote_r>` | ε | se elige con SGTE(`<lote_r>`) = {$} |
| `<turnos_r>` | <turno> <turnos_r> | {NUM} |
| `<turnos_r>` | ε | se elige con SGTE(`<turnos_r>`) = {FIN} |
| `<rol>` | CLIENTE | {CLIENTE} |
| `<rol>` | AGENTE | {AGENTE} |
| `<texto_r>` | PUNTO <texto_rr> | {PUNTO} |
| `<texto_r>` | ε | se elige con SGTE(`<texto_r>`) = {EOL} |
| `<texto_rr>` | <oracion> <texto_r> | {ADV_T, AGENTE, CORTESIA, NEG, SE, SUST, TICKET, V_ACC, V_CONT, V_COP, V_EST} |
| `<texto_rr>` | ε | se elige con SGTE(`<texto_rr>`) = {EOL} |
| `<cola>` | PERO <clausula> <cola> | {PERO} |
| `<cola>` | COMA <cola_c> | {COMA} |
| `<cola>` | Y <clausula> <cola> | {Y} |
| `<cola>` | ε | se elige con SGTE(`<cola>`) = {EOL, PUNTO} |
| `<cola_c>` | PERO <clausula> <cola> | {PERO} |
| `<cola_c>` | <clausula> <cola> | {ADV_T, AGENTE, CORTESIA, NEG, SE, SUST, TICKET, V_ACC, V_CONT, V_COP, V_EST} |
| `<adv_t_op>` | ADV_T | {ADV_T} |
| `<adv_t_op>` | ε | se elige con SGTE(`<adv_t_op>`) = {AGENTE, CORTESIA, NEG, SE, SUST, TICKET, V_ACC, V_CONT, V_COP, V_EST} |
| `<nucleo>` | <sujeto> <pred_s> | {AGENTE, SUST} |
| `<nucleo>` | <pred_l> | {NEG, SE, V_ACC, V_CONT, V_COP, V_EST} |
| `<nucleo>` | TICKET | {TICKET} |
| `<nucleo>` | CORTESIA | {CORTESIA} |
| `<sujeto>` | SUST | {SUST} |
| `<sujeto>` | AGENTE | {AGENTE} |
| `<pred_s>` | NEG <pred_neg> | {NEG} |
| `<pred_s>` | V_COP <atrib> | {V_COP} |
| `<pred_s>` | V_EST <compl> | {V_EST} |
| `<pred_s>` | SE V_EST <compl> | {SE} |
| `<pred_s>` | V_CONT <compl> | {V_CONT} |
| `<pred_s>` | V_ACC <obj> <modif_op> | {V_ACC} |
| `<pred_s>` | <modif> | {ADJ, INT} |
| `<pred_s>` | TICKET | {TICKET} |
| `<pred_s>` | ε | se elige con SGTE(`<pred_s>`) = {COMA, EOL, FREC, PERO, PUNTO, Y} |
| `<pred_l>` | NEG <pred_neg> | {NEG} |
| `<pred_l>` | V_COP <atrib> | {V_COP} |
| `<pred_l>` | V_EST <compl> <sujp> | {V_EST} |
| `<pred_l>` | SE V_EST <compl> <sujp> | {SE} |
| `<pred_l>` | V_CONT <compl> | {V_CONT} |
| `<pred_l>` | V_ACC <obj> <modif_op> | {V_ACC} |
| `<pred_neg>` | V_COP <atrib> | {V_COP} |
| `<pred_neg>` | V_EST <compl> <sujp> | {V_EST} |
| `<pred_neg>` | SE V_EST <compl> <sujp> | {SE} |
| `<pred_neg>` | V_CONT <compl> | {V_CONT} |
| `<pred_neg>` | V_ACC <obj> <modif_op> | {V_ACC} |
| `<atrib>` | <modif> | {ADJ, INT} |
| `<atrib>` | TICKET | {TICKET} |
| `<compl>` | <modif> | {ADJ, INT} |
| `<compl>` | SIN SUST | {SIN} |
| `<compl>` | ε | se elige con SGTE(`<compl>`) = {COMA, EOL, FREC, PERO, PUNTO, SUST, Y} |
| `<sujp>` | SUST | {SUST} |
| `<sujp>` | ε | se elige con SGTE(`<sujp>`) = {COMA, EOL, FREC, PERO, PUNTO, Y} |
| `<obj>` | SUST | {SUST} |
| `<obj>` | TICKET | {TICKET} |
| `<obj>` | ADV_T | {ADV_T} |
| `<obj>` | ε | se elige con SGTE(`<obj>`) = {ADJ, COMA, EOL, FREC, INT, PERO, PUNTO, Y} |
| `<modif>` | INT ADJ | {INT} |
| `<modif>` | ADJ | {ADJ} |
| `<modif_op>` | <modif> | {ADJ, INT} |
| `<modif_op>` | ε | se elige con SGTE(`<modif_op>`) = {COMA, EOL, FREC, PERO, PUNTO, Y} |
| `<frec>` | FREC <frec> | {FREC} |
| `<frec>` | ε | se elige con SGTE(`<frec>`) = {COMA, EOL, PERO, PUNTO, Y} |

## 5. Alcance de la negación y de la intensificación (decisión de diseño)

El alcance **queda determinado por la gramática**, no por una heurística:

- `NEG` solo aparece en `pred_s → NEG pred_neg` y `pred_l → NEG pred_neg`. Su alcance es **exactamente** el predicado
  `pred_neg` que lo sigue dentro de la misma cláusula: «no funciona», «no está lento», «no me atendieron bien».
- `SIN` solo aparece en `compl → SIN SUST`: afecta únicamente al sustantivo inmediato («sin internet», «sin cortes»).
- Ninguno de los dos **cruza** `PERO`, `COMA`, `Y` ni `PUNTO`: cada cláusula es una derivación independiente de
  `clausula`, por eso «No entendí la explicación, pero el agente fue amable» conserva CLARIDAD negativa y ATENCION
  positiva por separado.
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
