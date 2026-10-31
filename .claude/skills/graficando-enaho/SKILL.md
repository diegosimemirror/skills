---
name: graficando-enaho
description: Grafica la pobreza monetaria de la ENAHO del INEI por área (urbana o rural), sexo, grupo de edad o departamento, con barras ponderadas y reglas fijas de diseño. Úsala cuando pidan un gráfico, una figura o una comparación visual de la pobreza con la ENAHO.
argument-hint: [area|sexo|grupo_edad|departamento]
allowed-tools: Bash(uv run *)
---
# Graficar la ENAHO

Variable pedida: $ARGUMENTS (si está vacía, elige la que responde la pregunta: area, sexo, grupo_edad o departamento).

1. Si no existe salidas/personas_2024.parquet, usa primero la skill limpiando-enaho.
2. Corre exactamente: `uv run ${CLAUDE_SKILL_DIR}/scripts/graficar.py --por <variable>`
3. Muestra la tabla que imprime el script y la ruta del PNG en figuras/.

## Reglas fijas (ya están en el script; no las cambies)

- Pondera siempre con facpob07.
- Barras que empiezan en cero, ordenadas.
- Un solo color; el valor escrito en cada barra.
- El título dice qué y cuándo.
- Nota al pie: «Fuente: INEI, ENAHO 2024».
- PNG a 200 dpi en figuras/.

Si piden un gráfico que el script no hace, adáptalo respetando estas reglas y explica qué cambiaste.
