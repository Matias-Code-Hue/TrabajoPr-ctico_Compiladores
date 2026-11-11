# TP1 · Speech Analytics — Diseño de Compiladores (FPUNA 2026/2)

Analizador determinista de conversaciones de soporte técnico de Internet. Python 3.10+, **sin dependencias externas**
(no usa el módulo `re`: el AFD se construye con Thompson + subconjuntos).

## Ejecución

```bash
python3 main.py casos_guia.txt                       # vista de consola + salida.json
python3 main.py casos/caso_12.txt --traza S01        # traza: original → tokens → estructura → tabla de símbolos → acción → resultado
python3 main.py casos/caso_12.txt --traza S01 --detalle   # + cada celda M[A,a] de la tabla LL(1) usada
python3 main.py casos/caso_08.txt --dic lenta,lento  # diccionario reducido del caso 08
python3 pruebas.py                                   # 14 casos contra lo esperado
python3 pruebas.py --regresion                       # + comparación completa contra casos/golden/
python3 pruebas.py --informe                         # regenera RESULTADOS_PRUEBAS.md
python3 gramatica.py                                 # PRIM, SGTE y verificación LL(1)
python3 derivacion.py                                # derivación L0→L1→L2→L3 con diagnóstico por paso
```

## Pipeline y módulos

| Etapa | Módulo | Contenido |
|---|---|---|
| 1. Formato | `lector.py` | `SESION Sxx` / `n ROL: texto` / `FIN`; rechaza el turno inválido y **resincroniza en la línea siguiente**; rechaza ids de sesión repetidos; normaliza a NFC y tolera BOM |
| 2. Léxico | `lexico.py`, `vocabulario.json` | ER → AFN → AFD; lexema más largo + prioridad; posiciones (sesión, turno, desplazamiento); normalización; `TK-` + 3 a 6 dígitos |
| 3. Corrector | `corrector.py` | Levenshtein ≤ 1; corrige solo con candidato **único**; empate → se conserva y se registra |
| 4. Parser | `gramatica.py`, `sintaxis.py` | BNF LL(1) (PRIM/SGTE calculados); parser predictivo guiado por la tabla; recuperación en modo pánico con SGTE |
| 5. Semántica | `semantica.py` | reglas por producción; aspecto, valoración, declaración; estado y precedencia |
| 6. Símbolos | `simbolos.py` | tabla por sesión (SESION, PARTICIPANTE, TICKET), apariciones, control de duplicados, actualización; separada del diccionario |
| 7. Salida | `analizador.py`, `main.py` | JSON por lote + vista legible + traza |

Documentación: `INFORME_lexico.md` (léxico y AFD de TICKET), `GRAMATICA.md` (BNF, PRIM/SGTE, parser y recuperación),
`REGLAS_SEMANTICAS.md` (cuadros BNF | reglas semánticas, atributos, estado y árboles anotados), `DERIVACION.md`
(pasos de la gramática original a la LL(1)), `RESULTADOS_PRUEBAS.md` (esperado vs obtenido por caso).

## Decisiones de diseño (para la defensa)

1. **Léxico y sintaxis separados**: el lexer no ve contexto. `agente` es siempre `AGENTE`; el parser lo usa como rol o como sujeto («el agente fue amable»).
2. **Alcance de la negación = estructura de la gramática**: `NEG` solo aparece dentro de `pred_neg` / `seg`; no cruza `PERO` ni `COMA`. Cada cláusula es una derivación independiente.
3. **MIXTA no es promedio**: hay evidencia POSITIVA y NEGATIVA del mismo aspecto; se conservan ambas evidencias.
4. **«Ahora funciona» es evidencia POSITIVA del SERVICIO** (el caso 03 exige MIXTA con «se corta»).
5. **Opiniones del AGENTE**: se conservan con su autoría (`opiniones_agente`); no entran al resumen del CLIENTE ni al estado.
6. **Estado**: la última declaración explícita del CLIENTE sobre el funcionamiento prevalece sobre las promesas del agente (`R-EST-PREC`).
   - `OK` → RESUELTO · `FALLA` → NO_RESUELTO · `OK` y `RECUR` en el mismo turno, o `RECUR` tras una recuperación → TEMPORAL.
   - Sin declaración del cliente: compromiso del agente → PENDIENTE; si no, NO_CONFIRMADO.
   - «El servicio está lento» (valoración sin declaración de funcionamiento) **no** fija estado.
7. **Abstención**: palabras fuera del vocabulario, empates de Levenshtein, tickets mal formados y fragmentos que el parser no reconoce se marcan `NO_INTERPRETADO`; nunca se inventa una valoración.
8. **Corrección**: solo sobre `PALABRA`, con longitud mínima 4 (`MIN_LONG`) para no convertir «mas» en «mal».
9. **Análisis PARCIAL** = hubo un turno rechazado por formato o falta `FIN`. Los fragmentos NO_INTERPRETADO no vuelven parcial una sesión.
10. **Orden de turnos**: un turno fuera de orden se rechaza; el siguiente se acepta si es el número esperado o el consecutivo del último leído (en «1, 3, 4» solo se rechaza el 3, sin rechazo en cascada).
11. **Id de sesión repetido** en un lote: la segunda sesión se descarta completa (`SESION_DUPLICADA`), porque compartiría el ámbito de la tabla de símbolos con la primera.

## Dónde tocar en una modificación de reglas (defensa)

| Cambio pedido | Dónde |
|---|---|
| nuevo sinónimo o adjetivo | `vocabulario.json` (una línea) |
| qué significa «sigue + adjetivo» | `semantica.py`, regla `seg → modif` |
| alcance o efecto de la negación | `semantica.py`, reglas `pred_s/pred_l → NEG pred_neg` |
| criterio de estado | `semantica.py`, `decidir_estado` |
| promesa del agente posterior a una falla | interruptor `PROMESA_POSTERIOR_A_FALLA_ES_PENDIENTE` |
| distancia o longitud mínima de corrección | `corrector.py` (`MIN_LONG`, `== 1`) |
| nueva construcción lingüística | `gramatica.py` + regla en `semantica.py`; luego `python3 gramatica.py` debe seguir sin conflictos |

Tras cualquier cambio: `python3 pruebas.py --regresion`. Una mutación (p. ej. MIXTA promediada a POSITIVA) hace fallar los casos 01, 03, 07, 10, 13 y 14.

## Casos

| Caso | Origen | Qué prueba |
|---|---|---|
| 01–08 | enunciado | resuelto, contraste, temporal, claridad, corrección + ticket, pendiente, rol inválido, empate |
| 09 | propio | negación + contraste |
| 10 | propio | corrección única + precedencia cliente/agente |
| 11 | propio | abstención (fuera de la gramática) |
| 12 | propio | recuperación: orden inconsistente, rol inválido, ticket mal formado, sesión siguiente intacta |
| 13 | propio | sujeto explícito con «sigue» y «se corta» («El internet sigue lento») → TEMPORAL |
| 14 | propio | recuperación de formato: salto de número sin rechazo en cascada; id de sesión repetido |

## Límites conocidos

- Vocabulario acotado al dominio del enunciado; una palabra desconocida se descarta y el resto de la cláusula se interpreta igual.
- Las oraciones se separan con `.`; sin punto, la segunda oración se descarta como fuera de la gramática (necesario para mantener LL(1)).
- La verificación de equivalencia de gramáticas (`derivacion.py`) es acotada (hasta 5 tokens), no una demostración.
- Una cláusula con un error sintáctico en su interior no se interpreta (p. ej. «No funciona el internet», con el sujeto después del verbo): se prefiere la abstención a una valoración dudosa.
- Pendiente de la entrega: informe técnico unificado y la declaración de IA/contribuciones (abajo).

## Declaración de herramientas de IA y contribuciones (COMPLETAR por el grupo)

- Herramienta de IA utilizada: Claude (Anthropic), para diseño de arquitectura, generación de código y documentación, aplicando los algoritmos de clase (ER→AFN→AFD, PRIM/SGTE, Levenshtein).
- Bibliotecas: solo la biblioteca estándar de Python (`json`, `dataclasses`, `unicodedata`, `argparse`).
- Contribuciones de cada integrante: _completar_.
