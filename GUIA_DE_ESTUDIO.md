# Guía de estudio del TP1 · Speech Analytics

**Para qué sirve.** Entender el proyecto desde cero, saber qué partes profundizar y qué decisiones vas a tener que
defender, y llegar a la consulta con el profesor con preguntas concretas.

**Qué versión describe.** La del proyecto *TP Compiladores* (`tp1_completo/tp1/`, rama `cambio_gramatica`) después
de las respuestas del profesor y de la reestructuración del vocabulario: 19 casos (01 a 20, sin el 11); **diccionario de tres niveles**
(categoría → forma canónica → formas superficiales) con **categorías generales** (`SUST`, `ADJ`, `V_EST`, `V_ACC`…);
el significado sale de los **rasgos** de cada forma canónica, guardados en el mismo `vocabulario.json` (y validados
contra un catálogo cerrado de perfiles en el código);
**tabla de símbolos léxica persistente e interactiva** (menú cerrado, alta de formas canónicas, reinicio);
**tabla de entidades** por sesión; compatibilidad sujeto–predicado y `SIN_DOMINIO` en la semántica; precedencia
«prevalece lo último»; numeración que descarta el resto de la sesión ante un orden inconsistente. Todas las cifras de
esta guía salen de ejecutar esa versión (19 casos y 27 sesiones, todos OK, más 13 pruebas de la tabla léxica).

El documento de entrega que explica todo el proyecto de punta a punta es **`INFORME_TECNICO.md`**: leelo después de
esta guía; es lo que va a leer el profesor.

**Cómo usarla.** Leé la sección 1 y la 2 completas. Después recorré la sección 3 fase por fase: para cada una hay
una lista de **qué profundizar**, **qué considerar** y **ejercicios con respuesta** (desplegá la respuesta solo
después de intentarlo). La sección 6 es la lista de preguntas para el profesor; la sección 7, el ensayo de la defensa.

---

## 0. Plan para esta noche

| Prioridad | Tema | Por qué | Tiempo |
|---|---|---|---|
| 1 | Recorrido completo de una frase (sección 2) | Te da el mapa mental de todo lo demás | 20 min |
| 2 | BNF, PRIM/SGTE y derivación LL(1) (3.5) | Vale 22 puntos y es lo más preguntable en pizarra | 60 min |
| 3 | Parser y recuperación de errores (3.6) | Se evalúa junto con la BNF | 30 min |
| 4 | Léxico y AFD de `TICKET` (3.2) | 18 puntos; el procedimiento ER→AFN→AFD se pide a mano | 40 min |
| 5 | Semántica y estado (3.7) | 15 puntos; es donde están las decisiones discutibles | 40 min |
| 6 | Preguntas para el profesor (6) | Llevarlas escritas | 15 min |
| 7 | Corrector, las tablas, pruebas (3.3, 3.4, 3.9) | La tabla léxica interactiva es lo que pidió el profesor y es fácil que la pruebe en vivo | 45 min |

Comandos que conviene tener a mano (desde la carpeta del proyecto):

```bash
python3 main.py casos/caso_02.txt --traza S01 --detalle   # recorrido completo de una frase
python3 gramatica.py                                      # PRIM, SGTE, conflictos, tamaño de la tabla
python3 derivacion.py                                     # L0 → L1 → L2 → L3 con diagnóstico
python3 lexico.py "1 CLIENTE: tu frase aquí"              # tokens con desplazamiento
python3 pruebas.py --regresion                            # 19 casos + tabla léxica + comparación con golden
python3 main.py casos/caso_05.txt < /dev/null             # sin respuestas: regla del enunciado en el corrector
python3 main.py --reiniciar-aprendido                     # vuelve a la precarga (borra lo aprendido)
python3 main.py --tabla-inicial                           # tabla de símbolos léxica inicial (solo la precarga)
python3 main.py --tabla                                   # tabla vigente («+» = aprendido)
python3 main.py casos/caso_19.txt --tabla                 # analiza preguntando y muestra la tabla ya enriquecida
```

---

## 1. El proyecto en cinco minutos

**El problema.** Leer conversaciones de soporte de Internet y decir, por sesión: qué opina el cliente del
SERVICIO, la ATENCION y la CLARIDAD; en qué estado quedó el problema (RESUELTO, NO_RESUELTO, TEMPORAL, PENDIENTE,
NO_CONFIRMADO); y con qué evidencia (turno, fragmento, regla). La idea central del diseño: **la gramática ve
categorías generales** (`SUST`, `ADJ`, `V_EST`…) **y la semántica resuelve qué significa cada palabra** por los rasgos
de su forma canónica (`lento` → `ADJ/LENTO` → rasgos `{"pol": -1}`, perfil NEGATIVO → `pol = −1`). La trampa central del enunciado: **una valoración
positiva no es una confirmación de solución** («Me atendiste muy bien, pero sigo sin internet» → NO_RESUELTO).

**El pipeline.** Cada etapa es una fase clásica de un compilador:

```
archivo.txt
  │  lector.py ........... gramática de FORMATO, línea a línea (SESION / n ROL: texto / FIN)
  ▼
  │  lexico.py ........... ER → AFN (Thompson) → AFD (subconjuntos); lexema más largo + prioridad
  ▼
  │  corrector.py ........ Levenshtein ≤ 1; consulta.py pregunta solo si hay empate o no hay candidato
  │  tabla_lexica.py ..... tabla de símbolos LÉXICA: categoría → forma canónica → {rasgos, formas};
  │                        persistente, se enriquece; rasgos validados contra los perfiles
  ▼
  │  sintaxis.py ......... parser LL(1) predictivo guiado por la tabla M[A,a]; árbol de derivación
  ▼
  │  semantica.py ........ reglas por producción; lee los rasgos; PERFILES (catálogo cerrado) → «hechos»;
  │                        compatibilidad sujeto–predicado; SIN_DOMINIO; agregación; estado
  ▼
  │  entidades.py ........ tabla de ENTIDADES por sesión (SESION, PARTICIPANTE, TICKET); efímera
  ▼
  analizador.py + main.py → JSON por lote, vista de consola y traza
```

**Dónde está cada cosa.**

| Fase | Código | Documento | Puntos |
|---|---|---|---|
| Léxico y normalización | `lexico.py`, `tabla_lexica.py`, `vocabulario.json` | `INFORME_lexico.md`, `INFORME_TECNICO.md` §4 | 18 |
| Tabla de símbolos | `tabla_lexica.py`, `vocabulario.json` (léxica); `entidades.py` (entidades) | `INFORME_lexico.md` §1.5 y §1.6, `REGLAS_SEMANTICAS.md` §3 y §9, `INFORME_TECNICO.md` §5 | 10 |
| BNF y análisis sintáctico | `gramatica.py`, `sintaxis.py`, `derivacion.py` | `GRAMATICA.md`, `DERIVACION.md` | 22 |
| Semántica y estados | `semantica.py`, `analizador.py` | `REGLAS_SEMANTICAS.md`, `INFORME_TECNICO.md` §7 | 15 |
| Corrección y recuperación | `corrector.py`, `consulta.py`, `lector.py`, `sintaxis.py` | `README.md` | 10 |
| Pruebas y reproducibilidad | `pruebas.py`, `casos/` | `RESULTADOS_PRUEBAS.md` | 10 |
| Defensa individual | todo | esta guía | 15 |

---

## 2. Recorrido completo de una frase (caso 02)

Entrada: `1 CLIENTE: Me atendiste muy bien, pero sigo sin internet.`
Comando: `python3 main.py casos/caso_02.txt --traza S01 --detalle`

| # | Etapa | Qué pasa | Qué mirar en la traza |
|---|---|---|---|
| 1 | Lector | Reconoce `NUM CLIENTE DOSPUNTOS texto`; el turno es el 1 esperado; se acepta | línea `Turno 1 · CLIENTE` |
| 2 | Léxico | 10 tokens del texto, cada uno con desplazamiento en la línea: `RELLENO«Me»@11`, `V_ACC«atendiste»@14=ATENDER`, `INT«muy»@24`, `ADJ«bien»@28=BUENO`, `COMA@32`, `PERO@34`, `V_CONT«sigo»@39`, `SIN«sin»@44`, `SUST«internet»@48=SERVICIO`, `PUNTO@56` (después del `=` va la forma canónica) | `[2] Tokens` |
| 3 | Corrector | No hay tokens `PALABRA`: no actúa | sin líneas `corrector` |
| 4 | Filtro | Se quita `RELLENO` («Me»); el resto son terminales de la gramática | — |
| 5 | Parser | `M[nucleo, V_ACC] = nucleo → pred_l`; `M[pred_l, V_ACC] = pred_l → V_ACC obj modif_op`; `M[obj, INT] = obj → ε`; `M[cola, COMA] = cola → COMA cola_c`; `M[cola_c, PERO] = cola_c → PERO clausula cola`; `M[pred_l, V_CONT] = pred_l → V_CONT compl`; `M[compl, SIN] = compl → SIN SUST` | `[3] Estructura` y las líneas `M[…]` |
| 6 | Tabla de entidades | `BUSCAR PARTICIPANTE CLIENTE → NO_EXISTE`; `INSERTAR PARTICIPANTE CLIENTE` | `[4] Tabla entidades` |
| 7 | Semántica | `C1.1 «Me atendiste muy bien» → ATENCION=POSITIVA [R-VAL, R-MUY]` (ATENDER tiene los rasgos del perfil VAL_ATEN: valora la atención); `C1.2 «sigo sin internet» → SERVICIO=NEGATIVA, declaración FALLA [R-SEG-SIN, R-SIN, R-PERO]` (SERVICIO tiene perfil SERVICIO) | `[5] Acción semántica` |
| 8 | Resultado | Turno: ATENCION POSITIVA, SERVICIO NEGATIVA. Estado: la única declaración del cliente es FALLA → **NO_RESUELTO** (`R-EST-NORES`) | `[6] Resultado` y la vista de sesión |

Si podés explicar esta tabla sin mirarla, entendiste el proyecto. El resto es profundidad en cada fila.

---

## 3. Fase por fase

### 3.1 Formato y lector (`lector.py`)

**Qué hace.** Lee el archivo línea a línea y aplica la gramática de formato:

```
<lote>     ::= <sesion> <lote_r>
<lote_r>   ::= <sesion> <lote_r> | ε
<sesion>   ::= SESION ID_SESION EOL <turnos> FIN EOL
<turnos>   ::= <turno> <turnos_r>
<turnos_r> ::= <turno> <turnos_r> | ε
<turno>    ::= NUM <rol> DOSPUNTOS <texto> EOL
<rol>      ::= CLIENTE | AGENTE
```

**Qué profundizar.**
- Por qué el formato se valida línea a línea y no con el parser LL(1): cada `EOL` es un **punto de
  sincronización**. Ante un error se rechaza la línea y se sigue en la siguiente (recuperación en modo pánico).
- Qué restricciones **no** caben en una BNF libre de contexto y las verifica el código: que el turno sea `n+1`,
  que el texto no esté vacío, que un id de sesión no se repita.
- Los códigos de error. De turno: `ROL_INVALIDO`, `FALTA_DOSPUNTOS`, `TEXTO_VACIO`, `ORDEN_INCONSISTENTE`,
  `TURNO_FUERA_DE_SESION`. De sesión: `SESION_MAL_FORMADA`, `SESION_DUPLICADA`, `SESION_SIN_FIN`, `FIN_SIN_SESION`,
  `FIN_MAL_FORMADO`. De línea o lote: `LINEA_EN_BLANCO`, `LINEA_NO_RECONOCIDA`, `LOTE_VACIO`.

**Qué considerar.**
- **Análisis PARCIAL** = la sesión tiene algún error de formato o le falta `FIN`. Los fragmentos NO_INTERPRETADO
  dentro de un turno aceptado **no** la vuelven parcial. El profesor respondió «solo por falta de FIN», pero el caso
  07 del enunciado pide «primera sesión parcial» por un turno rechazado (con `FIN`): se mantuvo el criterio actual
  hasta confirmarlo con él (ver sección 6).
- **Numeración** (respuesta del profesor). Un turno rechazado por rol o formato consume su número y se sigue (caso
  07: 1, 2 rechazado, 3 aceptado). Un turno **fuera de orden** corta la sesión: se conservan los turnos anteriores y
  se descarta **todo lo que sigue** hasta el `FIN` (`ORDEN_INCONSISTENTE` y luego `TURNO_DESCARTADO` por cada turno).
  En «1, 3, 4» queda solo el 1 (caso 14). Las sesiones siguientes no se afectan.
- **Id repetido.** La segunda `SESION S01` se descarta entera (error global), porque compartiría el ámbito de la
  tabla de entidades con la primera (caso 14).
- **NFC y BOM.** Cada línea se normaliza a NFC antes de escanear. Los desplazamientos se miden sobre esa línea
  normalizada.

**Ejercicio 3.1.** ¿Qué turnos acepta el lector en `caso_12.txt`, y por qué S01 queda PARCIAL?

<details><summary>Respuesta</summary>

Líneas de S01: `1 CLIENTE` y `2 CLIENTE` (aceptados), `3 SOPORTE` (`ROL_INVALIDO`, consume el 3), `4 CLIENTE`
(aceptado), `6 CLIENTE` (se esperaba 5 → `ORDEN_INCONSISTENTE`) y `5 CLIENTE` (`TURNO_DESCARTADO`: todo lo posterior
a un orden inconsistente se descarta). Se aceptan los turnos 1, 2 y 4. S01 es PARCIAL porque tiene errores de
formato; S02 se analiza completa, lo que demuestra que el error no se propaga a otra sesión. Fijate la diferencia:
el rol inválido rechaza solo su turno; el orden inconsistente corta el resto de la sesión.
</details>

---

### 3.2 Analizador léxico (`lexico.py`, `vocabulario.json`)

**Qué hace.** Convierte cada línea en tokens `(categoría, lexema, normalizado, canónico, sesión, turno, desp)`.

**Conceptos de clase que aplica.**

| Concepto | Dónde |
|---|---|
| Alfabeto Σ por clases de símbolos (`D` = dígito, `Q` = `¿?¡!`) | `simbolo()` |
| ER como árbol (concatenación, unión, `*`, `+`, `?`, potencia `x{n,m}`) | `lit`, `cat`, `mas`, `est`, `rep` |
| Construcción de Thompson (AFN con ε) | `thompson()` |
| Cerradura-ε y `mover` | `cierre()`, `mover_afn()` |
| Construcción de subconjuntos (AFN → AFD) | `construir()` |
| Lexema más largo | `escanear()`: recuerda el último estado final visitado |
| Prioridad entre patrones | orden de la lista de patrones; `afd.ambiguos` registra los estados en conflicto |

**Qué profundizar (alta prioridad).**
1. **El AFD de `TICKET`** (`INFORME_lexico.md` §3). ER: `tk- D{3,6}` = `tk- DDD(D(D(D)?)?)?`. Tiene 10 estados
   en cadena (q0 a q9); son finales q6, q7, q8 y q9 (3, 4, 5 y 6 dígitos). Tenés que poder dibujarlo, escribir su
   tabla de transiciones y explicar por qué ya es mínimo (cada estado recuerda una cantidad distinta de caracteres).
2. **Las dos reglas de desambiguación.** Si dos patrones aceptan lexemas de **distinta longitud**, gana el más
   largo (`TK-204` como `TICKET` y no `tk` como `PALABRA`). Si aceptan **el mismo lexema**, gana la prioridad
   (`no` es `NEG` y no `PALABRA`).
3. **`TICKET_MAL`** (`tk- D*`, prioridad menor que `TICKET`): con 3 a 6 dígitos gana `TICKET` por prioridad; con
   0–2 o con 7 o más, `TICKET_MAL` es el único o el más largo y produce un error léxico específico.

**Qué considerar.**
- El AFD completo (estructura + vocabulario + `PALABRA`) tiene **409 estados**, con **124** estados de ambigüedad
  resuelta por prioridad. No está minimizado; en el informe se muestra solo el de `TICKET`.
- **Plegado** carácter a carácter (minúscula, sin tilde, conserva `ñ`): como es 1 a 1, el desplazamiento de un
  token sirve también para el texto original.
- **Desplazamiento** = índice 0-based del primer carácter del lexema **dentro de la línea completa** (incluye
  `1 CLIENTE:`). Cuenta caracteres, no bytes.
- **Turno del token.** Solo los tokens del texto (después de `:`) reciben el número de turno; los de la cabecera
  quedan con `turno = None`, porque `Turno` solo guarda los tokens del texto. Si el informe dice que *todos* los
  tokens llevan turno, conviene aclararlo o asignar el número a toda la línea en `lector.py` (una línea).
- **Un lexema, una categoría.** `agente` siempre es `AGENTE`; el parser decide si es rol o sujeto («el agente fue
  amable»). El lexer no ve contexto.
- `RELLENO` (artículos, clíticos, preposiciones) pertenece al lenguaje pero se filtra antes del parser.
- **Vocabulario.** 16 categorías con formas, 43 formas canónicas y 116 formas superficiales en la precarga (más
  `FUERA_DE_GRAMATICA/FUERA`, sin formas). Tres niveles: **categoría → forma canónica → formas superficiales**, y
  cada forma canónica guarda sus **rasgos**: `"LENTO": {"rasgos": {"pol": -1}, "formas": ["lento", "lenta"]}`. Las categorías son generales
  (`SUST`, `ADJ`, `V_COP`, `V_EST`, `V_CONT`, `V_ACC`, `ADV_T`, `NEG`, `SIN`, `INT`, `PERO`, `Y`, `SE`, `FREC`,
  `CORTESIA`, `RELLENO`) y son los terminales de la gramática. El léxico solo usa las formas; los rasgos los leen
  las reglas semánticas (3.4). La ER de cada categoría es la unión de sus formas en el diccionario vigente
  (precarga más lo aprendido), así que cambia cuando el usuario inserta una palabra.
- **Homógrafos.** Una forma tiene una sola categoría: «falla» y «corta» son verbos, «corte» y «cortes» sustantivos,
  «esta» es la cópula «está». Los tiempos verbales no se distinguen (fuera de alcance).

**Ejercicio 3.2a.** Tokenizá `2 AGENTE: Su ticket es TK-204.` con desplazamientos.

<details><summary>Respuesta</summary>

`NUM«2»@0`, `AGENTE«AGENTE»@2`, `DOSPUNTOS@8`, `RELLENO«Su»@10`, `SUST«ticket»@13` (canónico TICKET), `V_COP«es»@20`,
`TICKET«TK-204»@23` (normalizado `TK-204`), `PUNTO@29`. Comprobalo con `python3 lexico.py "2 AGENTE: Su ticket es TK-204."`.
</details>

**Ejercicio 3.2b.** ¿Qué token sale de `tk-0042`, `TK-12`, `TK-1234567` y `Sesión`?

<details><summary>Respuesta</summary>

`tk-0042` → `TICKET`, normalizado `TK-0042` (4 dígitos, mayúsculas y minúsculas se pliegan). `TK-12` y
`TK-1234567` → `TICKET_MAL`. `Sesión` → `SESION` (la tilde se pliega).
Recorrido de `TK-12` en el AFD de `TICKET`: q0 →t q1 →k q2 →- q3 →D q4 →D q5, y se termina la entrada en q5,
que no es final.
</details>

---

### 3.3 Corrector (`corrector.py`, `consulta.py`)

**Qué hace.** Para cada token `PALABRA` (palabra que no está en la tabla de símbolos léxica) busca formas de la tabla
a distancia de Levenshtein exactamente 1 y aplica la **regla del enunciado**. Solo cuando la regla no resuelve la
palabra, **le pregunta al usuario**:

| Candidatos a distancia 1 | Regla del enunciado | ¿Se pregunta? |
|---|---|---|
| exactamente 1 | `CORREGIDA`: el token toma la categoría y el canónico del candidato; conserva lexema y desplazamiento | **no** |
| 2 o más | `EMPATE`: se conserva la palabra, se registra el empate, queda NO_INTERPRETADO | **sí**: se ofrecen los candidatos, insertar o Enter |
| 0 | `SIN_CANDIDATO`: queda NO_INTERPRETADO | **sí**: insertar o Enter |
| palabra de menos de 4 letras | `OMITIDA_CORTA`: no se intenta (decisión del grupo, `MIN_LONG`) | no |

```
Palabra desconocida «lent» · sesión S01, turno 1: «El servicio está lent.»
   1) usar «lenta» (ADJ / LENTO) solo en esta aparición
   2) usar «lento» (ADJ / LENTO) solo en esta aparición
   n) insertar «lent» en la tabla de símbolos léxica
   Enter) regla del enunciado: conservar la palabra y registrar el empate (NO_INTERPRETADO)
```

| Respuesta | Acción registrada | ¿Cambia la tabla léxica? |
|---|---|---|
| un candidato (`1..k`, solo en un empate) | `CORREGIDA_USUARIO`: se corrige **solo esa aparición** | no (los errores de tipeo no se guardan) |
| `n` | `INSERTADA` (menú cerrado, ver 3.4) | sí, en `vocabulario_aprendido.json` |
| Enter | se mantiene la regla del enunciado | no |

Cada palabra se pregunta una vez por ejecución y lo aprendido vale para el resto de la entrada. Si la entrada se
termina (Ctrl-D o `< /dev/null`), lo que falta se resuelve con la regla del enunciado. `pruebas.py` y el golden
corren sin preguntas y con la precarga.

**Qué profundizar.** La programación dinámica de Levenshtein (borrado, inserción, sustitución) y por qué se
filtran antes los candidatos con `|len(a) − len(b)| ≤ 1`.

**Qué considerar.**
- Solo actúa sobre `PALABRA`: por eso nunca toca «no», los números ni `TK-204`, que ya tienen otra categoría.
- `MIN_LONG = 4` no está en el enunciado: evita que «mas» se corrija a «mal» e invente una valoración negativa.
- Levenshtein no trata la **transposición** como una sola operación: «amabel» está a distancia 2 de «amable» y no
  se corrige. (Damerau-Levenshtein la contaría como 1.)
- Las formas del vocabulario no se lematizan: por eso «lent» empata entre «lenta» y «lento».
- Con Enter (o sin respuestas), los casos 05 («lentto» → «lento», sin preguntar) y 08 (empate de «lent») dan lo que
  pide la guía.

**Ejercicio 3.3.** ¿Qué hace el corrector con `lentto`, `lent`, `mas`, `conexionn`, `amabel` y `buenp`?

<details><summary>Respuesta</summary>

`lentto` → CORREGIDA a `lento`. `lent` → EMPATE {lenta, lento}. `mas` → OMITIDA_CORTA. `conexionn` → CORREGIDA a
`conexion`. `amabel` → SIN_CANDIDATO (transposición = 2). `buenp` → EMPATE {buen, buena, bueno}.
</details>

---

### 3.4 Las tablas: tabla de símbolos léxica y tabla de entidades

El profesor pidió que la tabla de símbolos se **precargue**, **persista entre ejecuciones** y se **enriquezca**
preguntándole al usuario por los símbolos desconocidos. El grupo separó dos tablas:

| | Tabla de símbolos léxica (`tabla_lexica.py`) | Tabla de entidades (`entidades.py`) |
|---|---|---|
| Qué guarda | el lenguaje, en una sola estructura: categoría → forma canónica → {**rasgos**, formas superficiales} | lo que aparece en cada conversación: `SESION`, `PARTICIPANTE`, `TICKET` y sus apariciones `(turno, desp, lexema)` |
| Ámbito | global | la sesión |
| Persistencia | **sí**: se enriquece con las respuestas del usuario | **no**: se crea vacía en cada ejecución |
| Archivos | precarga: `vocabulario.json` (el programa nunca lo escribe); aprendido: `vocabulario_aprendido.json` (mismo formato; una escritura atómica por cambio) | ninguno: sale en el JSON de resultados (`entidades`) |
| Operaciones | `buscar`, `insertar` (variante de un canónico existente: hereda sus rasgos), `alta_canonico` (con los rasgos de un perfil existente), `reiniciar`; validación de rasgos al abrir | `buscar`, `insertar` (enlaza duplicados), `actualizar` |
| Quién la usa | el léxico (formas → AFD), el corrector, la consulta y la semántica (rasgos) | el analizador y las acciones semánticas |

**Cómo se obtiene el significado de una palabra** (de la misma entrada que sus formas):

```
«lentas» ──tabla de símbolos léxica──► ADJ / LENTO / rasgos {"pol": -1} ──semantica.sig──► pol = −1
```

Los rasgos no son libres. Los **perfiles** son el catálogo cerrado de combinaciones válidas, en el código (33): `ADJ` POSITIVO, NEGATIVO, SIN_DOMINIO; `SUST` SERVICIO,
ATENCION, CLARIDAD, EQUIPO, TICKET, PROBLEMA, SIN_DOMINIO; `V_EST` OK, FALLA, RECUR; `V_ACC` COMPRENSION, SOLICITUD,
COMPROMISO, VAL_ATEN, VAL_CLAR, SIN_DOMINIO; `ADV_T` AHORA, FUTURO; y un perfil único para cada categoría gramatical
(`NEG`, `SE`, `FREC`…), sin rasgos. Al abrir la tabla se valida que los rasgos de cada forma canónica coincidan con
un perfil de su categoría. La tabla completa (perfil → rasgos → atributos) está en `REGLAS_SEMANTICAS.md` §3.

**El menú de inserción es cerrado:**

1. **Categoría**: solo las existentes, agrupadas por tipo de palabra.
2. **Forma canónica** de la que la palabra es variante: primero se ofrecen las existentes de esa categoría (con sus
   rasgos y su perfil). Opción `c`: crear una nueva; el nombre se **normaliza** (sin tildes, mayúsculas, espacios como `_`) y se
   **rechaza si ya existe** en la categoría.
3. Si es nueva: **perfil obligatorio**, elegido entre los existentes de la categoría (si hay uno solo, se asigna). El
   programa copia los rasgos del perfil en la entrada nueva: el usuario nunca escribe rasgos.

No se pueden crear categorías, perfiles ni rasgos sueltos: un significado nuevo es un cambio del modelo semántico y se hace en el
código.

**Qué profundizar.**
- **Por qué dos tablas.** El enunciado exige «mantener separado el diccionario de vocabulario» de la tabla de
  sesión, participante y ticket. La tabla léxica es el lenguaje (cambia poco y conviene que persista); la de
  entidades es cada conversación (no tiene sentido arrastrarla a otra ejecución).
- **Por qué los rasgos están en el mismo `vocabulario.json`** (decisión final del grupo; se probó y se descartó un
  `significados.json` aparte). La razón es la **interactividad** de la tabla:
  1. *Atomicidad.* Un alta desde el menú crea la forma canónica y su significado. En un archivo es **una** escritura
     atómica (temporal + `os.replace`). Con dos archivos, cada escritura era atómica pero el cambio completo no, y si un
     archivo se borraba, restauraba o copiaba sin el otro, quedaban formas sin significado y la tabla no cargaba.
  2. *Vigencia inmediata.* El corrector y la semántica usan el **mismo objeto vivo** (`tabla.vocabulario()`): lo
     aprendido en un turno vale en el siguiente sin sincronizar dos estructuras.
  3. *Menú coherente.* Al ofrecer variantes se muestran los rasgos de la misma entrada en la que se va a insertar.
  4. *Mismo formato en precarga y aprendido.* Pasar algo aprendido a la precarga es copiar una entrada; la
     conciliación y el reinicio trabajan sobre un archivo.
  5. *El menú sigue cerrado.* Los rasgos se copian de un perfil y la carga rechaza combinaciones fuera del catálogo.

  Costo: los rasgos se repiten en cada forma canónica del mismo perfil, y si se cambia un perfil en el código hay que
  actualizar sus entradas (la validación las señala). Detalle en `INFORME_lexico.md` §1.6.
- **Persistencia en JSON** (sin base de datos): la precarga se lee y nunca se escribe; lo aprendido va a
  `vocabulario_aprendido.json`, con el mismo formato y una escritura atómica por cambio.
- **Sin archivo de auditoría** (decisión del grupo: se quitó `vocabulario_auditoria.jsonl`). Qué se aprendió se ve con
  `python3 main.py --tabla` («+» marca cada forma y forma canónica aprendida); qué se insertó en una ejecución, en qué
  turno y con qué categoría y forma canónica, queda en el JSON de resultados como corrección `INSERTADA`. Si algo
  aprendido se agrega después a la precarga, gana la precarga y `main.py` avisa qué se quitó de lo aprendido. Lo que
  se pierde: la historia entre ejecuciones (quién, cuándo y desde qué archivo se agregó cada palabra).
- **Duplicados en las dos tablas.** En la léxica, una forma no puede tener dos entradas y una forma canónica no se
  repite dentro de su categoría. En la de entidades, insertar una clave existente **enlaza** la aparición
  (`DUPLICADO->ENLAZAR`): `TK-204` mencionado dos veces = una entrada con dos apariciones.
- **Actualización desde la semántica.** Un compromiso sobre un ticket («Mañana revisaremos TK-205») actualiza su
  entrada con `seguimiento = COMPROMISO_FUTURO`. Al final de la sesión se actualiza la entrada `SESION` con su estado.

**Qué considerar.**
- **`SIN_DOMINIO` frente a `FUERA_DE_GRAMATICA`.** Las dos sirven para palabras sin significado útil, pero no son
  iguales. `FUERA_DE_GRAMATICA` (y `RELLENO`) **descartan** la palabra antes del parser, y el parser une lo que queda.
  `SIN_DOMINIO` deja la palabra en su lugar del árbol y la cláusula se **abstiene** entera (R-SINDOM). Para «hace»,
  «ruido» o «técnico» conviene `SIN_DOMINIO`.
- `python3 main.py --reiniciar-aprendido` vuelve a la precarga (borra `vocabulario_aprendido.json`).
- `--dic` (caso 08) usa una tabla solo en memoria: lo que se inserte no se guarda.

**Ejercicio 3.4a.** Se ejecuta dos veces `1 CLIENTE: El servicio anda fatal.` En la primera se responde `n`, categoría
`ADJ` y forma canónica existente `MALO`. ¿Qué estado da cada ejecución y qué archivos cambian?

<details><summary>Respuesta</summary>

Sin la palabra, «fatal» se descarta y queda «anda» → OK → RESUELTO (una valoración inventada por omisión). Con la
inserción, «fatal» es variante de `ADJ/MALO` y hereda sus rasgos `{"pol": -1}` (perfil NEGATIVO): «anda fatal» es `V_EST compl` con polaridad
negativa → FALLA → **NO_RESUELTO**. Cambia `vocabulario_aprendido.json` (`{"ADJ": {"MALO": {"formas": ["fatal"]}}}`); la precarga no
cambia, y el JSON de resultados registra la corrección `INSERTADA`. En la segunda ejecución no se pregunta: el
AFD ya incluye «fatal». Lo verifica `pruebas.py`.
</details>

**Ejercicio 3.4b.** «El internet colapsa seguido.» En el menú: `V_EST`, `c` (forma canónica nueva) con nombre
«colapsár», y perfil `FALLA`. ¿Qué se guarda y qué pasa en el turno siguiente «Ahora colapsa.»?

<details><summary>Respuesta</summary>

El nombre se normaliza a `COLAPSAR` y se crea `V_EST/COLAPSAR` con los rasgos del perfil FALLA,
`{"pol": -1, "decl": "FALLA"}`, en `vocabulario_aprendido.json`; después «colapsa» se inserta como su variante, en la misma
entrada. El
turno da SERVICIO NEGATIVA, FALLA. En «Ahora colapsa.» no se pregunta: lo aprendido vale para el resto de la entrada,
y la cláusula vuelve a dar FALLA. Si se intenta crear otra vez «Colapsar» en `V_EST`, se rechaza por duplicado.
</details>

**Ejercicio 3.4c.** ¿Por qué con «hace», «ruidos» y «raros» de perfil `SIN_DOMINIO` (rasgo `sin_dominio`) la frase «Mi router hace ruidos
raros» se abstiene, mientras que en la rama `prueba` (con esas palabras en categorías que no son terminales) da
SERVICIO NEGATIVA?

<details><summary>Respuesta</summary>

En la rama `prueba`, `VERBO_GEN` y `SUSTANTIVO` no son terminales: «hace» y «ruidos» se filtran antes del parser, que
recibe «router raros» y lo deriva como sujeto + cualidad («el router está raro») → SERVICIO NEGATIVA. Es un resultado
accidental. Con `SIN_DOMINIO`, las tres palabras son terminales (`V_ACC`, `SUST`, `ADJ`) y ocupan su lugar en el árbol
(`sujeto pred_s → V_ACC obj modif_op`); la regla de `clausula` detecta el rasgo `sin_dominio` y no la interpreta
(R-SINDOM). No se inventa nada.
</details>

**Ejercicio 3.4d.** Alguien edita a mano `vocabulario.json` y le pone a `ADJ/RARO` los rasgos `{"pol": 2}`. ¿Qué pasa
al ejecutar? ¿Y si en una versión con `significados.json` aparte se hubiera borrado `significados_aprendido.json` pero
no `vocabulario_aprendido.json`?

<details><summary>Respuesta</summary>

Con los rasgos en la tabla, la carga valida cada entrada contra los perfiles de su categoría: `{"pol": 2}` no es
ningún perfil de `ADJ`, así que la tabla no se abre y el mensaje dice qué entrada falla y qué perfiles hay. Lo
verifica la prueba «rasgos validados al cargar contra los perfiles». En la versión con dos archivos, las formas
aprendidas habrían quedado apuntando a formas canónicas sin perfil, y la tabla tampoco habría cargado, pero el error
venía de un archivo que faltaba, no de un dato mal escrito. Con un solo archivo eso no puede pasar: cada cambio es
una escritura atómica y lo aprendido queda entero o no queda.
</details>

---

### 3.5 BNF, PRIM/SGTE y LL(1) (`gramatica.py`, `GRAMATICA.md`, `DERIVACION.md`)

Es la parte de más peso. Dedicale el mayor tiempo.

**La gramática en números.** 27 variables (7 de formato y 20 lingüísticas), 68 producciones, 19 terminales en el
texto de un turno. Tabla predictiva con 170 celdas y sin conflictos.

**Gramática lingüística final (L3).**

```
<texto>     ::= <oracion> <texto_r>
<texto_r>   ::= PUNTO <texto_rr> | ε
<texto_rr>  ::= <oracion> <texto_r> | ε
<oracion>   ::= <clausula> <cola>
<cola>      ::= PERO <clausula> <cola> | COMA <cola_c> | Y <clausula> <cola> | ε
<cola_c>    ::= PERO <clausula> <cola> | <clausula> <cola>
<clausula>  ::= <adv_t_op> <nucleo> <frec>
<adv_t_op>  ::= ADV_T | ε
<nucleo>    ::= <sujeto> <pred_s> | <pred_l> | TICKET | CORTESIA
<sujeto>    ::= SUST | AGENTE
<pred_s>    ::= NEG <pred_neg> | V_COP <atrib> | V_EST <compl> | SE V_EST <compl> | V_CONT <compl>
              | V_ACC <obj> <modif_op> | <modif> | TICKET | ε
<pred_l>    ::= NEG <pred_neg> | V_COP <atrib> | V_EST <compl> <sujp> | SE V_EST <compl> <sujp>
              | V_CONT <compl> | V_ACC <obj> <modif_op>
<pred_neg>  ::= V_COP <atrib> | V_EST <compl> <sujp> | SE V_EST <compl> <sujp> | V_CONT <compl> | V_ACC <obj> <modif_op>
<atrib>     ::= <modif> | TICKET
<compl>     ::= <modif> | SIN SUST | ε
<sujp>      ::= SUST | ε
<obj>       ::= SUST | TICKET | ADV_T | ε
<modif>     ::= INT ADJ | ADJ          <modif_op> ::= <modif> | ε          <frec> ::= FREC <frec> | ε
```

Leela de arriba hacia abajo: un **texto** son oraciones separadas por punto; una **oración** son cláusulas unidas
por `PERO` o `COMA`; una **cláusula** es la unidad que produce un hecho semántico (una valoración, una declaración
de funcionamiento, una solicitud, un compromiso, un ticket o una cortesía).

**Categorías generales.** La gramática no distingue qué significa cada palabra: `ADJ` es «lento» o «bueno» por
igual. Lo que importa a la sintaxis es la **construcción**. `pred_s` es el predicado que sigue a un sujeto; `pred_l`, el
que va sin sujeto delante (tácito o pospuesto); `pred_neg`, el alcance de `NEG`. Los verbos se agrupan por
construcción: `V_COP` + `atrib`, `V_EST` + `compl` (con o sin «se»), `V_CONT` + `compl`, `V_ACC` + `obj`. El glosario
completo de no terminales está en `GRAMATICA.md` §2.1.

**Qué profundizar (alta prioridad).**
1. **Los algoritmos de PRIM y SGTE** tal como están en `primero()` y `siguiente()` (iteración hasta punto fijo).
   Calculá a mano al menos `PRIM(pred_s)`, `SGTE(clausula)` y `SGTE(pred_s)`.
2. **Las tres condiciones LL(1)** que verifica `verificar_ll1()`: sin recursión por la izquierda; PRIM de las
   alternativas de cada variable disjuntos; si una alternativa es anulable, su SGTE no se superpone con los PRIM de
   las otras (y hay a lo sumo una alternativa anulable).
3. **La derivación L0 → L3** (`DERIVACION.md`). Es lo que más probablemente te pidan reproducir:

| Gramática | Variables | Problema que tiene | Transformación de clase que se aplica |
|---|---|---|---|
| L0 (descriptiva) | 16 | recursión izquierda en `lista`, `oracion`, `frec`; factores comunes en 11 variables | — |
| L1 | 19 | factores comunes en `texto`, `sep`, `clausula`, `nucleo`, `est`, `acc`, `pred_l`, `pred_neg`; **nuevo** PRIM∩SGTE en `lista_r` | Paso 1: `A → Aα \| β` ⇒ `A → βR`, `R → αR \| ε` |
| L2 | 22 | solo PRIM∩SGTE en `lista_r` (`PUNTO`) | Paso 2: `A → αβ₁ \| αβ₂` ⇒ `A → αR`, `R → β₁ \| β₂` |
| L3 (final) | 20 | ninguno | Paso 3: consumir `PUNTO` y decidir después; sustituir `sep` en `cola` |

   Las cuatro generan el mismo lenguaje (verificado por enumeración: 23.220 cadenas de hasta 5 tokens; con
   `python3 derivacion.py 5` tarda unos 3 minutos). Es una verificación **acotada**, no una demostración.
4. **Por qué el conflicto de `lista_r` aparece recién en L1.** Lo crea el Paso 1, al introducir una variable
   anulable. Por eso hay que re-diagnosticar después de cada transformación.

**Qué considerar.**
- **`PUNTO` obligatorio entre oraciones.** Si dos oraciones pudieran ir pegadas, `NEG` estaría en PRIM(`oracion`)
  y en SGTE(`pred_s`), y `pred_s → ε` tendría conflicto. Consecuencia práctica: en «El servicio está lento la
  atención fue buena» la segunda oración se descarta.
- **Factor común de `sujeto`.** Las diez alternativas de `nucleo` en L0 que empiezan con `sujeto` se factorizan
  una sola vez y la decisión pasa a `pred_s`.
- **Variables anulables nuevas.** Al factorizar aparecen `compl`, `sujp`, `obj` y `modif_op`, además de `pred_s → ε`.
  Para cada una hay que comprobar PRIM contra SGTE; por ejemplo SGTE(`compl`) contiene los sustantivos (por `sujp`),
  y ninguna alternativa de `compl` empieza con un sustantivo.
- **«se corta» exige «se», pero lo controla la semántica.** La gramática acepta `V_EST` con o sin «se»; el perfil
  RECUR exige «se» y OK y FALLA no lo admiten. «El agente corta la llamada» y «se funciona» se reconocen pero no se
  interpretan (R-COMPAT).
- **La gramática acepta de más.** «El agente se corta» o «la explicación funciona bien» se reconocen; los descarta
  la semántica con la tabla de compatibilidad (3.7).
- **El alcance de la negación lo fija la gramática.** `NEG` solo aparece en `pred_s/pred_l → NEG pred_neg`, y `SIN`
  solo en `compl → SIN SUST`; después de `PERO`, `COMA` o `Y` empieza otra `clausula`, así que no hay forma de que la
  negación cruce el conector.
- **La gramática de L0 se reconstruyó hacia atrás** a partir de la final. Los pasos son correctos y están
  verificados, pero conviene que puedas rehacer el Paso 3 en la pizarra sin mirar.

**Ejercicio 3.5a.** Calculá `PRIM(pred_s)` y `SGTE(pred_s)`, y explicá cómo decide el parser la alternativa `ε`.

<details><summary>Respuesta</summary>

`PRIM(pred_s)` = {NEG, V_COP, V_EST, SE, V_CONT, V_ACC, INT, ADJ, TICKET, ε}. Los de `modif` son {INT, ADJ}.

`SGTE(pred_s)`: `pred_s` es el último símbolo de `nucleo → sujeto pred_s`, así que SGTE(pred_s) ⊇ SGTE(nucleo). En
`clausula → adv_t_op nucleo frec`, PRIM(frec) = {FREC, ε} aporta FREC y, por la ε, se agrega SGTE(clausula). En
`oracion → clausula cola`, PRIM(cola) = {PERO, COMA, Y, ε} aporta PERO, COMA e Y, y por la ε se agrega SGTE(oracion) =
{PUNTO, EOL}. Resultado: {FREC, COMA, PERO, Y, PUNTO, EOL}.

`pred_s → ε` se elige cuando el lookahead es uno de esos seis. Como son disjuntos de los PRIM de las otras
alternativas, no hay conflicto. Ejemplo: «la atención.» → mención NEUTRA.
</details>

**Ejercicio 3.5b.** En L1, ¿por qué `lista_r` tiene conflicto PRIM∩SGTE?

<details><summary>Respuesta</summary>

En L1, `texto → lista | lista PUNTO` y `lista_r → PUNTO oracion lista_r | ε`. PRIM(`lista_r`) = {PUNTO, ε}, y
SGTE(`lista_r`) = SGTE(`lista`) = {PUNTO, EOL} (por `texto → lista PUNTO`). PUNTO está en ambos: después de una
oración, con lookahead PUNTO, el parser no sabe si el punto separa otra oración o termina el texto. El Paso 3 lo
resuelve consumiendo el punto (`texto_r → PUNTO texto_rr`) y decidiendo con el token siguiente: un PRIM de
`oracion` u `EOL`.
</details>

---

### 3.6 Parser y recuperación de errores (`sintaxis.py`)

**Qué hace.** Un único procedimiento `parse(A)` consulta `M[A, lookahead]`, elige la producción, llama a `parse()`
por cada variable y a `_match()` por cada terminal. Es el analizador predictivo de clase con la pila de llamadas
en lugar de la pila explícita, lo que permite devolver el árbol de derivación. Dentro de un turno, `EOL` cumple el
papel de `$`.

**Qué profundizar.**
- Cómo se construye `M` en `tabla_ll1()`: para cada producción `A → α`, se carga `M[A, a]` para cada `a` en
  PRIM(α); si α es anulable, también para cada `b` en SGTE(A).
- Las tres situaciones de error y su acción:

| Situación | Acción | Efecto |
|---|---|---|
| Terminal esperado ≠ token | se informa y no se consume (se «desapila» el terminal) | `_match()` devuelve `None` |
| `M[A, a]` vacía y `a ∉ SGTE(A)` | se informa y se descartan tokens hasta uno de PRIM(A) ∪ SGTE(A) ∪ {EOL} | modo pánico |
| `M[A, a]` vacía y `a ∈ SGTE(A)` | se abandona `A` sin consumir | nodo `A!ERROR` |

- **La cláusula como unidad de recuperación.** Si hubo un error dentro de una `clausula`, el nodo queda marcado,
  no se evalúa, y sus tokens pasan a NO_INTERPRETADO. El resto del turno se sigue analizando.
- **Terminación.** `EOL` pertenece a todo conjunto de sincronización, así que el descarte siempre termina.

**Qué considerar.**
- Se informa **un** error por celda vacía, no uno por token descartado (diferencia con el pseudocódigo de clase).
- «No funciona el internet» (sujeto después del verbo) ahora se reconoce con `sujp`. Siguen fuera de la gramática
  «sigue sin funcionar» («sin» + verbo) y «revisaremos TK-204 mañana» (dos complementos): la cláusula entera queda
  NO_INTERPRETADO.

**Ejercicio 3.6.** ¿Qué celdas de `M` deciden «pero sigo sin internet» en el caso 02? ¿Qué pasa con «El servicio
está pero lento.»?

<details><summary>Respuesta</summary>

`M[cola_c, PERO] = cola_c → PERO clausula cola`; `M[nucleo, V_CONT] = nucleo → pred_l` (V_CONT no está en
PRIM(sujeto)); `M[pred_l, V_CONT] = pred_l → V_CONT compl`; `M[compl, SIN] = compl → SIN SUST`.

«El servicio está pero lento.»: tras `V_COP`, el parser llama a `parse(atrib)` con lookahead PERO; la celda está
vacía y PERO ∈ SGTE(atrib), así que se abandona `atrib`. La primera cláusula queda marcada con error. Después,
`cola → PERO clausula cola` y `parse(clausula)` con lookahead ADJ: celda vacía, se descarta «lento» y se abandona
la cláusula. Ninguna cláusula se interpreta. Verificalo con `--traza S01 --detalle`.
</details>

---

### 3.7 Semántica y estado (`semantica.py`, `REGLAS_SEMANTICAS.md`)

**Qué hace.** Evalúa el árbol con reglas asociadas a **producciones** (`@acc(variable, producción)`). Cada regla
devuelve atributos sintetizados al padre. Cada cláusula produce un *hecho* con `tipo`, `aspecto`, `valoracion`,
`intensidad`, `negada`, `declaracion` (OK, FALLA, RECUR) y la lista de reglas aplicadas.

**En números.** 46 reglas por producción. Las 12 producciones restantes de la gramática lingüística son estructurales
(`texto`, `oracion`, `cola`…) y las resuelve el recorrido `clausulas()`, que además calcula el conector (`PERO`,
`COMA`, `Y`, `PUNTO`) de cada cláusula. 27 reglas con identificador `R-…`: 21 de producción y 6 de estado. 33 perfiles.

**Qué profundizar (alta prioridad).**
0. **Dónde está el significado de cada palabra.** En los **rasgos** de su forma canónica, en la tabla de símbolos
   léxica. La regla lee los atributos que `sig()` calcula con esos rasgos: `modif → ADJ : modif.pol = ADJ.p.pol`,
   `sujeto → SUST : sujeto.asp = SUST.p.asp`, `pred → V_EST compl : pred.pol = (V_EST.p.pol = −1) ? −1 : …`. Es el
   atributo de un token que apunta a su entrada en la tabla de símbolos (Clase 6, §6.1). Las combinaciones válidas de
   rasgos (perfiles) están en `semantica.PERFILES`.
1. **Atributos sintetizados y heredados.** `pol`, `int`, `k`, `neg`, `asp` son sintetizados (valor de retorno).
   El actor, el turno y el conector bajan desde el turno: son heredados, pero se implementan fuera de `ev()`, en el
   recorrido. Conviene que lo puedas explicar con el cuadro **BNF | Reglas semánticas** de `REGLAS_SEMANTICAS.md`.
2. **`_construir()`**, el paso que convierte un predicado en hecho: primero la **compatibilidad** (tabla `COMPAT`,
   regla R-COMPAT: qué tipo de predicado admite cada clase de sujeto, y que «se» vaya solo con el perfil RECUR; si no es
   compatible la cláusula se abstiene), después el aspecto (del sujeto explícito o pospuesto, del propio predicado, o SERVICIO por defecto), la
   negación (invierte la polaridad **una sola vez**), la declaración (solo sobre el SERVICIO: `EST`, `SEG_ADJ` y
   `SEG_SIN` → OK o FALLA; `CORTE` sin negar → RECUR) y el tipo.
   - Tipos de predicado (`k`): `COP` (cópula + cualidad), `EST` (verbo de estado), `CORTE` («se corta»), `SEG_ADJ` y
     `SEG_SIN` (seguir), `ENT` (entender), `VAL` (atender, explicar), `SOLIC`, `COMPR`, `REF` (ticket), `MENCION`.
   - **«sin» + sustantivo** (R-SIN): «sin internet» es negativo; «sin cortes» es positivo porque el perfil PROBLEMA tiene
     polaridad −1.
   - **`SIN_DOMINIO`** (R-SINDOM): si alguna palabra de la cláusula tiene el rasgo `sin_dominio`, la cláusula se reconoce entera
     y no se interpreta. Se revisa antes de evaluar el núcleo.
3. **Combinación por aspecto (`combinar`).** POSITIVA y NEGATIVA juntas → **MIXTA** (no es promedio ni
   cancelación); solo una → esa; solo NEUTRA → NEUTRA; nada → SIN_EVIDENCIA.
4. **Resumen de la sesión.** Solo con evidencia del **CLIENTE**. Las opiniones del AGENTE se conservan aparte
   (`opiniones_agente`) y no entran en el estado.
5. **Estado** (`decidir_estado`). Se recorren las declaraciones del cliente, turno por turno:

| # | Condición en el turno | Estado | Regla |
|---|---|---|---|
| 1 | hay OK y RECUR, y la última es OK o RECUR | TEMPORAL | R-EST-TEMP |
| 2 | la última es OK | RESUELTO | R-EST-RES |
| 3 | la última es RECUR y antes estaba RESUELTO o TEMPORAL | TEMPORAL | R-EST-TEMP |
| 4 | en otro caso (FALLA, o RECUR sin recuperación previa) | NO_RESUELTO | R-EST-NORES |

   Sin declaraciones del cliente: compromiso del agente → PENDIENTE; si no, NO_CONFIRMADO.

   **Precedencia (`R-EST-PREC`), respuesta del profesor: prevalece lo último.** Si después de la última declaración
   del cliente el agente promete algo («mañana revisaremos TK-…»), la sesión queda **PENDIENTE**, sea esa declaración
   una falla o una confirmación. Si el cliente declara después de la promesa, prevalece el cliente. Una cortesía
   («Gracias») no es declaración y no cambia quién habló último. Coincide con la definición de PENDIENTE del
   enunciado: «compromiso futuro sin confirmación posterior del CLIENTE».

**Qué considerar (las decisiones discutibles).**
- «El servicio **está** lento» es una valoración NEGATIVA pero **no** una declaración de funcionamiento: no fija
  estado (caso 05 → NO_CONFIRMADO). «**Sigue** lento», «**no funciona**», «**se corta**» sí declaran.
- «La atención sigue mala» valora la ATENCION y no declara nada sobre el funcionamiento.
- «Ahora funciona» es evidencia POSITIVA del SERVICIO (necesario para que el caso 03 dé MIXTA).
- `AGENTE` como sujeto («el agente fue amable») se interpreta como ATENCION.
- El router (perfil EQUIPO) como sujeto valora el SERVICIO: «el router no anda» → SERVICIO NEGATIVA, FALLA.
- «No se corta» valora el SERVICIO como POSITIVA pero **no** declara que funcione.
- Un verbo de falla no se vuelve positivo por el adjetivo: «falla» es negativo siempre.
- «El agente no entendió» queda en abstención (`AGENTE` no admite `ENT` en `COMPAT`).
- **Una cláusula sin sujeto toma el aspecto por defecto SERVICIO**: «está lento» → SERVICIO. Combinado con el
  descarte de palabras desconocidas, «…pero el técnico fue amable» se lee como «fue amable» → SERVICIO POSITIVA. Es un
  límite conocido (ver sección 5); registrar «técnico» como `SIN_DOMINIO` lo evita.
- `INT` («muy») marca intensidad y no cambia la polaridad: «no es muy bueno» → NEGATIVA, intensidad ALTA.
- Interruptor `LO_ULTIMO_PREVALECE` (por defecto `True`, por la respuesta del profesor): con `False` vuelve a la
  lectura literal del enunciado (la declaración del cliente prevalece siempre) y cambian los casos 10 y 15.

**Ejercicio 3.7a.** ¿Qué hecho produce «No entendí la explicación»? ¿Y «La atención sigue mala»?

<details><summary>Respuesta</summary>

«No entendí la explicación»: `pred_l → NEG pred_neg`, `pred_neg → V_ACC obj modif_op`; «entendí» es `V_ACC/ENTENDER`,
de perfil COMPRENSION. Predicado `k=ENT`, `asp=CLARIDAD` (lo da el perfil), `pol=+1`, `neg=verdadero`. Sin sujeto →
compatible; la negación invierte → NEGATIVA; `ENT` no declara funcionamiento → tipo VALORACION. Reglas: R-ENT, R-NEG.

«La atención sigue mala»: `nucleo → sujeto pred_s`, `sujeto → SUST` («atención», perfil ATENCION),
`pred_s → V_CONT compl`, `compl → modif`. `SEG_ADJ` está en `COMPAT[ATENCION]` → compatible. Aspecto ATENCION,
NEGATIVA; como el aspecto no es SERVICIO, no hay declaración → el estado queda NO_CONFIRMADO. Reglas: R-SUJ, R-SEG-ADJ.
</details>

**Ejercicio 3.7b.** Caso 13: T1 «El internet sigue lento.», T2 (agente) «Reinicie el router.», T3 «Ahora funciona,
pero el servicio se corta todos los días.» ¿Valoración del SERVICIO y estado?

<details><summary>Respuesta</summary>

T1: `pred_s → V_CONT compl` → SERVICIO NEGATIVA, declaración FALLA. T3: C3.1 «Ahora funciona» (`V_EST` de perfil OK,
sin complemento) → POSITIVA, OK; C3.2 «el servicio se corta todos los días» (`pred_s → SE V_EST compl`, «corta» de
perfil RECUR, con `frec` al final de la cláusula) → NEGATIVA, RECUR. SERVICIO = **MIXTA**. Estado: T1 deja NO_RESUELTO (fila 4); T3 tiene OK y
RECUR y termina en RECUR (fila 1) → **TEMPORAL**. La solicitud del agente no es compromiso ni valoración.
</details>

**Ejercicio 3.7d.** Caso 16: «No funciona el internet y el router falla seguido.» y, en otra sesión, «El agente se
corta.» ¿Qué produce cada cláusula?

<details><summary>Respuesta</summary>

«No funciona el internet»: `pred_l → NEG pred_neg`, `pred_neg → V_EST compl sujp`, `sujp → SUST` (perfil
SERVICIO). El sujeto pospuesto aporta el aspecto SERVICIO; `EST` con negación → NEGATIVA, FALLA (R-EST, R-POSP, R-NEG).
«Y» abre otra cláusula: «el router falla seguido» → `sujeto → SUST` (perfil EQUIPO), `pred_s → V_EST compl` con
«falla» de perfil FALLA → NEGATIVA, FALLA, entidad ROUTER.

«El agente se corta»: la gramática lo acepta (`sujeto(AGENTE) pred_s → SE V_EST compl`), pero `CORTE` no está en
`COMPAT[AGENTE]`: R-COMPAT, la cláusula no se interpreta y sus tokens quedan NO_INTERPRETADO con el motivo
`SUJETO_PREDICADO_INCOMPATIBLE`.
</details>

**Ejercicio 3.7c.** Caso 10: T1 «La conexion esta inestabl.», T2 (agente) «Mañana revisaremos TK-310.», T3 «Ahora
funciona bien.», T4 (agente) «Revisaremos TK-310.» ¿Estado?

<details><summary>Respuesta</summary>

La última declaración del cliente es T3 (OK → RESUELTO), pero en T4 el agente vuelve a prometer. Prevalece lo último
→ **PENDIENTE** (`R-EST-PEND`, con la nota de `R-EST-PREC`). Con `LO_ULTIMO_PREVALECE = False` daría RESUELTO. Si
en cambio el cliente hubiera dicho «Sigo sin internet» *después* de la promesa, prevalece el cliente: NO_RESUELTO
(caso 15, sesión S02).
</details>

---

### 3.8 Salida y trazabilidad (`analizador.py`, `main.py`)

**Qué hace.** Produce un JSON por lote y una vista de consola. Por sesión: id, análisis COMPLETO o PARCIAL,
valoraciones por turno, resumen por aspecto, estado con regla y evidencias, entidades (tabla de entidades),
correcciones, errores, NO_INTERPRETADO y evidencias.

**Qué profundizar.**
- **La traza en 6 pasos** que pide el enunciado: `[1]` texto original → `[2]` tokens → `[3]` estructura →
  `[4]` tabla de entidades → `[5]` acción semántica → `[6]` resultado. Las decisiones del usuario sobre palabras
  desconocidas aparecen en `[2]`, en las líneas `corrector`.
- **Identificadores de cláusula** `C<turno>.<k>`: `k` es la posición textual de la cláusula en el turno (cuenta
  también las que tuvieron error, por eso puede haber huecos). Son únicos dentro de la sesión, no en el lote.
- **Fragmento** de una evidencia: desde el primer token de la cláusula (extendido hacia atrás sobre los `RELLENO`
  contiguos, para incluir «El» o «Me») hasta el final del último token.

---

### 3.9 Pruebas (`pruebas.py`, `casos/`)

| Casos | Origen | Qué prueba |
|---|---|---|
| 01–08 | enunciado | resuelto, contraste, temporal, claridad, corrección + ticket, pendiente, rol inválido, empate |
| 09 | propio | negación + contraste |
| 10 | propio | corrección única + precedencia: el agente promete después de la confirmación → PENDIENTE |
| 11 | — | **eliminado** (era «Mi router hace ruidos raros»: abstención por palabras desconocidas). La numeración se conserva; la abstención sigue cubierta por 08 (empate), 12 y 19/20 sin consulta |
| 12 | propio | recuperación: rol inválido, ticket mal formado con error sintáctico, orden inconsistente (descarta el resto) |
| 13 | propio | sujeto explícito con «sigue» y «se corta» → TEMPORAL |
| 14 | propio | salto de número («1, 3, 4» → solo el 1); id de sesión repetido |
| 15 | propio | precedencia «prevalece lo último»: falla + promesa → PENDIENTE; promesa + falla → NO_RESUELTO; confirmación + promesa → PENDIENTE |
| 16 | propio | sujeto pospuesto, «y», router como sujeto, «falla», «no me atendieron bien», «sin cortes»; incompatibilidad sujeto–predicado → abstención |
| 17 | propio (alcance) | lentitud y reinicio del router: la solicitud del agente no valora ni fija estado; en S01 el reinicio no resuelve (NO_RESUELTO), en S02 sí (RESUELTO) |
| 18 | propio (alcance) | cortes y seguimiento de tickets: ticket asignado y escalado (una entrada, dos apariciones, seguimiento `COMPROMISO_FUTURO`); el cliente declara después → NO_RESUELTO; el mismo TK-512 en S02 es otra entrada (ámbito sesión) → PENDIENTE |
| 19 | propio (alcance, **inserción**) | falta de conexión con palabras fuera del vocabulario: «intermitente» → variante de `ADJ/INESTABLE`, «conecta» → variante de `V_EST/FUNCIONAR`; se pregunta una vez y vale para el turno 3 → MIXTA, RESUELTO. Sin consulta: SIN_EVIDENCIA, NO_CONFIRMADO |
| 20 | propio (alcance, **inserción**) | cortes y tickets con formas canónicas nuevas: `V_EST/DESCONECTAR` (perfil RECUR) y `V_ACC/VERIFICAR` (perfil COMPROMISO) → NEGATIVA, PENDIENTE. Sin consulta: el corte no se interpreta y la promesa queda como mención del ticket |

**Qué considerar.**
- Cada caso tiene un esperado explícito en `casos.json`; `--regresion` compara además el JSON completo con
  `casos/golden/`.
- **Las pruebas detectan cambios de regla** (prueba de mutación): si MIXTA se promediara a POSITIVA fallan 01, 03,
  07, 10, 12, 13, 16, 17, 18 y 19; si la negación dejara de invertir fallan 04, 09, 14, 16, 17 y 18.
- **Tabla léxica.** `pruebas.py` también corre 13 pruebas con respuestas simuladas en una carpeta temporal: se
  pregunta solo después del corrector; inserción como variante; lo aprendido va aparte, con el formato de la precarga;
  empate con candidatos; alta de forma canónica (nombre normalizado, rasgos del perfil elegido); vale
  para el resto de la entrada; duplicados; `SIN_DOMINIO`; reconocimiento en una ejecución posterior; precarga intacta;
  rasgos validados al cargar; reinicio; baja por precarga.
- **Modo no interactivo.** Los casos y el golden se corren sin preguntas y solo con la precarga: lo aprendido nunca
  cambia los resultados esperados.
- **Casos 17 a 20: el alcance del enunciado** (§1: «falta de conexión, lentitud, cortes, reinicio del router y
  seguimiento de tickets»). 19 y 20 tienen palabras fuera del vocabulario: `casos.json` guarda las respuestas al menú
  (simbólicas: `#ADJ`, `@ADJ/INESTABLE`, `%V_EST/RECUR`), las preguntas esperadas y el `esperado_sin_consulta`.
  `pruebas.py` las simula sobre una tabla **solo en memoria** desde la precarga, así el resultado es reproducible y
  no toca `vocabulario_aprendido.json`. Las comprobaciones son discriminantes: si falta una respuesta, o se elige el
  perfil FALLA en vez de RECUR para «desconecta», el caso 20 falla (con FALLA, «se desconecta» cae en R-COMPAT).

**Ejercicio 3.9a.** Corré el caso 19 de las dos formas: `python3 main.py casos/caso_19.txt < /dev/null` y
`python3 main.py casos/caso_19.txt` respondiendo `n` → `ADJ` → `INESTABLE` y `n` → `V_EST` → `FUNCIONAR`. ¿Qué cambia
y por qué no se pregunta por el segundo «conecta»?

<details><summary>Respuesta</summary>

Sin respuestas, «intermitente» y «conecta» no tienen candidato a distancia 1 y se descartan; el parser recibe
«conexion esta y el modem no» y «Ahora bien», que no deriva: errores SINTAXIS, SERVICIO SIN_EVIDENCIA, NO_CONFIRMADO.
Con respuestas, T1 da «la conexión está intermitente» (VALORACION NEGATIVA, R-COP) y «el modem no conecta» (FALLA,
R-EST + R-NEG), y T3 «Ahora conecta bien» (OK) → SERVICIO MIXTA, **RESUELTO** (la última declaración del cliente es
OK). El segundo «conecta» no se pregunta porque la inserción se agrega al índice del corrector en el momento: lo
aprendido vale para el resto de la misma entrada. Al final, `python3 main.py --reiniciar-aprendido`.
</details>

**Ejercicio 3.9b.** En el caso 20, ¿por qué «desconecta» tiene que ser una forma canónica de perfil RECUR y no
FALLA, y por qué la sesión queda PENDIENTE?

<details><summary>Respuesta</summary>

La frase es «se desconecta»: con «se», la gramática usa `pred_s → SE V_EST compl` y la semántica exige el rasgo
`pronominal` (perfil RECUR). Con FALLA el verbo no es pronominal y la cláusula cae en R-COMPAT (abstención). Con RECUR
da SERVICIO NEGATIVA, declaración RECUR. Después el agente promete «Mañana verificaremos TK-620» (VERIFICAR, perfil
COMPROMISO): la promesa es posterior a la última declaración del cliente y, con `LO_ULTIMO_PREVALECE`, la sesión
queda **PENDIENTE** (R-EST-PEND). El ticket se actualiza con `seguimiento = COMPROMISO_FUTURO`.
</details>
- El enunciado pide al menos un caso de regresión que siga funcionando después de modificar una regla: en la
  defensa, el flujo es *modificar → `python3 pruebas.py --regresion` → explicar qué casos cambian y por qué*.

---

## 4. Decisiones de diseño que vas a defender

| Decisión | Por qué | Alternativa | Dónde |
|---|---|---|---|
| El lexer no ve contexto (`agente` siempre `AGENTE`) | Separación de fases; el parser decide por posición | Categorías distintas por contexto | `lexico.py` |
| `TICKET_MAL` como patrón propio | Error léxico específico en vez de `PALABRA - NUM` | Dejar que se parta en tres tokens | `lexico.py` |
| Corrección con `MIN_LONG = 4` | Evitar «mas» → «mal» | Corregir cualquier longitud | `corrector.py` |
| Formato validado línea a línea | `EOL` como punto de sincronización; reglas `n+1` fuera de la BNF | Todo en el parser | `lector.py` |
| `PUNTO` obligatorio entre oraciones | Mantener la gramática LL(1) | Gramática no LL(1) | `gramatica.py` |
| Un `parse(A)` guiado por la tabla | Mismo algoritmo de clase, devuelve árbol, la tabla y el parser no se desincronizan | Un procedimiento por variable | `sintaxis.py` |
| La cláusula es la unidad de abstención | Un error no contamina el resto del turno | Descartar el turno entero | `sintaxis.py`, `analizador.py` |
| Negación con alcance gramatical | No cruza `PERO`/`COMA`/`Y`; se explica con el árbol | Ventana de palabras | `gramatica.py`, `semantica.py` |
| Diccionario de tres niveles con categorías generales | Es la estructura que pide el enunciado; la gramática queda chica (19 terminales, 170 celdas) | Subcategorías con significado (`ADJ_NEG`…), o rasgos guardados en el diccionario | `vocabulario.json`, `gramatica.py` |
| Rasgos en cada forma canónica, validados contra perfiles cerrados | Una palabra o forma canónica nueva no requiere código; un significado nuevo sí (es un cambio del modelo) | Significado en el código por forma canónica (sin poder crear canónicos desde el menú) | `vocabulario.json`, `semantica.PERFILES` |
| Rasgos en el mismo JSON, no en `significados.json` aparte | Interactividad: una escritura atómica por cambio, un objeto vivo para lo aprendido, mismo formato en precarga y aprendido | Tabla de significados separada (probada y descartada) | `tabla_lexica.py` |
| Menú de inserción cerrado | El usuario no puede crear categorías, perfiles ni rasgos que la gramática o la semántica no conozcan | Categorías libres (como la rama `prueba`: pegan palabras) | `consulta.py` |
| `SIN_DOMINIO` en lugar de descartar | La cláusula se abstiene entera; no se inventa una valoración con lo que queda | `FUERA_DE_GRAMATICA` / `RELLENO` | `semantica.PERFILES`, `_clausula` |
| Consulta solo después del corrector | Respeta la regla del enunciado; solo se pregunta lo que la regla no resuelve | Preguntar por toda palabra desconocida | `corrector.py`, `consulta.py` |
| Verbos agrupados por construcción | Un verbo nuevo hereda la construcción de su grupo | Una producción por verbo | `gramatica.py` |
| Compatibilidad sujeto–predicado en la semántica | La gramática general acepta de más; es el chequeo de tipos | Una variante de predicado por tipo de sujeto en la gramática | `COMPAT` en `semantica.py` |
| «se corta» con `SE` obligatorio | «corta» sin «se» es la lectura transitiva; lo controla el perfil RECUR | Una producción propia para «se corta» | `semantica.py` (`_p_est`) |
| `SIN` separado de `NEG`; `Y` como conector | «sin» va con sustantivo; «y» une cláusulas | Ambos como antes (`NEG`, `RELLENO`) | `vocabulario.json`, `gramatica.py` |
| MIXTA = ambas polaridades | El enunciado prohíbe promediar | Promedio o mayoría | `combinar()` |
| Opiniones del agente aparte | No son confirmaciones del cliente | Mezclarlas en el resumen | `resumen_aspectos()` |
| «Está lento» no fija estado | Es una valoración, no una declaración de funcionamiento | Tratarla como FALLA | `_construir()` paso 6 |
| Prevalece lo último (promesa posterior → PENDIENTE) | Respuesta del profesor; coincide con la definición de PENDIENTE | La declaración del cliente prevalece siempre (enunciado §5) | `LO_ULTIMO_PREVALECE` en `semantica.py` |
| Orden inconsistente descarta el resto de la sesión | Respuesta del profesor («eliminamos todo lo que viene después») | Rechazar solo el turno fuera de orden | `lector.py` |
| Dos tablas: léxica persistente y de entidades efímera | El profesor pidió persistencia y enriquecimiento; el enunciado, separar el vocabulario | Una sola tabla, o persistir también las entidades | `tabla_lexica.py`, `entidades.py` |
| Persistencia en JSON, sin archivo de auditoría | Se lee y se versiona en git; sin dependencias; lo aprendido se ve con `--tabla` y cada inserción en el JSON de resultados | SQLite; auditoría `.jsonl` (se quitó) | `tabla_lexica.py` |
| Corregir con el candidato solo esa aparición | Los errores de tipeo no ensucian la tabla | Guardar la variante | `consulta.py` |

---

## 5. Límites conocidos (verificados)

| Entrada | Resultado | Motivo |
|---|---|---|
| «Sigue sin funcionar.» / «Revisaremos TK-204 mañana.» | la cláusula queda NO_INTERPRETADO | «sin» + verbo y dos complementos no están en la gramática |
| «Esta conexión es lenta.» | no se interpreta | «esta» demostrativo se confunde con la cópula «está» |
| «Muy lento.» | no se interpreta | un adjetivo suelto solo se admite después de un sujeto |
| «…pero el técnico fue amable» (con «técnico» desconocida) | «fue amable» → **SERVICIO POSITIVA** | la palabra se descarta y la cláusula toma el aspecto por defecto; se evita con `SIN_DOMINIO`; regla general R-DESC propuesta (`INFORME_TECNICO.md` §9) |
| «Hace dos días que no funciona.» con «hace» como `SIN_DOMINIO` | la cláusula se abstiene y se pierde la FALLA | la construcción temporal «hace + tiempo» no está en la gramática |
| «El agente se corta.» | se reconoce pero no se interpreta | incompatibilidad sujeto–predicado (R-COMPAT) |
| «falla», «corte» | una sola lectura (verbo / sustantivo) | una forma tiene una sola categoría |
| «El servicio está lento la atención fue buena.» | solo la primera oración se interpreta | falta el punto entre oraciones |
| «amabel» | no se corrige | la transposición cuesta 2 en Levenshtein |
| «Ya reinicié el router.» (CLIENTE) | cláusula de tipo SOLICITUD | «reinicié» se pliega a «reinicie»: una forma, una categoría, sin tiempos verbales; no cambia valoraciones ni estado |
| Palabra desconocida que el usuario no inserta | se descarta y el resto se interpreta | el filtro previo al parser la aparta (ver la fila del «técnico») |
| AFD completo | 409 estados, sin minimizar | solo se muestra y se garantiza mínimo el de `TICKET` |
| Equivalencia L0 = L3 | verificada hasta 5 tokens | es acotada, no una demostración |
| Tokens de la cabecera del turno | `turno = None` | solo los del texto reciben el número |

---

## 6. Preguntas para el profesor

### Respuestas recibidas y qué se hizo

| Pregunta | Respuesta | Qué se hizo |
|---|---|---|
| ¿La tabla de símbolos persiste entre ejecuciones? | Sí: se precarga, se enriquece sesión a sesión y, si falta un símbolo, el programa pregunta a qué token corresponde | Tabla de símbolos léxica persistente con consulta (3.4). La tabla de entidades sigue por sesión, sin persistir: **conviene confirmarlo**, porque la pregunta original era sobre las entidades |
| Promesa del agente posterior a «sigo sin internet» | «Se tiene en cuenta lo último nomás, o sea lo que dijo el agente» | Prevalece lo último: PENDIENTE (3.7, casos 10 y 15) |
| ¿Un turno con NO_INTERPRETADO vuelve PARCIAL la sesión? | «Por falta de FIN nomás» | **No se cambió**: el caso 07 del enunciado exige PARCIAL por un turno rechazado. Pendiente de confirmar citándole el caso 07 |
| Numeración «1, 3, 4» | «Eliminamos todo lo que viene después del 1» | Orden inconsistente descarta el resto de la sesión (3.1, casos 12 y 14) |

Preguntas nuevas que conviene llevar:

- **Formas canónicas desde el menú.** ¿Es aceptable que el usuario cree formas canónicas eligiendo un perfil
  existente, y que un significado nuevo requiera código?
- **Palabras desconocidas descartadas.** ¿Prefiere que una cláusula se abstenga si se descartó una palabra
  desconocida en su tramo (R-DESC)? Corregiría «el técnico fue amable» → SERVICIO POSITIVA.

### Preguntas originales

Ordenadas por impacto. Las del bloque A pueden cambiar resultados de los casos; las del bloque B, la nota de BNF,
parser o léxico.

### A. Interpretación del enunciado

1. **«El servicio está lento» sin otra declaración**: ¿es una declaración de que la falla persiste (NO_RESUELTO)
   o solo una valoración negativa (hoy queda NO_CONFIRMADO, caso 05)?
2. ~~**Precedencia con promesa posterior**~~ — respondida: prevalece lo último (PENDIENTE).
3. **Opiniones del agente**: ¿deben contar en el resumen por aspecto? Hoy se listan aparte y no influyen.
4. **Valoración por turno del agente**: hoy un turno del agente muestra sus propias valoraciones (con su autoría).
   ¿Es lo esperado?
5. **NEUTRA**: hoy solo se produce con un sujeto sin predicado («la atención»). ¿Qué ejemplo de NEUTRA espera la
   cátedra?
6. **Análisis PARCIAL** — respondida («solo por falta de FIN»), pero contradice el caso 07 del enunciado. Repreguntar:
   en el caso 07 (rol `SOPORTE`, sesión con `FIN`), ¿la primera sesión es PARCIAL o COMPLETA?
7. ~~**Numeración de turnos**~~ — respondida: se descarta todo lo posterior al 1. Queda sin respuesta si un id de
   sesión repetido debe rechazarse (hoy se rechaza la segunda sesión).
8. **Corrector**: ¿es aceptable el mínimo de 4 letras para corregir? ¿La transposición («amabel») debería contar
   como distancia 1 (Damerau) o se usa Levenshtein estricto?
9. ~~**Orden libre**~~ — resuelto en el diseño: el sujeto después del verbo se reconoce con `sujp`.

### B. Metodología

10. **Parser**: ¿se acepta un único procedimiento `parse(A)` guiado por la tabla `M` (descendente recursivo con la
    pila de llamadas), o se espera un procedimiento por no terminal como en los ejemplos de clase?
11. **Recuperación**: ¿alcanza con informar un error por celda vacía, o debe informarse cada token descartado?
12. **Gramática original**: ¿hay que presentar una gramática descriptiva previa y su transformación paso a paso
    (como en `DERIVACION.md`)? ¿Es suficiente la verificación de equivalencia por enumeración acotada?
13. **AFD**: ¿basta con mostrar ER → AFN → AFD de una categoría (`TICKET`) y declarar que el resto se genera con el
    mismo algoritmo? ¿Hay que dibujar el AFN de Thompson completo, o minimizar el AFD completo?
14. **Tabla LL(1)**: ¿el informe debe incluir la tabla `M` completa (170 celdas) o bastan PRIM, SGTE y las
    decisiones por variable?
15. **Atributos heredados**: actor, turno y conector se propagan en un recorrido aparte, no como parámetros de cada
    regla. ¿Es aceptable si el cuadro BNF | Reglas semánticas los documenta?
16. **Dos niveles de gramática**: ¿es válido que el formato lo procese el lector línea a línea y el texto el parser
    LL(1), con una única BNF que describe ambos?

### C. Entrega y defensa

17. ¿El informe técnico debe ser un único documento? ¿Hay un formato o una extensión esperada? (Hoy: `INFORME_TECNICO.md`
    con los documentos de apoyo.)
18. En la defensa, ¿la modificación de regla se hace en vivo sobre nuestro código? ¿Cuánto tiempo hay?
19. ¿Qué nivel de detalle se espera en la declaración de uso de IA y de contribuciones?

---

## 7. Ensayo de la defensa

La defensa tiene tres partes: una ejecución (conocida o reservada), una traza y una modificación breve de regla.

**Ejecución y traza.** Practicá con un caso que no sea de los tuyos: escribí una sesión nueva, ejecutala con
`--traza S01 --detalle` y explicá cada uno de los 6 pasos en voz alta.

**Modificaciones para practicar.** Para cada una: hacela, corré `python3 pruebas.py --regresion`, explicá qué casos
cambian y por qué, y deshacela.

| Pedido posible | Dónde se toca |
|---|---|
| Agregar una palabra («fatal» como cualidad negativa, «colapsa» como verbo de falla) | en ejecución: `n` → categoría → forma canónica existente (`ADJ/MALO`) o nueva con los rasgos de un perfil existente (`V_EST`, perfil FALLA); para la precarga: una entrada en `vocabulario.json` con los rasgos de un perfil |
| Que el router no cuente como SERVICIO | quitar `aspecto` del perfil `EQUIPO` en `semantica.PERFILES` **y** de los rasgos de `SUST/ROUTER` en `vocabulario.json`; ya **ningún caso lo detecta** (lo detectaba solo el 11, eliminado): para cubrirlo hace falta un caso con el router mencionado sin cualidad («El router.» da hoy SERVICIO NEUTRA); si se cambia solo el perfil, la carga rechaza `SUST/ROUTER` |
| Que «el agente no entendió» valore la ATENCION | agregar `ENT` a `COMPAT['AGENTE']` |
| Que «no se corta» declare que funciona | paso 6 de `_construir()` |
| Agregar un significado nuevo (p. ej. un perfil FACTURACION de `SUST`) | `semantica.PERFILES` (plantilla de rasgos) + `COMPAT` + reglas que lo usen; después ya se pueden crear canónicos de ese perfil desde el menú |
| Que una palabra deje de interpretarse (abstención) | registrarla con perfil `SIN_DOMINIO` desde el menú |
| Que «sigue + adjetivo positivo» no confirme el funcionamiento | `_construir()` paso 6, o `_p_seguir` |
| Que «el agente fue amable» no cuente como ATENCION | `_sujeto_agente` |
| Que la declaración del cliente prevalezca siempre sobre las promesas | `LO_ULTIMO_PREVALECE = False` (cambian los casos 10 y 15) |
| Que un turno fuera de orden se rechace solo (sin descartar el resto) | `lector.py`, bloque de `truncada` |
| Corregir también palabras de 3 letras | `MIN_LONG` en `corrector.py` |
| Admitir una construcción nueva | producción en `gramatica.py` + regla `@acc` en `semantica.py`; `python3 gramatica.py` debe seguir sin conflictos |

**Preguntas rápidas que te pueden hacer.**
- ¿Qué diferencia hay entre una categoría léxica y una forma canónica?
- ¿Dónde está definido que «lento» es negativo? ¿Y que «internet» habla del SERVICIO? (Tabla léxica → forma canónica →
  rasgos → atributos.)
- ¿Qué puede crear el usuario desde el menú y qué no? ¿Por qué?
- ¿Por qué los rasgos se guardan en `vocabulario.json` y no en un archivo aparte? ¿Qué se pierde con esa decisión?
- ¿Qué diferencia hay entre registrar una palabra como `SIN_DOMINIO` y como `FUERA_DE_GRAMATICA`?
- ¿Por qué «el agente se corta» se reconoce pero no se interpreta?
- Si inserto «colapsa» como variante de `V_EST/FALLAR`, ¿qué frases nuevas se interpretan sin tocar la gramática?
- ¿Por qué `TK-204` no se reconoce como `PALABRA`? ¿Y `no` como `PALABRA`?
- ¿Qué es una cláusula y por qué es la unidad de la semántica?
- ¿Por qué el caso 02 es NO_RESUELTO si la atención es POSITIVA?
- ¿Por qué el caso 03 es TEMPORAL y no RESUELTO?
- ¿Qué pasa con un turno de rol `SOPORTE`?
- Mostrá en la traza dónde se insertó un ticket en la tabla de entidades.
- ¿Qué diferencia hay entre la tabla de símbolos léxica y la tabla de entidades? ¿Cuál persiste y por qué?
- ¿Dónde queda registrado lo que se inserta? ¿Y cuando se elige un candidato de un empate? (Inserción y alta:
  `vocabulario_aprendido.json` y la corrección `INSERTADA` del JSON; candidato: solo la corrección `CORREGIDA_USUARIO`
  del JSON, la tabla no cambia.)

---

## 8. Glosario

| Término | Significado en el proyecto |
|---|---|
| Categoría léxica | Nombre del token; es un terminal de la gramática (`ADJ`, `SUST`, `V_EST`) |
| Rasgos | Datos semánticos de una forma canónica, guardados en su entrada de la tabla léxica: `aspecto`, `entidad`, `pol`, `decl`, `pronominal`, `clase`, `tiempo`, `sin_dominio` |
| Perfil | Combinación válida de rasgos de una categoría (`NEGATIVO` = `{"pol": -1}`, `FALLA`, `EQUIPO`…); catálogo cerrado en `semantica.PERFILES` |
| `SIN_DOMINIO` | Perfil (rasgo `sin_dominio`) de palabras reconocidas sin significado para el dominio: la cláusula se abstiene (R-SINDOM) |
| Alta de forma canónica | Forma canónica nueva creada desde el menú, con los rasgos del perfil elegido |
| Compatibilidad (R-COMPAT) | Chequeo semántico de qué predicado admite cada sujeto; si falla, la cláusula se abstiene |
| Sujeto pospuesto (`sujp`) | Sujeto que va después del verbo: «no funciona el internet» |
| Forma canónica | Representante de las variantes de una palabra (`lenta`, `lento` → `LENTO`) |
| Desplazamiento | Posición 0-based del primer carácter del lexema dentro de la línea |
| `RELLENO` | Artículos, clíticos y preposiciones: pertenecen al lenguaje pero no tienen semántica |
| Tabla de símbolos léxica | Categoría → forma canónica → {rasgos, formas}. Precarga + lo aprendido (mismo formato); persiste |
| Tabla de entidades | Sesión, participante y ticket con sus apariciones; ámbito sesión, no persiste |
| `FUERA_DE_GRAMATICA` | Categoría para palabras conocidas sin función en la gramática: quedan NO_INTERPRETADO |
| `TURNO_DESCARTADO` | Turno posterior a un orden inconsistente en la misma sesión |
| Cláusula | Unidad mínima que produce un hecho: `<clausula> ::= <adv_t_op> <nucleo> <frec>` |
| Hecho | Resultado semántico de una cláusula (tipo, aspecto, valoración, declaración, reglas) |
| Declaración | Afirmación del cliente sobre el funcionamiento: OK, FALLA o RECUR |
| Evidencia | Cláusula interpretada que aporta valoración, declaración o compromiso, identificada `C<turno>.<k>` |
| NO_INTERPRETADO | Palabra o fragmento que no se pudo analizar; nunca produce valoración |
| `sinc` | Conjunto de sincronización de la recuperación: PRIM(A) ∪ SGTE(A) ∪ {EOL} |
| PARCIAL | Sesión con algún turno rechazado o descartado por formato, o sin `FIN` |
