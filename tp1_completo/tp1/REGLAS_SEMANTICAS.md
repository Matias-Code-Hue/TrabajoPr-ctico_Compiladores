# TP1 · Reglas semánticas

Definición dirigida por la sintaxis del analizador: qué atributo calcula cada producción de la gramática
(`GRAMATICA.md`) y cómo se llega desde ellos a la valoración por aspecto y al estado de la sesión.
Implementación: `semantica.py` (perfiles, reglas por producción y estado) y `analizador.py` (atributos de contexto y
tabla de entidades). La tabla de símbolos léxica vigente, con los rasgos de cada forma canónica, la mantiene
`tabla_lexica.py`.

## 1. Notación

Se usa la notación de clase (Clases 2 y 3): un cuadro **BNF | Reglas semánticas**, donde `X.a` es el atributo `a`
del símbolo `X` y un subíndice (`frec₁`) distingue dos apariciones del mismo símbolo en una producción.

- **Atributo sintetizado**: su valor depende solo de los hijos. Es el **valor de retorno** del procedimiento del
  no terminal.
- **Atributo heredado**: su valor lo entrega el padre o un hermano. Es un **parámetro**. En los cuadros se marca
  con el sufijo `.i`, como en la transformación `A → βR` de la Clase 3.
- Los terminales traen los atributos que les puso el analizador léxico: `tok.cat` (categoría), `tok.lex` (lexema
  original), `tok.norm` (normalizado) y `tok.canon` (forma canónica). Para las categorías con significado,
  **`tok.p`** son los atributos que salen de los **rasgos** de su forma canónica (sección 3), guardados en la tabla de
  símbolos léxica: `tok.p.pol`, `tok.p.asp`, …
- `‖` concatena listas; `nulo` significa «sin valor».

**Cómo se evalúan.** El parser LL(1) (`sintaxis.py`) devuelve el árbol de derivación del turno. Después,
`semantica.ev(nodo)` busca la regla de la producción del nodo y la ejecuta; cada regla llama a `ev()` sobre sus
hijos y **retorna** sus atributos sintetizados. Cada fila de los cuadros de las secciones 3 a 6 es una función
registrada con `@acc(variable, producción)`:

```python
@acc('modif', 'INT ADJ')                              # BNF:    modif → INT ADJ
def _modif_int(n):                                    # Regla:  modif.pol = ADJ.p.pol ; modif.int = ALTA
    return {'pol': sig(n.hijos[1])['pol'], 'int': 'ALTA'}   #   sig(): atributos de los rasgos del token ADJ
```

Si una producción de la gramática no tiene regla registrada, `@acc` falla al cargar el módulo (verifica que la
producción exista en `gramatica.py`), de modo que el cuadro y la gramática no pueden desincronizarse.

## 2. Atributos

| Símbolo | Atributo | Tipo | Valores | Significado |
|---|---|---|---|---|
| `SUST`, `ADJ`, `V_EST`, `V_ACC`, `ADV_T` (terminales) | `p` | del léxico (rasgos de la forma canónica) | los de un perfil de su categoría (sección 3) | qué significa la palabra |
| `sujeto`, `sujp` | `clase` | sintetizado | `SERVICIO`, `EQUIPO`, `ATENCION`, `CLARIDAD`, `TICKET`, `PROBLEMA`, `AGENTE` | para la tabla de compatibilidad |
| ídem | `asp` | sintetizado | `SERVICIO`, `ATENCION`, `CLARIDAD`, `nulo` | aspecto del que se habla |
| ídem | `pol` | sintetizado | `0`, `−1` | `−1` si el sustantivo es un problema («corte») |
| ídem | `ent` | sintetizado | `EQUIPO`, `TICKET`, `nulo` | tipo de entidad |
| `modif`, `modif_op`, `atrib`, `compl` | `pol` | sintetizado | `+1`, `−1` | polaridad de la cualidad o del complemento |
| `modif`, `modif_op`, `atrib`, `compl` | `int` | sintetizado | `ALTA`, `nulo` | intensidad («muy», «bastante») |
| `adv_t_op` | `t` | sintetizado | `AHORA`, `FUTURO`, `nulo` | marca temporal |
| `atrib` | `ticket` | sintetizado | token, `nulo` | ticket después de la cópula |
| `compl` | `t` | sintetizado | `CUAL`, `SIN`, `nulo` | tipo de complemento |
| `compl` | `asp` | sintetizado | aspecto del sustantivo de «sin» | — |
| `obj` | `s`, `ticket`, `plazo` | sintetizado | sustantivo, token, tiempo, `nulo` | objeto del verbo de acción |
| `frec` | `n` | sintetizado | entero ≥ 0 | cantidad de tokens de frecuencia |
| `pred_s`, `pred_l`, `pred_neg` | `k` | sintetizado | `COP`, `EST`, `CORTE`, `SEG_ADJ`, `SEG_SIN`, `ENT`, `VAL`, `SOLIC`, `COMPR`, `REF`, `MENCION`, `INCOMPLETO`, `SE_INCOMPATIBLE` | tipo de predicado |
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

Las cláusulas que no se interpretan (error sintáctico, R-COMPAT o R-SINDOM) no producen hecho: sus palabras pasan a
`NO_INTERPRETADO` con el motivo correspondiente.

## 3. Rasgos y perfiles: qué significa cada palabra

El significado de una palabra está en la **misma entrada** de la tabla de símbolos léxica que sus formas:

```
forma superficial ──(tabla de símbolos léxica)──► categoría + forma canónica + rasgos ──(sig)──► atributos
«lentas»                                          ADJ / LENTO / {"pol": -1}                     pol = −1
```

- **Tabla de símbolos léxica** (`vocabulario.json` + `vocabulario_aprendido.json`): categoría → forma canónica →
  `{"rasgos": {...}, "formas": [...]}`. Los rasgos son los datos que leen las reglas: `aspecto`, `entidad`, `pol`,
  `decl`, `pronominal`, `clase`, `tiempo` y `sin_dominio`.
- **Perfiles** (`semantica.PERFILES`, en el código): catálogo **cerrado** de combinaciones de rasgos válidas por
  categoría. Es el modelo semántico. Al cargar la tabla se valida que los rasgos de cada forma canónica coincidan
  exactamente con un perfil de su categoría (`errores_de_rasgos`), así que en las reglas «el perfil de una forma
  canónica» y «sus rasgos» son lo mismo. Un perfil nuevo es un cambio de las reglas y se hace en el código.
- **`semantica.sig(tok)`** traduce los rasgos a los atributos que usan los cuadros (`tok.p`): `asp` ← `aspecto`,
  `ent` ← `entidad`, `pol` ← `pol` (0 si no está), `pron` ← `pronominal`, `t` ← `tiempo`; `clase` es, en `SUST`, el
  nombre del perfil (lo usa `COMPAT`) y, en `V_ACC`, el tipo de predicado (COMPRENSION → ENT, SOLICITUD → SOLIC,
  COMPROMISO → COMPR, VALORABLE → VAL). Con `sin_dominio`, `clase = SIN_DOMINIO`. El rasgo `decl` documenta la
  declaración del verbo; las reglas la deducen de `pol` y `pron`.

Una palabra nueva entra como variante de una forma canónica existente (hereda sus rasgos), o como forma canónica nueva
con los rasgos de un perfil existente (el menú los copia del catálogo). En los dos casos no se toca la gramática ni las
reglas.

| Categoría | Perfil | Rasgos (en `vocabulario.json`) | Atributos (`sig`) | Qué significa | Formas canónicas de la precarga |
|---|---|---|---|---|---|
| `SUST` | `SERVICIO` | `{"aspecto": "SERVICIO"}` | clase = SERVICIO; asp = SERVICIO; pol = 0; ent = nulo | habla del servicio (internet, conexión) | SERVICIO |
| `SUST` | `ATENCION` | `{"aspecto": "ATENCION"}` | clase = ATENCION; asp = ATENCION; pol = 0; ent = nulo | habla de la atención (trato) | ATENCION |
| `SUST` | `CLARIDAD` | `{"aspecto": "CLARIDAD"}` | clase = CLARIDAD; asp = CLARIDAD; pol = 0; ent = nulo | habla de la explicación (indicaciones) | CLARIDAD |
| `SUST` | `EQUIPO` | `{"aspecto": "SERVICIO", "entidad": "EQUIPO"}` | clase = EQUIPO; asp = SERVICIO; pol = 0; ent = EQUIPO | un equipo; valora el servicio (router, módem) | ROUTER |
| `SUST` | `TICKET` | `{"entidad": "TICKET"}` | clase = TICKET; asp = nulo; pol = 0; ent = TICKET | un ticket o caso | TICKET |
| `SUST` | `PROBLEMA` | `{"aspecto": "SERVICIO", "pol": -1}` | clase = PROBLEMA; asp = SERVICIO; pol = -1; ent = nulo | un problema del servicio (corte) | CORTE |
| `SUST` | `SIN_DOMINIO` | `{"sin_dominio": true}` | clase = SIN_DOMINIO; asp = nulo; pol = 0; ent = nulo | sin significado para el dominio (ruido, técnico) | — |
| `ADJ` | `POSITIVO` | `{"pol": 1}` | pol = +1 | cualidad buena (bien, rápido, amable) | BUENO, RAPIDO, ESTABLE, AMABLE, CLARO |
| `ADJ` | `NEGATIVO` | `{"pol": -1}` | pol = -1 | cualidad mala (mal, lento, confuso) | MALO, LENTO, INESTABLE, CONFUSO |
| `ADJ` | `SIN_DOMINIO` | `{"sin_dominio": true}` | clase = SIN_DOMINIO; pol = 0 | cualidad sin valor para el dominio (raro) | — |
| `V_EST` | `OK` | `{"pol": 1, "decl": "OK"}` | pol = +1; pron = falso | el servicio anda bien (funciona, anda) | FUNCIONAR |
| `V_EST` | `FALLA` | `{"pol": -1, "decl": "FALLA"}` | pol = -1; pron = falso | el servicio anda mal (falla) | FALLAR |
| `V_EST` | `RECUR` | `{"pol": -1, "decl": "RECUR", "pronominal": true}` | pol = -1; pron = verdadero | falla que se repite; va con «se» (se corta) | CORTAR |
| `V_ACC` | `COMPRENSION` | `{"clase": "COMPRENSION", "aspecto": "CLARIDAD"}` | clase = ENT; asp = CLARIDAD | comprender (entendí) | ENTENDER |
| `V_ACC` | `SOLICITUD` | `{"clase": "SOLICITUD"}` | clase = SOLIC; asp = nulo | pedido al cliente (reinicie) | REINICIAR |
| `V_ACC` | `COMPROMISO` | `{"clase": "COMPROMISO"}` | clase = COMPR; asp = nulo | promesa a futuro (revisaremos) | REVISAR, LLAMAR, ESCALAR |
| `V_ACC` | `VAL_ATEN` | `{"clase": "VALORABLE", "aspecto": "ATENCION"}` | clase = VAL; asp = ATENCION | valora la atención (atendiste) | ATENDER |
| `V_ACC` | `VAL_CLAR` | `{"clase": "VALORABLE", "aspecto": "CLARIDAD"}` | clase = VAL; asp = CLARIDAD | valora la explicación (explicaste) | EXPLICAR |
| `V_ACC` | `SIN_DOMINIO` | `{"sin_dominio": true}` | clase = SIN_DOMINIO; asp = nulo | acción sin significado para el dominio (hace, tiene) | — |
| `ADV_T` | `AHORA` | `{"tiempo": "AHORA"}` | t = AHORA | el momento actual (ahora, ya) | AHORA |
| `ADV_T` | `FUTURO` | `{"tiempo": "FUTURO"}` | t = FUTURO | más adelante (mañana, luego) | MAÑANA |
| `V_COP` | `COPULA` | `{}` | — | ser o estar | SER_ESTAR |
| `V_CONT` | `CONTINUIDAD` | `{}` | — | seguir | SEGUIR |
| `NEG` | `NEGACION` | `{}` | — | niega el predicado que sigue | NO |
| `SIN` | `PRIVACION` | `{}` | — | «sin» + sustantivo | SIN |
| `INT` | `INTENSIFICADOR` | `{}` | — | intensifica el adjetivo (muy) | MUY |
| `PERO` | `CONTRASTE` | `{}` | — | contraste entre cláusulas | PERO |
| `Y` | `UNION` | `{}` | — | une cláusulas | Y |
| `SE` | `PRONOMINAL` | `{}` | — | marca de verbo pronominal | SE |
| `FREC` | `FRECUENCIA` | `{}` | — | frecuencia (siempre, todos los días) | TODOS, DIA, SIEMPRE |
| `CORTESIA` | `CORTESIA` | `{}` | — | cortesía (gracias, hola) | GRACIAS, SALUDO |
| `RELLENO` | `SIN_SIGNIFICADO` | `{}` | — | artículo, clítico o preposición; se filtra antes del parser | ART, CLITICO, PREP |
| `FUERA_DE_GRAMATICA` | `FUERA` | `{}` | — | conocida, sin función en la gramática; queda NO_INTERPRETADO | FUERA |

**`SIN_DOMINIO`** (en `SUST`, `ADJ` y `V_ACC`) es la forma correcta de registrar una palabra que la gramática debe
reconocer en su lugar pero que no tiene significado para el dominio («hace», «ruido», «técnico», «raro»). La
cláusula que la contiene se reconoce entera y no se interpreta (R-SINDOM, sección 5). Si en cambio la palabra se
descartara antes del parser, el parser uniría lo que queda («el router … raros» → «el router está raro») e
inventaría una valoración.

### 3.1 Modificadores y complementos

| BNF | Reglas semánticas | Regla |
|---|---|---|
| `modif → ADJ` | `modif.pol = ADJ.p.pol; modif.int = nulo` | |
| `modif → INT ADJ` | `modif.pol = ADJ.p.pol; modif.int = ALTA` | R-MUY |
| `modif_op → modif` | `modif_op.pol = modif.pol; modif_op.int = modif.int` | |
| `modif_op → ε` | `modif_op = nulo` | |
| `atrib → modif` | `atrib.pol = modif.pol; atrib.int = modif.int; atrib.ticket = nulo` | |
| `atrib → TICKET` | `atrib.ticket = TICKET` | |
| `compl → modif` | `compl.t = CUAL; compl.pol = modif.pol; compl.int = modif.int` | |
| `compl → SIN SUST` | `compl.t = SIN; compl.asp = SUST.p.asp; compl.pol = (SUST.p.pol = −1) ? +1 : −1` | R-SIN |
| `compl → ε` | `compl = nulo` | |
| `sujp → SUST` | `sujp = SUST.p` (clase, asp, pol, ent) | R-POSP |
| `sujp → ε` | `sujp = nulo` | |
| `obj → SUST` | `obj.s = SUST.p` | |
| `obj → TICKET` | `obj.ticket = TICKET` | |
| `obj → ADV_T` | `obj.plazo = ADV_T.p.t` | |
| `obj → ε` | `obj.s = obj.ticket = obj.plazo = nulo` | |
| `frec → FREC frec₁` | `frec.n = 1 + frec₁.n` | |
| `frec → ε` | `frec.n = 0` | |
| `adv_t_op → ADV_T` | `adv_t_op.t = ADV_T.p.t` | |
| `adv_t_op → ε` | `adv_t_op = nulo` | |

`compl → SIN SUST` distingue lo que falta: «sin internet» es negativo porque falta algo bueno; «sin cortes» es
positivo porque lo que falta es un problema. `frec → FREC frec₁` es el mismo esquema del robot de la Clase 6
(`R → INSRT R₁`); `frec.n` se calcula pero no interviene en ninguna decisión.

## 4. Sujeto y predicados

| BNF | Reglas semánticas | Regla |
|---|---|---|
| `sujeto → SUST` | `sujeto = SUST.p` (clase, asp, pol, ent) | R-SUJ |
| `sujeto → AGENTE` | `sujeto.clase = AGENTE; sujeto.asp = ATENCION; sujeto.pol = 0; sujeto.ent = nulo` | R-SUJ |

Las reglas de predicado valen igual para `pred_s`, `pred_l` y `pred_neg`. En `pred_l` y `pred_neg`, las
alternativas con `sujp` agregan `pred.pos = sujp`; en `pred_s` no hay sujeto pospuesto.

| BNF | Reglas semánticas | Regla |
|---|---|---|
| `pred → V_COP atrib` | si `atrib.ticket ≠ nulo`: `pred.k = REF; pred.ticket = atrib.ticket`. Si no: `pred.k = COP; pred.pol = atrib.pol; pred.int = atrib.int` | R-TICKET / R-COP |
| `pred_s → modif` | `pred_s.k = COP; pred_s.pol = modif.pol; pred_s.int = modif.int` | R-COP |
| `pred_s → TICKET` | `pred_s.k = REF; pred_s.ticket = TICKET` | R-TICKET |
| `pred_s → ε` | `pred_s.k = MENCION` | R-MEN |
| `pred → V_EST compl [sujp]` | si `V_EST.p.pron`: `pred.k = SE_INCOMPATIBLE`. Si no: `pred.k = EST; pred.pol = (V_EST.p.pol = −1) ? −1 : (compl ≠ nulo ? compl.pol : +1); pred.int = compl.int` | R-EST (y R-SIN si `compl.t = SIN`) |
| `pred → SE V_EST compl [sujp]` | si `V_EST.p.pron`: `pred.k = CORTE; pred.pol = −1`. Si no: `pred.k = SE_INCOMPATIBLE` | R-CORTE |
| `pred → V_CONT compl` | `compl.t = CUAL`: `pred.k = SEG_ADJ; pred.pol = compl.pol; pred.int = compl.int`. `compl.t = SIN`: `pred.k = SEG_SIN; pred.pol = compl.pol; pred.asp = compl.asp`. `compl = nulo`: `pred.k = INCOMPLETO` | R-SEG-ADJ / R-SEG-SIN |
| `pred → V_ACC obj modif_op` | según `V_ACC.p.clase` (cuadro siguiente) | |
| `pred_s → NEG pred_neg`, `pred_l → NEG pred_neg` | copia todos los atributos de `pred_neg`; `pred.neg = verdadero` | R-NEG |

Para `pred → V_ACC obj modif_op`:

| `V_ACC.p.clase` | Reglas semánticas | Regla |
|---|---|---|
| `ENT` (perfil COMPRENSION) | `pred.k = ENT; pred.asp = CLARIDAD; pred.pol = (modif_op ≠ nulo) ? modif_op.pol : +1` | R-ENT |
| `VAL` (VAL_ATEN, VAL_CLAR), con `modif_op` | `pred.k = VAL; pred.asp = V_ACC.p.asp; pred.pol = modif_op.pol; pred.int = modif_op.int` | R-VAL |
| `VAL`, sin `modif_op` | `pred.k = MENCION; pred.asp = V_ACC.p.asp` | R-MEN |
| `SOLIC` (SOLICITUD) | `pred.k = SOLIC; pred.ent = obj.s` | R-SOLIC |
| `COMPR` (COMPROMISO) | `pred.k = COMPR; pred.ticket = obj.ticket; pred.plazo = obj.plazo` | R-COMPR |

Donde no se indica, `neg = falso`. `pred_s → modif` es la cópula omitida («el servicio **muy lento**»).
En `pred → NEG pred_neg` la polaridad **no** se invierte todavía: se retorna la del predicado y la marca `neg`; la
inversión se hace una sola vez, en `construir()` (sección 5). En `pred → V_EST compl`, un verbo de perfil FALLA no se
vuelve positivo por el complemento. «Se» lo exige solo el perfil RECUR: «el servicio corta» y «se funciona» dan
`SE_INCOMPATIBLE` y se abstienen (R-COMPAT).

## 5. Núcleo y cláusula

| BNF | Reglas semánticas | Regla |
|---|---|---|
| `nucleo → sujeto pred_s` | `nucleo.h = construir(pred_s, sujeto)` | la del predicado + R-SUJ |
| `nucleo → pred_l` | `nucleo.h = construir(pred_l, nulo)` | la del predicado |
| `nucleo → TICKET` | `nucleo.h = hecho(TICKET, entidades = [TICKET.norm])` | R-TICKET |
| `nucleo → CORTESIA` | `nucleo.h = hecho(CORTESIA)` | R-CORT |
| `clausula → adv_t_op nucleo frec` | si alguna hoja de la cláusula tiene el rasgo `sin_dominio` (perfil `SIN_DOMINIO`): la cláusula **no se interpreta** (no se evalúa `nucleo`). Si no: `clausula.h = nucleo.h`; si `adv_t_op.t = AHORA`: `clausula.h.temporal = AHORA` | R-SINDOM / R-AHORA |

`hecho(tipo, …)` crea un registro con el resto de los campos en `nulo`. La función `construir(p, s)` convierte los
atributos de un predicado `p` y el sujeto explícito `s` (`nulo` si la cláusula no tiene sujeto delante) en un hecho.
`suj` es el sujeto que aporta el aspecto: `s` o, si no hay, el pospuesto `p.pos`.

| Paso | Regla de cálculo |
|---|---|
| 1 | **Compatibilidad (R-COMPAT).** Si `p.k ∈ {INCOMPLETO, SE_INCOMPATIBLE}`, hay sujeto delante **y** detrás, o la combinación sujeto–predicado no está en `COMPAT` (cuadro siguiente), la cláusula **no se interpreta**: sus tokens pasan a `NO_INTERPRETADO`. Fin. |
| 2 | `p.k = MENCION`: `hecho(MENCION, aspecto = s.asp o p.asp, valoracion = NEUTRA)`; si el sujeto es un ticket, `hecho(TICKET)`. `SOLIC`: `hecho(SOLICITUD, entidades = [equipo])`. `COMPR`: `hecho(COMPROMISO, entidades = [p.ticket])`. `REF`: `hecho(TICKET, entidades = [p.ticket])`. Fin. |
| 3 | `aspecto = p.asp` si `p.k = SEG_SIN`; si no, `suj.asp` cuando hay sujeto; si no, `p.asp` (`ENT`, `VAL`); si no, `SERVICIO`. |
| 4 | `pol' = −p.pol` si `p.neg` (R-NEG); si no, `pol' = p.pol`. |
| 5 | `valoracion = POSITIVA` si `pol' = +1`; `NEGATIVA` si `pol' = −1`. |
| 6 | `declaracion`, solo cuando `aspecto = SERVICIO`: `EST`, `SEG_ADJ` y `SEG_SIN` → `OK` si `pol' = +1`, `FALLA` si `pol' = −1`; `CORTE` sin negar → `RECUR`; `CORTE` negado, `COP`, `ENT` y `VAL` → `nulo`. |
| 7 | `tipo = FUNCIONAMIENTO` si `declaracion ≠ nulo`; si no, `VALORACION`. |
| 8 | `intensidad = p.int` (R-MUY si no es `nulo`); `negada = p.neg`; `entidades = [equipo]` si el sujeto es de perfil EQUIPO. |

**Compatibilidad sujeto–predicado** (tabla `COMPAT` en `semantica.py`, indexada por `sujeto.clase`). Es el chequeo
de tipos del análisis semántico: la gramática acepta «el agente se corta», pero no tiene sentido interpretarlo.

| Sujeto (`clase`) | Predicados admitidos (`k`) |
|---|---|
| `SERVICIO`, `EQUIPO` | `COP`, `EST`, `SEG_ADJ`, `SEG_SIN`, `CORTE`, `MENCION` |
| `ATENCION`, `AGENTE` | `COP`, `SEG_ADJ`, `MENCION`; `VAL` si el verbo valora la ATENCION |
| `CLARIDAD` | `COP`, `SEG_ADJ`, `MENCION`; `VAL` si el verbo valora la CLARIDAD |
| `TICKET` | `REF`, `MENCION` |
| `PROBLEMA` | `COP`, `SEG_ADJ`, `MENCION` |
| sin sujeto | todos, salvo `INCOMPLETO` y `SE_INCOMPATIBLE` |

El sujeto pospuesto se comprueba con la misma tabla. Un sujeto de perfil `SIN_DOMINIO` nunca llega a este paso: la
cláusula ya se abstuvo por R-SINDOM.

Consecuencias que conviene tener presentes:

- «El servicio **está** lento» (`COP`) es una valoración NEGATIVA del SERVICIO, pero **no** es una declaración de
  funcionamiento: no fija el estado. «**Sigue** lento», «**no funciona**», «**falla**» y «**se corta**» sí lo son.
- «La atención sigue mala» valora la ATENCION y no declara nada sobre el funcionamiento (paso 6).
- «No se corta» valora el SERVICIO como POSITIVA, pero no declara que funcione (paso 6).
- «El router no anda» valora y declara sobre el SERVICIO, y registra `ROUTER` como entidad.
- Una cláusula sin sujeto con cópula toma el aspecto por defecto (paso 3): «está lento» → SERVICIO. Ver la limitación
  de la sección 13.
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
| R-SUJ | `sujeto → SUST \| AGENTE` | `_sig`, `_sujeto_agente` |
| R-COP | `pred → V_COP atrib` (con cualidad); `pred_s → modif` | `_p_cop`, `_p_cop_dir` |
| R-EST | `pred → V_EST compl [sujp]` (perfiles OK y FALLA) | `_p_est` |
| R-CORTE | `pred → SE V_EST compl [sujp]` (perfil RECUR) | `_p_est` |
| R-SEG-ADJ | `pred → V_CONT compl`, con `compl → modif` | `_p_seguir` |
| R-SEG-SIN | `pred → V_CONT compl`, con `compl → SIN SUST` | `_p_seguir` |
| R-SIN | `compl → SIN SUST` | `_compl_sin` |
| R-ENT | `pred → V_ACC obj modif_op`, perfil COMPRENSION | `_p_acc` |
| R-VAL | ídem, perfiles VAL_ATEN / VAL_CLAR con cualidad | `_p_acc` |
| R-MEN | `pred_s → ε`; verbo valorativo sin cualidad | `_p_mencion`, `_p_acc` |
| R-SOLIC | ídem, perfil SOLICITUD | `_p_acc` |
| R-COMPR | ídem, perfil COMPROMISO | `_p_acc` |
| R-NEG | `pred_s → NEG pred_neg`; `pred_l → NEG pred_neg` | `_p_neg`; inversión en `_construir` |
| R-MUY | `modif → INT ADJ` | `_modif_int` |
| R-TICKET | `pred → V_COP atrib` (con ticket); `pred_s → TICKET`; `nucleo → TICKET` | `_p_cop`, `_p_ref`, `_n_tk` |
| R-CORT | `nucleo → CORTESIA` | `_n_cort` |
| R-AHORA | `clausula → adv_t_op nucleo frec`, con perfil AHORA | `_clausula` |
| R-POSP | `sujp → SUST` | `_sig`; `_construir` |
| R-COMPAT | paso 1 de `construir()` | `COMPAT`, `_compatible` |
| R-SINDOM | `clausula → adv_t_op nucleo frec` con una hoja de rasgo `sin_dominio` | `_clausula` |
| R-PERO | `cola → PERO clausula cola`; `cola_c → PERO clausula cola` | `clausulas`; `analizador._analizar_turno` |
| R-EST-RES, R-EST-NORES, R-EST-TEMP, R-EST-PEND, R-EST-NC, R-EST-PREC | sección 8 | `decidir_estado` |

## 11. Alcance de la negación, de «sin» y de «muy»

El alcance lo fija la gramática, no una heurística sobre la distancia entre palabras:

- `NEG` solo aparece en `pred → NEG pred_neg`. Niega **exactamente** el predicado `pred_neg` que lo sigue («no
  funciona», «no está lento», «no entendí la explicación», «no me atendieron bien»).
- `SIN` solo aparece en `compl → SIN SUST`: afecta al sustantivo inmediato, y su signo depende del perfil de ese
  sustantivo (R-SIN).
- Ninguno cruza `PERO`, `COMA`, `Y` ni `PUNTO`: después de un conector empieza otra derivación de `clausula`, con su
  propio `neg = falso`. En «No entendí la explicación, pero el agente fue amable», la segunda cláusula no queda negada.
- `INT` solo aparece en `modif → INT ADJ`: intensifica el adjetivo inmediato y no cambia la polaridad.
  «No es muy bueno» produce `pol = +1`, `int = ALTA`, `neg = verdadero` → `NEGATIVA`.

## 12. Árboles anotados de prueba

Como en clase, se comprueba el cuadro sobre una cadena concreta anotando el árbol con los valores esperados.

### 12.1 Caso 02: «Me atendiste muy bien, pero sigo sin internet.»

Tokens que llegan al parser (`Me` es `RELLENO` y se filtra):
`V_ACC INT ADJ COMA PERO V_CONT SIN SUST PUNTO`

```
texto  .L=[C1.1, C1.2]
├─ oracion  .con.i=nulo  .L=[C1.1, C1.2]
│  ├─ clausula  .con.i=nulo  .h=C1.1 {VALORACION, ATENCION, POSITIVA, int=ALTA}
│  │  ├─ adv_t_op → ε
│  │  ├─ nucleo  .h=construir(pred_l, nulo)
│  │  │  └─ pred_l  .k=VAL  .asp=ATENCION  .pol=+1  .int=ALTA      ← pred_l → V_ACC obj modif_op
│  │  │     ├─ V_ACC «atendiste»  .p=VAL_ATEN (clase VAL, asp ATENCION)
│  │  │     ├─ obj → ε
│  │  │     └─ modif_op  .pol=+1  .int=ALTA
│  │  │        └─ modif  ← INT «muy»  ADJ «bien» .p=POSITIVO (pol +1)
│  │  └─ frec → ε  .n=0
│  └─ cola  .L=[C1.2]
│     ├─ COMA
│     └─ cola_c  .L=[C1.2]
│        ├─ PERO
│        ├─ clausula  .con.i=PERO  .h=C1.2 {FUNCIONAMIENTO, SERVICIO, NEGATIVA, decl=FALLA}
│        │  └─ nucleo  .h=construir(pred_l, nulo)
│        │     └─ pred_l  .k=SEG_SIN  .pol=−1  .asp=SERVICIO       ← pred_l → V_CONT compl
│        │        ├─ V_CONT «sigo»
│        │        └─ compl  .t=SIN  .asp=SERVICIO  .pol=−1         ← SIN «sin»  SUST «internet» .p=SERVICIO (pol 0)
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
      └─ pred_neg  .k=ENT  .asp=CLARIDAD  .pol=+1                 ← pred_neg → V_ACC obj modif_op
         ├─ V_ACC «entendí»  .p=COMPRENSION (clase ENT, asp CLARIDAD)
         ├─ obj  .s=SUST «explicación» .p=CLARIDAD
         └─ modif_op → ε
```

`construir`: sin sujeto, compatible (paso 1); `aspecto = p.asp = CLARIDAD` (paso 3); `neg` → `pol' = −1` (paso 4) →
`NEGATIVA`; `ENT` no declara funcionamiento (paso 6). Reglas: R-ENT, R-NEG.

### 12.3 Caso 03: «Ahora funciona, pero se corta todos los días.»

| Cláusula | Predicado | Hecho | Reglas |
|---|---|---|---|
| C1.1 «Ahora funciona» | `pred_l → V_EST compl sujp`; «funciona» `.p = OK`; `compl → ε`: `k=EST`, `pol=+1` | SERVICIO = POSITIVA, declaración `OK`, temporal `AHORA` | R-EST, R-AHORA |
| C1.2 «se corta todos los días» | `pred_l → SE V_EST compl sujp`; «corta» `.p = RECUR` (exige «se»): `k=CORTE`, `pol=−1`; `frec.n=2` | SERVICIO = NEGATIVA, declaración `RECUR` | R-CORTE, R-PERO |

`combinar({POSITIVA, NEGATIVA}) = MIXTA`. Estado: el turno tiene `OK` y `RECUR` y termina en `RECUR` → fila 1 →
**TEMPORAL** (R-EST-TEMP), no RESUELTO.

### 12.4 Caso 16 y abstenciones: sujeto pospuesto, incompatibilidad y SIN_DOMINIO

| Cláusula | Derivación | Resultado |
|---|---|---|
| «No funciona el internet» | `pred_l → NEG pred_neg`, `pred_neg → V_EST compl sujp`, `sujp → SUST` (perfil SERVICIO) | compatible; aspecto del sujeto pospuesto; SERVICIO NEGATIVA, `FALLA` (R-EST, R-POSP, R-NEG) |
| «el router falla seguido» | `sujeto → SUST` (perfil EQUIPO), `pred_s → V_EST compl` con «falla» de perfil FALLA, `frec` | SERVICIO NEGATIVA, `FALLA`, entidad `ROUTER` |
| «ahora funciona sin cortes» | `pred_l → V_EST compl`, `compl → SIN SUST` (perfil PROBLEMA) | `compl.pol = +1` → SERVICIO POSITIVA, `OK` (R-EST, R-SIN, R-AHORA) |
| «El agente se corta» | `sujeto(AGENTE) pred_s → SE V_EST compl` | `CORTE ∉ COMPAT[AGENTE]` → no se interpreta (R-COMPAT) |
| «El servicio corta todos los días» | `pred_s → V_EST compl` con «corta» de perfil RECUR, sin «se» | `SE_INCOMPATIBLE` → no se interpreta (R-COMPAT) |
| «Mi router hace ruidos raros», con «hace», «ruidos» y «raros» de perfil SIN_DOMINIO | `sujeto(SUST) pred_s → V_ACC obj modif_op` | se reconoce entera; R-SINDOM → no se interpreta (no se inventa «el router está raro») |

Para reproducir cualquiera de estos árboles: `python3 main.py casos/caso_02.txt --traza S01 --detalle`.

## 13. Cómo modificar una regla, y límites

| Cambio | Dónde | Sección |
|---|---|---|
| Qué significa una forma canónica | sus `rasgos` en `vocabulario.json` (deben ser los de un perfil), o desde el menú al crearla | 3 |
| Qué rasgos tiene un perfil (p. ej. que el perfil EQUIPO no valore el SERVICIO) | `semantica.PERFILES` y las entradas de `vocabulario.json` de ese perfil (la validación de carga las señala) | 3 |
| Un perfil nuevo (un significado que el modelo no tiene) | `semantica.PERFILES` + reglas que lo usen + `REGLAS_SEMANTICAS.md` | 3 a 5 |
| Qué sujeto admite qué predicado (p. ej. que «el agente no entendió» valore la ATENCION) | tabla `COMPAT` | 5 |
| Qué significa «sigue + adjetivo» | `_p_seguir` | 4 |
| El signo de «sin» + sustantivo | `_compl_sin` | 3.1 |
| Efecto de la negación | `_p_neg` y paso 4 de `_construir` | 4 y 5 |
| Qué predicados declaran funcionamiento (p. ej. que «no se corta» declare `OK`) | paso 6 de `_construir` | 5 |
| Cómo se combinan las evidencias | `combinar` | 7 |
| Criterio de estado | `decidir_estado`, interruptor `LO_ULTIMO_PREVALECE` | 8 |
| Una construcción lingüística nueva | producción en `gramatica.py` + función `@acc` | 3 a 5 |

Después de cualquier cambio: `python3 gramatica.py` (la gramática debe seguir sin conflictos LL(1)) y
`python3 pruebas.py --regresion`.

**Límite conocido.** Una palabra desconocida que el usuario no inserta se descarta antes del parser, y el parser une
lo que queda. Si lo que se pierde es el sujeto, la cláusula queda sin sujeto y toma el aspecto por defecto:
«El servicio no funciona, pero el técnico fue amable» → «fue amable» → **SERVICIO POSITIVA**. Registrar «técnico»
con perfil `SIN_DOMINIO` (rasgo `sin_dominio`) lo evita (la cláusula se abstiene). Una regla general (abstenerse cuando en el tramo de la
cláusula se descartó una palabra desconocida) se probó en una copia: corrige este caso y, cuando se midió, solo
cambiaba el turno «Muchas gracias» del caso 11, que ya se eliminó de la batería. Queda propuesta, no aplicada.
