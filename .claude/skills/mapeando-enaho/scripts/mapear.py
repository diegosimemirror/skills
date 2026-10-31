# ============================================================
# mapear.py — Mapa de la pobreza monetaria por departamento (ENAHO)
# Insumo:    salidas/personas_<año>.parquet y datos/peru_departamental_simple.geojson
# Resultado: mapas/pobreza_departamento.png y la validación en pantalla
# Uso:       uv run .claude/skills/mapeando-enaho/scripts/mapear.py
# ============================================================

# --- Paquetes ---
# Instalar (una sola vez por computadora): uv add pandas pyarrow geopandas matplotlib
# argparse: lee las opciones que se escriben al correr el script (--anio)
import argparse
# math: redondea hacia arriba el máximo de la escala de colores
import math
# sys: detiene el script con un mensaje si falta un archivo o falla la validación
import sys
# pathlib: arma rutas de carpetas que funcionan en Windows y en Mac
from pathlib import Path

# geopandas: tablas con una columna de formas (los límites de cada departamento)
import geopandas as gpd
# matplotlib: dibuja el mapa; "Agg" lo guarda directo en un archivo, sin abrir ventanas
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
# pandas: lee la base limpia y calcula la pobreza por departamento
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

# --- Reglas fijas ---
URL_GEOJSON = (
    "https://raw.githubusercontent.com/d2cml-ai/Data-Science-Python/main/"
    "sessions/06-geoespacial/lab/Data/peru_departamental_simple.geojson"
)
# Cifras de referencia de la clase (calculadas con la sumaria); se aceptan diferencias de hasta 1 punto
REFERENCIAS = {2024: {"06": 45.0, "16": 43.0, "21": 39.9, "11": 6.0, "18": 11.0, "17": 11.1}}
TOLERANCIA = 1.0
DEPARTAMENTOS = {
    "01": "Amazonas", "02": "Áncash", "03": "Apurímac", "04": "Arequipa", "05": "Ayacucho",
    "06": "Cajamarca", "07": "Callao", "08": "Cusco", "09": "Huancavelica", "10": "Huánuco",
    "11": "Ica", "12": "Junín", "13": "La Libertad", "14": "Lambayeque", "15": "Lima",
    "16": "Loreto", "17": "Madre de Dios", "18": "Moquegua", "19": "Pasco", "20": "Piura",
    "21": "Puno", "22": "San Martín", "23": "Tacna", "24": "Tumbes", "25": "Ucayali",
}


def main():
    opciones = argparse.ArgumentParser(description="Mapa de la pobreza monetaria por departamento")
    opciones.add_argument("--anio", type=int, default=2024)
    opciones.add_argument("--geojson", default="datos/peru_departamental_simple.geojson")
    opciones.add_argument("--salida", default="mapas")
    args = opciones.parse_args()

    # ============================================================
    # PROCESO 1: Leer la base limpia y los límites departamentales
    # Insumo:    parquet de personas y GeoJSON
    # Resultado: personas (tabla) y limites (25 formas con su código FIRST_IDDP)
    # ============================================================
    ruta_base = Path(f"salidas/personas_{args.anio}.parquet")
    if not ruta_base.exists():
        sys.exit(f"Falta {ruta_base}. Usa primero la skill limpiando-enaho.")
    if not Path(args.geojson).exists():
        sys.exit(f"Falta {args.geojson}. Bájalo de {URL_GEOJSON}")
    personas = pd.read_parquet(ruta_base)
    limites = gpd.read_file(args.geojson)

    # ============================================================
    # PROCESO 2: Calcular la pobreza ponderada por departamento
    # Insumo:    personas
    # Resultado: pobreza (una fila por código de departamento)
    # ============================================================
    # Ponderar: suma de facpob07 de los pobres / suma de facpob07 (como SUMAPRODUCTO / SUMA)
    personas["peso_pobre"] = personas["facpob07"] * personas["pobre"]
    sumas = personas.groupby("departamento")[["peso_pobre", "facpob07"]].sum()
    #   Antes: una fila por persona | Después: 25 filas, una por departamento
    pobreza = (100 * sumas["peso_pobre"] / sumas["facpob07"]).rename("pobreza").reset_index()

    # ============================================================
    # PROCESO 3: Unir la pobreza a los límites POR CÓDIGO, nunca por nombre
    # Insumo:    limites (FIRST_IDDP «01») y pobreza (departamento «01»)
    # Resultado: mapa_datos (25 formas con su pobreza)
    # ============================================================
    # validate="1:1": cada departamento aparece una sola vez en cada tabla; si no, falla
    # how="left": conserva los 25 límites aunque alguno no tenga dato (para detectarlo)
    mapa_datos = limites.merge(pobreza, left_on="FIRST_IDDP", right_on="departamento", how="left", validate="1:1")

    # ============================================================
    # PROCESO 4: Validar antes de dibujar
    # Insumo:    mapa_datos
    # Resultado: lista de verificaciones (OK o FALLA)
    # ============================================================
    sin_dato = mapa_datos.loc[mapa_datos["pobreza"].isna(), "NOMBDEP"].tolist()
    verificaciones = [
        ("Hay 25 departamentos en el mapa", len(mapa_datos) == 25),
        (f"Todos tienen dato (sin dato: {sin_dato or 'ninguno'})", not sin_dato),
        ("Lima (15) y Callao (07) van separados", {"15", "07"} <= set(mapa_datos["departamento"].dropna())),
    ]
    valores = mapa_datos.set_index("FIRST_IDDP")["pobreza"]
    for codigo, referencia in REFERENCIAS.get(args.anio, {}).items():
        valor = valores.get(codigo)
        verificaciones.append((
            f"{DEPARTAMENTOS[codigo]}: {valor:.1f} % (referencia {referencia} %)",
            valor is not None and abs(valor - referencia) <= TOLERANCIA,
        ))
    for texto, ok in verificaciones:
        print(f"[{'OK' if ok else 'FALLA'}] {texto}")
    if not all(ok for _, ok in verificaciones):
        sys.exit("RESULTADO: no se dibuja el mapa; revisar las FALLAS")

    # ============================================================
    # PROCESO 5: Dibujar y guardar el mapa
    # Insumo:    mapa_datos validado
    # Resultado: mapas/pobreza_departamento.png
    # ============================================================
    # Mapa coroplético: cada departamento se pinta según su valor, en un solo color de claro a oscuro desde 0
    maximo = math.ceil(mapa_datos["pobreza"].max() / 10) * 10
    figura, eje = plt.subplots(figsize=(7, 9))
    mapa_datos.plot(
        column="pobreza", cmap="Blues", vmin=0, vmax=maximo, edgecolor="white", linewidth=0.6, ax=eje,
        legend=True, legend_kwds={"label": "% de personas en pobreza monetaria", "shrink": 0.5},
    )
    eje.set_axis_off()
    eje.set_title(f"Pobreza monetaria por departamento, Perú {args.anio}", loc="left", fontsize=13, fontweight="bold")
    figura.text(0.02, 0.02, f"Fuente: INEI, ENAHO {args.anio}. Ponderado con facpob07.", fontsize=8, color="#6B645A")

    carpeta = Path(args.salida)
    carpeta.mkdir(exist_ok=True)
    ruta_png = carpeta / "pobreza_departamento.png"
    figura.savefig(ruta_png, dpi=200, bbox_inches="tight")

    ordenado = mapa_datos.sort_values("pobreza", ascending=False)
    nombres = ordenado["FIRST_IDDP"].map(DEPARTAMENTOS)
    print("Más pobreza:", " · ".join(f"{n} {v:.1f} %" for n, v in zip(nombres[:3], ordenado["pobreza"][:3])))
    print("Menos pobreza:", " · ".join(f"{n} {v:.1f} %" for n, v in zip(nombres[-3:], ordenado["pobreza"][-3:])))
    print(f"Guardado: {ruta_png}")


if __name__ == "__main__":
    main()
