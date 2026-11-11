# TP1 · Reglas semánticas

Definición dirigida por la sintaxis del analizador: qué atributo calcula cada producción de la gramática
(`GRAMATICA.md`) y cómo se llega desde ellos a la valoración por aspecto y al estado de la sesión.
Implementación: `semantica.py` (reglas por producción y estado) y `analizador.py` (atributos de contexto y
tabla de símbolos).

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
registrada con `@acc(variable, producción)`:

```python
@acc('modif', 'INT adj')                 # BNF:    modif → INT adj
def _modif_int(n):                       # Regla:  modif.pol = adj.pol ; modif.int = ALTA
    a = ev(n.hijos[1])                   #   primero se evalúa el hijo adj (su valor de retorno)
    return {**a, 'int': 'ALTA', ...}     #   y se retornan los atributos sintetizados de modif
```

Si una producción de la gramática no tiene regla registrada, `@acc` falla al cargar el módulo (verifica que la
producción exista en `gramatica.py`), de modo que el cuadro y la gramática no pueden desincronizarse.

## 2. Atributos

| Símbolo | Atributo | Tipo | Valores | Significado |
|---|---|---|---|---|
| `adj`, `modif`, `modif_op` | `pol` | sintetizado | `+1`, `−1` (`nulo` en `modif_op → ε`) | polaridad del adjetivo |
| `modif`, `modif_op` | `int` | sintetizado | `ALTA`, `nulo` | intensidad («muy», «bastante») |
| `sujeto` | `asp` | sintetizado | `SERVICIO`, `ATENCION`, `CLARIDAD` | aspecto del que se habla |
| `frec` | `n` | sintetizado | entero ≥ 0 | cantidad de tokens de frecuencia |
| `obj_clar` | `obj` | sintetizado | token, `nulo` | objeto de «entender» |
| `obj_router` | `ent` | sintetizado | token, `nulo` | equipo que se pide reiniciar |
| `ref_op`, `tk_op` | `ticket` | sintetizado | `TK-ddd`, `nulo` | ticket referido |
| `ref_op` | `plazo` | sintetizado | token, `nulo` | plazo del compromiso («mañana») |
| `ahora_op` | `t` | sintetizado | `AHORA`, `nulo` | marca temporal |
| `pred_s`, `pred_l`, `pred_neg`, `seg` | `k` | sintetizado | `COP`, `FUNC`, `ENT`, `SEG_ADJ`, `SEG_SIN`, `CORTE`, `SOLIC`, `COMPR`, `MENCION` | tipo de predicado |
| ídem | `pol`, `int` | sintetizado | como arriba | polaridad **antes** de negar, intensidad |
| `pred_s`, `pred_l` | `neg` | sintetizado | verdadero, falso | el predicado está negado |
| `nucleo`, `clausula` | `h` | sintetizado | registro *hecho* (abajo) | interpretación de la cláusula |
| `texto`, `oracion`, `cola`, … | `L` | sintetizado | lista de hechos | cláusulas del turno, en orden textual |
| `texto`, `oracion`, `clausula` | `actor.i`, `turno.i` | heredado | rol y número del turno | autoría de la evidencia |
| `oracion`, `clausula` | `con.i` | heredado | `nulo`, `COMA`, `PUNTO`, `PERO` | conector que precede a la cláusula |
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

## 3. Adjetivos, modificadores y elementos opcionales

| BNF | Reglas semánticas |
|---|---|
| `adj → ADJ_POS` | `adj.pol = +1` |
| `adj → ADJ_NEG` | `adj.pol = −1` |
| `modif → adj` | `modif.pol = adj.pol; modif.int = nulo` |
| `modif → INT adj` | `modif.pol = adj.pol; modif.int = ALTA` |
| `modif_op → modif` | `modif_op.pol = modif.pol; modif_op.int = modif.int` |
| `modif_op → ε` | `modif_op.pol = nulo; modif_op.int = nulo` |
| `frec → FREC frec₁` | `frec.n = 1 + frec₁.n` |
| `frec → ε` | `frec.n = 0` |
| `obj_clar → ASP_CLAR` | `obj_clar.obj = ASP_CLAR` |
| `obj_clar → ε` | `obj_clar.obj = nulo` |
| `obj_router → ROUTER` | `obj_router.ent = ROUTER` |
| `obj_router → ε` | `obj_router.ent = nulo` |
| `ref_op → TICKET` | `ref_op.ticket = TICKET.norm; ref_op.plazo = nulo` |
| `ref_op → T_FUTURO` | `ref_op.ticket = nulo; ref_op.plazo = T_FUTURO` |
| `ref_op → ε` | `ref_op.ticket = nulo; ref_op.plazo = nulo` |
| `tk_op → V_COPULA TICKET` | `tk_op.ticket = TICKET.norm` |
| `tk_op → TICKET` | `tk_op.ticket = TICKET.norm` |
| `tk_op → ε` | `tk_op.ticket = nulo` |
| `ahora_op → T_AHORA` | `ahora_op.t = AHORA` |
| `ahora_op → ε` | `ahora_op.t = nulo` |

`frec → FREC frec₁` es el mismo esquema del robot de la Clase 6 (`R → INSRT R₁`): el caso `ε` retorna el valor
base y cada nivel suma al retornar. `frec.n` se calcula pero no interviene en ninguna decisión: «se corta» declara
recurrencia con o sin expresión de frecuencia.

## 4. Sujeto y predicados

| BNF | Reglas semánticas | Regla |
|---|---|---|
| `sujeto → ASP_SERV` | `sujeto.asp = SERVICIO` | R-SUJ |
| `sujeto → ASP_ATEN` | `sujeto.asp = ATENCION` | R-SUJ |
| `sujeto → ASP_CLAR` | `sujeto.asp = CLARIDAD` | R-SUJ |
| `sujeto → AGENTE` | `sujeto.asp = ATENCION` | R-SUJ |
| `pred_s → V_COPULA modif` | `pred_s.k = COP; pred_s.pol = modif.pol; pred_s.int = modif.int` | R-COP |
| `pred_s → modif` | `pred_s.k = COP; pred_s.pol = modif.pol; pred_s.int = modif.int` | R-COP |
| `pred_s → V_FUNC modif_op` | `pred_s.k = FUNC; pred_s.pol = (modif_op.pol ≠ nulo) ? modif_op.pol : +1; pred_s.int = modif_op.int` | R-FUNC |
| `pred_s → V_SEGUIR seg` | `pred_s.k = seg.k; pred_s.pol = seg.pol; pred_s.int = seg.int` | (la de `seg`) |
| `pred_s → SE V_CORTA frec` | `pred_s.k = CORTE; pred_s.pol = −1; pred_s.n = frec.n` | R-CORTE |
| `pred_s → NEG pred_neg` | `pred_s.k = pred_neg.k; pred_s.pol = pred_neg.pol; pred_s.int = pred_neg.int; pred_s.neg = verdadero` | R-NEG |
| `pred_s → ε` | `pred_s.k = MENCION` | R-MEN |
| `pred_l → NEG pred_neg` | igual que `pred_s → NEG pred_neg` | R-NEG |
| `pred_l → V_FUNC modif_op` | igual que `pred_s → V_FUNC modif_op` | R-FUNC |
| `pred_l → V_SEGUIR seg` | igual que `pred_s → V_SEGUIR seg` | (la de `seg`) |
| `pred_l → SE V_CORTA frec` | igual que `pred_s → SE V_CORTA frec` | R-CORTE |
| `pred_l → V_ENTENDER obj_clar` | `pred_l.k = ENT; pred_l.pol = +1; pred_l.obj = obj_clar.obj` | R-ENT |
| `pred_l → V_SOLICITUD obj_router` | `pred_l.k = SOLIC; pred_l.ent = obj_router.ent` | R-SOLIC |
| `pred_l → T_FUTURO V_COMPROMISO ref_op` | `pred_l.k = COMPR; pred_l.ticket = ref_op.ticket` | R-COMPR |
| `pred_l → V_COMPROMISO ref_op` | `pred_l.k = COMPR; pred_l.ticket = ref_op.ticket` | R-COMPR |
| `pred_neg → V_FUNC modif_op` | `pred_neg.k = FUNC; pred_neg.pol = (modif_op.pol ≠ nulo) ? modif_op.pol : +1; pred_neg.int = modif_op.int` | R-FUNC |
| `pred_neg → V_COPULA modif` | `pred_neg.k = COP; pred_neg.pol = modif.pol; pred_neg.int = modif.int` | R-COP |
| `pred_neg → V_ENTENDER obj_clar` | `pred_neg.k = ENT; pred_neg.pol = +1; pred_neg.obj = obj_clar.obj` | R-ENT |
| `seg → modif` | `seg.k = SEG_ADJ; seg.pol = modif.pol; seg.int = modif.int` | R-SEG-ADJ |
| `seg → NEG ASP_SERV` | `seg.k = SEG_SIN; seg.pol = −1` | R-SEG-SIN |

Donde no se indica, `neg = falso`. `pred_s → modif` es la cópula omitida de «Me atendiste **muy bien**».
En `pred → NEG pred_neg` la polaridad **no** se invierte todavía: se retorna la del predicado y la marca `neg`; la
inversión se hace una sola vez, en `construir()` (sección 5).

## 5. Núcleo y cláusula

| BNF | Reglas semánticas | Regla |
|---|---|---|
| `nucleo → sujeto pred_s` | `nucleo.h = construir(pred_s, sujeto.asp)` | la del predicado + R-SUJ |
| `nucleo → pred_l` | `nucleo.h = construir(pred_l, nulo)` | la del predicado |
| `nucleo → TICKET_PAL tk_op` | `nucleo.h = hecho(TICKET, entidades = [tk_op.ticket])` | R-TICKET |
| `nucleo → TICKET` | `nucleo.h = hecho(TICKET, entidades = [TICKET.norm])` | R-TICKET |
| `nucleo → CORTESIA` | `nucleo.h = hecho(CORTESIA)` | R-CORT |
| `clausula → ahora_op nucleo` | `clausula.h = nucleo.h; clausula.h.temporal = ahora_op.t` | R-AHORA si `ahora_op.t ≠ nulo` |

`hecho(tipo, …)` crea un registro con el resto de los campos en `nulo`. La función `construir(p, asp)` convierte los
atributos de un predicado `p` y el aspecto del sujeto (`nulo` si la cláusula no tiene sujeto) en un hecho:

| Paso | Regla de cálculo |
|---|---|
| 1 | Si `p.k = MENCION`: `hecho(MENCION, aspecto = asp, valoracion = NEUTRA)`. Fin. |
| 2 | Si `p.k = SOLIC`: `hecho(SOLICITUD, entidades = [p.ent])`. Fin. |
| 3 | Si `p.k = COMPR`: `hecho(COMPROMISO, entidades = [p.ticket])`. Fin. |
| 4 | `aspecto = SERVICIO` si `p.k = SEG_SIN`; si no, `asp` cuando hay sujeto; si no, `CLARIDAD` cuando `p.k = ENT` y `SERVICIO` en los demás casos. |
| 5 | `pol' = −p.pol` si `p.neg` (R-NEG); si no, `pol' = p.pol`. |
| 6 | `valoracion = POSITIVA` si `pol' = +1`; `NEGATIVA` si `pol' = −1`. |
| 7 | `declaracion`, solo cuando `aspecto = SERVICIO`: `FUNC` y `SEG_ADJ` → `OK` si `pol' = +1`, `FALLA` si `pol' = −1`; `SEG_SIN` → `FALLA`; `CORTE` → `RECUR`; `COP` y `ENT` → `nulo`. |
| 8 | `tipo = FUNCIONAMIENTO` si `declaracion ≠ nulo`; si no, `VALORACION`. |
| 9 | `intensidad = p.int` (R-MUY si no es `nulo`); `negada = p.neg`. |

Consecuencias que conviene tener presentes:

- «El servicio **está** lento» (`COP`) es una valoración NEGATIVA del SERVICIO, pero **no** es una declaración de
  funcionamiento: no fija el estado. «**Sigue** lento», «**no funciona**» y «**se corta**» sí lo son.
- «La atención sigue mala» valora la ATENCION y no declara nada sobre el funcionamiento (paso 7).
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
| `D ≠ ∅` | el que resulta de recorrer `D` (cuadro siguiente) | R-EST-RES, R-EST-NORES o R-EST-TEMP |
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

El estado de la sesión es el `e` que deja el **último** turno con declaraciones: la última declaración explícita del
cliente prevalece. Las promesas del agente (`K`) no lo modifican, sean anteriores o posteriores (**R-EST-PREC**); si
existen, se deja una nota en la salida.

| Caso | Declaraciones del cliente | Estado |
|---|---|---|
| 01 | T3: `OK` («Ahora funciona bien») | `RESUELTO` (fila 2) |
| 02 | T1: `FALLA` («sigo sin internet») | `NO_RESUELTO` (fila 4) |
| 03 | T1: `OK`, `RECUR` («Ahora funciona, pero se corta todos los días») | `TEMPORAL` (fila 1) |
| 04 | ninguna, sin compromiso | `NO_CONFIRMADO` |
| 06 | ninguna; compromiso del agente («Mañana revisaremos TK-205») | `PENDIENTE` |
| 10 | T3: `OK`; el agente promete antes y después | `RESUELTO` (R-EST-PREC) |
| 13 | T1: `FALLA`; T3: `OK`, `RECUR` | `TEMPORAL` (fila 1 en T3) |

**Interruptor de política.** Con `PROMESA_POSTERIOR_A_FALLA_ES_PENDIENTE = True` (en `semantica.py`), si el
resultado es `NO_RESUELTO` y hay un compromiso del agente posterior a la última declaración, el estado pasa a
`PENDIENTE`. Por defecto está en `False`: lectura literal de la regla de precedencia del enunciado.

## 9. Acciones sobre la tabla de símbolos

Ámbito = sesión. Toda operación queda en la bitácora que muestra la traza.

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
| R-SUJ | `sujeto → ASP_SERV \| ASP_ATEN \| ASP_CLAR \| AGENTE` | `_sujeto`, `ASP_DE` |
| R-COP | `pred_s → V_COPULA modif \| modif`; `pred_neg → V_COPULA modif` | `_p_cop`, `_p_cop_dir` |
| R-FUNC | `… → V_FUNC modif_op` | `_p_func` |
| R-NEG | `pred_s → NEG pred_neg`; `pred_l → NEG pred_neg` | `_p_neg`; inversión en `_construir` |
| R-MUY | `modif → INT adj` | `_modif_int` |
| R-SEG-ADJ | `seg → modif` | `_seg_adj` |
| R-SEG-SIN | `seg → NEG ASP_SERV` | `_seg_sin` |
| R-CORTE | `… → SE V_CORTA frec` | `_p_corta` |
| R-ENT | `… → V_ENTENDER obj_clar` | `_p_ent` |
| R-MEN | `pred_s → ε` | `_p_mencion` |
| R-SOLIC | `pred_l → V_SOLICITUD obj_router` | `_p_solic` |
| R-COMPR | `pred_l → [T_FUTURO] V_COMPROMISO ref_op` | `_p_compr1`, `_p_compr2` |
| R-TICKET | `nucleo → TICKET_PAL tk_op \| TICKET` | `_n_tkpal`, `_n_tk` |
| R-CORT | `nucleo → CORTESIA` | `_n_cort` |
| R-AHORA | `clausula → ahora_op nucleo`, con `ahora_op → T_AHORA` | `_clausula` |
| R-PERO | `cola → PERO clausula cola`; `cola_c → PERO clausula cola` | `clausulas`; `analizador._analizar_turno` |
| R-EST-RES, R-EST-NORES, R-EST-TEMP, R-EST-PEND, R-EST-NC, R-EST-PREC | sección 8 | `decidir_estado` |

## 11. Alcance de la negación y de «muy»

El alcance lo fija la gramática, no una heurística sobre la distancia entre palabras:

- `NEG` solo aparece en `pred → NEG pred_neg` y en `seg → NEG ASP_SERV`. Niega **exactamente** el predicado
  `pred_neg` que lo sigue («no funciona», «no está lento», «no entendí la explicación») o el sustantivo de servicio
  («sin internet»).
- No cruza `PERO`, `COMA` ni `PUNTO`: después de un conector empieza otra derivación de `clausula`, con su propio
  `neg = falso`. En «No entendí la explicación, pero el agente fue amable», la segunda cláusula no queda negada.
- `INT` solo aparece en `modif → INT adj`: intensifica el adjetivo inmediato y no cambia la polaridad.
  «No es muy bueno» produce `pol = +1`, `int = ALTA`, `neg = verdadero` → `NEGATIVA`.

## 12. Árboles anotados de prueba

Como en clase, se comprueba el cuadro sobre una cadena concreta anotando el árbol con los valores esperados.

### 12.1 Caso 02: «Me atendiste muy bien, pero sigo sin internet.»

Tokens que llegan al parser (`Me` es `RELLENO` y se filtra):
`ASP_ATEN INT ADJ_POS COMA PERO V_SEGUIR NEG ASP_SERV PUNTO`

```
texto  .L=[C1.1, C1.2]
├─ oracion  .con.i=nulo  .L=[C1.1, C1.2]
│  ├─ clausula  .con.i=nulo  .h=C1.1 {VALORACION, ATENCION, POSITIVA, int=ALTA}
│  │  ├─ ahora_op → ε  .t=nulo
│  │  └─ nucleo  .h=construir(pred_s, ATENCION)
│  │     ├─ sujeto  .asp=ATENCION                         ← ASP_ATEN «atendiste»
│  │     └─ pred_s  .k=COP  .pol=+1  .int=ALTA
│  │        └─ modif  .pol=+1  .int=ALTA
│  │           ├─ INT «muy»
│  │           └─ adj  .pol=+1                            ← ADJ_POS «bien»
│  └─ cola  .L=[C1.2]
│     ├─ COMA
│     └─ cola_c  .L=[C1.2]
│        ├─ PERO
│        ├─ clausula  .con.i=PERO  .h=C1.2 {FUNCIONAMIENTO, SERVICIO, NEGATIVA, decl=FALLA}
│        │  ├─ ahora_op → ε  .t=nulo
│        │  └─ nucleo  .h=construir(pred_l, nulo)
│        │     └─ pred_l  .k=SEG_SIN  .pol=−1
│        │        ├─ V_SEGUIR «sigo»
│        │        └─ seg  .k=SEG_SIN  .pol=−1             ← NEG «sin» ASP_SERV «internet»
│        └─ cola → ε  .L=[ ]
└─ texto_r → PUNTO texto_rr   (texto_rr → ε, .L=[ ])
```

| Cláusula | Fragmento | Hecho | Reglas |
|---|---|---|---|
| C1.1 | «Me atendiste muy bien» | ATENCION = POSITIVA, intensidad ALTA | R-SUJ, R-COP, R-MUY |
| C1.2 | «sigo sin internet» | SERVICIO = NEGATIVA, declaración FALLA, en contraste con C1.1 | R-SEG-SIN, R-PERO |

Turno y sesión: `ATENCION = POSITIVA`, `SERVICIO = NEGATIVA`, `CLARIDAD = SIN_EVIDENCIA`. Estado: `D = [C1.2]`,
`dₙ = FALLA` → **NO_RESUELTO** (R-EST-NORES). La valoración positiva de la atención no se confunde con una
confirmación de solución.

### 12.2 Caso 04, primera cláusula: «No entendí la explicación»

```
clausula  .h=C1.1 {VALORACION, CLARIDAD, NEGATIVA, negada}
└─ nucleo  .h=construir(pred_l, nulo)
   └─ pred_l  .k=ENT  .pol=+1  .neg=verdadero             ← pred_l → NEG pred_neg
      ├─ NEG «No»
      └─ pred_neg  .k=ENT  .pol=+1                        ← pred_neg → V_ENTENDER obj_clar
         ├─ V_ENTENDER «entendí»
         └─ obj_clar  .obj=ASP_CLAR «explicación»
```

`construir`: sin sujeto y `k = ENT` → `aspecto = CLARIDAD` (paso 4); `neg` → `pol' = −1` (paso 5) → `NEGATIVA`;
`ENT` no declara funcionamiento (paso 7). Reglas: R-ENT, R-NEG.

### 12.3 Caso 03: «Ahora funciona, pero se corta todos los días.»

| Cláusula | Predicado | Hecho | Reglas |
|---|---|---|---|
| C1.1 «Ahora funciona» | `pred_l → V_FUNC modif_op`, `modif_op → ε`: `k=FUNC`, `pol=+1` | SERVICIO = POSITIVA, declaración `OK`, temporal `AHORA` | R-FUNC, R-AHORA |
| C1.2 «se corta todos los días» | `pred_l → SE V_CORTA frec`: `k=CORTE`, `pol=−1`, `n=2` | SERVICIO = NEGATIVA, declaración `RECUR` | R-CORTE, R-PERO |

`combinar({POSITIVA, NEGATIVA}) = MIXTA`. Estado: el turno tiene `OK` y `RECUR` y termina en `RECUR` → fila 1 →
**TEMPORAL** (R-EST-TEMP), no RESUELTO.

Para reproducir cualquiera de estos árboles: `python3 main.py casos/caso_02.txt --traza S01 --detalle`.

## 13. Cómo modificar una regla

| Cambio | Dónde | Fila de este documento |
|---|---|---|
| El aspecto de un sujeto (p. ej. que «agente» no cuente como ATENCION) | `ASP_DE` | sección 4, `sujeto → …` |
| Qué significa «sigue + adjetivo» | `_seg_adj` | sección 4, `seg → modif` |
| Efecto de la negación | `_p_neg` y paso 5 de `_construir` | secciones 4 y 5 |
| Qué predicados declaran funcionamiento | paso 7 de `_construir` | sección 5 |
| Cómo se combinan las evidencias | `combinar` | sección 7 |
| Criterio de estado | `decidir_estado` | sección 8 |
| Una construcción lingüística nueva | producción en `gramatica.py` + función `@acc` | secciones 3 a 5 |

Después de cualquier cambio: `python3 gramatica.py` (la gramática debe seguir sin conflictos LL(1)) y
`python3 pruebas.py --regresion`.
