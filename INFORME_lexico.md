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
| **Diccionario de vocabulario** | Palabras del dominio con su categoría y forma canónica | `vocabulario.json` |
| **Estructura fija** | `SESION`, `FIN`, `CLIENTE`, `AGENTE` | código (`ESTRUCTURA`) |
| **Tabla de símbolos** | Sesión, rol, tickets y apariciones (ámbito: sesión) | módulo aparte (paso posterior) |

El vocabulario se mantiene **separado de la tabla de símbolos**, como exige el enunciado. Se carga por parámetro (`construir_afd(vocab)`), lo que permite probar el caso 08 con el diccionario reducido `{lenta, lento}`.

### 1.2 Estructura del vocabulario

Cada entrada tiene la forma `categoría → forma canónica → [formas superficiales]`. Se guardan **formas superficiales** (`lenta` y `lento` por separado, sin lematizar) para que el empate de `lent` en el caso 08 sea detectable. Si una forma aparece dos veces con categorías o canónicos distintos, la carga falla (control de duplicados).

| Categoría | Canónico → formas |
|---|---|
| `ASP_SERV` | SERVICIO → servicio, internet, conexion, red, wifi |
| `ASP_ATEN` | ATENCION → atencion, atendiste, atendio, atendieron, trato |
| `ASP_CLAR` | EXPLICACION → explicacion, explicaciones, explico, explicaste, indicaciones, instrucciones |
| `ADJ_POS` | BUENO → bien, bueno, buena, buen, excelente, perfecto, perfecta · RAPIDO → rapido, rapida · ESTABLE → estable · AMABLE → amable · CLARO → claro, clara |
| `ADJ_NEG` | MALO → mal, malo, mala, pesimo, pesima · LENTO → lento, lenta · INESTABLE → inestable · CONFUSO → confuso, confusa |
| `V_FUNC` | FUNCIONAR → funciona, anda |
| `V_CORTA` | CORTAR → corta, cortan, corte, cortes |
| `V_SEGUIR` | SEGUIR → sigue, sigo, siguen |
| `V_COPULA` | SER_ESTAR → es, esta, estan, fue, estuvo, era |
| `V_ENTENDER` | ENTENDER → entendi, entendio, entiendo |
| `V_SOLICITUD` | REINICIAR → reinicie, reinicia, reiniciar, reinicien |
| `V_COMPROMISO` | REVISAR → revisaremos, revisare · LLAMAR → llamaremos, contactaremos · ESCALAR → escalaremos |
| `T_FUTURO` | MANANA → manana, luego |
| `T_AHORA` | AHORA → ahora, ya |
| `NEG` | NO → no, nunca, tampoco · SIN → sin |
| `INT` | MUY → muy, bastante |
| `PERO` | PERO → pero |
| `FREC` | TODOS → todos, todas · DIA → dia, dias · SIEMPRE → siempre, seguido |
| `SE` | SE → se |
| `ROUTER` | ROUTER → router, modem |
| `TICKET_PAL` | TICKET → ticket, caso |
| `CORTESIA` | GRACIAS → gracias · SALUDO → hola, adios |
| `RELLENO` | ART, CLITICO, PREP (el, la, me, de, en, que, y, …) |

### 1.3 Política de normalización

- **Plegado**: minúsculas y sin tildes, carácter a carácter (`á → a`), conservando la `ñ`. Es una transformación 1 a 1, por lo que **los desplazamientos del texto original siguen siendo válidos**.
- Cada token conserva tres formas: **lexema original** (`Está`), **normalizado** (`esta`) y **canónico** (`SER_ESTAR`).
- Los tickets se normalizan a mayúsculas (`tk-204 → TK-204`).
- Posición de cada token: `(sesión, turno, desplazamiento)`, con desplazamiento 0-based dentro de la línea.

### 1.4 Decisiones de diseño (para la defensa)

| Decisión | Justificación |
|---|---|
| **Un lexema, una categoría** | `agente` es rol (`2 AGENTE:`) y sustantivo (`el agente fue amable`, caso 04). El lexer no ve contexto: siempre emite `AGENTE`, y el **parser** decide según la posición. |
| `sin` en `NEG` | Caso 02 («sigo sin internet»): es una negación con alcance sobre el sustantivo siguiente. |
| `gracias` en `CORTESIA` | No es valoración; así el caso 06 da `SIN_EVIDENCIA`. |
| `RELLENO` | Pertenece al lenguaje (no es `NO_INTERPRETADO`) pero no aporta semántica; el parser lo saltea. |
| El corrector actúa solo sobre `PALABRA` | `no`, números y `TK-xxx` quedan intactos sin reglas especiales. |
| Estructura fuera del JSON | En el caso 08 el diccionario es `{lenta, lento}`, pero la sesión igual debe poder leerse. |

---

## 2. Categorías léxicas y prioridades

### 2.1 Tabla de categorías

La **prioridad** es el orden de declaración (índice menor = más prioridad).

| Prio | Categoría | ER (sobre el texto plegado) | Observación |
|---|---|---|---|
| 1 | `KW_SESION`, `KW_FIN`, `CLIENTE`, `AGENTE` | literales: `sesion`, `fin`, `cliente`, `agente` | estructura fija |
| 2 | `ID_SESION` | `s D D` | `S01` |
| 3 | `NUM` | `D+` | número de turno |
| 4 | `DOSPUNTOS`, `PUNTO`, `COMA`, `SIGNO` | `:` · `.` · `,` · `[¿?¡!]` | puntuación |
| 5 | `TICKET` | `tk- D{3,6}` | ver sección 3 |
| 6 | `TICKET_MAL` | `tk- D*` | error léxico específico |
| 7 | categorías del vocabulario | unión de formas (`ADJ_NEG`, `NEG`, `PERO`, …) | ver sección 1 |
| 8 | `PALABRA` | `letra+` | palabra desconocida; entrada del corrector |
| — | `DESCONOCIDO` | ningún patrón acepta | un carácter; error léxico |

Notación: `D = [0-9]`, `letra = [a-zñ]` (sobre texto ya plegado). La notación `x{n,m}` es la de potencia vista en clase: `x{3,6} = xxx(x(x(x)?)?)?`.

### 2.2 Cómo se resuelve la ambigüedad léxica

Siguiendo la Clase 5 (§5.3), hay dos situaciones y dos reglas distintas:

| Situación | Ejemplo | Regla |
|---|---|---|
| Lexemas de **distinta longitud** | `TK-204` (6 caracteres) vs `PALABRA` `tk` (2) | **lexema más largo**: gana `TICKET` |
| **Mismo lexema** aceptado por dos patrones | `no` ∈ `NEG` y `no` ∈ `PALABRA` | **prioridad**: gana `NEG` (índice menor) |

En el AFD combinado, un estado final puede reunir finales de varios tokens (como `F = {6, 8}` en el ejemplo `abb` de la Clase 5). La implementación elige el de menor índice y registra esos estados en `afd.ambiguos` (122 en el AFD completo), que sirven como evidencia para el informe.

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
| 14 | ASP_SERV | `internet` | `internet` | SERVICIO |
| 23 | V_COPULA | `está` | `esta` | SER_ESTAR |
| 28 | PALABRA | `lentto` | `lentto` | – |
| 34 | PUNTO | `.` | `.` | – |
| 36 | PALABRA | `Ver` | `ver` | – |
| 40 | TICKET | `TK-204` | `TK-204` | – |
| 46 | COMA | `,` | `,` | – |
| 48 | TICKET_MAL | `TK-12` | `tk-12` | – |
| 54 | RELLENO | `y` | `y` | PREP |
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
- Está pendiente la minimización del AFD completo (Clase 5, §5.4); el AFD de `TICKET` ya es mínimo.

## 5. Próximos pasos

1. Lector de formato: `SESION Sxx` / turno / `FIN`, con rechazo de rol inválido y resincronización en la línea siguiente.
2. BNF y gramática LL(1) con PRIM/SGTE, usando estas categorías como terminales.
3. Tabla de símbolos, acciones semánticas y corrector de Levenshtein.
