---
name: mapeando-enaho
description: Hace mapas de la pobreza monetaria de la ENAHO del INEI por departamento del Perú, uniendo por código de ubigeo con los límites departamentales. Úsala cuando pidan un mapa, la distribución territorial o una comparación de la pobreza entre departamentos o regiones.
allowed-tools: Bash(uv run *)
---
# Mapear la ENAHO

1. Si no existe salidas/personas_2024.parquet, usa primero la skill limpiando-enaho.
2. Si no existe datos/peru_departamental_simple.geojson, bájalo de
   https://raw.githubusercontent.com/d2cml-ai/Data-Science-Python/main/sessions/06-geoespacial/lab/Data/peru_departamental_simple.geojson
3. Corre exactamente: `uv run ${CLAUDE_SKILL_DIR}/scripts/mapear.py`
4. Si el script imprime alguna FALLA, detente y explícala; no muestres ni describas un mapa.
5. Responde con los tres departamentos con más y con menos pobreza y la ruta mapas/pobreza_departamento.png.

## Reglas fijas (ya están en el script; no las cambies)

- Une por código: ubigeo[:2] con FIRST_IDDP. Nunca por nombre: «APURIMAC» no es «Apurímac».
- Exige los 25 departamentos y ninguno sin dato.
- Un solo color, de claro a oscuro, desde 0; nunca arcoíris.
- Leyenda con la unidad: % de personas.
- Lima (15) y Callao (07) van separados.
