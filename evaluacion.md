# Evaluación: tres pedidos con y sin skills

## Método

- Cada pedido se corrió una vez con `claude -p` (Claude Code 2.1.316), en **una copia aislada del proyecto** que solo
  tenía `datos/` (los dos zip del INEI y el GeoJSON), sin base limpia, sin figuras y sin mapas.
- **Con skills:** `claude -p "<pedido>" --allowedTools Bash Read Write Edit Glob Grep Skill`
- **Sin skills:** `claude -p "<pedido>" --allowedTools Bash Read Write Edit Glob Grep --disallowedTools Skill`.
  Además se borró `.claude/skills/` de la copia, para que Claude no leyera los scripts por su cuenta.
- Las skills activadas se leyeron del registro de herramientas (`--output-format stream-json`).

## Resultados

| Pedido | Modo | Skills que se activaron | Cifra | ¿Ponderó? | Figura | Tiempo · costo |
| --- | --- | --- | --- | --- | --- | --- |
| ¿Cuál fue la pobreza en Cusco en 2024? | Con | limpiando-enaho | **18.5 %** (referencia 18.5 %) | Sí, facpob07 | — | 104 s · US$ 0.59 |
| | Sin | ninguna | Ninguna: intentó buscar en la web, no miró `datos/` y pidió más datos | — | — | 23 s · US$ 0.20 |
| Grafica la pobreza urbana y rural | Con | graficando-enaho **+ limpiando-enaho** | Rural **39.4 %** · Urbano **24.7 %** (referencia 39.3 / 24.8) | Sí, facpob07 | `figuras/pobreza_por_area.png`: barras desde cero, un color, valores escritos, fuente | 59 s · US$ 0.45 |
| | Sin | ninguna | Ninguna: exploró y se detuvo a pedir 4 confirmaciones | Lo planeó (factor07 × mieperho) | No hizo el gráfico | 164 s · US$ 0.77 |
| Haz un mapa de la pobreza por departamento con la ENAHO 2024 | Con | mapeando-enaho **+ limpiando-enaho** | Cajamarca **45.0 %** · Ica **5.9 %** (referencia 45.0 / 6.0); 25 con dato | Sí, facpob07 | `mapas/pobreza_departamento.png`: un color, de claro a oscuro desde 0 | 52 s · US$ 0.48 |
| | Sin | ninguna | Solo el total nacional preliminar (27.58 %); se detuvo a pedir 4 confirmaciones | Lo planeó (factor07 × mieperho) | No hizo el mapa | 245 s · US$ 1.14 |

## Lo que muestra

1. **Las tres skills se activaron solas**, sin escribir `/`, y los pedidos 2 y 3 **encadenaron dos skills**:
   como no existía la base limpia, Claude usó primero `limpiando-enaho`.
2. **Con skills, las cifras coinciden con las de referencia** (diferencias de 0.1 puntos o menos) y la validación
   se leyó antes de responder.
3. **Sin skills, Claude no entregó ningún resultado.** Las corridas 2 y 3 sí razonaron bien la metodología (ponderar
   con factor07 × mieperho, urbano = estratos 1 a 5), pero se detuvieron a pedir confirmaciones y tardaron entre 3 y 5 veces más.
   La corrida 1 ni siquiera encontró los datos locales.
4. **Las skills fijan decisiones que sin ellas quedan abiertas.** Sin skills, Claude propuso calcular con la sumaria
   (hogares) y descartó el módulo de personas, propuso resaltar una barra en otro color y preguntó si agregar márgenes de
   error. Con skills, estas decisiones ya están tomadas y son las mismas en cada corrida.

## Limitaciones

- Es una sola corrida por pedido; no mide la variación entre corridas.
- Las corridas usan las instrucciones globales del usuario (`CLAUDE.md`), que piden explorar y confirmar antes de
  programar. Eso explica en parte por qué las corridas sin skills se detuvieron: la skill convierte ese flujo general
  en un procedimiento fijo y ya validado.
- Las cifras de referencia de la clase se calcularon con la sumaria (factor07 × mieperho). La base de personas usa
  facpob07, por eso hay diferencias de algunas décimas.
