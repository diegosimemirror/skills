# Referencia de la ENAHO para limpiando-enaho

Léelo solo cuando el pedido necesite algo que no está en salidas/personas_<año>.parquet.

## Fuente

- Encuesta Nacional de Hogares (ENAHO), INEI. Portal: proyectos.inei.gob.pe/microdatos
- Código del año en el portal: 966 = 2024. Descarga: `proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo34.zip` (y `966-Modulo02.zip`)
- Cada zip trae `Diccionario2024.pdf` y la ficha técnica.

## Módulos que usa la skill

| Módulo | Archivo dentro del zip | Una fila por | Filas 2024 | Llaves | Factor |
| --- | --- | --- | --- | --- | --- |
| 34 · Sumaria | `966-Modulo34/sumaria-2024.dta` | hogar | 33,691 | conglome, vivienda, hogar | factor07 |
| 02 · Miembros | `966-Modulo02/enaho01-2024-200.dta` | persona | 117,721 | las tres + codperso | facpob07 |

El zip 34 trae también `sumaria-2024-12g.dta` (gasto en 12 grupos); la skill usa `sumaria-2024.dta`.

## Variables de la base limpia

| Variable | Qué es | Valores |
| --- | --- | --- |
| conglome, vivienda, hogar, codperso | Llave de la persona | Texto con ceros a la izquierda |
| ubigeo | Distrito | Texto de 6 dígitos («010101») |
| departamento | ubigeo[:2] | «01» Amazonas … «25» Ucayali; Lima 15 y Callao 07 separados |
| estrato | Estrato geográfico | 1 a 5 urbano, 6 a 8 rural |
| urbano / area | Área de residencia | True/False · «Urbano»/«Rural» |
| p203 | Parentesco con el jefe del hogar | Código del diccionario |
| sexo (p207) | Sexo | «Hombre» (1), «Mujer» (2) |
| edad (p208a) | Edad en años | 0 a 98 |
| pobreza | Condición de pobreza del hogar | 1 pobre extremo, 2 pobre no extremo, 3 no pobre |
| pobre / pobre_extremo | pobreza ≤ 2 / pobreza = 1 | True/False |
| mieperho | Total de miembros del hogar | Número |
| factor07 | Factor de expansión del hogar | Hogares que representa la fila |
| facpob07 | Factor de expansión de la persona | Personas que representa la fila; **úsalo para toda cifra de personas** |

## Otras variables de la sumaria (no están en la base; agrégalas en el Proceso 4 de limpiar.py)

| Variable | Etiqueta del INEI |
| --- | --- |
| gashog2d | Gasto total bruto del hogar (anual) |
| inghog1d / inghog2d | Ingreso bruto / ingreso neto total del hogar (anual) |
| linea / linpe | Línea de pobreza total / alimentaria |
| totmieho | Total de personas en el hogar |
| percepho | Total de perceptores de ingresos |
| pobrezav | Pobreza y vulnerabilidad con línea corriente |

## Definiciones fijas

- **Residente habitual:** (p204 = 1 y p205 = 2) o (p204 = 2 y p206 = 1). Excluye a 9,057 de 117,721 filas en 2024:
  1,787 miembros ausentes 30 días o más, 3,304 no miembros que no estuvieron presentes y 3,966 registros vacíos (p203 = 0).
- **Pobreza oficial 2024:** 27.6 % (27.53 % con la base de personas y facpob07; 27.58 % con la sumaria y factor07 × mieperho). Pobreza extrema: 5.5 %.

## Seis trampas

1. Ceros a la izquierda: conglome «015009», ubigeo «010101». Como número, la unión falla.
2. La columna del año llega como «aÑo»: se normaliza a `anio`.
3. No todos son residentes: filtrar antes de calcular.
4. Uniones que duplican: usar `validate="m:1"`.
5. Encuestas no son personas: 33,691 hogares representan unos 34.5 millones de personas con su factor.
6. `pobreza` es un código, no un número: pobre es `pobreza <= 2`, nunca un promedio.
7. Extra: miembros y sumaria tienen las dos `estrato` y `dominio`; se toman de la sumaria.
