# TP1 · Reglas semánticas

Definición dirigida por la sintaxis del analizador: qué atributo calcula cada producción de la gramática
(`GRAMATICA.md`) y cómo se llega desde ellos a la valoración por aspecto y al estado de la sesión.
Implementación: `semantica.py` (reglas por producción y estado) y `analizador.py` (atributos de contexto y
tabla de entidades).

## 1. Notación

Se usa la notación de clase (Clases 2 y 3): un cuadro **BNF | Reglas semánticas**, donde `X.a` es el atributo `a`
del símbolo `X` y un subíndice (`frec₁`) distingue dos apariciones del mismo símbolo en una producción.

- **Atributo sintetizado**: su valor depende solo de los hijos. Es el **valor de retorno** del procedimiento del
  no terminal.
- **Atributo heredado**: su valor lo entrega el padre o un hermano. Es un **parámetro**. En los cuadros se marca
  con el sufijo `.i`, como en la transformación `A → βR` de la Clase 3.
- Los terminales traen los atributos que les puso el analizador léxico: `tok.cat` (categoría), `tok.lex` (lexema
  original) y `tok.norm` (normalizado).
- `‖` concatena listas; `nulo` significa «sin valor».

**Cómo se evalúan.** El parser LL(1) (`sintaxis.py`) devuelve el árbol de derivación del turno. Después,
`semantica.ev(nodo)` busca la regla de la producción del nodo y la ejecuta; cada regla llama a `ev()` sobre sus
hijos y **retorna** sus atributos sintetizados. Cada fila de los cuadros de las secciones 3 a 6 es una función
registrada con `@acc(variable, producción)` (las de la sección 3, con `_constante(...)`, que registra una regla de
atributos fijos):

```python
@acc('modif', 'INT adj')                              # BNF:    modif → INT adj
def _modif_int(n):                                    # Regla:  modif.pol = adj.pol ; modif.int = ALTA
    return {'pol': ev(n.hijos[1])['pol'], 'int': 'ALTA'}   #   evalúa el hijo adj y retorna los atributos de modif
```

Si una producción de la gramática no tiene regla registrada, `@acc` falla al cargar el módulo (verifica que la
producción exista en `gramatica.py`), de modo que el cuadro y la gramática no pueden desincronizarse.

## 2. Atributos

| Símbolo | Atributo | Tipo | Valores | Significado |
|---|---|---|---|---|
| `sust`, `sujeto`, `sujp` | `cat` | sintetizado | subcategoría (`SUST_SERV`…, `AGENTE`) | para la tabla de compatibilidad |
| ídem | `asp` | sintetizado | `SERVICIO`, `ATENCION`, `CLARIDAD`, `nulo` | aspecto del que se habla |
| ídem | `pol` | sintetizado | `0`, `−1` | `−1` si el sustantivo es un problema («corte») |
| ídem | `ent` | sintetizado | `EQUIPO`, `TICKET`, `nulo` | tipo de entidad |
| `adj`, `modif`, `modif_op`, `atrib`, `compl` | `pol` | sintetizado | `+1`, `−1` | polaridad de la cualidad o del complemento |
| `modif`, `modif_op`, `atrib`, `compl` | `int` | sintetizado | `ALTA`, `nulo` | intensidad («muy», «bastante») |
| `v_est` | `pol` | sintetizado | `+1`, `−1` | el servicio anda bien / anda mal |
| `v_acc` | `clase` | sintetizado | `ENT`, `SOLIC`, `COMPR`, `VAL` | entender, pedir, prometer, valorar |
| `v_acc` | `asp` | sintetizado | `ATENCION`, `CLARIDAD`, `nulo` | aspecto que valora el verbo |
| `adv_t`, `adv_t_op` | `t` | sintetizado | `AHORA`, `FUTURO`, `nulo` | marca temporal |
| `atrib` | `ticket` | sintetizado | token, `nulo` | ticket después de la cópula |
| `compl` | `t` | sintetizado | `CUAL`, `SIN`, `nulo` | tipo de complemento |
| `compl` | `asp` | sintetizado | aspecto del sustantivo de «sin» | — |
| `obj` | `s`, `ticket`, `plazo` | sintetizado | sustantivo, token, tiempo, `nulo` | objeto del verbo de acción |
| `frec` | `n` | sintetizado | entero ≥ 0 | cantidad de tokens de frecuencia |
| `pred_s`, `pred_l`, `pred_neg` | `k` | sintetizado | `COP`, `EST`, `CORTE`, `SEG_ADJ`, `SEG_SIN`, `ENT`, `VAL`, `SOLIC`, `COMPR`, `REF`, `MENCION`, `INCOMPLETO` | tipo de predicado |
| ídem | `pol`, `int`, `asp` | sintetizado | como arriba | polaridad **antes** de negar, intensidad, aspecto propio |
| ídem | `pos` | sintetizado | sustantivo, `nulo` | sujeto pospuesto |
| `pred_s`, `pred_l` | `neg` | sintetizado | verdadero, falso | el predicado está negado |
| `nucleo`, `clausula` | `h` | sintetizado | registro *hecho* (abajo) | interpretación de la cláusula |
| `texto`, `oracion`, `cola`, … | `L` | sintetizado | lista de hechos | cláusulas del turno, en orden textual |
| `texto`, `oracion`, `clausula` | `actor.i`, `turno.i` | heredado | rol y número del turno | autoría de la evidencia |
| `oracion`, `clausula` | `con.i` | heredado | `nulo`, `COMA`, `Y`, `PUNTO`, `PERO` | conector que precede a la cláusula |
| `turno` | `val[a]` | sintetizado | valoración por aspecto | resultado del turno |
| `sesion` | `resumen[a]`, `estado` | sintetizado | secciones 7 y 8 | resultado de la sesión |

**Registro *hecho*** (`clausula.h`), una entrada por cláusula interpretada:

| Campo | Valores |
|---|---|
| `tipo` | `VALORACION`, `FUNCIONAMIENTO`, `MENCION`, `SOLICITUD`, `COMPROMISO`, `TICKET`, `CORTESIA` |
| `aspecto` | `SERVICIO`, `ATENCION`, `CLARIDAD`, `nulo` |
| `valoracion` | `POSITIVA`, `NEGATIVA`, `NEUTRA`, `nulo` |
| `intensidad` | `ALTA`, `nulo` |
| `negada` | verdadero, falso |
| `declaracion` | `OK` (funciona), `FALLA` (no funciona), `RECUR` (se corta), `nulo` |
| `entidades` | lista de tickets o equipos |
| `temporal` | `AHORA`, `nulo` |
| `reglas` | identificadores `R-…` aplicados (trazabilidad, sección 10) |

## 3. Grupos de subcategorías: qué significa cada categoría léxica

La tabla de símbolos léxica solo guarda `forma → categoría`. El significado de cada categoría lo fija la regla de su
producción unitaria, igual que `dig → 0 : dig.x = '0'` en los apuntes. Por eso insertar una palabra nueva no requiere
tocar ninguna regla: basta con elegir su subcategoría.

| BNF | Reglas semánticas |
|---|---|
| `sust → SUST_SERV` | `sust.asp = SERVICIO; sust.pol = 0; sust.ent = nulo` |
| `sust → SUST_ATEN` | `sust.asp = ATENCION; sust.pol = 0; sust.ent = nulo` |
| `sust → SUST_CLAR` | `sust.asp = CLARIDAD; sust.pol = 0; sust.ent = nulo` |
| `sust → SUST_EQUIPO` | `sust.asp = SERVICIO; sust.pol = 0; sust.ent = EQUIPO` |
| `sust → SUST_TICKET` | `sust.asp = nulo; sust.pol = 0; sust.ent = TICKET` |
| `sust → SUST_PROB` | `sust.asp = SERVICIO; sust.pol = −1; sust.ent = nulo` |
| `adj → ADJ_POS` | `adj.pol = +1` |
| `adj → ADJ_NEG` | `adj.pol = −1` |
| `v_est → V_EST_OK` | `v_est.pol = +1` |
| `v_est → V_EST_FALLA` | `v_est.pol = −1` |
| `v_acc → V_ENTENDER` | `v_acc.clase = ENT; v_acc.asp = CLARIDAD` |
| `v_acc → V_SOLICITUD` | `v_acc.clase = SOLIC; v_acc.asp = nulo` |
| `v_acc → V_COMPROMISO` | `v_acc.clase = COMPR; v_acc.asp = nulo` |
| `v_acc → V_VAL_ATEN` | `v_acc.clase = VAL; v_acc.asp = ATENCION` |
| `v_acc → V_VAL_CLAR` | `v_acc.clase = VAL; v_acc.asp = CLARIDAD` |
| `adv_t → T_AHORA` | `adv_t.t = AHORA` |
| `adv_t → T_FUTURO` | `adv_t.t = FUTURO` |

Todas agregan además `cat` (la subcategoría) y `tok` (el token). `V_EST_RECUR` («corta») no pertenece a ningún grupo:
solo aparece en la producción `SE V_EST_RECUR`.

### 3.1 Modificadores y complementos

| BNF | Reglas semánticas | Regla |
|---|---|---|
| `modif → adj` | `modif.pol = adj.pol; modif.int = nulo` | |
| `modif → INT adj` | `modif.pol = adj.pol; modif.int = ALTA` | R-MUY |
| `modif_op → modif` | `modif_op.pol = modif.pol; modif_op.int = modif.int` | |
| `modif_op → ε` | `modif_op = nulo` | |
| `atrib → modif` | `atrib.pol = modif.pol; atrib.int = modif.int; atrib.ticket = nulo` | |
| `atrib → TICKET` | `atrib.ticket = TICKET` | |
| `compl → modif` | `compl.t = CUAL; compl.pol = modif.pol; compl.int = modif.int` | |
| `compl → SIN sust` | `compl.t = SIN; compl.asp = sust.asp; compl.pol = (sust.pol = −1) ? +1 : −1` | R-SIN |
| `compl → ε` | `compl = nulo` | |
| `sujp → sust` | `sujp = sust` (todos sus atributos) | R-POSP |
| `sujp → ε` | `sujp = nulo` | |
| `obj → sust` | `obj.s = sust` | |
| `obj → TICKET` | `obj.ticket = TICKET` | |
| `obj → adv_t` | `obj.plazo = adv_t.t` | |
| `obj → ε` | `obj.s = obj.ticket = obj.plazo = nulo` | |
| `frec → FREC frec₁` | `frec.n = 1 + frec₁.n` | |
| `frec → ε` | `frec.n = 0` | |
| `adv_t_op → adv_t` | `adv_t_op.t = adv_t.t` | |
| `adv_t_op → ε` | `adv_t_op = nulo` | |

`compl → SIN sust` distingue lo que falta: «sin internet» es negativo porque falta algo bueno; «sin cortes» es
positivo porque lo que falta es un problema. `frec → FREC frec₁` es el mismo esquema del robot de la Clase 6
(`R → INSRT R₁`); `frec.n` se calcula pero no interviene en ninguna decisión.

## 4. Sujeto y predicados

| BNF | Reglas semánticas | Regla |
|---|---|---|
| `sujeto → sust` | `sujeto = sust` (todos sus atributos) | R-SUJ |
| `sujeto → AGENTE` | `sujeto.cat = AGENTE; sujeto.asp = ATENCION; sujeto.pol = 0; sujeto.ent = nulo` | R-SUJ |

Las reglas de predicado valen igual para `pred_s`, `pred_l` y `pred_neg`. En `pred_l` y `pred_neg`, las
alternativas con `sujp` agregan `pred.pos = sujp`; en `pred_s` no hay sujeto pospuesto.

| BNF | Reglas semánticas | Regla |
|---|---|---|
| `pred → V_COP atrib` | si `atrib.ticket ≠ nulo`: `pred.k = REF; pred.ticket = atrib.ticket`. Si no: `pred.k = COP; pred.pol = atrib.pol; pred.int = atrib.int` | R-TICKET / R-COP |
| `pred_s → modif` | `pred_s.k = COP; pred_s.pol = modif.pol; pred_s.int = modif.int` | R-COP |
| `pred_s → TICKET` | `pred_s.k = REF; pred_s.ticket = TICKET` | R-TICKET |
| `pred_s → ε` | `pred_s.k = MENCION` | R-MEN |
| `pred → v_est compl [sujp]` | `pred.k = EST; pred.pol = (v_est.pol = −1) ? −1 : (compl ≠ nulo ? compl.pol : +1); pred.int = compl.int` | R-EST (y R-SIN si `compl.t = SIN`) |
| `pred → SE V_EST_RECUR [sujp]` | `pred.k = CORTE; pred.pol = −1` | R-CORTE |
| `pred → V_CONT compl` | `compl.t = CUAL`: `pred.k = SEG_ADJ; pred.pol = compl.pol; pred.int = compl.int`. `compl.t = SIN`: `pred.k = SEG_SIN; pred.pol = compl.pol; pred.asp = compl.asp`. `compl = nulo`: `pred.k = INCOMPLETO` | R-SEG-ADJ / R-SEG-SIN |
| `pred → v_acc obj modif_op` | según `v_acc.clase` (cuadro siguiente) | |
| `pred_s → NEG pred_neg`, `pred_l → NEG pred_neg` | copia todos los atributos de `pred_neg`; `pred.neg = verdadero` | R-NEG |

Para `pred → v_acc obj modif_op`:

| `v_acc.clase` | Reglas semánticas | Regla |
|---|---|---|
| `ENT` | `pred.k = ENT; pred.asp = CLARIDAD; pred.pol = (modif_op ≠ nulo) ? modif_op.pol : +1` | R-ENT |
| `VAL`, con `modif_op` | `pred.k = VAL; pred.asp = v_acc.asp; pred.pol = modif_op.pol; pred.int = modif_op.int` | R-VAL |
| `VAL`, sin `modif_op` | `pred.k = MENCION; pred.asp = v_acc.asp` | R-MEN |
| `SOLIC` | `pred.k = SOLIC; pred.ent = obj.s` | R-SOLIC |
| `COMPR` | `pred.k = COMPR; pred.ticket = obj.ticket; pred.plazo = obj.plazo` | R-COMPR |

Donde no se indica, `neg = falso`. `pred_s → modif` es la cópula omitida («el servicio **muy lento**»).
En `pred → NEG pred_neg` la polaridad **no** se invierte todavía: se retorna la del predicado y la marca `neg`; la
inversión se hace una sola vez, en `construir()` (sección 5). En `pred → v_est compl`, un verbo de falla no se vuelve
positivo por el complemento: «falla» es negativo aunque lo siga un adjetivo.

## 5. Núcleo y cláusula

| BNF | Reglas semánticas | Regla |
|---|---|---|
| `nucleo → sujeto pred_s` | `nucleo.h = construir(pred_s, sujeto)` | la del predicado + R-SUJ |
| `nucleo → pred_l` | `nucleo.h = construir(pred_l, nulo)` | la del predicado |
| `nucleo → TICKET` | `nucleo.h = hecho(TICKET, entidades = [TICKET.norm])` | R-TICKET |
| `nucleo → CORTESIA` | `nucleo.h = hecho(CORTESIA)` | R-CORT |
| `clausula → adv_t_op nucleo frec` | `clausula.h = nucleo.h; si adv_t_op.t = AHORA: clausula.h.temporal = AHORA` | R-AHORA |

`hecho(tipo, …)` crea un registro con el resto de los campos en `nulo`. La función `construir(p, s)` convierte los
atributos de un predicado `p` y el sujeto explícito `s` (`nulo` si la cláusula no tiene sujeto delante) en un hecho.
`suj` es el sujeto que aporta el aspecto: `s` o, si no hay, el pospuesto `p.pos`.

| Paso | Regla de cálculo |
|---|---|
| 1 | **Compatibilidad (R-COMPAT).** Si la combinación no es válida (cuadro siguiente), la cláusula **no se interpreta**: sus tokens pasan a `NO_INTERPRETADO`. Fin. |
| 2 | `p.k = MENCION`: `hecho(MENCION, aspecto = s.asp o p.asp, valoracion = NEUTRA)`; si el sujeto es un `SUST_TICKET`, `hecho(TICKET)`. `SOLIC`: `hecho(SOLICITUD, entidades = [equipo])`. `COMPR`: `hecho(COMPROMISO, entidades = [p.ticket])`. `REF`: `hecho(TICKET, entidades = [p.ticket])`. Fin. |
| 3 | `aspecto = p.asp` si `p.k = SEG_SIN`; si no, `suj.asp` cuando hay sujeto; si no, `p.asp` (`ENT`, `VAL`); si no, `SERVICIO`. |
| 4 | `pol' = −p.pol` si `p.neg` (R-NEG); si no, `pol' = p.pol`. |
| 5 | `valoracion = POSITIVA` si `pol' = +1`; `NEGATIVA` si `pol' = −1`. |
| 6 | `declaracion`, solo cuando `aspecto = SERVICIO`: `EST`, `SEG_ADJ` y `SEG_SIN` → `OK` si `pol' = +1`, `FALLA` si `pol' = −1`; `CORTE` sin negar → `RECUR`; `CORTE` negado, `COP`, `ENT` y `VAL` → `nulo`. |
| 7 | `tipo = FUNCIONAMIENTO` si `declaracion ≠ nulo`; si no, `VALORACION`. |
| 8 | `intensidad = p.int` (R-MUY si no es `nulo`); `negada = p.neg`; `entidades = [equipo]` si el sujeto es un `SUST_EQUIPO`. |

**Compatibilidad sujeto–predicado** (tabla `COMPAT` en `semantica.py`). Es el chequeo de tipos del análisis
semántico: la gramática acepta «el agente se corta», pero no tiene sentido interpretarlo.

| Sujeto (`cat`) | Predicados admitidos (`k`) |
|---|---|
| `SUST_SERV`, `SUST_EQUIPO` | `COP`, `EST`, `SEG_ADJ`, `SEG_SIN`, `CORTE`, `MENCION` |
| `SUST_ATEN`, `AGENTE` | `COP`, `SEG_ADJ`, `MENCION`; `VAL` si el verbo valora la ATENCION |
| `SUST_CLAR` | `COP`, `SEG_ADJ`, `MENCION`; `VAL` si el verbo valora la CLARIDAD |
| `SUST_TICKET` | `REF`, `MENCION` |
| `SUST_PROB` | `COP`, `SEG_ADJ`, `MENCION` |
| sin sujeto | todos, salvo `INCOMPLETO` |

También se rechaza una cláusula con sujeto delante **y** detrás del verbo («el servicio no funciona el internet») y
un `V_CONT` sin complemento («sigue»). El sujeto pospuesto se comprueba con la misma tabla.

Consecuencias que conviene tener presentes:

- «El servicio **está** lento» (`COP`) es una valoración NEGATIVA del SERVICIO, pero **no** es una declaración de
  funcionamiento: no fija el estado. «**Sigue** lento», «**no funciona**», «**falla**» y «**se corta**» sí lo son.
- «La atención sigue mala» valora la ATENCION y no declara nada sobre el funcionamiento (paso 6).
- «No se corta» valora el SERVICIO como POSITIVA, pero no declara que funcione (paso 6).
- «El router no anda» valora y declara sobre el SERVICIO, y registra `ROUTER` como entidad.
- Una solicitud, un compromiso, un ticket o una cortesía no tienen aspecto ni valoración: no aportan evidencia a
  ningún aspecto.

## 6. Turno: lista de cláusulas y atributos heredados

La cláusula no sabe por sí sola quién la dijo ni qué conector la precede: eso baja desde el turno. Estas reglas
recorren el árbol en orden textual.

| BNF | Reglas semánticas |
|---|---|
| `turno → NUM rol DOSPUNTOS texto EOL` | `texto.actor.i = rol.r; texto.turno.i = NUM.val; turno.L = texto.L; turno.val[a] = combinar({ h.valoracion : h ∈ turno.L, h.aspecto = a })` |
| `rol → CLIENTE` | `rol.r = CLIENTE` |
| `rol → AGENTE` | `rol.r = AGENTE` |
| `texto → oracion texto_r` | `oracion.con.i = nulo; texto.L = oracion.L ‖ texto_r.L` |
| `texto_r → PUNTO texto_rr` | `texto_r.L = texto_rr.L` |
| `texto_r → ε` | `texto_r.L = [ ]` |
| `texto_rr → oracion texto_r` | `oracion.con.i = PUNTO; texto_rr.L = oracion.L ‖ texto_r.L` |
| `texto_rr → ε` | `texto_rr.L = [ ]` |
| `oracion → clausula cola` | `clausula.con.i = oracion.con.i; oracion.L = [clausula.h] ‖ cola.L` |
| `cola → PERO clausula cola₁` | `clausula.con.i = PERO; cola.L = [clausula.h] ‖ cola₁.L` |
| `cola → COMA cola_c` | `cola.L = cola_c.L` |
| `cola → Y clausula cola₁` | `clausula.con.i = Y; cola.L = [clausula.h] ‖ cola₁.L` |
| `cola → ε` | `cola.L = [ ]` |
| `cola_c → PERO clausula cola` | `clausula.con.i = PERO; cola_c.L = [clausula.h] ‖ cola.L` |
| `cola_c → clausula cola` | `clausula.con.i = COMA; cola_c.L = [clausula.h] ‖ cola.L` |

`actor.i` y `turno.i` se propagan sin cambios de `texto` a cada `clausula`. Al completar cada hecho con sus
atributos heredados:

- `h.actor = clausula.actor.i`, `h.turno = clausula.turno.i`, `h.id = C<turno>.<k>` (k = posición de la cláusula
  en el turno) y `h.fragmento` = texto original de la cláusula, con sus desplazamientos `desde` y `hasta`.
- Si `clausula.con.i = PERO`: se agrega **R-PERO** y `h.en_contraste_con` = id de la cláusula interpretada anterior
  del mismo turno. Las dos cláusulas se conservan por separado; el contraste no modifica ninguna valoración.
- Una cláusula con error sintáctico **no se evalúa**: sus tokens pasan a `NO_INTERPRETADO` y no entra en `L`.
  Lo mismo ocurre con una cláusula que `construir()` rechaza por incompatibilidad (R-COMPAT).

**Implementación.** A diferencia de las secciones 3 a 5, estos atributos no viajan como parámetros de `ev()`:
`semantica.clausulas(raiz)` recorre el árbol y entrega cada cláusula con su conector, y
`analizador._analizar_turno()` agrega actor, turno, id y fragmento. La gramática de formato (`turno`, `rol`) la
procesa `lector.py` línea a línea.

## 7. Valoración por aspecto

`combinar(V)`, sobre el conjunto de valoraciones `V` de un aspecto:

| Condición sobre `V` | Resultado |
|---|---|
| contiene `POSITIVA` y `NEGATIVA` | `MIXTA` |
| contiene `POSITIVA` (y no `NEGATIVA`) | `POSITIVA` |
| contiene `NEGATIVA` (y no `POSITIVA`) | `NEGATIVA` |
| solo contiene `NEUTRA` | `NEUTRA` |
| vacío | `SIN_EVIDENCIA` |

`MIXTA` no es un promedio ni una cancelación: las dos evidencias se conservan en la salida con su turno y texto.

| Nivel | Regla |
|---|---|
| Turno | `turno.val[a] = combinar` de las cláusulas del turno con `aspecto = a` |
| Sesión | `sesion.resumen[a].valoracion = combinar` de las cláusulas con `aspecto = a` **y `actor = CLIENTE`** |
| Sesión | `sesion.resumen[a].evidencias` = ids de esas cláusulas |
| Sesión | `sesion.resumen[a].opiniones_agente` = cláusulas con `aspecto = a` y `actor = AGENTE` (id y valoración) |

Las opiniones del AGENTE se conservan con su autoría, pero no entran en la valoración del resumen ni en el estado:
no se presentan como confirmaciones del CLIENTE.

## 8. Estado conversacional

Sobre la lista `L` de todas las cláusulas interpretadas de la sesión, en orden:

- `D` = cláusulas con `actor = CLIENTE` y `declaracion ≠ nulo` (declaraciones del cliente sobre el funcionamiento).
- `K` = cláusulas con `actor = AGENTE` y `tipo = COMPROMISO`.

| Condición | Estado | Regla |
|---|---|---|
| `D ≠ ∅` y hay una promesa en `K` **posterior** a la última declaración de `D` | `PENDIENTE` | R-EST-PEND (por R-EST-PREC) |
| `D ≠ ∅` en otro caso | el que resulta de recorrer `D` (cuadro siguiente) | R-EST-RES, R-EST-NORES o R-EST-TEMP |
| `D = ∅` y `K ≠ ∅` | `PENDIENTE` | R-EST-PEND |
| `D = ∅` y `K = ∅` | `NO_CONFIRMADO` | R-EST-NC |

Cuando `D ≠ ∅`, se recorre turno por turno, en orden. Para cada turno del cliente con declaraciones `d₁ … dₙ` se
aplica la primera fila que se cumpla; `e` es el estado que dejó el turno anterior (al inicio, `nulo`):

| # | Condición en el turno | Nuevo `e` | Regla |
|---|---|---|---|
| 1 | hay un `OK` y un `RECUR`, y `dₙ ∈ {OK, RECUR}` | `TEMPORAL` | R-EST-TEMP |
| 2 | `dₙ = OK` | `RESUELTO` | R-EST-RES |
| 3 | `dₙ = RECUR` y `e ∈ {RESUELTO, TEMPORAL}` | `TEMPORAL` | R-EST-TEMP |
| 4 | en otro caso (`dₙ = FALLA`, o `RECUR` sin recuperación previa) | `NO_RESUELTO` | R-EST-NORES |

El estado de la sesión es el `e` que deja el **último** turno con declaraciones, salvo que después haya una promesa
del agente.

**Precedencia (R-EST-PREC): prevalece lo último.** Es la respuesta del profesor a la consulta («se tiene en cuenta lo
último nomás, o sea lo que dijo el agente») y coincide con la definición de PENDIENTE del enunciado: «existe un
compromiso o seguimiento futuro, sin confirmación posterior del CLIENTE».

- Promesa del agente **posterior** a la última declaración del cliente → `PENDIENTE`, sea esa declaración una falla
  o una confirmación. La nota de la salida indica qué estado daba la declaración.
- Declaración del cliente **posterior** a la promesa → prevalece la declaración; la nota lo registra.
- Las cortesías («Gracias») y las solicitudes no son declaraciones: no cambian quién habló último.

| Caso | Declaraciones del cliente | Estado |
|---|---|---|
| 01 | T3: `OK` («Ahora funciona bien») | `RESUELTO` (fila 2) |
| 02 | T1: `FALLA` («sigo sin internet») | `NO_RESUELTO` (fila 4) |
| 03 | T1: `OK`, `RECUR` («Ahora funciona, pero se corta todos los días») | `TEMPORAL` (fila 1) |
| 04 | ninguna, sin compromiso | `NO_CONFIRMADO` |
| 06 | ninguna; compromiso del agente («Mañana revisaremos TK-205») | `PENDIENTE` |
| 10 | T3: `OK`; el agente promete antes (T2) y **después** (T4) | `PENDIENTE` (R-EST-PREC: lo último es T4) |
| 13 | T1: `FALLA`; T3: `OK`, `RECUR` | `TEMPORAL` (fila 1 en T3) |
| 15 S01 | T1: `FALLA`; promesa en T2; «Gracias» en T3 | `PENDIENTE` (la cortesía no es declaración) |
| 15 S02 | promesa en T1; T2: `FALLA` | `NO_RESUELTO` (la declaración es posterior) |
| 15 S03 | T1: `OK`; promesa en T2 | `PENDIENTE` |

**Interruptor de política.** `LO_ULTIMO_PREVALECE` (en `semantica.py`) está en `True`. En `False` vuelve a la lectura
literal del enunciado (§5): la última declaración del cliente prevalece siempre sobre las promesas del agente, y los
casos 10 y 15 cambian de resultado.

## 9. Acciones sobre la tabla de entidades

La tabla de entidades (`entidades.py`) es la tabla de símbolos de sesión, participante y ticket del enunciado.
Ámbito = sesión; se crea vacía en cada ejecución y no persiste (la que persiste es la tabla de símbolos léxica,
`INFORME_lexico.md` §1.5). Toda operación queda en la bitácora que muestra la traza.

| Momento | Acción |
|---|---|
| Inicio de `sesion` | `buscar(SESION, id)`; `insertar(SESION, id, linea_inicio)` |
| Cada `turno` aceptado | `buscar(PARTICIPANTE, rol)`; `insertar(PARTICIPANTE, rol, aparición(turno, desp))` |
| Cada token `TICKET` del turno | `buscar(TICKET, norm)`; `insertar(TICKET, norm, aparición(turno, desp), ultima_mencion = turno)` |
| Cláusula con `tipo = COMPROMISO` y ticket | `actualizar(TICKET, norm, seguimiento = COMPROMISO_FUTURO, compromiso_turno, compromiso_actor)` |
| Fin de `sesion` | `actualizar(SESION, id, estado, analisis)` |

`insertar` sobre una clave existente no duplica: enlaza la nueva aparición a la entrada única
(`DUPLICADO->ENLAZAR` en la bitácora). Un id de sesión repetido en el lote se rechaza en el lector
(`SESION_DUPLICADA`), porque dos sesiones compartirían el mismo ámbito.

## 10. Catálogo de reglas y dónde está cada una

Cada evidencia de la salida lleva los identificadores de las reglas que la produjeron (`reglas`), junto con el
turno y el fragmento de texto.

| Regla | Producción o condición | En `semantica.py` |
|---|---|---|
| R-SUJ | `sujeto → sust \| AGENTE` | `_sube`, `_sujeto_agente`; grupo `sust` |
| R-COP | `pred → V_COP atrib` (con cualidad); `pred_s → modif` | `_p_cop`, `_p_cop_dir` |
| R-EST | `pred → v_est compl [sujp]` | `_p_est`; grupo `v_est` |
| R-CORTE | `pred → SE V_EST_RECUR [sujp]` | `_p_corta` |
| R-SEG-ADJ | `pred → V_CONT compl`, con `compl → modif` | `_p_seguir` |
| R-SEG-SIN | `pred → V_CONT compl`, con `compl → SIN sust` | `_p_seguir` |
| R-SIN | `compl → SIN sust` | `_compl_sin` |
| R-ENT | `pred → v_acc obj modif_op`, con `V_ENTENDER` | `_p_acc` |
| R-VAL | ídem, con `V_VAL_ATEN` o `V_VAL_CLAR` y cualidad | `_p_acc` |
| R-MEN | `pred_s → ε`; verbo valorativo sin cualidad | `_p_mencion`, `_p_acc` |
| R-SOLIC | ídem, con `V_SOLICITUD` | `_p_acc` |
| R-COMPR | ídem, con `V_COMPROMISO` | `_p_acc` |
| R-NEG | `pred_s → NEG pred_neg`; `pred_l → NEG pred_neg` | `_p_neg`; inversión en `_construir` |
| R-MUY | `modif → INT adj` | `_modif_int` |
| R-TICKET | `pred → V_COP atrib` (con ticket); `pred_s → TICKET`; `nucleo → TICKET` | `_p_cop`, `_p_ref`, `_n_tk` |
| R-CORT | `nucleo → CORTESIA` | `_n_cort` |
| R-AHORA | `clausula → adv_t_op nucleo frec`, con `T_AHORA` | `_clausula` |
| R-POSP | `sujp → sust` | `_sube`; `_construir` |
| R-COMPAT | paso 1 de `construir()` | `COMPAT`, `_compatible` |
| R-PERO | `cola → PERO clausula cola`; `cola_c → PERO clausula cola` | `clausulas`; `analizador._analizar_turno` |
| R-EST-RES, R-EST-NORES, R-EST-TEMP, R-EST-PEND, R-EST-NC, R-EST-PREC | sección 8 | `decidir_estado` |

## 11. Alcance de la negación, de «sin» y de «muy»

El alcance lo fija la gramática, no una heurística sobre la distancia entre palabras:

- `NEG` solo aparece en `pred → NEG pred_neg`. Niega **exactamente** el predicado `pred_neg` que lo sigue («no
  funciona», «no está lento», «no entendí la explicación», «no me atendieron bien»).
- `SIN` solo aparece en `compl → SIN sust`: afecta al sustantivo inmediato, y su signo depende de ese sustantivo
  (R-SIN).
- Ninguno cruza `PERO`, `COMA`, `Y` ni `PUNTO`: después de un conector empieza otra derivación de `clausula`, con su
  propio `neg = falso`. En «No entendí la explicación, pero el agente fue amable», la segunda cláusula no queda negada.
- `INT` solo aparece en `modif → INT adj`: intensifica el adjetivo inmediato y no cambia la polaridad.
  «No es muy bueno» produce `pol = +1`, `int = ALTA`, `neg = verdadero` → `NEGATIVA`.

## 12. Árboles anotados de prueba

Como en clase, se comprueba el cuadro sobre una cadena concreta anotando el árbol con los valores esperados.

### 12.1 Caso 02: «Me atendiste muy bien, pero sigo sin internet.»

Tokens que llegan al parser (`Me` es `RELLENO` y se filtra):
`V_VAL_ATEN INT ADJ_POS COMA PERO V_CONT SIN SUST_SERV PUNTO`

```
texto  .L=[C1.1, C1.2]
├─ oracion  .con.i=nulo  .L=[C1.1, C1.2]
│  ├─ clausula  .con.i=nulo  .h=C1.1 {VALORACION, ATENCION, POSITIVA, int=ALTA}
│  │  ├─ adv_t_op → ε
│  │  ├─ nucleo  .h=construir(pred_l, nulo)
│  │  │  └─ pred_l  .k=VAL  .asp=ATENCION  .pol=+1  .int=ALTA      ← pred_l → v_acc obj modif_op
│  │  │     ├─ v_acc  .clase=VAL  .asp=ATENCION                    ← V_VAL_ATEN «atendiste»
│  │  │     ├─ obj → ε
│  │  │     └─ modif_op  .pol=+1  .int=ALTA
│  │  │        └─ modif  ← INT «muy»  adj .pol=+1 (ADJ_POS «bien»)
│  │  └─ frec → ε  .n=0
│  └─ cola  .L=[C1.2]
│     ├─ COMA
│     └─ cola_c  .L=[C1.2]
│        ├─ PERO
│        ├─ clausula  .con.i=PERO  .h=C1.2 {FUNCIONAMIENTO, SERVICIO, NEGATIVA, decl=FALLA}
│        │  └─ nucleo  .h=construir(pred_l, nulo)
│        │     └─ pred_l  .k=SEG_SIN  .pol=−1  .asp=SERVICIO       ← pred_l → V_CONT compl
│        │        ├─ V_CONT «sigo»
│        │        └─ compl  .t=SIN  .asp=SERVICIO  .pol=−1         ← SIN «sin»  sust (SUST_SERV «internet», pol=0)
│        └─ cola → ε  .L=[ ]
└─ texto_r → PUNTO texto_rr   (texto_rr → ε, .L=[ ])
```

| Cláusula | Fragmento | Hecho | Reglas |
|---|---|---|---|
| C1.1 | «Me atendiste muy bien» | ATENCION = POSITIVA, intensidad ALTA | R-VAL, R-MUY |
| C1.2 | «sigo sin internet» | SERVICIO = NEGATIVA, declaración FALLA, en contraste con C1.1 | R-SEG-SIN, R-SIN, R-PERO |

Turno y sesión: `ATENCION = POSITIVA`, `SERVICIO = NEGATIVA`, `CLARIDAD = SIN_EVIDENCIA`. Estado: `D = [C1.2]`,
`dₙ = FALLA` → **NO_RESUELTO** (R-EST-NORES). La valoración positiva de la atención no se confunde con una
confirmación de solución.

### 12.2 Caso 04, primera cláusula: «No entendí la explicación»

```
clausula  .h=C1.1 {VALORACION, CLARIDAD, NEGATIVA, negada}
└─ nucleo  .h=construir(pred_l, nulo)
   └─ pred_l  .k=ENT  .asp=CLARIDAD  .pol=+1  .neg=verdadero      ← pred_l → NEG pred_neg
      ├─ NEG «No»
      └─ pred_neg  .k=ENT  .asp=CLARIDAD  .pol=+1                 ← pred_neg → v_acc obj modif_op
         ├─ v_acc  .clase=ENT  .asp=CLARIDAD                      ← V_ENTENDER «entendí»
         ├─ obj  .s=sust (SUST_CLAR «explicación»)
         └─ modif_op → ε
```

`construir`: sin sujeto, compatible (paso 1); `aspecto = p.asp = CLARIDAD` (paso 3); `neg` → `pol' = −1` (paso 4) →
`NEGATIVA`; `ENT` no declara funcionamiento (paso 6). Reglas: R-ENT, R-NEG.

### 12.3 Caso 03: «Ahora funciona, pero se corta todos los días.»

| Cláusula | Predicado | Hecho | Reglas |
|---|---|---|---|
| C1.1 «Ahora funciona» | `pred_l → v_est compl sujp`, `v_est → V_EST_OK`, `compl → ε`: `k=EST`, `pol=+1` | SERVICIO = POSITIVA, declaración `OK`, temporal `AHORA` | R-EST, R-AHORA |
| C1.2 «se corta todos los días» | `pred_l → SE V_EST_RECUR sujp`: `k=CORTE`, `pol=−1`; `frec.n=2` | SERVICIO = NEGATIVA, declaración `RECUR` | R-CORTE, R-PERO |

`combinar({POSITIVA, NEGATIVA}) = MIXTA`. Estado: el turno tiene `OK` y `RECUR` y termina en `RECUR` → fila 1 →
**TEMPORAL** (R-EST-TEMP), no RESUELTO.

### 12.4 Caso 16: sujeto pospuesto e incompatibilidad

| Cláusula | Derivación | Resultado |
|---|---|---|
| «No funciona el internet» | `pred_l → NEG pred_neg`, `pred_neg → v_est compl sujp`, `sujp → sust(SUST_SERV)` | compatible; aspecto del sujeto pospuesto; SERVICIO NEGATIVA, `FALLA` (R-EST, R-POSP, R-NEG) |
| «el router falla seguido» | `sujeto → sust(SUST_EQUIPO)`, `pred_s → v_est(V_EST_FALLA) compl(ε)`, `frec` | SERVICIO NEGATIVA, `FALLA`, entidad `ROUTER` |
| «ahora funciona sin cortes» | `pred_l → v_est compl`, `compl → SIN sust(SUST_PROB)` | `compl.pol = +1` → SERVICIO POSITIVA, `OK` (R-EST, R-SIN, R-AHORA) |
| «El agente se corta» | `sujeto(AGENTE) pred_s → SE V_EST_RECUR` | `CORTE ∉ COMPAT[AGENTE]` → no se interpreta (R-COMPAT) |

Para reproducir cualquiera de estos árboles: `python3 main.py casos/caso_02.txt --traza S01 --detalle`.

## 13. Cómo modificar una regla

| Cambio | Dónde | Fila de este documento |
|---|---|---|
| Qué significa una subcategoría (p. ej. que «el router» no cuente como SERVICIO) | llamadas a `_constante(...)` | sección 3 |
| Qué sujeto admite qué predicado (p. ej. que «el agente no entendió» valore la ATENCION) | tabla `COMPAT` | sección 5 |
| Qué significa «sigue + adjetivo» | `_p_seguir` | sección 4 |
| El signo de «sin» + sustantivo | `_compl_sin` | sección 3.1 |
| Efecto de la negación | `_p_neg` y paso 4 de `_construir` | secciones 4 y 5 |
| Qué predicados declaran funcionamiento (p. ej. que «no se corta» declare `OK`) | paso 6 de `_construir` | sección 5 |
| Cómo se combinan las evidencias | `combinar` | sección 7 |
| Criterio de estado | `decidir_estado` | sección 8 |
| Una subcategoría nueva | terminal en el grupo de `gramatica.py` + `_constante(...)` + entrada en `consulta.MENU` | sección 3 |
| Una construcción lingüística nueva | producción en `gramatica.py` + función `@acc` | secciones 3 a 5 |

Después de cualquier cambio: `python3 gramatica.py` (la gramática debe seguir sin conflictos LL(1)) y
`python3 pruebas.py --regresion`.
