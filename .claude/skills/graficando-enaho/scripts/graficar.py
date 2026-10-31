# ============================================================
# graficar.py — Gráfico de barras de la pobreza monetaria (ENAHO)
# Insumo:    salidas/personas_<año>.parquet (lo crea la skill limpiando-enaho)
# Resultado: figuras/pobreza_por_<variable>.png y la tabla de cifras en pantalla
# Uso:       uv run .claude/skills/graficando-enaho/scripts/graficar.py --por area
# ============================================================

# --- Paquetes ---
# Instalar (una sola vez por computadora): uv add pandas pyarrow matplotlib
# argparse: lee las opciones que se escriben al correr el script (--por, --anio)
import argparse
# sys: detiene el script con un mensaje si falta la base
import sys
# pathlib: arma rutas de carpetas que funcionan en Windows y en Mac
from pathlib import Path

# matplotlib: dibuja el gráfico; "Agg" lo guarda directo en un archivo, sin abrir ventanas
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
# pandas: lee la base limpia y calcula la pobreza por grupo
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

# --- Reglas fijas de diseño: no se discuten en cada pedido ---
COLOR = "#2E5E7E"        # un solo color para todas las barras
COLOR_TEXTO = "#3E3A34"
DPI = 200
TITULOS = {"area": "área de residencia", "sexo": "sexo", "grupo_edad": "grupo de edad", "departamento": "departamento"}
DEPARTAMENTOS = {
    "01": "Amazonas", "02": "Áncash", "03": "Apurímac", "04": "Arequipa", "05": "Ayacucho",
    "06": "Cajamarca", "07": "Callao", "08": "Cusco", "09": "Huancavelica", "10": "Huánuco",
    "11": "Ica", "12": "Junín", "13": "La Libertad", "14": "Lambayeque", "15": "Lima",
    "16": "Loreto", "17": "Madre de Dios", "18": "Moquegua", "19": "Pasco", "20": "Piura",
    "21": "Puno", "22": "San Martín", "23": "Tacna", "24": "Tumbes", "25": "Ucayali",
}


def main():
    opciones = argparse.ArgumentParser(description="Grafica la pobreza monetaria de la ENAHO")
    opciones.add_argument("--por", choices=list(TITULOS), default="area")
    opciones.add_argument("--anio", type=int, default=2024)
    opciones.add_argument("--salida", default="figuras")
    args = opciones.parse_args()

    # ============================================================
    # PROCESO 1: Leer la base limpia
    # Insumo:    salidas/personas_<año>.parquet
    # Resultado: personas (una fila por residente habitual)
    # ============================================================
    ruta_base = Path(f"salidas/personas_{args.anio}.parquet")
    if not ruta_base.exists():
        sys.exit(f"Falta {ruta_base}. Usa primero la skill limpiando-enaho.")
    personas = pd.read_parquet(ruta_base)

    # ============================================================
    # PROCESO 2: Preparar la variable de agrupación
    # Insumo:    personas
    # Resultado: personas con la columna por la que se agrupa
    # ============================================================
    if args.por == "grupo_edad":
        # pd.cut(): convierte la edad en tramos, como agrupar edades en una tabla dinámica
        #   Antes: 0, 1, 2… 98 | Después: «0-17», «18-29»…
        personas["grupo_edad"] = pd.cut(
            personas["edad"], bins=[-1, 17, 29, 44, 59, 200], labels=["0-17", "18-29", "30-44", "45-59", "60 a más"]
        )
    if args.por == "departamento":
        #   Antes: código «08» | Después: nombre «Cusco»
        personas["departamento"] = personas["departamento"].map(DEPARTAMENTOS)

    # ============================================================
    # PROCESO 3: Calcular la pobreza ponderada por grupo
    # Insumo:    personas
    # Resultado: tabla con el % de personas pobres de cada grupo
    # ============================================================
    # Ponderar: suma de facpob07 de los pobres / suma de facpob07 del grupo (como SUMAPRODUCTO / SUMA)
    personas["peso_pobre"] = personas["facpob07"] * personas["pobre"]
    sumas = personas.groupby(args.por, observed=True)[["peso_pobre", "facpob07"]].sum()
    #   Antes: miles de filas | Después: una fila por grupo, ordenada de menor a mayor
    pobreza = (100 * sumas["peso_pobre"] / sumas["facpob07"]).sort_values()

    # ============================================================
    # PROCESO 4: Dibujar y guardar el gráfico
    # Insumo:    tabla de pobreza por grupo
    # Resultado: figuras/pobreza_por_<variable>.png
    # ============================================================
    # Barras horizontales: los nombres se leen sin girar la cabeza; la mayor queda arriba
    figura, eje = plt.subplots(figsize=(8, 0.45 * len(pobreza) + 1.8))
    eje.barh(pobreza.index.astype(str), pobreza.values, color=COLOR)
    eje.set_xlim(0, pobreza.max() * 1.15)   # el eje empieza en cero
    for posicion, valor in enumerate(pobreza.values):
        eje.text(valor + pobreza.max() * 0.01, posicion, f"{valor:.1f} %", va="center", fontsize=10, color=COLOR_TEXTO)
    # Menos ruido: sin marco ni eje x, porque cada barra ya tiene su valor escrito
    for lado in ("top", "right", "bottom"):
        eje.spines[lado].set_visible(False)
    eje.xaxis.set_visible(False)
    eje.tick_params(axis="y", length=0, labelsize=10, labelcolor=COLOR_TEXTO)
    eje.set_title(
        f"Pobreza monetaria por {TITULOS[args.por]}, Perú {args.anio}\n% de personas",
        loc="left", fontsize=13, fontweight="bold", color="#1C1A17",
    )
    figura.text(0.01, 0.01, f"Fuente: INEI, ENAHO {args.anio}. Ponderado con facpob07.", fontsize=8, color="#6B645A")
    figura.tight_layout(rect=(0, 0.04, 1, 1))

    carpeta = Path(args.salida)
    carpeta.mkdir(exist_ok=True)
    ruta_png = carpeta / f"pobreza_por_{args.por}.png"
    figura.savefig(ruta_png, dpi=DPI)

    print(f"Pobreza monetaria por {TITULOS[args.por]} (% de personas, ponderado con facpob07)")
    for grupo, valor in pobreza.sort_values(ascending=False).items():
        print(f"  {grupo}: {valor:.1f} %")
    print(f"Guardado: {ruta_png}")


if __name__ == "__main__":
    main()
