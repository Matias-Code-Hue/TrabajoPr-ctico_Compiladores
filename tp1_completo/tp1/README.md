# TP1 · Speech Analytics — Diseño de Compiladores (FPUNA 2026/2)

Analizador determinista de conversaciones de soporte técnico de Internet. Python 3.10+, **sin dependencias externas**
(no usa el módulo `re`: el AFD se construye con Thompson + subconjuntos).

## Ejecución

```bash
python3 main.py casos_guia.txt                       # vista de consola + salida.json; pregunta por cada palabra desconocida
python3 main.py casos_guia.txt < /dev/null           # sin respuestas: toda palabra desconocida sigue la regla del enunciado
python3 main.py casos/caso_12.txt --traza S01        # traza: original → tokens → estructura → tabla de entidades → acción → resultado
python3 main.py casos/caso_12.txt --traza S01 --detalle   # + cada celda M[A,a] de la tabla LL(1) usada
python3 main.py casos/caso_08.txt --dic lenta,lento  # diccionario reducido del caso 08
python3 pruebas.py                                   # 16 casos contra lo esperado + pruebas de la tabla de símbolos léxica
python3 pruebas.py --regresion                       # + comparación completa contra casos/golden/
python3 pruebas.py --informe                         # regenera RESULTADOS_PRUEBAS.md
python3 gramatica.py                                 # PRIM, SGTE y verificación LL(1)
python3 derivacion.py                                # derivación L0→L1→L2→L3 con diagnóstico por paso
```

## Pipeline y módulos

| Etapa | Módulo | Contenido |
|---|---|---|
| 1. Formato | `lector.py` | `SESION Sxx` / `n ROL: texto` / `FIN`; rechaza el turno inválido y continúa en la línea siguiente; tras un **orden inconsistente** descarta el resto de la sesión; rechaza ids de sesión repetidos; normaliza a NFC y tolera BOM |
| 2. Léxico | `lexico.py`, `tabla_lexica.py` | ER → AFN → AFD sobre la **tabla de símbolos léxica** (29 subcategorías: `SUST_*`, `ADJ_*`, `V_*`, …); lexema más largo + prioridad; posiciones (sesión, turno, desplazamiento); normalización; `TK-` + 3 a 6 dígitos |
| 3. Corrector | `corrector.py`, `consulta.py` | Levenshtein ≤ 1; por cada palabra desconocida **consulta al usuario**: tomar un candidato (solo esa aparición), insertar la palabra en la tabla léxica, o Enter = regla del enunciado (candidato único → se corrige; empate → se conserva y se registra) |
| 4. Parser | `gramatica.py`, `sintaxis.py` | BNF LL(1) (PRIM/SGTE calculados; 305 celdas) con construcciones generales y cinco grupos de subcategorías; parser predictivo guiado por la tabla; recuperación en modo pánico con SGTE |
| 5. Semántica | `semantica.py` | reglas por producción; cada subcategoría fija su significado; compatibilidad sujeto–predicado; aspecto, valoración, declaración; estado y precedencia |
| 6. Entidades | `entidades.py` | **tabla de entidades** por sesión (SESION, PARTICIPANTE, TICKET), apariciones, control de duplicados, actualización; efímera |
| 7. Salida | `analizador.py`, `main.py` | JSON por lote + vista legible + traza |

## Las dos tablas

| | Tabla de símbolos léxica (`tabla_lexica.py`) | Tabla de entidades (`entidades.py`) |
|---|---|---|
| Qué guarda | el lenguaje: forma → token (categoría) y canónico | lo que aparece en cada conversación: sesión, participante, ticket y sus apariciones |
| Ámbito | global (todas las sesiones y ejecuciones) | la sesión |
| Persistencia | **sí**, entre ejecuciones; se enriquece con las respuestas del usuario | **no**: se crea vacía en cada ejecución |
| Archivos | `vocabulario.json` (precarga manual, el programa nunca lo escribe), `vocabulario_aprendido.json` (formas incorporadas, con origen), `vocabulario_auditoria.jsonl` (una línea por cambio, solo se agregan) | ninguno (sale en el JSON de resultados, `entidades`) |
| Operaciones | buscar, insertar (con control de duplicados) | buscar, insertar (enlaza duplicados), actualizar |

`pruebas.py` corre los casos con la precarga y sin consultas, así lo aprendido en ejecuciones interactivas no cambia
los resultados esperados. Para volver a la precarga basta con borrar `vocabulario_aprendido.json` (la auditoría se conserva).

Documentación: `INFORME_lexico.md` (léxico, AFD de TICKET y tabla de símbolos léxica), `GRAMATICA.md` (BNF, PRIM/SGTE, parser y recuperación),
`REGLAS_SEMANTICAS.md` (cuadros BNF | reglas semánticas, atributos, estado y árboles anotados), `DERIVACION.md`
(pasos de la gramática original a la LL(1)), `RESULTADOS_PRUEBAS.md` (esperado vs obtenido por caso).

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
7. **Abstención**: palabras desconocidas que el usuario no resuelve, empates de Levenshtein, tickets mal formados y fragmentos que el parser no reconoce se marcan `NO_INTERPRETADO`; nunca se inventa una valoración.
8. **Corrección**: solo sobre `PALABRA`, con longitud mínima 4 (`MIN_LONG`) para no convertir «mas» en «mal»; las palabras más cortas no se consultan. Elegir un candidato corrige **solo esa aparición** (los errores de tipeo no se guardan); insertar agrega la forma a la tabla léxica y deja una línea de auditoría.
9. **Análisis PARCIAL** = hubo un turno rechazado por formato o falta `FIN`. Los fragmentos NO_INTERPRETADO no vuelven parcial una sesión.
10. **Orden de turnos** (respuesta del profesor): ante un número fuera de orden se conservan los turnos anteriores y se descarta todo lo que sigue en la sesión (`ORDEN_INCONSISTENTE` y luego `TURNO_DESCARTADO`); en «1, 3, 4» queda solo el 1. La sesión queda PARCIAL y las siguientes se analizan normalmente. Un rol inválido, en cambio, rechaza solo ese turno (caso 07).
12. **Vocabulario por subcategorías**: la categoría léxica dice qué clase de palabra es y qué significa (`SUST_SERV`, `ADJ_NEG`, `V_EST_FALLA`). La gramática describe construcciones con grupos (`sust`, `adj`, `v_est`, `v_acc`, `adv_t`) y la regla semántica de cada producción del grupo fija el atributo. Una palabra nueva se inserta eligiendo su subcategoría; no hace falta tocar la gramática ni guardar rasgos en la tabla.
13. **Compatibilidad sujeto–predicado** (`R-COMPAT`): la gramática acepta «el agente se corta», pero la semántica no lo interpreta. Es el chequeo de tipos: tabla `COMPAT` en `semantica.py`.
14. **«se corta» exige «se»**: `SE V_EST_RECUR` es una producción propia; «el agente corta la llamada» queda en abstención.
11. **Id de sesión repetido** en un lote: la segunda sesión se descarta completa (`SESION_DUPLICADA`), porque compartiría el ámbito de la tabla de entidades con la primera.

## Dónde tocar en una modificación de reglas (defensa)

| Cambio pedido | Dónde |
|---|---|
| nuevo sinónimo, adjetivo o verbo | en ejecución: responder `n` y elegir la subcategoría; para la precarga: `vocabulario.json` (una línea) |
| nueva subcategoría | terminal en su grupo de `gramatica.py` + `_constante(...)` en `semantica.py` + entrada en `consulta.MENU` |
| qué significa una subcategoría (aspecto, polaridad) | `semantica.py`, llamadas a `_constante(...)` |
| qué sujeto admite qué predicado | `semantica.py`, tabla `COMPAT` |
| qué significa «sigue + adjetivo» | `semantica.py`, `_p_seguir` |
| alcance o efecto de la negación | `semantica.py`, reglas `pred_s/pred_l → NEG pred_neg` |
| criterio de estado | `semantica.py`, `decidir_estado` |
| precedencia promesa del agente / declaración del cliente | interruptor `LO_ULTIMO_PREVALECE` en `semantica.py` |
| distancia o longitud mínima de corrección | `corrector.py` (`MIN_LONG`, `== 1`) |
| nueva construcción lingüística | `gramatica.py` + regla en `semantica.py`; luego `python3 gramatica.py` debe seguir sin conflictos |

Tras cualquier cambio: `python3 pruebas.py --regresion`. Una mutación (p. ej. MIXTA promediada a POSITIVA) hace fallar los casos 01, 03, 07, 10, 12, 13 y 16.

## Casos

| Caso | Origen | Qué prueba |
|---|---|---|
| 01–08 | enunciado | resuelto, contraste, temporal, claridad, corrección + ticket, pendiente, rol inválido, empate |
| 09 | propio | negación + contraste |
| 10 | propio | corrección única + precedencia: el agente promete después de la confirmación → PENDIENTE |
| 11 | propio | abstención: palabras desconocidas; «Mi router hace ruidos raros» queda como mención NEUTRA |
| 12 | propio | recuperación: rol inválido, ticket mal formado con error sintáctico, orden inconsistente (se descarta el resto), sesión siguiente intacta |
| 13 | propio | sujeto explícito con «sigue» y «se corta» («El internet sigue lento») → TEMPORAL |
| 14 | propio | recuperación de formato: salto de número («1, 3, 4» → solo el 1); id de sesión repetido |
| 15 | propio | precedencia «prevalece lo último»: falla + promesa → PENDIENTE; promesa + falla → NO_RESUELTO; confirmación + promesa → PENDIENTE |
| 16 | propio | gramática por subcategorías: sujeto pospuesto, «y», router como sujeto, «falla», «no me atendieron bien», «sin cortes»; sujeto y predicado incompatibles → abstención |

## Límites conocidos

- Vocabulario acotado al dominio del enunciado; una palabra desconocida que el usuario no inserta se descarta y el resto de la cláusula se interpreta igual.
- Una palabra nueva entra en una subcategoría existente; una construcción nueva requiere cambiar la gramática.
- Las oraciones se separan con `.`; sin punto, la segunda oración se descarta como fuera de la gramática (necesario para mantener LL(1)).
- La verificación de equivalencia de gramáticas (`derivacion.py`) es acotada (hasta 5 símbolos, con los grupos de subcategorías colapsados), no una demostración.
- Una cláusula con un error sintáctico en su interior no se interpreta: se prefiere la abstención a una valoración dudosa.
- Siguen fuera de la gramática: «sin» + verbo («sigue sin funcionar»), dos complementos («revisaremos TK-204 mañana») y el demostrativo «esta» («esta conexión es lenta»), que se confunde con «está».
- Una forma tiene una sola categoría: los homógrafos («falla», «corte») se leen de una única manera. Los tiempos verbales no se distinguen.
- Pendiente de la entrega: informe técnico unificado y la declaración de IA/contribuciones (abajo).

## Declaración de herramientas de IA y contribuciones (COMPLETAR por el grupo)

- Herramienta de IA utilizada: Claude (Anthropic), para diseño de arquitectura, generación de código y documentación, aplicando los algoritmos de clase (ER→AFN→AFD, PRIM/SGTE, Levenshtein).
- Bibliotecas: solo la biblioteca estándar de Python (`json`, `dataclasses`, `unicodedata`, `argparse`, `tempfile`, `getpass`).
- Contribuciones de cada integrante: _completar_.
