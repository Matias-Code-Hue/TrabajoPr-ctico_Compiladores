# TP1 · Derivación de la gramática: de la BNF descriptiva a la LL(1)

Este documento reconstruye **todos los pasos intermedios** entre la gramática original (descriptiva) y la gramática
predictiva final de `GRAMATICA.md`, siguiendo la metodología de clase:

> *Consejo del profesor (Clase 2):* primero describir el lenguaje sin dejar fuera ninguna cadena válida; después
> convertir la gramática en predictiva con las técnicas estudiadas, y **comprobar que no se introdujo «basura»**.

Cada gramática intermedia se **diagnostica con el código** (`derivacion.py`: PRIM, SGTE y condiciones LL(1)) y se
comprueba por enumeración que todas generan **el mismo lenguaje**. Para repetirlo: `python3 derivacion.py` (N=4, ~3 s) o
`python3 derivacion.py 5` (~3 min).

## 0. Resumen de la derivación

| Gramática | Qué se hizo | Estado |
|---|---|---|
| **F0 / L0** | Gramática original, descriptiva | recursión por la izquierda, factores comunes |
| **L1** | Paso 1: eliminar recursión por la izquierda | quedan factores comunes y un conflicto PRIM∩SGTE |
| **L2** | Paso 2: factorizar por la izquierda | solo queda el conflicto PRIM∩SGTE en `lista_r` |
| **F1 / L3** | Paso 3: resolver PRIM∩SGTE y simplificar por sustitución | **LL(1)** |

### Diagnóstico calculado por el código

| Parte | Gramática | Variables | Recursión izq. | PRIM∩PRIM (factor común) | PRIM∩SGTE |
|---|---|---|---|---|---|
| Formato | F0 (original) | 5 | `lote`, `turnos` | `lote`, `turnos` | — |
| Formato | F1 (final LL(1)) | 7 | — | — | — |
| Lingüística | L0 (original) | 16 | `frec`, `lista`, `oracion` | `acc`, `clausula`, `est`, `frec`, `lista`, `nucleo`, `oracion`, `pred_l`, `pred_neg`, `sep`, `texto` | — |
| Lingüística | L1 (sin rec. izq.) | 19 | — | `acc`, `clausula`, `est`, `nucleo`, `pred_l`, `pred_neg`, `sep`, `texto` | `lista_r` |
| Lingüística | L2 (factorizada) | 22 | — | — | `lista_r` |
| Lingüística | L3 (final LL(1)) | 20 | — | — | — |

### Equivalencia del lenguaje

(En la parte de formato, `texto` se trata como un terminal más; su lenguaje se verifica en la parte lingüística.)

Se enumeran todas las cadenas que genera cada gramática hasta una longitud acotada y se comparan con las de la
gramática original:

| Parte | Longitud máx. | Cadenas generadas | Original = L1 = L2 = final |
|---|---|---|---|
| Formato | 21 tokens | 18 | sí |
| Lingüística | 5 tokens | 23 220 | sí |

Es una verificación **acotada**, no una demostración; las transformaciones de clase preservan el lenguaje por
construcción, y la enumeración protege contra errores de aplicación (exactamente el caso de `VIV` en el ejercicio de números romanos).

---

## 1. Gramática de formato (archivo, sesiones, turnos)

### F0 — original (descriptiva)

```
<lote>   ::= <lote> <sesion> | <sesion>
<turnos> ::= <turnos> <turno> | <turno>
```
(resto de producciones: `sesion`, `turno`, `rol`, ver apéndice A.1)

**Diagnóstico.** `lote` y `turnos` tienen **recursión por la izquierda** directa: un descenso recursivo llamaría
a `lote()` sin consumir ningún token y no terminaría.

### Transformación (A → Aα | β  ≡  A → βR ; R → αR | ε)

| Variable | A | α | β |
|---|---|---|---|
| `lote` | `lote` | `<sesion>` | `<sesion>` |
| `turnos` | `turnos` | `<turno>` | `<turno>` |

```
<lote>     ::= <sesion> <lote_r>            <turnos>   ::= <turno> <turnos_r>
<lote_r>   ::= <sesion> <lote_r> | ε       <turnos_r> ::= <turno> <turnos_r> | ε
```

**Verificación de predictividad (F1).** PRIM(`lote_r`) = {SESION, ε} y SGTE(`lote_r`) = {$}: disjuntos.
PRIM(`turnos_r`) = {NUM, ε} y SGTE(`turnos_r`) = {FIN}: disjuntos. No hay factores comunes
(`rol` se decide por `CLIENTE`/`AGENTE`). **F1 es LL(1)** y es la gramática de formato final.

---

## 2. Gramática lingüística (texto de un turno)

### L0 — gramática original (descriptiva)

Se escribió pensando solo en **describir** el lenguaje: sin preocuparse por la predictividad, con recursión por la
izquierda natural para listas, y con una alternativa por cada forma de escribir una cláusula (con o sin marca
temporal, con o sin frecuencia, con o sin complemento). El alcance de la negación ya está fijado aquí: `NEG` solo
precede a `pred_neg`. Gramática completa en el apéndice A.2.

Fragmento representativo:

```
<lista>    ::= <lista> PUNTO <oracion> | <oracion>
<oracion>  ::= <oracion> <sep> <clausula> | <clausula>
<sep>      ::= PERO | COMA | COMA PERO | Y
<clausula> ::= <nucleo> | ADV_T <nucleo> | <nucleo> <frec> | ADV_T <nucleo> <frec>
<nucleo>   ::= <sujeto> | <sujeto> V_COP <atrib> | <sujeto> <modif> | <sujeto> TICKET | <sujeto> <est>
             | <sujeto> SE <est> | <sujeto> V_CONT | <sujeto> V_CONT <compl> | <sujeto> <acc>
             | <sujeto> NEG <pred_neg> | <pred_l> | TICKET | CORTESIA
<est>      ::= V_EST | V_EST <compl>
<acc>      ::= V_ACC | V_ACC <obj> | V_ACC <modif> | V_ACC <obj> <modif>
<frec>     ::= <frec> FREC | FREC
```

**Diagnóstico L0** (calculado): recursión por la izquierda en `frec`, `lista`, `oracion`; y factor común en
`acc`, `clausula`, `est`, `frec`, `lista`, `nucleo`, `oracion`, `pred_l`, `pred_neg`, `sep`, `texto`.

---

### Paso 1 — Eliminación de la recursión por la izquierda  (L0 → L1)

Regla de clase: `A → Aα | β  ≡  A → βR ; R → αR | ε`.

| Variable | α (lo que se repite) | β (caso base) | Resultado |
|---|---|---|---|
| `lista` | `PUNTO <oracion>` | `<oracion>` | `lista → oracion lista_r` ; `lista_r → PUNTO oracion lista_r \| ε` |
| `oracion` | `<sep> <clausula>` | `<clausula>` | `oracion → clausula oracion_r` ; `oracion_r → sep clausula oracion_r \| ε` |
| `frec` | `FREC` | `FREC` | `frec → FREC frec_r` ; `frec_r → FREC frec_r \| ε` |

**Diagnóstico L1** (calculado): recursión por la izquierda **eliminada**. Quedan:

- factores comunes (PRIM∩PRIM) en `acc`, `clausula`, `est`, `nucleo`, `pred_l`, `pred_neg`, `sep`, `texto`;
- un **conflicto PRIM∩SGTE** nuevo en `lista_r`: PUNTO ∈ PRIM(`lista_r`) y PUNTO ∈ SGTE(`lista_r`). Aparece porque `texto`
  admite un `PUNTO` final opcional (`texto → lista | lista PUNTO`).

Este conflicto **no existía en L0**: lo introduce el Paso 1, porque `lista_r` es una variable anulable (`lista_r → ε`)
y para esas variables hay que comprobar PRIM contra SGTE. Por eso se diagnostica de nuevo después de cada transformación.

---

### Paso 2 — Factorización por la izquierda  (L1 → L2)

Regla de clase: `A → αβ₁ | αβ₂  ≡  A → αR ; R → β₁ | β₂`. Se detectaron los conflictos con PRIM
(PRIM de dos alternativas con intersección no vacía ⇒ factor común directo o indirecto).

| Variable | Alternativas con prefijo común α | Factorización |
|---|---|---|
| `texto` | `lista`, `lista PUNTO` (α = `lista`) | `texto → lista texto_p` ; `texto_p → PUNTO \| ε` |
| `sep` | `COMA`, `COMA PERO` (α = `COMA`) | `sep → PERO \| COMA sep_c \| Y` ; `sep_c → PERO \| ε` |
| `clausula` | `nucleo`, `nucleo frec` y `ADV_T nucleo`, `ADV_T nucleo frec` | `clausula → ADV_T nucleo frec_op \| nucleo frec_op` ; `frec_op → FREC frec_r \| ε` |
| `nucleo` | diez alternativas que empiezan con `sujeto` | `nucleo → sujeto pred_s \| …` ; `pred_s → NEG pred_neg \| V_COP atrib \| V_EST compl \| SE V_EST compl \| V_CONT compl \| V_ACC obj modif_op \| modif \| TICKET \| ε` |
| `est` | `V_EST`, `V_EST compl` | `V_EST compl`, con `compl → modif \| SIN SUST \| ε` |
| `pred_l` / `pred_neg` | `est`, `est SUST` y `SE est`, `SE est SUST` | `V_EST compl sujp` y `SE V_EST compl sujp`, con `sujp → SUST \| ε` |
| `pred_l` / `pred_neg` / `nucleo` | `V_CONT`, `V_CONT compl` | `V_CONT compl` (con `compl` anulable) |
| `acc` | `V_ACC`, `V_ACC obj`, `V_ACC modif`, `V_ACC obj modif` | `V_ACC obj modif_op`, con `obj → SUST \| TICKET \| ADV_T \| ε` y `modif_op → modif \| ε` |

Observaciones de método (como en el ejercicio de romanos):

- **`nucleo` es un caso de factor común *directo***: diez alternativas comparten el prefijo `sujeto`. Se factoriza
  `sujeto` una sola vez y la decisión pasa a `pred_s`.
- **`NEG` dentro de `pred_s`**: al factorizar, la alternativa `sujeto NEG pred_neg` pasa a ser `pred_s → NEG pred_neg`.
  El alcance de la negación **no cambió**: sigue siendo exactamente `pred_neg`.
- Al factorizar aparecen cuatro variables anulables nuevas (`compl`, `sujp`, `obj`, `modif_op`) además de `pred_s → ε`.
  Para cada una hubo que comprobar que su SGTE no se superpone con los PRIM de sus otras alternativas:
  `compl` ({INT, ADJ, SIN} frente a un SGTE con `SUST`, `FREC` y separadores), `sujp` (`SUST` frente a
  `FREC` y separadores), `obj` (`SUST`, `TICKET`, `ADV_T` frente a {INT, ADJ}, `FREC` y separadores). **No se superponen.**
- `est` y `acc` desaparecen: eran solo agrupaciones de la gramática descriptiva.

**Diagnóstico L2** (calculado): **PRIM∩PRIM = ∅** en todas las variables. Solo persiste el conflicto
PRIM∩SGTE de `lista_r` con `PUNTO`.

---

### Paso 3 — Resolución del conflicto PRIM∩SGTE y simplificación  (L2 → L3 final)

#### 3.1 El conflicto en `lista_r`

En L2:

```
<texto>   ::= <lista> <texto_p>        <texto_p> ::= PUNTO | ε
<lista_r> ::= PUNTO <oracion> <lista_r> | ε
```

Tras una oración, si el siguiente token es `PUNTO`, el parser no puede decidir si ese punto *separa* otra oración
(`lista_r → PUNTO oracion …`) o *termina* el texto (`texto_p → PUNTO`):

- PRIM(`lista_r`) = {PUNTO, ε}
- SGTE(`lista_r`) = PRIM(`texto_p`) ∪ SGTE(`texto`) = {PUNTO, EOL}

PUNTO está en ambos: **conflicto PRIM∩SGTE** (con la alternativa anulable `lista_r → ε`).

#### 3.2 Solución: consumir el `PUNTO` y decidir después

Se mueve la decisión *después* del punto, factorizando `PUNTO`:

```
<texto>    ::= <oracion> <texto_r>
<texto_r>  ::= PUNTO <texto_rr> | ε
<texto_rr> ::= <oracion> <texto_r> | ε
```

Tras `PUNTO`, `texto_rr` decide con **un solo token**: si es un PRIM de `oracion`, hay otra oración; si es `EOL`
(SGTE), el texto terminó. Se fusionan `texto`, `lista`, `lista_r` y `texto_p` en estas tres variables.

#### 3.3 Simplificación por sustitución

`oracion_r`, `sep` y `sep_c` se sustituyen entre sí, y `COMA PERO` queda representado en `cola_c`:

```
oracion_r → sep clausula oracion_r | ε      con sep → PERO | COMA sep_c | Y ; sep_c → PERO | ε
          ⇒ PERO clausula oracion_r | COMA PERO clausula oracion_r | COMA clausula oracion_r | Y clausula oracion_r | ε
```

Al renombrar `oracion_r` como `cola` y agrupar las alternativas que comienzan con `COMA`:

```
<oracion> ::= <clausula> <cola>
<cola>    ::= PERO <clausula> <cola> | COMA <cola_c> | Y <clausula> <cola> | ε
<cola_c>  ::= PERO <clausula> <cola> | <clausula> <cola>
```

Además se fusionan `frec_op` y `frec_r` en una sola variable (`frec → FREC frec | ε`), y las dos alternativas de
`clausula` se unifican con `adv_t_op` (`ADV_T | ε`): `clausula → adv_t_op nucleo frec`.

#### 3.4 Verificación final (L3)

| Condición | Resultado |
|---|---|
| Recursión por la izquierda | ninguna |
| PRIM de alternativas disjuntos | **sí**, en todas las variables |
| PRIM∩SGTE en alternativas anulables | **vacío** |
| Lenguaje igual a L0 (≤ 5 tokens, 23 220 cadenas) | **sí** |

**L3 es LL(1)** y es la gramática de `GRAMATICA.md`, con su tabla de PRIM/SGTE y su tabla predictiva (170 celdas, sin colisiones).

---

## 3. Qué demuestra cada paso

| Paso | Técnica de clase | Conflicto que elimina | Cómo se detecta |
|---|---|---|---|
| 1 | `A → Aα \| β` ⇒ `A → βR` | recursión por la izquierda (`lista`, `oracion`, `frec`, `lote`, `turnos`) | inspección + `verificar_ll1` |
| 2 | `A → αβ₁ \| αβ₂` ⇒ `A → αR` | factor común directo e indirecto | PRIM(αᵢ) ∩ PRIM(αⱼ) ≠ ∅ |
| 3 | factorizar `PUNTO` y sustituir | PRIM ∩ SGTE en una alternativa anulable | PRIM(`lista_r`) ∩ SGTE(`lista_r`) ≠ ∅ |

---

## Apéndice A. Gramáticas completas de cada paso (generadas por el código)

### A.1 Formato F0 (original)

```
<lote> ::= <lote> <sesion> | <sesion>
<sesion> ::= SESION ID_SESION EOL <turnos> FIN EOL
<turnos> ::= <turnos> <turno> | <turno>
<turno> ::= NUM <rol> DOSPUNTOS texto EOL
<rol> ::= CLIENTE | AGENTE
```

### A.2 Lingüística L0 (original)

```
<texto> ::= <lista> | <lista> PUNTO
<lista> ::= <lista> PUNTO <oracion> | <oracion>
<oracion> ::= <oracion> <sep> <clausula> | <clausula>
<sep> ::= PERO | COMA | COMA PERO | Y
<clausula> ::= <nucleo> | ADV_T <nucleo> | <nucleo> <frec> | ADV_T <nucleo> <frec>
<nucleo> ::= <sujeto> | <sujeto> V_COP <atrib> | <sujeto> <modif> | <sujeto> TICKET | <sujeto> <est> | <sujeto> SE <est> | <sujeto> V_CONT | <sujeto> V_CONT <compl> | <sujeto> <acc> | <sujeto> NEG <pred_neg> | <pred_l> | TICKET | CORTESIA
<pred_l> ::= NEG <pred_neg> | V_COP <atrib> | <est> | <est> SUST | SE <est> | SE <est> SUST | V_CONT | V_CONT <compl> | <acc>
<pred_neg> ::= V_COP <atrib> | <est> | <est> SUST | SE <est> | SE <est> SUST | V_CONT | V_CONT <compl> | <acc>
<est> ::= V_EST | V_EST <compl>
<acc> ::= V_ACC | V_ACC <obj> | V_ACC <modif> | V_ACC <obj> <modif>
<compl> ::= <modif> | SIN SUST
<obj> ::= SUST | TICKET | ADV_T
<sujeto> ::= SUST | AGENTE
<atrib> ::= <modif> | TICKET
<modif> ::= INT ADJ | ADJ
<frec> ::= <frec> FREC | FREC
```

### A.3 Lingüística L1 (sin recursión por la izquierda)

```
<texto> ::= <lista> | <lista> PUNTO
<lista> ::= <oracion> <lista_r>
<lista_r> ::= PUNTO <oracion> <lista_r> | ε
<oracion> ::= <clausula> <oracion_r>
<oracion_r> ::= <sep> <clausula> <oracion_r> | ε
<sep> ::= PERO | COMA | COMA PERO | Y
<clausula> ::= <nucleo> | ADV_T <nucleo> | <nucleo> <frec> | ADV_T <nucleo> <frec>
<nucleo> ::= <sujeto> | <sujeto> V_COP <atrib> | <sujeto> <modif> | <sujeto> TICKET | <sujeto> <est> | <sujeto> SE <est> | <sujeto> V_CONT | <sujeto> V_CONT <compl> | <sujeto> <acc> | <sujeto> NEG <pred_neg> | <pred_l> | TICKET | CORTESIA
<pred_l> ::= NEG <pred_neg> | V_COP <atrib> | <est> | <est> SUST | SE <est> | SE <est> SUST | V_CONT | V_CONT <compl> | <acc>
<pred_neg> ::= V_COP <atrib> | <est> | <est> SUST | SE <est> | SE <est> SUST | V_CONT | V_CONT <compl> | <acc>
<est> ::= V_EST | V_EST <compl>
<acc> ::= V_ACC | V_ACC <obj> | V_ACC <modif> | V_ACC <obj> <modif>
<compl> ::= <modif> | SIN SUST
<obj> ::= SUST | TICKET | ADV_T
<sujeto> ::= SUST | AGENTE
<atrib> ::= <modif> | TICKET
<modif> ::= INT ADJ | ADJ
<frec> ::= FREC <frec_r>
<frec_r> ::= FREC <frec_r> | ε
```

### A.4 Lingüística L2 (factorizada)

```
<texto> ::= <lista> <texto_p>
<texto_p> ::= PUNTO | ε
<lista> ::= <oracion> <lista_r>
<lista_r> ::= PUNTO <oracion> <lista_r> | ε
<oracion> ::= <clausula> <oracion_r>
<oracion_r> ::= <sep> <clausula> <oracion_r> | ε
<sep> ::= PERO | COMA <sep_c> | Y
<sep_c> ::= PERO | ε
<clausula> ::= ADV_T <nucleo> <frec_op> | <nucleo> <frec_op>
<frec_op> ::= FREC <frec_r> | ε
<frec_r> ::= FREC <frec_r> | ε
<nucleo> ::= <sujeto> <pred_s> | <pred_l> | TICKET | CORTESIA
<pred_s> ::= NEG <pred_neg> | V_COP <atrib> | V_EST <compl> | SE V_EST <compl> | V_CONT <compl> | V_ACC <obj> <modif_op> | <modif> | TICKET | ε
<pred_l> ::= NEG <pred_neg> | V_COP <atrib> | V_EST <compl> <sujp> | SE V_EST <compl> <sujp> | V_CONT <compl> | V_ACC <obj> <modif_op>
<pred_neg> ::= V_COP <atrib> | V_EST <compl> <sujp> | SE V_EST <compl> <sujp> | V_CONT <compl> | V_ACC <obj> <modif_op>
<compl> ::= <modif> | SIN SUST | ε
<sujp> ::= SUST | ε
<obj> ::= SUST | TICKET | ADV_T | ε
<modif_op> ::= <modif> | ε
<sujeto> ::= SUST | AGENTE
<atrib> ::= <modif> | TICKET
<modif> ::= INT ADJ | ADJ
```

### A.5 Lingüística L3 (final, LL(1))

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
