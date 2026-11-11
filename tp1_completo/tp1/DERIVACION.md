# TP1 · Derivación de la gramática: de la BNF descriptiva a la LL(1)

Este documento reconstruye **todos los pasos intermedios** entre la gramática original (descriptiva) y la gramática
predictiva final de `GRAMATICA.md`, siguiendo la metodología de clase:

> *Consejo del profesor (Clase 2):* primero describir el lenguaje sin dejar fuera ninguna cadena válida; después
> convertir la gramática en predictiva con las técnicas estudiadas, y **comprobar que no se introdujo «basura»**.

Cada gramática intermedia se **diagnostica con el código** (`derivacion.py`: PRIM, SGTE y condiciones LL(1)) y se
comprueba por enumeración que todas generan **el mismo lenguaje**. Para repetirlo: `python3 derivacion.py` (N=4, ~1 s) o
`python3 derivacion.py 5` (~40 s).

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
| Lingüística | L0 (original) | 13 | `frec`, `lista`, `oracion` | `texto`, `lista`, `oracion`, `sep`, `nucleo`, `pred_l`, `pred_neg`, `frec` | — |
| Lingüística | L1 (sin rec. izq.) | 16 | — | `texto`, `sep`, `nucleo`, `pred_l`, `pred_neg` | `lista_r` |
| Lingüística | L2 (factorizada) | 24 | — | — | `lista_r` |
| Lingüística | L3 (final LL(1)) | 22 | — | — | — |

### Equivalencia del lenguaje

(En la parte de formato, `texto` se trata como un terminal más; su lenguaje se verifica en la parte lingüística.)

Se enumeran todas las cadenas de terminales que genera cada gramática hasta una longitud acotada y se comparan con las
de la gramática original:

| Parte | Longitud máx. | Cadenas generadas | Original = L1 = L2 = final |
|---|---|---|---|
| Formato | 21 tokens | 18 | sí |
| Lingüística | 5 tokens | 28 425 | sí |

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

**Verificación de predictividad (F1).** PRIM(`lote_r`) = {KW_SESION, ε} y SGTE(`lote_r`) = {$}: disjuntos.
PRIM(`turnos_r`) = {NUM, ε} y SGTE(`turnos_r`) = {KW_FIN}: disjuntos. No hay factores comunes
(`rol` se decide por `CLIENTE`/`AGENTE`). **F1 es LL(1)** y es la gramática de formato final.

---

## 2. Gramática lingüística (texto de un turno)

### L0 — gramática original (descriptiva)

Se escribió pensando solo en **describir** el lenguaje: sin preocuparse por la predictividad, con recursión por la
izquierda natural para listas, y con una alternativa por cada forma de escribir una cláusula
(`sujeto V_COPULA modif`, `sujeto modif`, `sujeto V_FUNC`, `sujeto V_SEGUIR seg`, `sujeto SE V_CORTA`, …). El alcance de la negación ya está fijado aquí:
`NEG` solo precede a `pred_neg` o a un sustantivo (`seg`). Gramática completa en el apéndice A.2.

Fragmento representativo:

```
<lista>   ::= <lista> PUNTO <oracion> | <oracion>
<oracion> ::= <oracion> <sep> <clausula> | <clausula>
<sep>     ::= PERO | COMA | COMA PERO
<nucleo>  ::= <sujeto> | <sujeto> V_COPULA <modif> | <sujeto> <modif> | <sujeto> V_FUNC | <sujeto> V_FUNC <modif>
            | <sujeto> V_SEGUIR <seg> | <sujeto> SE V_CORTA | <sujeto> SE V_CORTA <frec>
            | <sujeto> NEG <pred_neg> | <pred_l> | TICKET_PAL | TICKET_PAL TICKET | TICKET_PAL V_COPULA TICKET | TICKET | CORTESIA
<frec>    ::= <frec> FREC | FREC
```

**Diagnóstico L0** (calculado): recursión por la izquierda en `lista`, `oracion` y `frec`; y factor común en
`texto`, `lista`, `oracion`, `sep`, `nucleo`, `pred_l`, `pred_neg`, `frec`.

---

### Paso 1 — Eliminación de la recursión por la izquierda  (L0 → L1)

Regla de clase: `A → Aα | β  ≡  A → βR ; R → αR | ε`.

| Variable | α (lo que se repite) | β (caso base) | Resultado |
|---|---|---|---|
| `lista` | `PUNTO <oracion>` | `<oracion>` | `lista → oracion lista_r` ; `lista_r → PUNTO oracion lista_r \| ε` |
| `oracion` | `<sep> <clausula>` | `<clausula>` | `oracion → clausula oracion_r` ; `oracion_r → sep clausula oracion_r \| ε` |
| `frec` | `FREC` | `FREC` | `frec → FREC frec_r` ; `frec_r → FREC frec_r \| ε` |

```
<lista>     ::= <oracion> <lista_r>
<lista_r>   ::= PUNTO <oracion> <lista_r> | ε
<oracion>   ::= <clausula> <oracion_r>
<oracion_r> ::= <sep> <clausula> <oracion_r> | ε
<frec>      ::= FREC <frec_r>
<frec_r>    ::= FREC <frec_r> | ε
```

**Diagnóstico L1** (calculado): recursión por la izquierda **eliminada**. Quedan:

- factores comunes (PRIM∩PRIM) en `texto`, `sep`, `nucleo`, `pred_l`, `pred_neg`;
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
| `sep` | `COMA`, `COMA PERO` (α = `COMA`) | `sep → PERO \| COMA sep_c` ; `sep_c → PERO \| ε` |
| `nucleo` | nueve alternativas que empiezan con `sujeto` | `nucleo → sujeto pred_s \| …` ; `pred_s → NEG pred_neg \| V_COPULA modif \| V_FUNC modif_op \| V_SEGUIR seg \| SE V_CORTA frec_op \| modif \| ε` |
| `nucleo` | `TICKET_PAL`, `TICKET_PAL TICKET`, `TICKET_PAL V_COPULA TICKET` | `TICKET_PAL tk_op` ; `tk_op → V_COPULA TICKET \| TICKET \| ε` |
| `pred_l` / `pred_neg` | `V_FUNC`, `V_FUNC modif` | `V_FUNC modif_op` ; `modif_op → modif \| ε` |
| `pred_l` / `pred_s` | `SE V_CORTA`, `SE V_CORTA frec` | `SE V_CORTA frec_op` |
| `pred_l` / `pred_neg` | `V_ENTENDER`, `V_ENTENDER ASP_CLAR` | `V_ENTENDER obj_clar` ; `obj_clar → ASP_CLAR \| ε` |
| `pred_l` | `V_SOLICITUD`, `V_SOLICITUD ROUTER` | `V_SOLICITUD obj_router` ; `obj_router → ROUTER \| ε` |
| `pred_l` | `T_FUTURO V_COMPROMISO [TICKET \| T_FUTURO]` y `V_COMPROMISO [TICKET \| T_FUTURO]` | `… V_COMPROMISO ref_op` ; `ref_op → TICKET \| T_FUTURO \| ε` |
| `frec_op` | `FREC frec_r`, ε (opcionalidad de `frec` tras `SE V_CORTA`) | `frec_op → FREC frec_r \| ε` |

Observaciones de método (como en el ejercicio de romanos):

- **`nucleo` es un caso de factor común *directo***: nueve alternativas comparten el prefijo `sujeto`. Se factoriza
  `sujeto` una sola vez y la decisión pasa a `pred_s`. Como `sujeto` deriva cuatro terminales distintos
  (`ASP_SERV`, `ASP_ATEN`, `ASP_CLAR`, `AGENTE`), el PRIM de esas alternativas coincide completo.
- **`NEG` dentro de `pred_s`**: al factorizar, la alternativa `sujeto NEG pred_neg` pasa a ser `pred_s → NEG pred_neg`.
  El alcance de la negación **no cambió**: sigue siendo exactamente `pred_neg`.
- Se introdujo la alternativa `pred_s → ε` (sujeto solo, p. ej. «el servicio»). Fue necesario
  comprobar que su SGTE `{COMA, EOL, PERO, PUNTO}` no se superpone con los PRIM de las demás alternativas de
  `pred_s` (`NEG`, `V_COPULA`, `V_FUNC`, `V_SEGUIR`, `SE`, `INT`, `ADJ_*`). **No se superpone.**

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

Se mueve la decisión *después* del punto, factorizando `PUNTO` (otro caso de factor común, esta vez entre una
alternativa y su continuación):

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
oracion_r → sep clausula oracion_r | ε      con sep → PERO | COMA sep_c ; sep_c → PERO | ε
          ⇒ PERO clausula oracion_r | COMA PERO clausula oracion_r | COMA clausula oracion_r | ε
```

Al renombrar `oracion_r` como `cola` y agrupar las alternativas que comienzan con `COMA`:

```
<oracion> ::= <clausula> <cola>
<cola>    ::= PERO <clausula> <cola> | COMA <cola_c> | ε
<cola_c>  ::= PERO <clausula> <cola> | <clausula> <cola>
```

Además se fusionan `frec_op` y `frec_r` en una sola variable (`frec → FREC frec | ε`), y se introduce
`ahora_op` (`T_AHORA | ε`) para la cláusula `clausula → ahora_op nucleo`.

#### 3.4 Verificación final (L3)

| Condición | Resultado |
|---|---|
| Recursión por la izquierda | ninguna |
| PRIM de alternativas disjuntos | **sí**, en todas las variables |
| PRIM∩SGTE en alternativas anulables | **vacío** |
| Lenguaje igual a L0 (≤ 5 tokens, 28 425 cadenas) | **sí** |

**L3 es LL(1)** y es la gramática de `GRAMATICA.md`, con su tabla de PRIM/SGTE y su tabla predictiva (199 celdas, sin colisiones).

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
<sesion> ::= KW_SESION ID_SESION EOL <turnos> KW_FIN EOL
<turnos> ::= <turnos> <turno> | <turno>
<turno> ::= NUM <rol> DOSPUNTOS texto EOL
<rol> ::= CLIENTE | AGENTE
```

### A.2 Lingüística L0 (original)

```
<texto> ::= <lista> | <lista> PUNTO
<lista> ::= <lista> PUNTO <oracion> | <oracion>
<oracion> ::= <oracion> <sep> <clausula> | <clausula>
<sep> ::= PERO | COMA | COMA PERO
<clausula> ::= T_AHORA <nucleo> | <nucleo>
<nucleo> ::= <sujeto> | <sujeto> V_COPULA <modif> | <sujeto> <modif> | <sujeto> V_FUNC | <sujeto> V_FUNC <modif> | <sujeto> V_SEGUIR <seg> | <sujeto> SE V_CORTA | <sujeto> SE V_CORTA <frec> | <sujeto> NEG <pred_neg> | <pred_l> | TICKET_PAL | TICKET_PAL TICKET | TICKET_PAL V_COPULA TICKET | TICKET | CORTESIA
<sujeto> ::= ASP_SERV | ASP_ATEN | ASP_CLAR | AGENTE
<pred_l> ::= NEG <pred_neg> | V_FUNC | V_FUNC <modif> | V_SEGUIR <seg> | SE V_CORTA | SE V_CORTA <frec> | V_ENTENDER | V_ENTENDER ASP_CLAR | V_SOLICITUD | V_SOLICITUD ROUTER | T_FUTURO V_COMPROMISO | T_FUTURO V_COMPROMISO TICKET | T_FUTURO V_COMPROMISO T_FUTURO | V_COMPROMISO | V_COMPROMISO TICKET | V_COMPROMISO T_FUTURO
<pred_neg> ::= V_FUNC | V_FUNC <modif> | V_COPULA <modif> | V_ENTENDER | V_ENTENDER ASP_CLAR
<seg> ::= <modif> | NEG ASP_SERV
<modif> ::= INT <adj> | <adj>
<adj> ::= ADJ_POS | ADJ_NEG
<frec> ::= <frec> FREC | FREC
```

### A.3 Lingüística L1 (sin recursión por la izquierda)

```
<texto> ::= <lista> | <lista> PUNTO
<lista> ::= <oracion> <lista_r>
<lista_r> ::= PUNTO <oracion> <lista_r> | ε
<oracion> ::= <clausula> <oracion_r>
<oracion_r> ::= <sep> <clausula> <oracion_r> | ε
<sep> ::= PERO | COMA | COMA PERO
<clausula> ::= T_AHORA <nucleo> | <nucleo>
<nucleo> ::= <sujeto> | <sujeto> V_COPULA <modif> | <sujeto> <modif> | <sujeto> V_FUNC | <sujeto> V_FUNC <modif> | <sujeto> V_SEGUIR <seg> | <sujeto> SE V_CORTA | <sujeto> SE V_CORTA <frec> | <sujeto> NEG <pred_neg> | <pred_l> | TICKET_PAL | TICKET_PAL TICKET | TICKET_PAL V_COPULA TICKET | TICKET | CORTESIA
<sujeto> ::= ASP_SERV | ASP_ATEN | ASP_CLAR | AGENTE
<pred_l> ::= NEG <pred_neg> | V_FUNC | V_FUNC <modif> | V_SEGUIR <seg> | SE V_CORTA | SE V_CORTA <frec> | V_ENTENDER | V_ENTENDER ASP_CLAR | V_SOLICITUD | V_SOLICITUD ROUTER | T_FUTURO V_COMPROMISO | T_FUTURO V_COMPROMISO TICKET | T_FUTURO V_COMPROMISO T_FUTURO | V_COMPROMISO | V_COMPROMISO TICKET | V_COMPROMISO T_FUTURO
<pred_neg> ::= V_FUNC | V_FUNC <modif> | V_COPULA <modif> | V_ENTENDER | V_ENTENDER ASP_CLAR
<seg> ::= <modif> | NEG ASP_SERV
<modif> ::= INT <adj> | <adj>
<adj> ::= ADJ_POS | ADJ_NEG
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
<sep> ::= PERO | COMA <sep_c>
<sep_c> ::= PERO | ε
<clausula> ::= T_AHORA <nucleo> | <nucleo>
<nucleo> ::= <sujeto> <pred_s> | <pred_l> | TICKET_PAL <tk_op> | TICKET | CORTESIA
<sujeto> ::= ASP_SERV | ASP_ATEN | ASP_CLAR | AGENTE
<pred_s> ::= NEG <pred_neg> | V_COPULA <modif> | V_FUNC <modif_op> | V_SEGUIR <seg> | SE V_CORTA <frec_op> | <modif> | ε
<pred_l> ::= NEG <pred_neg> | V_FUNC <modif_op> | V_SEGUIR <seg> | SE V_CORTA <frec_op> | V_ENTENDER <obj_clar> | V_SOLICITUD <obj_router> | T_FUTURO V_COMPROMISO <ref_op> | V_COMPROMISO <ref_op>
<pred_neg> ::= V_FUNC <modif_op> | V_COPULA <modif> | V_ENTENDER <obj_clar>
<seg> ::= <modif> | NEG ASP_SERV
<modif> ::= INT <adj> | <adj>
<modif_op> ::= <modif> | ε
<adj> ::= ADJ_POS | ADJ_NEG
<frec_op> ::= FREC <frec_r> | ε
<frec_r> ::= FREC <frec_r> | ε
<obj_clar> ::= ASP_CLAR | ε
<obj_router> ::= ROUTER | ε
<ref_op> ::= TICKET | T_FUTURO | ε
<tk_op> ::= V_COPULA TICKET | TICKET | ε
```

### A.5 Lingüística L3 (final, LL(1))

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
