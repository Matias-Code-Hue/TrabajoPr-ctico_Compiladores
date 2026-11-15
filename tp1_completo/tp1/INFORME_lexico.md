# TP1 · Diseño de Compiladores (FPUNA 2026/2)
## Analizador léxico: vocabulario, categorías y AFD de `TICKET`

Este documento resume los tres pasos realizados del analizador léxico:

1. Vocabulario canónico y política de normalización
2. Categorías léxicas y prioridades
3. ER, AFN, AFD y tabla de transiciones de `TICKET`

Implementación: `lexico.py` (Python 3, sin el módulo `re`) y `vocabulario.json`.
Procedimiento aplicado (apuntes de clase, Clases 4 y 5): **ER → AFN (Thompson) → AFD (subconjuntos) → `mover()` + lexema más largo + prioridad**.

---

## 1. Vocabulario canónico y normalización

### 1.1 Separación de diccionarios

| Componente | Contenido | Dónde vive |
|---|---|---|
| **Tabla de símbolos léxica** (diccionario de vocabulario) | Palabras del dominio con su categoría y forma canónica; persistente, se enriquece (§1.5) | `vocabulario.json` (precarga) + `vocabulario_aprendido.json`; `tabla_lexica.py` |
| **Estructura fija** | `SESION`, `FIN`, `CLIENTE`, `AGENTE` | código (`ESTRUCTURA`) |
| **Tabla de entidades** | Sesión, rol, tickets y apariciones (ámbito: sesión; efímera) | `entidades.py` |

La tabla léxica se mantiene **separada de la tabla de entidades**, como exige el enunciado («mantener separado el diccionario de vocabulario»). El léxico la recibe por parámetro (`construir_afd(vocab)`), lo que permite probar el caso 08 con el diccionario reducido `{lenta, lento}`.

### 1.2 Estructura del vocabulario

Cada entrada tiene la forma `categoría → forma canónica → [formas superficiales]`. Se guardan **formas superficiales** (`lenta` y `lento` por separado, sin lematizar) para que el empate de `lent` en el caso 08 sea detectable. Si una forma aparece dos veces con categorías o canónicos distintos, la carga falla (control de duplicados).

| Categoría | Grupo en la gramática | Qué es | Canónico → formas |
|---|---|---|---|
| `SUST_SERV` | `sust` | sustantivo: el servicio | SERVICIO → servicio, internet, conexion, red, wifi |
| `SUST_ATEN` | `sust` | sustantivo: la atención | ATENCION → atencion, trato |
| `SUST_CLAR` | `sust` | sustantivo: la explicación | CLARIDAD → explicacion, explicaciones, indicaciones, instrucciones |
| `SUST_EQUIPO` | `sust` | sustantivo: un equipo | ROUTER → router, modem |
| `SUST_TICKET` | `sust` | sustantivo: ticket o caso | TICKET → ticket, caso |
| `SUST_PROB` | `sust` | sustantivo: un problema del servicio | CORTE → corte, cortes |
| `ADJ_POS` | `adj` | cualidad positiva | BUENO → bien, bueno, buena, buen, excelente, perfecto, perfecta · RAPIDO → rapido, rapida · ESTABLE → estable · AMABLE → amable · CLARO → claro, clara |
| `ADJ_NEG` | `adj` | cualidad negativa | MALO → mal, malo, mala, pesimo, pesima · LENTO → lento, lenta · INESTABLE → inestable · CONFUSO → confuso, confusa |
| `V_COP` | — | ser / estar | SER_ESTAR → es, esta, estan, fue, estuvo, era |
| `V_EST_OK` | `v_est` | verbo de estado: anda bien | FUNCIONAR → funciona, anda |
| `V_EST_FALLA` | `v_est` | verbo de estado: anda mal | FALLAR → falla, fallan |
| `V_EST_RECUR` | — | verbo pronominal: falla que se repite («se corta») | CORTAR → corta, cortan |
| `V_CONT` | — | seguir | SEGUIR → sigue, sigo, siguen |
| `V_ENTENDER` | `v_acc` | verbo de acción: entender | ENTENDER → entendi, entendio, entiendo |
| `V_SOLICITUD` | `v_acc` | verbo de acción: pedido | REINICIAR → reinicie, reinicia, reiniciar, reinicien |
| `V_COMPROMISO` | `v_acc` | verbo de acción: promesa a futuro | REVISAR → revisaremos, revisare · LLAMAR → llamaremos, contactaremos · ESCALAR → escalaremos |
| `V_VAL_ATEN` | `v_acc` | verbo de acción: atender | ATENDER → atendiste, atendio, atendieron |
| `V_VAL_CLAR` | `v_acc` | verbo de acción: explicar | EXPLICAR → explico, explicaste |
| `T_AHORA` | `adv_t` | momento: ahora | AHORA → ahora, ya |
| `T_FUTURO` | `adv_t` | momento: más adelante | MAÑANA → mañana, luego |
| `NEG` | — | negación de un predicado | NO → no, nunca, tampoco |
| `SIN` | — | «sin» + sustantivo | SIN → sin |
| `INT` | — | intensificador | MUY → muy, bastante |
| `PERO` | — | contraste | PERO → pero |
| `Y` | — | unión de cláusulas | Y → y |
| `SE` | — | marca pronominal | SE → se |
| `FREC` | — | frecuencia | TODOS → todos, todas · DIA → dia, dias · SIEMPRE → siempre, seguido |
| `CORTESIA` | — | cortesía | GRACIAS → gracias · SALUDO → hola, adios |
| `RELLENO` | — | artículos, clíticos y preposiciones (sin semántica) | ART → el, la, los, las, un, una, mi, su, tu · CLITICO → me, te, lo, le · PREP → de, del, en, a, al, con, por, para, que |

Las categorías son **subcategorías léxicas**: el nombre dice qué clase de palabra es y qué significa (`SUST_SERV` es un
sustantivo que habla del servicio; `ADJ_NEG`, una cualidad negativa). La gramática las agrupa con cinco no terminales
(`sust`, `adj`, `v_est`, `v_acc`, `adv_t`) y trata igual a todas las de un grupo; el significado de cada una lo fija
la regla semántica de su producción (`REGLAS_SEMANTICAS.md` §3). Así la tabla solo necesita guardar `forma →
categoría`, y una palabra nueva se incorpora eligiendo su subcategoría, sin tocar la gramática.

### 1.3 Política de normalización

- **Plegado**: minúsculas y sin tildes, carácter a carácter (`á → a`), conservando la `ñ`. Es una transformación 1 a 1, por lo que **los desplazamientos del texto original siguen siendo válidos**.
- Cada token conserva tres formas: **lexema original** (`Está`), **normalizado** (`esta`) y **canónico** (`SER_ESTAR`).
- Los tickets se normalizan a mayúsculas (`tk-204 → TK-204`).
- Posición de cada token: `(sesión, turno, desplazamiento)`, con desplazamiento 0-based dentro de la línea.

### 1.4 Decisiones de diseño (para la defensa)

| Decisión | Justificación |
|---|---|
| **Un lexema, una categoría** | `agente` es rol (`2 AGENTE:`) y sustantivo (`el agente fue amable`, caso 04). El lexer no ve contexto: siempre emite `AGENTE`, y el **parser** decide según la posición. |
| `SIN` separado de `NEG` | «sin» precede a un sustantivo («sigo sin internet», caso 02) y «no» a un predicado. Con una sola categoría la gramática aceptaba «sigo no internet». |
| `Y` como categoría propia | «y» une cláusulas («está lento y se corta»); como `RELLENO` desaparecía y la segunda cláusula se perdía. |
| Verbos por construcción, no por palabra | `V_COP`, `V_EST_*`, `V_CONT` y los de acción (`V_ENTENDER`, `V_SOLICITUD`, `V_COMPROMISO`, `V_VAL_*`): un verbo nuevo («falla») entra en la subcategoría de su construcción. |
| `V_EST_RECUR` aparte de `V_EST_OK`/`V_EST_FALLA` | «corta» solo se acepta con «se» (`SE V_EST_RECUR`): sin «se» es la lectura transitiva («el agente corta la llamada»). |
| Formas verbales de «atender» y «explicar» como verbos | «atendiste» y «explicó» son `V_VAL_ATEN` / `V_VAL_CLAR`; los sustantivos «atención» y «explicación» son `SUST_ATEN` / `SUST_CLAR`. Permite «no me atendieron bien». |
| `gracias` en `CORTESIA` | No es valoración; así el caso 06 da `SIN_EVIDENCIA`. |
| `RELLENO` | Pertenece al lenguaje (no es `NO_INTERPRETADO`) pero no aporta semántica; el parser lo saltea. |
| El corrector actúa solo sobre `PALABRA` | `no`, números y `TK-xxx` quedan intactos sin reglas especiales. |
| Estructura fuera del JSON | En el caso 08 el diccionario es `{lenta, lento}`, pero la sesión igual debe poder leerse. |

### 1.5 Tabla de símbolos léxica persistente

La tabla léxica se **precarga** a mano y se **enriquece** sesión a sesión con las respuestas del usuario.
Se guarda en tres archivos JSON (sin base de datos):

| Archivo | Contenido | Quién lo escribe |
|---|---|---|
| `vocabulario.json` | precarga manual (`categoría → canónico → formas`) | solo el grupo, a mano; el programa **nunca** lo modifica |
| `vocabulario_aprendido.json` | `{forma: {categoria, canonico, fecha, origen}}`; origen = archivo, sesión, turno, desplazamiento y texto | el programa, con escritura atómica (archivo temporal + `os.replace`) |
| `vocabulario_auditoria.jsonl` | una línea JSON por cambio: `fecha`, `operacion`, `forma`, `antes`, `despues`, `operador`, `origen`, `decision` | el programa; **solo se agregan líneas** |

Tabla vigente = precarga ∪ aprendido. Operaciones:

- **buscar(forma)** → `(categoría, canónico, origen)`, con origen `PRECARGA` o `APRENDIDA`.
- **insertar(forma, categoría, canónico)** → falla si la forma ya existe (control de duplicados); si no, persiste y
  audita `INSERTAR`.
- **Conciliación**: si una forma aprendida se agrega después a la precarga, gana la precarga y la entrada aprendida se
  da de baja (`BAJA_POR_PRECARGA` en la auditoría). Sin esto la forma tendría dos entradas y el léxico la rechazaría.

**Consulta al usuario** (`consulta.py`). Toda palabra desconocida (`PALABRA` de al menos `MIN_LONG = 4` letras) pasa
por Levenshtein y se consulta:

```
Palabra desconocida «lentto» · sesión S01, turno 3: «El internet está lentto.»
   1) usar «lento» (ADJ_NEG / LENTO) solo en esta aparición
   n) insertar «lentto» como palabra nueva en la tabla de símbolos léxica
   Enter) regla del enunciado: corregir a «lento» (único candidato a distancia 1)
```

| Respuesta | Efecto | ¿Cambia la tabla? | Acción registrada |
|---|---|---|---|
| `1..k` | se toma ese candidato **solo en esta aparición** | no | `CORREGIDA_USUARIO` |
| `n` | se elige la subcategoría en un menú agrupado por tipo de palabra (cualidad, cosa, acción, momento, palabra gramatical, `RELLENO` o `FUERA_DE_GRAMATICA`) y el canónico; la forma se incorpora | sí, con auditoría | `INSERTADA` |
| Enter | regla del enunciado: candidato único → se corrige; empate o ninguno → se conserva | no | `CORREGIDA`, `EMPATE`, `SIN_CANDIDATO` |

- Los errores de tipeo no se guardan: elegir «lento» para «lentto» no agrega «lentto» a la tabla.
- `FUERA_DE_GRAMATICA` sirve para palabras conocidas sin función en la gramática («igual», «ayer»): quedan
  `NO_INTERPRETADO` y el corrector no las vuelve a tocar.
- Cada palabra se consulta una vez por ejecución. Una forma insertada se reconoce en el resto del lote y, en la
  ejecución siguiente, el AFD ya la incluye como patrón.
- Si la entrada estándar se termina (Ctrl-D o `< /dev/null`), el resto se resuelve con la regla del enunciado. Así
  Enter (o ninguna respuesta) reproduce siempre los resultados de la guía (casos 05 y 08).
- `--dic` (caso 08) usa una tabla solo en memoria: lo insertado no se guarda.

---

## 2. Categorías léxicas y prioridades

### 2.1 Tabla de categorías

La **prioridad** es el orden de declaración (índice menor = más prioridad).

| Prio | Categoría | ER (sobre el texto plegado) | Observación |
|---|---|---|---|
| 1 | `SESION`, `FIN`, `CLIENTE`, `AGENTE` | literales: `sesion`, `fin`, `cliente`, `agente` | estructura fija |
| 2 | `ID_SESION` | `s D D` | `S01` |
| 3 | `NUM` | `D+` | número de turno |
| 4 | `DOSPUNTOS`, `PUNTO`, `COMA`, `SIGNO` | `:` · `.` · `,` · `[¿?¡!]` | puntuación |
| 5 | `TICKET` | `tk- D{3,6}` | ver sección 3 |
| 6 | `TICKET_MAL` | `tk- D*` | error léxico específico |
| 7 | las 29 subcategorías del vocabulario (`SUST_*`, `ADJ_*`, `V_*`, `T_*`, `NEG`, `SIN`, `Y`, …) | unión de las formas que tiene la tabla de símbolos léxica (precarga ∪ aprendido) | ver sección 1; la ER cambia cuando el usuario inserta una palabra |
| 8 | `PALABRA` | `letra+` | palabra desconocida; entrada del corrector |
| — | `DESCONOCIDO` | ningún patrón acepta | un carácter; error léxico |

Notación: `D = [0-9]`, `letra = [a-zñ]` (sobre texto ya plegado). La notación `x{n,m}` es la de potencia vista en clase: `x{3,6} = xxx(x(x(x)?)?)?`.

### 2.2 Cómo se resuelve la ambigüedad léxica

Siguiendo la Clase 5 (§5.3), hay dos situaciones y dos reglas distintas:

| Situación | Ejemplo | Regla |
|---|---|---|
| Lexemas de **distinta longitud** | `TK-204` (6 caracteres) vs `PALABRA` `tk` (2) | **lexema más largo**: gana `TICKET` |
| **Mismo lexema** aceptado por dos patrones | `no` ∈ `NEG` y `no` ∈ `PALABRA` | **prioridad**: gana `NEG` (índice menor) |

En el AFD combinado, un estado final puede reunir finales de varios tokens (como `F = {6, 8}` en el ejemplo `abb` de la Clase 5). La implementación elige el de menor índice y registra esos estados en `afd.ambiguos` (124 en el AFD completo, de 409 estados), que sirven como evidencia para el informe.

### 2.3 Tratamiento de errores léxicos

| Lexema | Resultado | Motivo |
|---|---|---|
| `TK-12` | `TICKET_MAL` | menos de 3 dígitos |
| `TK-1234567` | `TICKET_MAL` | más de 6 dígitos: `TICKET_MAL` es más largo que `TICKET` |
| `@` | `DESCONOCIDO` | carácter fuera de Σ |
| `lentto` | `PALABRA` | no está en el vocabulario; pasa al corrector |

Sin `TICKET_MAL`, `TK-12` quedaría como `PALABRA(tk) '-' NUM(12)` y se perdería la causa del error.

### 2.4 Verificación

Entrada: `2 CLIENTE: El internet está lentto. Ver TK-204, TK-12 y TK-1234567 ¡Gracias!`

| Desp. | Categoría | Lexema | Normalizado | Canónico |
|---|---|---|---|---|
| 0 | NUM | `2` | `2` | – |
| 2 | CLIENTE | `CLIENTE` | `cliente` | CLIENTE |
| 9 | DOSPUNTOS | `:` | `:` | – |
| 11 | RELLENO | `El` | `el` | ART |
| 14 | SUST_SERV | `internet` | `internet` | SERVICIO |
| 23 | V_COP | `está` | `esta` | SER_ESTAR |
| 28 | PALABRA | `lentto` | `lentto` | – |
| 34 | PUNTO | `.` | `.` | – |
| 36 | PALABRA | `Ver` | `ver` | – |
| 40 | TICKET | `TK-204` | `TK-204` | – |
| 46 | COMA | `,` | `,` | – |
| 48 | TICKET_MAL | `TK-12` | `tk-12` | – |
| 54 | Y | `y` | `y` | Y |
| 56 | TICKET_MAL | `TK-1234567` | `tk-1234567` | – |
| 67 | SIGNO | `¡` | `¡` | – |
| 68 | CORTESIA | `Gracias` | `gracias` | GRACIAS |
| 75 | SIGNO | `!` | `!` | – |

---

## 3. AFD de `TICKET`

### 3.1 Expresión regular

```
TICKET = tk- D D D ( D ( D ( D )? )? )?        con D = [0-9]
       = tk- D{3,6}
```

El patrón se aplica sobre el texto plegado, por eso `tk` va en minúsculas y `TK-204` se reconoce igual.

### 3.2 AFN (construcción de Thompson)

Cada símbolo es un fragmento `i → f`; la concatenación une fragmentos con transiciones ε, y cada `( … )?` añade una arista ε que permite omitir el bloque. Esquema simplificado:

```
q0 -t-> q1 -k-> q2 --(-)--> q3 -D-> q4 -D-> q5 -D-> q6
                                                      |-- D --> q7 -- D --> q8 -- D --> q9
        ε hacia el estado final desde q6, q7, q8 y q9  (los cuatro opcionales)
```

### 3.3 Subconjuntos y AFD

Aplicando el algoritmo de subconjuntos (`cerradura-ε` y `mover`), cada estado del AFD es un conjunto de estados del AFN. Como el patrón es una cadena sin ramas, la construcción no ramifica: cada conjunto lleva a uno solo.

- **Estado inicial**: `q0 = cε({0})`.
- **Estados finales**: q6, q7, q8, q9. Cada uno contiene al estado final del AFN, tras las aristas ε de los opcionales.
- **Estado de error**: transición indefinida (conjunto vacío).

**Tabla de transiciones** (símbolos: `t`, `k`, `-`, y `D` = dígito):

| Estado | `t` | `k` | `-` | `D` | ¿Final? | Significado |
|---|---|---|---|---|---|---|
| q0 (inicio) | q1 | – | – | – | no | |
| q1 | – | q2 | – | – | no | leyó `t` |
| q2 | – | – | q3 | – | no | leyó `tk` |
| q3 | – | – | – | q4 | no | leyó `tk-` |
| q4 | – | – | – | q5 | no | 1 dígito |
| q5 | – | – | – | q6 | no | 2 dígitos |
| q6 | – | – | – | q7 | **sí** | 3 dígitos |
| q7 | – | – | – | q8 | **sí** | 4 dígitos |
| q8 | – | – | – | q9 | **sí** | 5 dígitos |
| q9 | – | – | – | – | **sí** | 6 dígitos |

Las celdas con "–" llevan al estado de error implícito.

**Diagrama de estados:**

```
inicio → (q0) -t→ (q1) -k→ (q2) -'-'→ (q3) -D→ (q4) -D→ (q5) -D→ ((q6)) -D→ ((q7)) -D→ ((q8)) -D→ ((q9))
```

(los dobles paréntesis indican estados finales)

El AFD ya es determinista y mínimo: no hay dos estados equivalentes, porque cada uno recuerda una cantidad distinta de caracteres leídos.

### 3.4 Código del reconocedor

Es la simulación del AFD de los apuntes (`S = mover(S, c)`), ampliada con la regla del lexema más largo: se recuerda el último estado final visitado.

```text
estado = q0; ultimo = nulo
mientras haya carácter c con transición (estado, simbolo(c)):
    estado = mover(estado, simbolo(c))
    si estado es final: ultimo = (posición, token)
devolver ultimo       # si es nulo → error léxico
```

### 3.5 Trazas

| Entrada | Recorrido | Resultado |
|---|---|---|
| `TK-204` | q0 →t q1 →k q2 →- q3 →D q4 →D q5 →D q6 (final) | `TICKET` |
| `TK-12` | q0 … q3 →D q4 →D q5, fin de entrada en q5 (no final) | `TICKET` no acepta; el patrón `TICKET_MAL` (`tk- D*`) sí → `TICKET_MAL` |
| `TK-1234567` | … q9 tras 6 dígitos; el 7.º dígito no tiene transición | último final: `TK-123456` (6 dígitos). `TICKET_MAL` consume los 7 y es más largo → `TICKET_MAL` |
| `TK-204` frente a `tk` | `PALABRA` aceptaría solo `TK` (2 caracteres) | lexema más largo: gana `TICKET` |

---

## 4. Límites documentados

- El id de sesión es `S` seguido de exactamente 2 dígitos.
- Los tickets se aceptan en cualquier combinación de mayúsculas y minúsculas, porque el texto se pliega antes de analizar.
- No hay palabras compuestas: «todos los días» son tres tokens (`FREC`, `RELLENO`, `FREC`) y la gramática los compone.
- Una forma tiene una sola entrada en la tabla: los homógrafos obligan a elegir una lectura («falla» y «corta» son verbos; «corte» y «cortes», sustantivos; «esta» es la cópula «está»).
- Los tiempos verbales no se distinguen: quedan fuera del alcance.
- Está pendiente la minimización del AFD completo (Clase 5, §5.4); el AFD de `TICKET` ya es mínimo.

## 5. Etapas siguientes del pipeline

1. Lector de formato (`lector.py`): `SESION Sxx` / turno / `FIN`. Antes de escanear normaliza cada línea a NFC
   (una «á» escrita como `a` + tilde combinante pasa a ser un solo carácter) y descarta el BOM inicial.
2. Corrector (`corrector.py`, `consulta.py`): Levenshtein sobre los tokens `PALABRA`, con consulta al usuario (§1.5).
3. Gramática LL(1) y parser (`GRAMATICA.md`, `DERIVACION.md`), con estas categorías como terminales.
4. Reglas semánticas y estado (`REGLAS_SEMANTICAS.md`) y tabla de entidades (`entidades.py`).
