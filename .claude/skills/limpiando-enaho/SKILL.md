---
name: limpiando-enaho
description: Limpia los módulos 34 (sumaria) y 02 (miembros) de la ENAHO del INEI y arma una base de personas residentes con pobreza monetaria y factor de expansión, validada contra la cifra oficial. Úsala cuando pidan limpiar, unir o analizar la ENAHO, o calcular pobreza por departamento, región, área, sexo o edad.
argument-hint: [año]
allowed-tools: Bash(uv run *)
---
# Limpiar la ENAHO

Año pedido: $ARGUMENTS (si está vacío, usa 2024).

1. Si faltan los zip en datos/, pide al usuario bajarlos del INEI (código 966 = 2024).
2. Corre exactamente: `uv run ${CLAUDE_SKILL_DIR}/scripts/limpiar.py --anio <año>`
3. Lee salidas/validacion.txt. Si alguna línea dice FALLA, detente y muéstrala; no respondas con esa base.
4. Responde con salidas/personas_<año>.parquet. Toda cifra va ponderada con facpob07,
   y "pobre" es la columna `pobre` (True/False): nunca promedies el código `pobreza`.
5. Si piden una variable que no está en la base, lee reference.md; si tampoco está ahí,
   dilo y propone agregarla en limpiar.py.
