# TP1 · Speech Analytics — Diseño de Compiladores (FPUNA 2026/2)

Analizador determinista de conversaciones de soporte técnico de Internet. Python 3.10+, **sin dependencias externas**
(no usa el módulo `re` en el léxico: el AFD se construye con Thompson + subconjuntos).

El funcionamiento completo, fase por fase, está en **`INFORME_TECNICO.md`**.

## Ejecución

```bash
python3 main.py casos_guia.txt                       # vista de consola + salida.json; pregunta por las palabras que el corrector no resuelve
python3 main.py casos_guia.txt < /dev/null           # sin respuestas: toda palabra desconocida sigue la regla del enunciado
python3 main.py casos/caso_12.txt --traza S01        # traza: original → tokens → estructura → tabla de entidades → acción → resultado
python3 main.py casos/caso_12.txt --traza S01 --detalle   # + cada celda M[A,a] de la tabla LL(1) usada
python3 main.py casos/caso_08.txt --dic lenta,lento  # diccionario reducido del caso 08 (solo en memoria)
python3 main.py --reiniciar-aprendido                # borra lo aprendido y vuelve a la precarga
python3 main.py --tabla-inicial                      # tabla de símbolos léxica INICIAL (solo la precarga vocabulario.json)
python3 main.py --tabla                              # tabla VIGENTE (precarga + aprendido, «+» = aprendido)
python3 main.py casos/caso_19.txt --tabla            # analiza (preguntando) y después muestra la tabla ya enriquecida
python3 main.py --tabla ADJ                          # solo una categoría (también --tabla-inicial ADJ)
python3 pruebas.py                                   # 19 casos + 13 pruebas de la tabla léxica (solo precarga; 19 y 20 con respuestas simuladas)
python3 pruebas.py --regresion                       # + comparación completa contra casos/golden/
python3 pruebas.py --golden                          # regenera el golden (sin preguntas, solo precarga)
python3 pruebas.py --informe                         # regenera RESULTADOS_PRUEBAS.md
python3 gramatica.py                                 # PRIM, SGTE y verificación LL(1)
python3 derivacion.py                                # derivación L0→L1→L2→L3 con diagnóstico por paso
```

## Pipeline y módulos

| Etapa | Módulo | Contenido |
|---|---|---|
| 1. Formato | `lector.py` | `SESION Sxx` / `n ROL: texto` / `FIN`; rechaza el turno inválido y continúa en la línea siguiente; tras un **orden inconsistente** descarta el resto de la sesión; rechaza ids de sesión repetidos; normaliza a NFC y tolera BOM |
| 2. Léxico | `lexico.py`, `tabla_lexica.py` | ER → AFN → AFD sobre el diccionario de la **tabla de símbolos léxica** (16 categorías); lexema más largo + prioridad; posiciones (sesión, turno, desplazamiento); normalización; `TK-` + 3 a 6 dígitos |
| 3. Corrector | `corrector.py`, `consulta.py` | Levenshtein ≤ 1: candidato único → se corrige; **empate o sin candidato → se consulta al usuario** (elegir un candidato, insertar la palabra o mantener la regla del enunciado) |
| 4. Parser | `gramatica.py`, `sintaxis.py` | BNF LL(1) (PRIM/SGTE calculados; 170 celdas, sin conflictos); parser predictivo guiado por la tabla; recuperación en modo pánico con SGTE |
| 5. Semántica | `semantica.py` | reglas por producción; el significado sale de los **rasgos** de la forma canónica (guardados en la tabla de símbolos léxica); compatibilidad sujeto–predicado; aspecto, valoración, declaración; estado y precedencia |
| 6. Entidades | `entidades.py` | **tabla de entidades** por sesión (SESION, PARTICIPANTE, TICKET), apariciones, control de duplicados, actualización; efímera |
| 7. Salida | `analizador.py`, `main.py` | JSON por lote + vista legible + traza |

## Las tablas

| | Tabla de símbolos léxica (`tabla_lexica.py`) | Tabla de entidades (`entidades.py`) |
|---|---|---|
| Qué guarda | el lenguaje, en **una sola estructura**: categoría → forma canónica → {**rasgos**, formas superficiales} | lo que aparece en cada conversación: sesión, participante, ticket y sus apariciones |
| Ámbito | global (todas las sesiones y ejecuciones) | la sesión |
| Persistencia | **sí**, entre ejecuciones; se enriquece con las respuestas del usuario | **no**: se crea vacía en cada ejecución |
| Archivos | precarga: `vocabulario.json` (el programa nunca lo escribe); aprendido: `vocabulario_aprendido.json` (mismo formato, una escritura atómica por cambio) | ninguno (sale en el JSON de resultados, `entidades`) |
| Operaciones | buscar, insertar (variante de un canónico existente: hereda sus rasgos), alta de forma canónica (con los rasgos de un perfil existente), reinicio; control de duplicados, normalización y validación de rasgos al cargar | buscar, insertar (enlaza duplicados), actualizar |

Cada entrada de `vocabulario.json` tiene la forma
`"LENTO": {"rasgos": {"pol": -1}, "formas": ["lento", "lenta"]}`. Los **rasgos** (aspecto, entidad, pol, decl,
pronominal, clase, tiempo, sin_dominio) son lo que leen las reglas semánticas. No son libres: los **perfiles**
(`semantica.PERFILES`) son el catálogo cerrado de combinaciones válidas por categoría, y al cargar la tabla se valida que
los rasgos de cada forma canónica coincidan con uno. Desde el menú se crean formas superficiales y formas canónicas
(eligiendo un perfil: el programa copia sus rasgos), nunca rasgos sueltos, perfiles ni categorías.

**Por qué los rasgos están en el mismo JSON y no en un `significados.json` aparte** (decisión del grupo, basada en la
interactividad de la tabla):

1. *Una escritura atómica por cambio.* Cada alta o inserción hecha desde el menú se guarda con una única escritura
   atómica (temporal + `os.replace`) de `vocabulario_aprendido.json`: la forma canónica y sus rasgos nunca quedan
   separados. Con dos archivos cada escritura era atómica por separado, pero el cambio completo no: la consistencia
   dependía del orden en que se escribían y de que ambos archivos se borraran, restauraran o copiaran siempre juntos.
   Si faltaba uno, quedaban formas aprendidas cuya forma canónica no tenía significado y la tabla no cargaba.
2. *Lo aprendido vale enseguida.* La tabla vigente es un solo objeto vivo: el menú agrega la entrada con sus rasgos y
   el corrector y la semántica la ven en el turno siguiente de la misma entrada, sin sincronizar dos estructuras.
3. *El menú muestra y guarda lo mismo.* Al ofrecer las formas canónicas existentes como variante se muestran sus
   rasgos, leídos de la misma entrada en la que se va a insertar la palabra.
4. *Lo aprendido tiene el formato de la precarga.* Pasar una palabra aprendida a la precarga es copiar una línea, y la
   conciliación (gana la precarga) y el reinicio trabajan sobre un solo archivo.
5. *El menú sigue cerrado.* Que los rasgos estén en el JSON no los vuelve editables desde el programa: se copian de un
   perfil, y un rasgo editado a mano que no coincida con ningún perfil se rechaza al cargar.

Costo aceptado: los rasgos de un perfil se repiten en cada forma canónica (por ejemplo, `{"pol": -1}` en cuatro
adjetivos). Si se cambia un perfil en el código, la validación de carga señala las entradas que hay que actualizar.

`pruebas.py` y el golden corren sin consultas y con la precarga, así lo aprendido en ejecuciones interactivas no
cambia los resultados esperados.

Documentación: `INFORME_TECNICO.md` (cómo funciona el proyecto, de punta a punta), `INFORME_lexico.md` (léxico, AFD de
TICKET y tabla de símbolos léxica), `GRAMATICA.md` (BNF, PRIM/SGTE, parser y recuperación), `DERIVACION.md` (pasos de la
gramática original a la LL(1)), `REGLAS_SEMANTICAS.md` (perfiles, cuadros BNF | reglas semánticas, estado y árboles
anotados), `RESULTADOS_PRUEBAS.md` (esperado vs obtenido por caso).

## Decisiones de diseño (para la defensa)

1. **Léxico y sintaxis separados**: el lexer no ve contexto. `agente` es siempre `AGENTE`; el parser lo usa como rol o como sujeto («el agente fue amable»).
2. **Alcance de la negación = estructura de la gramática**: `NEG` solo aparece ante `pred_neg` y `SIN` ante un sustantivo; no cruzan `PERO`, `COMA` ni `Y`. Cada cláusula es una derivación independiente.
3. **MIXTA no es promedio**: hay evidencia POSITIVA y NEGATIVA del mismo aspecto; se conservan ambas evidencias.
4. **«Ahora funciona» es evidencia POSITIVA del SERVICIO** (el caso 03 exige MIXTA con «se corta»).
5. **Opiniones del AGENTE**: se conservan con su autoría (`opiniones_agente`); no entran al resumen del CLIENTE ni al estado.
6. **Estado**: prevalece lo último (`R-EST-PREC`, respuesta del profesor): una promesa del agente posterior a la última declaración del CLIENTE deja la sesión `PENDIENTE`; una declaración del cliente posterior a la promesa prevalece sobre ella. Interruptor `LO_ULTIMO_PREVALECE`.
   - `OK` → RESUELTO · `FALLA` → NO_RESUELTO · `OK` y `RECUR` en el mismo turno, o `RECUR` tras una recuperación → TEMPORAL.
   - Sin declaración del cliente: compromiso del agente → PENDIENTE; si no, NO_CONFIRMADO.
   - «El servicio está lento» (valoración sin declaración de funcionamiento) **no** fija estado.
7. **Abstención**: palabras desconocidas que el usuario no resuelve, empates de Levenshtein, tickets mal formados, fragmentos que el parser no reconoce, combinaciones incompatibles (R-COMPAT) y cláusulas con palabras sin dominio (R-SINDOM) se marcan `NO_INTERPRETADO`.
8. **Corrección**: solo sobre `PALABRA`, con longitud mínima 4 (`MIN_LONG`) para no convertir «mas» en «mal». Se consulta al usuario solo después del corrector (empate o sin candidato). Elegir un candidato corrige **solo esa aparición**; insertar agrega la forma a la tabla léxica (`vocabulario_aprendido.json`) y queda como corrección `INSERTADA` en el JSON de resultados, con su turno, categoría y forma canónica.
9. **Análisis PARCIAL** = hubo un turno rechazado o descartado por formato, o falta `FIN`. Los fragmentos NO_INTERPRETADO no vuelven parcial una sesión.
10. **Orden de turnos** (respuesta del profesor): ante un número fuera de orden se conservan los turnos anteriores y se descarta todo lo que sigue en la sesión (`ORDEN_INCONSISTENTE` y luego `TURNO_DESCARTADO`); en «1, 3, 4» queda solo el 1. Un rol inválido, en cambio, rechaza solo ese turno (caso 07).
11. **Id de sesión repetido** en un lote: la segunda sesión se descarta completa (`SESION_DUPLICADA`), porque compartiría el ámbito de la tabla de entidades con la primera.
12. **Rasgos en la tabla de símbolos léxica; perfiles cerrados**: la tabla tiene tres niveles (categoría → forma canónica → formas superficiales) y cada forma canónica guarda sus rasgos. Las combinaciones válidas de rasgos son los perfiles del código. La gramática usa categorías generales (19 terminales en el texto) y una palabra nueva no requiere tocarla (ver la justificación en «Las tablas»).
13. **Compatibilidad sujeto–predicado** (`R-COMPAT`): la gramática acepta «el agente se corta», pero la semántica no lo interpreta. Es el chequeo de tipos: tabla `COMPAT` en `semantica.py`. También verifica que «se» vaya solo con un verbo de rasgo `pronominal` (perfil RECUR) («el agente corta la llamada» se abstiene).
14. **`SIN_DOMINIO`**: una palabra reconocida pero sin significado para el dominio («hace», «ruido») ocupa su lugar en el árbol y la cláusula se abstiene (R-SINDOM). Así no se «pegan» las palabras restantes en una valoración inventada.

## Dónde tocar en una modificación de reglas (defensa)

| Cambio pedido | Dónde |
|---|---|
| nueva palabra (sinónimo, adjetivo, verbo) | en ejecución: responder `n`, elegir la categoría y la forma canónica (o crear una con un perfil existente); para la precarga: una línea en `vocabulario.json` con los rasgos de un perfil |
| qué significa una forma canónica | sus `rasgos` en `vocabulario.json` (deben coincidir con un perfil de `semantica.PERFILES`) |
| qué rasgos tiene un perfil | `semantica.py`, `PERFILES` (y actualizar las entradas de `vocabulario.json` que señale la validación) |
| un significado nuevo (perfil nuevo) | `semantica.py`, `PERFILES` + reglas que lo usen + `REGLAS_SEMANTICAS.md` |
| qué sujeto admite qué predicado | `semantica.py`, tabla `COMPAT` |
| qué significa «sigue + adjetivo» | `semantica.py`, `_p_seguir` |
| alcance o efecto de la negación | `semantica.py`, `_p_neg` y paso 4 de `_construir` |
| criterio de estado | `semantica.py`, `decidir_estado` |
| precedencia promesa del agente / declaración del cliente | interruptor `LO_ULTIMO_PREVALECE` en `semantica.py` |
| distancia o longitud mínima de corrección | `corrector.py` (`MIN_LONG`, `== 1`) |
| nueva construcción lingüística | `gramatica.py` + regla en `semantica.py`; luego `python3 gramatica.py` debe seguir sin conflictos |

Tras cualquier cambio: `python3 pruebas.py --regresion`. Una mutación (p. ej. MIXTA promediada a POSITIVA) hace fallar los casos 01, 03, 07, 10, 12, 13, 16, 17, 18 y 19.

## Casos

| Caso | Origen | Qué prueba |
|---|---|---|
| 01–08 | enunciado | resuelto, contraste, temporal, claridad, corrección + ticket, pendiente, rol inválido, empate |
| 09 | propio | negación + contraste |
| 10 | propio | corrección única + precedencia: el agente promete después de la confirmación → PENDIENTE |
| 12 | propio | recuperación: rol inválido, ticket mal formado con error sintáctico, orden inconsistente (se descarta el resto), sesión siguiente intacta |
| 13 | propio | sujeto explícito con «sigue» y «se corta» («El internet sigue lento») → TEMPORAL |
| 14 | propio | recuperación de formato: salto de número («1, 3, 4» → solo el 1); id de sesión repetido |
| 15 | propio | precedencia «prevalece lo último»: falla + promesa → PENDIENTE; promesa + falla → NO_RESUELTO; confirmación + promesa → PENDIENTE |
| 16 | propio | sujeto pospuesto, «y», router como sujeto, «falla», «no me atendieron bien», «sin cortes»; sujeto y predicado incompatibles → abstención |
| 17 | propio (alcance) | lentitud y reinicio del router: la solicitud del agente no valora ni fija estado; en S01 el reinicio no resuelve (NO_RESUELTO), en S02 sí (RESUELTO) |
| 18 | propio (alcance) | cortes y seguimiento de tickets: ticket asignado y escalado (una entrada, dos apariciones, seguimiento `COMPROMISO_FUTURO`); el cliente declara después → NO_RESUELTO; el mismo TK-512 en S02 es otra entrada (ámbito sesión) → PENDIENTE |
| 19 | propio (alcance, **inserción**) | falta de conexión con palabras fuera del vocabulario: «intermitente» → variante de `ADJ/INESTABLE`, «conecta» → variante de `V_EST/FUNCIONAR`; se pregunta una vez y vale para el turno 3 → MIXTA, RESUELTO. Sin consulta: SIN_EVIDENCIA, NO_CONFIRMADO |
| 20 | propio (alcance, **inserción**) | cortes y tickets con formas canónicas nuevas: `V_EST/DESCONECTAR` (perfil RECUR) y `V_ACC/VERIFICAR` (perfil COMPROMISO) → NEGATIVA, PENDIENTE. Sin consulta: el corte no se interpreta y la promesa queda como mención del ticket |

Los casos 17 a 20 cubren el alcance del enunciado (§1: falta de conexión, lentitud, cortes, reinicio del router y
seguimiento de tickets). En 19 y 20 hay palabras fuera del vocabulario: `casos.json` trae las **respuestas al menú**
(`"respuestas"`, simbólicas: `#ADJ` = la categoría ADJ, `@ADJ/INESTABLE` = esa forma canónica, `%V_EST/RECUR` = ese
perfil), las **preguntas esperadas** y el **resultado sin consulta** (`"esperado_sin_consulta"`). `pruebas.py` simula
las respuestas sobre una tabla solo en memoria creada desde la precarga: no escribe `vocabulario_aprendido.json`.
Para mostrarlos en la defensa: `python3 main.py casos/caso_19.txt` y responder `n` → `ADJ` → `INESTABLE`, y `n` →
`V_EST` → `FUNCIONAR` (los números del menú dependen de lo ya aprendido; con la precarga: `n 2 6 n 4 3`). Después,
`python3 main.py --reiniciar-aprendido`.

Además, `pruebas.py` verifica la tabla léxica con 13 pruebas de consulta simulada: preguntas solo después del
corrector, inserción, lo aprendido con el formato de la precarga, empate, alta de forma canónica con nombre normalizado
y los rasgos del perfil elegido, «vale para el resto de la entrada», duplicados, `SIN_DOMINIO`, persistencia, precarga
intacta, rasgos validados al cargar, reinicio y baja por precarga.

## Límites conocidos

- Vocabulario acotado al dominio del enunciado. Una palabra desconocida que el usuario no inserta se descarta antes del parser y el parser une lo que queda: «…pero el técnico fue amable» → «fue amable» se lee como SERVICIO POSITIVA. Registrar la palabra con perfil `SIN_DOMINIO` lo evita; una regla general de abstención (R-DESC) está propuesta en `INFORME_TECNICO.md` §9.
- Desde el menú no se crean categorías ni perfiles: un significado nuevo requiere código. Una construcción nueva requiere cambiar la gramática.
- Las oraciones se separan con `.`; sin punto, la segunda oración se descarta como fuera de la gramática (necesario para mantener LL(1)).
- La verificación de equivalencia de gramáticas (`derivacion.py`) es acotada (hasta 5 tokens), no una demostración.
- Siguen fuera de la gramática: «sin» + verbo («sigue sin funcionar»), dos complementos («revisaremos TK-204 mañana»), adjetivo suelto sin sujeto («muy lento») y el demostrativo «esta» («esta conexión es lenta»), que se confunde con «está».
- Una forma tiene una sola categoría: los homógrafos («falla», «corte») se leen de una única manera. Los tiempos verbales no se distinguen: «Ya reinicié el router», dicho por el cliente, se pliega a «reinicie» y se lee como una SOLICITUD (no cambia valoraciones ni estado, pero el tipo de la cláusula es incorrecto).
- Pendiente de la entrega: la declaración de IA y contribuciones (abajo).

## Declaración de herramientas de IA y contribuciones (COMPLETAR por el grupo)

- Herramienta de IA utilizada: Claude (Anthropic), para diseño de arquitectura, generación de código y documentación, aplicando los algoritmos de clase (ER→AFN→AFD, PRIM/SGTE, Levenshtein).
- Bibliotecas: solo la biblioteca estándar de Python (`json`, `dataclasses`, `unicodedata`, `argparse`, `tempfile`, `getpass`, `re`).
- Contribuciones de cada integrante: _completar_.
