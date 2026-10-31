# ============================================================
# limpiar.py — Base de personas de la ENAHO con pobreza y factor de expansión
# Insumo:    datos/<código>-Modulo34.zip (sumaria) y datos/<código>-Modulo02.zip (miembros)
# Resultado: salidas/personas_<año>.parquet y salidas/validacion.txt
# Uso:       uv run .claude/skills/limpiando-enaho/scripts/limpiar.py --anio 2024
# ============================================================

# --- Paquetes ---
# Instalar (una sola vez por computadora): uv add pandas pyarrow
# argparse: lee las opciones que se escriben al correr el script (--anio)
import argparse
# sys: permite detener el script con un mensaje de error
import sys
# zipfile: abre los zip del INEI sin descomprimirlos en el disco
import zipfile
# pathlib: arma rutas de carpetas que funcionan en Windows y en Mac
from pathlib import Path

# pandas: trabaja con tablas (filas y columnas) como en Excel, pero con código
import pandas as pd

# La consola de Windows no muestra bien tildes ni eñes si no se le pide UTF-8
sys.stdout.reconfigure(encoding="utf-8")

# --- Constantes: decisiones fijas que no se discuten en cada pedido ---
# Código del INEI para cada año en su portal de microdatos
CODIGOS_INEI = {2024: "966"}
# Cifras oficiales contra las que se valida la base
OFICIAL = {2024: {"pobreza": 27.6, "personas": 108_664}}
# Llaves que identifican un hogar y una persona (como la columna de búsqueda de un BUSCARV)
LLAVES_HOGAR = ["conglome", "vivienda", "hogar"]
LLAVES_PERSONA = LLAVES_HOGAR + ["codperso"]


def leer_dta(ruta_zip, nombre_interno):
    """Lee un .dta que está dentro de un zip, sin descomprimirlo."""
    with zipfile.ZipFile(ruta_zip) as archivo_zip, archivo_zip.open(nombre_interno) as archivo:
        # convert_categoricals=False: conserva los códigos (1, 2, 3) en lugar de las etiquetas de texto
        return pd.read_stata(archivo, convert_categoricals=False)


def main():
    opciones = argparse.ArgumentParser(description="Limpia la ENAHO y arma una base de personas")
    opciones.add_argument("--anio", type=int, default=2024)
    opciones.add_argument("--datos", default="datos")
    opciones.add_argument("--salidas", default="salidas")
    args = opciones.parse_args()
    anio = args.anio
    if anio not in CODIGOS_INEI:
        sys.exit(f"No conozco el código del INEI para {anio}. Años disponibles: {list(CODIGOS_INEI)}")
    codigo = CODIGOS_INEI[anio]
    carpeta_datos = Path(args.datos)
    carpeta_salidas = Path(args.salidas)

    # ============================================================
    # PROCESO 1: Leer la sumaria y el módulo de miembros
    # Insumo:    los dos zip del INEI
    # Resultado: sumaria (una fila por hogar) y miembros (una fila por persona)
    # ============================================================
    zip_sumaria = carpeta_datos / f"{codigo}-Modulo34.zip"
    zip_miembros = carpeta_datos / f"{codigo}-Modulo02.zip"
    for ruta in (zip_sumaria, zip_miembros):
        if not ruta.exists():
            sys.exit(f"Falta {ruta}. Bájalo de proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/{ruta.name}")

    #   Antes: archivos .dta dentro de los zip | Después: dos tablas en memoria; las llaves llegan como texto
    sumaria = leer_dta(zip_sumaria, f"{codigo}-Modulo34/sumaria-{anio}.dta")
    miembros = leer_dta(zip_miembros, f"{codigo}-Modulo02/enaho01-{anio}-200.dta")
    print(f"Proceso 1 · sumaria {sumaria.shape} · miembros {miembros.shape}")

    # ============================================================
    # PROCESO 2: Normalizar los nombres de las columnas
    # Insumo:    tablas con nombres como «aÑo»
    # Resultado: nombres en minúscula y sin eñe («anio»)
    # ============================================================
    #   Antes: «aÑo», «AÑO» | Después: «anio»; el resto de columnas no cambia
    for tabla in (sumaria, miembros):
        tabla.columns = [c.lower().replace("ñ", "ni") for c in tabla.columns]
    # Las llaves y el ubigeo se fuerzan a texto para no perder los ceros a la izquierda («010101», no 10101)
    for tabla in (sumaria, miembros):
        for columna in LLAVES_HOGAR + ["ubigeo"]:
            tabla[columna] = tabla[columna].astype(str)
    miembros["codperso"] = miembros["codperso"].astype(str)
    print("Proceso 2 · columnas normalizadas")

    # ============================================================
    # PROCESO 3: Filtrar a los residentes habituales (definición del INEI)
    # Insumo:    miembros (todas las personas registradas)
    # Resultado: personas (solo residentes habituales)
    # ============================================================
    # Residente habitual: miembro (p204 = 1) que no estuvo ausente 30 días o más (p205 = 2),
    # o no miembro (p204 = 2) que estuvo presente 30 días o más (p206 = 1)
    es_residente = ((miembros["p204"] == 1) & (miembros["p205"] == 2)) | (
        (miembros["p204"] == 2) & (miembros["p206"] == 1)
    )
    #   Antes: todas las filas | Después: menos filas, mismas columnas
    personas = miembros.loc[es_residente].copy()
    print(f"Proceso 3 · {len(personas):,} residentes · {len(miembros) - len(personas):,} excluidos")

    # ============================================================
    # PROCESO 4: Unir cada persona con los datos de su hogar
    # Insumo:    personas y sumaria
    # Resultado: base (una fila por persona, con la pobreza de su hogar)
    # ============================================================
    columnas_hogar = LLAVES_HOGAR + ["pobreza", "mieperho", "factor07", "estrato", "dominio"]
    # merge(): como un BUSCARV de cada persona a su hogar
    # validate="m:1": muchas personas por hogar; si un hogar aparece dos veces, falla en vez de duplicar filas
    # how="left": conserva a todas las personas aunque su hogar no esté en la sumaria
    # estrato y dominio están en las dos tablas: se usan los de la sumaria para no duplicar columnas (_x, _y)
    personas = personas.drop(columns=["estrato", "dominio"], errors="ignore")
    #   Antes: personas sin pobreza | Después: mismas filas, con las columnas del hogar agregadas
    base = personas.merge(sumaria[columnas_hogar], on=LLAVES_HOGAR, how="left", validate="m:1")
    print(f"Proceso 4 · base {base.shape}")

    # ============================================================
    # PROCESO 5: Construir las variables de análisis
    # Insumo:    base unida
    # Resultado: base con departamento, área, sexo, edad y pobreza en sí / no
    # ============================================================
    #   Antes: códigos del INEI | Después: columnas nuevas, fáciles de agrupar
    base["departamento"] = base["ubigeo"].str[:2]                      # «010101» → «01» (Amazonas)
    base["urbano"] = base["estrato"].le(5)                             # estratos 1 a 5 son urbanos
    base["area"] = base["urbano"].map({True: "Urbano", False: "Rural"})
    base["sexo"] = base["p207"].map({1: "Hombre", 2: "Mujer"})
    base["edad"] = base["p208a"]
    base["pobre"] = base["pobreza"].le(2)                              # 1 extremo y 2 no extremo son pobres
    base["pobre_extremo"] = base["pobreza"].eq(1)
    columnas_finales = LLAVES_PERSONA + [
        "anio", "ubigeo", "departamento", "dominio", "estrato", "urbano", "area",
        "p203", "sexo", "edad", "pobreza", "pobre", "pobre_extremo", "mieperho", "factor07", "facpob07",
    ]
    base = base[columnas_finales]
    print("Proceso 5 · variables construidas")

    # ============================================================
    # PROCESO 6: Validar contra la cifra oficial del INEI
    # Insumo:    base final
    # Resultado: lista de verificaciones (OK o FALLA) que se escribe en validacion.txt
    # ============================================================
    # Pobreza ponderada: suma de factores de los pobres / suma de todos los factores (como SUMAPRODUCTO)
    pobreza = 100 * base.loc[base["pobre"], "facpob07"].sum() / base["facpob07"].sum()
    pobreza_extrema = 100 * base.loc[base["pobre_extremo"], "facpob07"].sum() / base["facpob07"].sum()
    oficial = OFICIAL.get(anio)
    verificaciones = [
        ("Llave de persona única", not base.duplicated(LLAVES_PERSONA).any()),
        ("La unión no perdió ni duplicó filas", len(base) == len(personas)),
        ("Todas las personas tienen pobreza de su hogar", base["pobreza"].notna().all()),
        ("Los 25 departamentos tienen datos", base["departamento"].nunique() == 25),
    ]
    if oficial:
        verificaciones += [
            (f"Residentes = {oficial['personas']:,} (INEI)", len(base) == oficial["personas"]),
            (f"Pobreza {pobreza:.2f} % ≈ {oficial['pobreza']} % (INEI, tolerancia 0.1)",
             abs(pobreza - oficial["pobreza"]) < 0.1),
        ]

    # ============================================================
    # PROCESO 7: Guardar la base y el informe de validación
    # Insumo:    base validada
    # Resultado: salidas/personas_<año>.parquet y salidas/validacion.txt
    # ============================================================
    carpeta_salidas.mkdir(exist_ok=True)
    lineas = [
        f"Validación ENAHO {anio}",
        f"Personas (residentes habituales): {len(base):,}",
        f"Personas representadas con facpob07: {base['facpob07'].sum() / 1e6:.2f} millones",
        f"Pobreza monetaria: {pobreza:.2f} %",
        f"Pobreza extrema: {pobreza_extrema:.2f} %",
        "",
    ] + [f"[{'OK' if ok else 'FALLA'}] {texto}" for texto, ok in verificaciones]
    todo_ok = all(ok for _, ok in verificaciones)
    lineas.append("")
    lineas.append("RESULTADO: base válida" if todo_ok else "RESULTADO: NO usar la base; revisar las FALLAS")
    (carpeta_salidas / "validacion.txt").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print("\n".join(lineas))

    if not todo_ok:
        sys.exit(1)
    # to_parquet(): guarda la tabla en un archivo comprimido que conserva los tipos de cada columna
    #   Antes: tabla en memoria | Después: archivo en salidas/
    base.to_parquet(carpeta_salidas / f"personas_{anio}.parquet", index=False)
    print(f"Proceso 7 · guardado salidas/personas_{anio}.parquet")


if __name__ == "__main__":
    main()
