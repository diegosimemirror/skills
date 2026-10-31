# Skills de Claude Code para limpiar, graficar y mapear la ENAHO

Tres skills de Claude Code que convierten los microdatos de la ENAHO 2024 (INEI) en una base de personas
validada contra la pobreza oficial, y producen gráficos y un mapa con reglas fijas.
Sesión 16 del curso Data Science con Python (d2cml).

| Skill | Insumo | Resultado |
| --- | --- | --- |
| `limpiando-enaho` | `datos/966-Modulo34.zip` y `datos/966-Modulo02.zip` | `salidas/personas_2024.parquet` y `salidas/validacion.txt` |
| `graficando-enaho` | Base limpia + variable (`area`, `sexo`, `grupo_edad`, `departamento`) | `figuras/pobreza_por_<variable>.png` |
| `mapeando-enaho` | Base limpia + `datos/peru_departamental_simple.geojson` | `mapas/pobreza_departamento.png` |

`graficando-enaho` y `mapeando-enaho` usan primero `limpiando-enaho` si la base limpia no existe,
así que un solo pedido («haz un mapa de la pobreza») activa dos skills seguidas.

## Cómo reproducirlo

Requisitos: [uv](https://docs.astral.sh/uv/) y [Claude Code](https://code.claude.com).

```bash
git clone https://github.com/diegosimemirror/skills.git
cd skills
uv sync                      # instala pandas, pyarrow, geopandas y matplotlib

# Datos (no se suben al repositorio)
mkdir datos
curl -L -o datos/966-Modulo34.zip https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo34.zip
curl -L -o datos/966-Modulo02.zip https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo02.zip
curl -L -o datos/peru_departamental_simple.geojson https://raw.githubusercontent.com/d2cml-ai/Data-Science-Python/main/sessions/06-geoespacial/lab/Data/peru_departamental_simple.geojson
```

Con Claude Code abierto en la carpeta del repositorio:

- `/limpiando-enaho 2024` llama a la skill a mano.
- «¿Cuál fue la pobreza en Cusco en 2024?» la activa sola.
- «Haz un mapa de la pobreza por departamento con la ENAHO 2024» activa `mapeando-enaho` (y `limpiando-enaho` si hace falta).

Sin Claude, los scripts se corren así:

```bash
uv run .claude/skills/limpiando-enaho/scripts/limpiar.py --anio 2024
uv run .claude/skills/graficando-enaho/scripts/graficar.py --por area
uv run .claude/skills/mapeando-enaho/scripts/mapear.py
```

## Validación

Resultado de `limpiar.py` (ver `salidas/validacion.txt`):

| Indicador | Esta base | INEI |
| --- | --- | --- |
| Residentes habituales | 108,664 | 108,664 |
| Pobreza monetaria | 27.53 % | 27.6 % |
| Pobreza extrema | 5.50 % | 5.5 % |

El mapa también se valida: los 25 departamentos tienen dato, y Cajamarca (45.0 %), Loreto, Puno, Ica (5.9 %),
Moquegua y Madre de Dios quedan a menos de 1 punto de las cifras de referencia de la clase.

## Decisiones de limpieza

| Decisión | Registros afectados | Por qué |
| --- | --- | --- |
| Solo residentes habituales: (p204 = 1 y p205 = 2) o (p204 = 2 y p206 = 1) | Se excluyen 9,057 de 117,721 (1,787 miembros ausentes 30 días o más, 3,304 no miembros no presentes y 3,966 registros vacíos con p203 = 0) | Definición del INEI para medir pobreza |
| Llaves y ubigeo como texto | Todas | Conservar ceros a la izquierda («010101») |
| «aÑo» → `anio` | 1 columna | La eñe llega mal codificada |
| `estrato` y `dominio` se toman de la sumaria | 2 columnas | Están en los dos módulos; evita columnas duplicadas `_x`, `_y` |
| Unión personas → hogar con `validate="m:1"` | 108,664 personas, ninguna sin hogar | Falla en vez de duplicar filas |
| Toda cifra se pondera con `facpob07` | — | 108,664 encuestados representan 34.15 millones de personas |

## Evaluación

Ver [evaluacion.md](evaluacion.md): tres pedidos corridos con `claude -p`, con y sin skills.

## Estructura

```
.claude/skills/
├── limpiando-enaho/   SKILL.md · reference.md · scripts/limpiar.py
├── graficando-enaho/  SKILL.md · scripts/graficar.py
└── mapeando-enaho/    SKILL.md · scripts/mapear.py
salidas/validacion.txt · figuras/ · mapas/ · evaluacion.md · pyproject.toml · uv.lock
```

`datos/` y `salidas/*.parquet` están en `.gitignore`.
