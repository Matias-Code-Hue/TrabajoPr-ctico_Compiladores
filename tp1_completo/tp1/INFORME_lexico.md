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
| **Tabla de símbolos léxica** | categoría → forma canónica → {rasgos, formas superficiales}; persistente, se enriquece (§1.5) | `vocabulario.json` (precarga) + `vocabulario_aprendido.json` (mismo formato); `tabla_lexica.py` |
| **Perfiles** | combinaciones de rasgos válidas por categoría; catálogo cerrado (el menú elige entre ellas y la carga las valida) | código (`semantica.PERFILES`) |
| **Estructura fija** | `SESION`, `FIN`, `CLIENTE`, `AGENTE` | código (`ESTRUCTURA`) |
| **Tabla de entidades** | Sesión, rol, tickets y apariciones (ámbito: sesión; efímera) | `entidades.py` |

La tabla léxica se mantiene **separada de la tabla de entidades**, como exige el enunciado («mantener separado el diccionario de vocabulario»). El léxico recibe el diccionario por parámetro (`construir_afd(vocab)`), lo que permite probar el caso 08 con el diccionario reducido `{lenta, lento}`.

### 1.2 Estructura del vocabulario

La tabla tiene tres niveles: **categoría léxica → forma canónica → formas superficiales**, y cada forma canónica guarda
además sus **rasgos**:

```json
"ADJ":   {"LENTO":  {"rasgos": {"pol": -1},                                "formas": ["lento", "lenta"]}},
"V_EST": {"CORTAR": {"rasgos": {"pol": -1, "decl": "RECUR", "pronominal": true}, "formas": ["corta", "cortan"]}}
```

 Se guardan **formas superficiales** (`lenta` y `lento` por separado, sin lematizar) para que el empate de `lent` en el caso 08 sea detectable. Si una forma aparece dos veces con categorías o canónicos distintos, la carga falla (control de duplicados).

El léxico solo usa las formas; los rasgos los leen las reglas semánticas (`REGLAS_SEMANTICAS.md` §3). Los rasgos de cada
forma canónica tienen que ser exactamente los de un **perfil** de su categoría (catálogo cerrado `semantica.PERFILES`,
abajo); la carga rechaza cualquier otra combinación. En la tabla, entre paréntesis, el perfil cuyos rasgos tiene cada
forma canónica. Las categorías son generales y coinciden con los terminales de la gramática, que trata igual a todas
las palabras de una categoría.

| Categoría | Qué es | Forma canónica → formas superficiales (perfil) |
|---|---|---|
| `SUST` | sustantivo | SERVICIO → servicio, internet, conexion, red, wifi (SERVICIO) · ATENCION → atencion, trato (ATENCION) · CLARIDAD → explicacion, explicaciones, indicaciones, instrucciones (CLARIDAD) · ROUTER → router, modem (EQUIPO) · TICKET → ticket, caso (TICKET) · CORTE → corte, cortes (PROBLEMA) |
| `ADJ` | cualidad (adjetivo o adverbio) | BUENO → bien, bueno, buena, buen, excelente, perfecto, perfecta (POSITIVO) · RAPIDO → rapido, rapida (POSITIVO) · ESTABLE → estable (POSITIVO) · AMABLE → amable (POSITIVO) · CLARO → claro, clara (POSITIVO) · MALO → mal, malo, mala, pesimo, pesima (NEGATIVO) · LENTO → lento, lenta (NEGATIVO) · INESTABLE → inestable (NEGATIVO) · CONFUSO → confuso, confusa (NEGATIVO) |
| `V_COP` | ser / estar | SER_ESTAR → es, esta, estan, fue, estuvo, era (COPULA) |
| `V_EST` | verbo de estado del servicio | FUNCIONAR → funciona, anda (OK) · FALLAR → falla, fallan (FALLA) · CORTAR → corta, cortan (RECUR) |
| `V_CONT` | seguir | SEGUIR → sigue, sigo, siguen (CONTINUIDAD) |
| `V_ACC` | verbo de acción (objeto opcional) | ENTENDER → entendi, entendio, entiendo (COMPRENSION) · REINICIAR → reinicie, reinicia, reiniciar, reinicien (SOLICITUD) · REVISAR → revisaremos, revisare (COMPROMISO) · LLAMAR → llamaremos, contactaremos (COMPROMISO) · ESCALAR → escalaremos (COMPROMISO) · ATENDER → atendiste, atendio, atendieron (VAL_ATEN) · EXPLICAR → explico, explicaste (VAL_CLAR) |
| `ADV_T` | momento | AHORA → ahora, ya (AHORA) · MAÑANA → mañana, luego (FUTURO) |
| `NEG` | negación de un predicado | NO → no, nunca, tampoco (NEGACION) |
| `SIN` | «sin» + sustantivo | SIN → sin (PRIVACION) |
| `INT` | intensificador | MUY → muy, bastante (INTENSIFICADOR) |
| `PERO` | contraste | PERO → pero (CONTRASTE) |
| `Y` | unión de cláusulas | Y → y (UNION) |
| `SE` | marca pronominal | SE → se (PRONOMINAL) |
| `FREC` | frecuencia | TODOS → todos, todas (FRECUENCIA) · DIA → dia, dias (FRECUENCIA) · SIEMPRE → siempre, seguido (FRECUENCIA) |
| `CORTESIA` | cortesía | GRACIAS → gracias (CORTESIA) · SALUDO → hola, adios (CORTESIA) |
| `RELLENO` | artículos, clíticos y preposiciones (sin semántica) | ART → el, la, los, las, un, una, mi, su, tu (SIN_SIGNIFICADO) · CLITICO → me, te, lo, le (SIN_SIGNIFICADO) · PREP → de, del, en, a, al, con, por, para, que (SIN_SIGNIFICADO) |

16 categorías con formas, 43 formas canónicas y 116 formas superficiales en la precarga. Además, la categoría
`FUERA_DE_GRAMATICA` tiene una sola forma canónica (`FUERA`, sin formas): recibe las palabras que el usuario marca como
conocidas pero sin función en la gramática.

Perfiles con rasgos (las demás categorías tienen un solo perfil, sin rasgos: su efecto lo da la producción):

| Categoría | Perfil `rasgos` |
|---|---|
| `SUST` | SERVICIO `{"aspecto": "SERVICIO"}` · ATENCION `{"aspecto": "ATENCION"}` · CLARIDAD `{"aspecto": "CLARIDAD"}` · EQUIPO `{"aspecto": "SERVICIO", "entidad": "EQUIPO"}` · TICKET `{"entidad": "TICKET"}` · PROBLEMA `{"aspecto": "SERVICIO", "pol": -1}` · SIN_DOMINIO `{"sin_dominio": true}` |
| `ADJ` | POSITIVO `{"pol": 1}` · NEGATIVO `{"pol": -1}` · SIN_DOMINIO `{"sin_dominio": true}` |
| `V_EST` | OK `{"pol": 1, "decl": "OK"}` · FALLA `{"pol": -1, "decl": "FALLA"}` · RECUR `{"pol": -1, "decl": "RECUR", "pronominal": true}` |
| `V_ACC` | COMPRENSION `{"clase": "COMPRENSION", "aspecto": "CLARIDAD"}` · SOLICITUD `{"clase": "SOLICITUD"}` · COMPROMISO `{"clase": "COMPROMISO"}` · VAL_ATEN `{"clase": "VALORABLE", "aspecto": "ATENCION"}` · VAL_CLAR `{"clase": "VALORABLE", "aspecto": "CLARIDAD"}` · SIN_DOMINIO `{"sin_dominio": true}` |
| `ADV_T` | AHORA `{"tiempo": "AHORA"}` · FUTURO `{"tiempo": "FUTURO"}` |

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
| Verbos por construcción, no por palabra | `V_COP` (+ cualidad), `V_EST` (estado del servicio), `V_CONT` (seguir) y `V_ACC` (acción con objeto). Un verbo nuevo («colapsa») entra en la categoría de su construcción con los rasgos de un perfil existente (FALLA). |
| Significado por rasgos, no por categoría | `LENTO` y `BUENO` son ambas `ADJ`; las distinguen sus rasgos (`pol` −1 y +1, perfiles NEGATIVO y POSITIVO). Así la gramática es chica (19 terminales en el texto) y una palabra nueva no requiere tocarla. |
| Rasgos dentro de la tabla léxica | Se guardan en la misma entrada que las formas, no en un archivo aparte; la justificación está en §1.6. |
| Formas verbales de «atender» y «explicar» como verbos | «atendiste» y «explicó» son `V_ACC` (perfiles VAL_ATEN y VAL_CLAR); los sustantivos «atención» y «explicación» son `SUST`. Permite «no me atendieron bien». |
| «corta» exige «se» | Lo exige su rasgo `pronominal` (perfil RECUR), y lo verifica la semántica: «el agente corta la llamada» (lectura transitiva) queda en abstención. |
| `gracias` en `CORTESIA` | No es valoración; así el caso 06 da `SIN_EVIDENCIA`. |
| `RELLENO` | Pertenece al lenguaje (no es `NO_INTERPRETADO`) pero no aporta semántica; el parser lo saltea. |
| El corrector actúa solo sobre `PALABRA` | `no`, números y `TK-xxx` quedan intactos sin reglas especiales. |
| Estructura fuera del JSON | En el caso 08 el diccionario es `{lenta, lento}`, pero la sesión igual debe poder leerse. |

### 1.5 Tabla de símbolos léxica persistente e interactiva

La tabla léxica se **precarga** a mano y se **enriquece** sesión a sesión con las respuestas del usuario. Se guarda en
archivos JSON, sin base de datos:

| Archivo | Contenido | Quién lo escribe |
|---|---|---|
| `vocabulario.json` | precarga: `{categoría: {canónico: {"rasgos": {...}, "formas": [...]}}}` | solo el grupo, a mano; el programa **nunca** lo modifica |
| `vocabulario_aprendido.json` | lo aprendido, **con el mismo formato**: una forma canónica de la precarga aparece solo con `"formas"` (las variantes aprendidas heredan sus rasgos); una forma canónica nueva aparece con `"rasgos"` (copiados del perfil elegido) y `"formas"` | el programa, con **una** escritura atómica por cambio (archivo temporal + `os.replace`) |

No hay archivo de auditoría (se decidió quitarlo). Lo aprendido se ve con `python3 main.py --tabla` («+» marca cada
forma y forma canónica aprendida) y, para cada ejecución, en el JSON de resultados: cada inserción es una corrección
`INSERTADA` con su turno, desplazamiento, categoría y forma canónica. Ejemplo de `vocabulario_aprendido.json` después de insertar «fatal» como variante de `MALO` y crear
`COLAPSAR`:

```json
{"ADJ":   {"MALO":     {"formas": ["fatal"]}},
 "V_EST": {"COLAPSAR": {"rasgos": {"decl": "FALLA", "pol": -1}, "formas": ["colapsa"]}}}
```

Operaciones de la tabla (`TablaSimbolosLexica`):

| Operación | Efecto |
|---|---|
| `buscar(forma)` | → `(categoría, canónico, origen)`, con origen `PRECARGA` o `APRENDIDA` |
| `insertar(forma, categoría, canónico)` | agrega una forma como variante de una forma canónica **existente** (hereda sus rasgos); rechaza formas repetidas |
| `alta_canonico(categoría, nombre, perfil)` | crea una forma canónica con los rasgos de un perfil **existente** de la categoría (el programa los copia); normaliza el nombre (sin tildes, mayúsculas, espacios como `_`) y rechaza nombres repetidos en la categoría |
| `mostrar()` (`main.py --tabla-inicial`, `main.py --tabla [CAT]`) | la tabla inicial (precarga) o la vigente, una fila por forma canónica (perfil, rasgos, formas); «+» marca lo aprendido |
| `reiniciar()` (`main.py --reiniciar-aprendido`) | borra `vocabulario_aprendido.json` y vuelve a la precarga |
| validación al abrir | los rasgos de cada forma canónica (precarga y aprendida) deben coincidir con un perfil; si no, la tabla no se abre y se informa la entrada |
| conciliación al abrir | si algo aprendido se agregó después a la precarga, gana la precarga (la forma o los rasgos de la forma canónica) y `main.py` avisa qué se quitó |

**Consulta al usuario** (`consulta.py`). Se pregunta **después del corrector**, solo cuando la regla del enunciado no
resuelve la palabra (`PALABRA` de al menos `MIN_LONG = 4` letras):

| Resultado del corrector | ¿Se pregunta? | Opciones |
|---|---|---|
| un candidato a distancia 1 | no: se corrige (`CORREGIDA`) | — |
| `EMPATE` | sí | un candidato (corrige **solo esa aparición**: `CORREGIDA_USUARIO`), `n` (insertar) o Enter (se conserva el empate) |
| `SIN_CANDIDATO` | sí | `n` (insertar) o Enter (queda `NO_INTERPRETADO`) |
| palabra de menos de 4 letras | no (`OMITIDA_CORTA`) | — |

Al insertar, el menú es **cerrado**:

```
Palabra desconocida «colapsa» · sesión S01, turno 1: «El internet colapsa seguido.»
     (sin candidatos a distancia 1)
   n) insertar «colapsa» en la tabla de símbolos léxica
   Enter) regla del enunciado: conservar la palabra (NO_INTERPRETADO)
  1) ¿Qué tipo de palabra es «colapsa»?          → solo las categorías existentes (agrupadas por tipo)
  2) ¿De qué forma canónica de V_EST es variante? → primero las existentes, con sus rasgos:
                                                    CORTAR {"pol": -1, "decl": "RECUR", "pronominal": true} …
       c) crear una forma canónica nueva          → nombre normalizado (COLAPSAR), sin repetir en la categoría
  3) ¿Qué significa? (perfil de V_EST)           → solo los perfiles existentes, con sus rasgos:
                                                    OK {"pol": 1, "decl": "OK"} · FALLA {"pol": -1, "decl": "FALLA"} · RECUR …
  ✔ forma canónica nueva V_EST/COLAPSAR (perfil FALLA, rasgos {"pol": -1, "decl": "FALLA"})
```

- Los errores de tipeo no se guardan: elegir «lento» para un empate corrige solo esa aparición.
- Lo aprendido vale para el resto de la misma entrada: las otras apariciones se reconocen sin preguntar.
- **`SIN_DOMINIO`** (rasgo `sin_dominio`, en perfiles de `SUST`, `ADJ` y `V_ACC`) registra palabras que la gramática debe reconocer en su lugar
  pero sin significado para el dominio («hace», «ruido», «técnico»): la cláusula se reconoce entera y no se
  interpreta. `FUERA_DE_GRAMATICA` y `RELLENO`, en cambio, descartan la palabra antes del parser.
- Si la entrada estándar se termina (Ctrl-D o `< /dev/null`), el resto se resuelve con la regla del enunciado.
- **Modo no interactivo**: `pruebas.py` y el golden no preguntan y usan solo la precarga, así lo aprendido no cambia
  los resultados esperados. `--dic` (caso 08) usa una tabla solo en memoria.

### 1.6 Por qué los rasgos están en `vocabulario.json` (y no en un archivo aparte)

Durante el desarrollo se probó separar el significado en `significados.json` (forma canónica → perfil) y lo aprendido
en dos archivos (`vocabulario_aprendido.json` y `significados_aprendido.json`). Se volvió a una sola estructura por
cómo funciona la **interactividad** de la tabla de símbolos léxica:

| Aspecto de la interactividad | Con un archivo aparte de significados | Con los rasgos en la misma entrada (actual) |
|---|---|---|
| Alta de forma canónica desde el menú | toca dos estructuras: la forma canónica (sin significado) y su perfil | una entrada `{rasgos, formas}`, creada de una vez |
| Persistencia de cada cambio | cada archivo se escribe de forma atómica, pero el cambio completo no; la consistencia depende del orden de escritura | **una** escritura atómica de `vocabulario_aprendido.json` por cambio |
| Borrar, restaurar o copiar lo aprendido | si se mueve un archivo sin el otro, quedan formas cuya forma canónica no tiene significado y la tabla no carga | un solo archivo: queda entero o no queda |
| «Lo aprendido vale para el resto de la entrada» | el corrector mira el diccionario y la semántica la tabla de significados: dos objetos vivos que actualizar juntos | un solo objeto vivo (`tabla.vocabulario()`) que usan el corrector y la semántica |
| Lo que muestra el menú | rasgos de un archivo, formas de otro | los rasgos de la misma entrada en la que se inserta la palabra |
| Pasar lo aprendido a la precarga | dos archivos que editar | copiar la entrada: lo aprendido tiene el formato de la precarga |
| Reinicio y conciliación | sobre dos archivos | sobre uno |

Lo que **no** cambia: el menú sigue cerrado. Los rasgos no se escriben desde el programa, se copian de un perfil del
catálogo `semantica.PERFILES`, y la validación al cargar rechaza un rasgo editado a mano que no coincida con ningún
perfil (prueba «rasgos validados al cargar contra los perfiles» en `pruebas.py`).

Costo aceptado: los rasgos de un perfil se repiten en cada forma canónica (`{"pol": -1}` aparece en cuatro
adjetivos), y si se cambia un perfil en el código hay que actualizar sus entradas en `vocabulario.json`. La validación
de carga las señala una por una.

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
| 7 | las 16 categorías del vocabulario (`SUST`, `ADJ`, `V_EST`, `V_ACC`, `ADV_T`, `NEG`, `SIN`, `Y`, …) | unión de las formas que tiene la tabla de símbolos léxica (precarga ∪ aprendido) | ver sección 1; la ER cambia cuando el usuario inserta una palabra |
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
| 14 | SUST | `internet` | `internet` | SERVICIO |
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
- Desde el menú no se crean categorías ni perfiles: un significado nuevo requiere un perfil nuevo en `semantica.PERFILES`.
- Está pendiente la minimización del AFD completo (Clase 5, §5.4); el AFD de `TICKET` ya es mínimo.

## 5. Etapas siguientes del pipeline

1. Lector de formato (`lector.py`): `SESION Sxx` / turno / `FIN`. Antes de escanear normaliza cada línea a NFC
   (una «á» escrita como `a` + tilde combinante pasa a ser un solo carácter) y descarta el BOM inicial.
2. Corrector (`corrector.py`, `consulta.py`): Levenshtein sobre los tokens `PALABRA`; consulta al usuario en empates y palabras sin candidato (§1.5).
3. Gramática LL(1) y parser (`GRAMATICA.md`, `DERIVACION.md`), con estas categorías como terminales.
4. Reglas semánticas y estado (`REGLAS_SEMANTICAS.md`) y tabla de entidades (`entidades.py`).
