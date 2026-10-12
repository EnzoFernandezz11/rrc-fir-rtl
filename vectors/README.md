# Vectores de prueba (A05)

Generados por [`model/vectors.py`](../model/vectors.py) desde los modelos fijos de A04 ([formatos](../docs/contratos/senales-y-formatos.md#formatos-de-punto-fijo-a04)). **No editar a mano:** regenerar con `python3 -m model.vectors`. `tests/test_vectors.py` falla si algún archivo no coincide con el generador. Se versionan solo los casos smoke; la regresión QPSK, más grande, se genera en `build/vectors/` con el mismo comando.

## Formato

Un archivo de texto por caso, una línea por muestra de entrada, enteros decimales con signo separados por un espacio:

```text
n last x_i x_q yt_i yt_q yf_i yf_q
```

| Columna | Significado | Formato |
|---|---|---|
| `n` | Índice de la muestra en el archivo, desde 0. | — |
| `last` | 1 en la última muestra de cada trama. Cada trama empieza con historial cero. | 1 bit |
| `x_i`, `x_q` | Entrada I/Q: `in_i`, `in_q`, `in_last = last`. | Q2.0, {−1, 0, +1} |
| `yt_i`, `yt_q` | Salida esperada de la rama **temporal** para la muestra `n`. | Q2.7, 9 bits |
| `yf_i`, `yf_q` | Salida esperada de la rama **en frecuencia** para la muestra `n`. | Q2.7, 9 bits |

Cada RTL se compara **palabra por palabra** con su columna (`yt` o `yf`), por índice de resultado aceptado y no por ciclo. `out_last` debe coincidir con `last`. Entre ramas, las columnas difieren como máximo en 2 LSB.

## Casos

| Archivo | Tramas | Muestras | Qué prueba |
|---|---:|---:|---|
| `impulso.txt` | 1 | 32 | x[0] = 1 − j: devuelve los coeficientes `h_q` con signo opuesto en Q. |
| `ceros.txt` | 1 | 32 | Salida nula. |
| `extremos_tiempo.txt` | 1 | 16 | Salida temporal en +Σ\|h_q\| y −Σ\|h_q\| (±234). |
| `extremos_frecuencia.txt` | 9 | 144 | Por cada etapa del motor de C01, la ventana QPSK que lleva `work` a su máximo; es la segunda ventana de cada trama de 16. |
| `bordes.txt` | 19 | 202 | Tramas de 1 a 17, 24 y 25 muestras: parciales, bloque justo, fronteras 8/16/24 y reinicio de historial entre tramas. |
| `build/vectors/qpsk_s1.txt` | 1 | 2048 | QPSK 2×, semilla 1, 1024 símbolos. Regresión, SQNR y actividad SAIF para potencia (D06). Generado, no versionado. |

**Smoke:** los cinco archivos de `vectors/` (426 muestras). **Regresión:** además `build/vectors/qpsk_s1.txt`.

## Lectores

Python: `read(path)` de `model/vectors.py` devuelve un diccionario de columnas.

SystemVerilog (probado con `iverilog -g2012`): `%d` conserva el signo al asignar a señales `signed`.

```systemverilog
integer fd, code, n, last, x_i, x_q, yt_i, yt_q, yf_i, yf_q;
fd = $fopen("vectors/bordes.txt", "r");
if (fd == 0) $fatal(1, "no se pudo abrir vectors/bordes.txt");
while (!$feof(fd)) begin
  code = $fscanf(fd, "%d %d %d %d %d %d %d %d\n", n, last, x_i, x_q, yt_i, yt_q, yf_i, yf_q);
  if (code == 8) begin
    // in_i = x_i; in_q = x_q; in_last = last;  (logic signed [1:0])
    // guardar yt_* o yf_* en la cola de esperados (logic signed [8:0])
  end
end
$fclose(fd);
```

Las rutas son relativas a la raíz del repo, que es el directorio desde donde la CI corre `vvp`.
