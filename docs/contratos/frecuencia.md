# Contrato: filtro en el dominio de la frecuencia

**Estado:** Propuesto. La revisión y las condiciones de cierre se resumen al final.
**Issues:** E01, A03, C01, C02; optimización posterior en C03/C04.
**Fuente:** [consigna vigente](../consigna-actualizada.md). [Diagrama general](../frecuencia/general_diagram.md).

## Alcance y correspondencia entre filtros

Ambas implementaciones usan **los mismos ocho coeficientes RRCOS, roll-off 0,5**: convolución FIR causal en tiempo y procesamiento por FFT con superposición del 50 % en frecuencia. La consigna exige verificar la correspondencia de resultados entre ambas.

Enzo confirmó el **upsampling 2× el 7/10/2026** como decisión de diseño, aunque la consigna no especifica el factor. Un **upsampler** separado del generador prepara las mismas muestras para ambas ramas: `x[2m]=a[m]`, `x[2m+1]=0`, con símbolos QPSK de componentes `±1`. E02 fija una única tabla de coeficientes, fase y normalización compartida; el upsampling por sí solo no determina esa tabla.

Con iguales entradas, coeficientes e historial inicial, la salida por overlap-save debe coincidir con la convolución FIR temporal, alineada por índice de muestra y con el mismo recorte de cola. En flotante se admiten diferencias de redondeo; la evidencia de E01 usa error absoluto por muestra menor que `1e−10`. En punto fijo, A04 fija la tolerancia entre dominios según sus escalados y redondeos; cada RTL se contrasta además con su modelo fijo.

Enzo confirmó el 7/10/2026 los mínimos del proyecto: **SQNR ≥ 40 dB**, reloj **≥ 10 MHz en las variantes lentas** y **≥ 100 MHz en las rápidas**. Su evaluación corresponde a A04 y a las tareas de RTL/PPA.

## Decisiones confirmadas por Enzo

| Decisión | Elección | Consecuencia |
|---|---|---|
| 2 — Método | A: **overlap-save**. | Ventanas de entrada superpuestas exactamente al 50 %; sin suma de colas. |
| 3 — Transformada | **FFT16 e IFFT16**, complejas. | Ocho muestras de historial y ocho nuevas; avance `B=8`. |
| 4 — Fuente | **Generador QPSK separado y reutilizable**, con etapa de upsampling 2× separada del generador. | El generador entrega símbolos; el upsampler pertenece a la cadena del filtro y el núcleo FFT recibe muestras. |
| 5 — Coeficientes espectrales | A: **H precalculada en Python**, guardada como constantes o ROM. | No se calcula la FFT de los coeficientes durante cada bloque ni se requiere hardware para calcular H. |
| 6 — Arquitectura | **Primero simple y funcional**, un bloque a la vez. | Compartir recursos es admisible; la elección de paralelismo, pipeline y optimización PPA se desarrolla en C03/C04. |

## Módulos y responsabilidades

1. **Generador QPSK reutilizable:** produce `a[m]` con I y Q en `{-1,+1}`. No conoce FFT, historial ni coeficientes. Puede alimentar las pruebas de cualquiera de los filtros. La utilidad Python [model/stimuli.py](../../model/stimuli.py) permite generar símbolos con semilla; no fija el mapeo bits → símbolos ni implementa un generador RTL. A01/E02 completan el generador definitivo y su formato.
2. **Upsampler 2×:** transforma cada símbolo en dos muestras: `x[2m]=a[m]`, `x[2m+1]=0`. Es una etapa propia de la cadena RRC. La utilidad Python reproduce esta operación; su interfaz por ciclos se define en E03/C01.
3. **Formador de bloques:** combina ocho muestras anteriores con ocho nuevas, equivalentes a cuatro símbolos nuevos después del upsampler.
4. **Núcleo de filtrado:** FFT16 → productos espectrales → IFFT16 → selección de las últimas ocho posiciones.
5. **Control de salida:** entrega las muestras en orden, limita el último bloque a las muestras reales de la trama y reinicia el historial entre tramas independientes.

El generador es una fuente de pruebas separada: el núcleo de filtrado también puede recibir muestras desde vectores u otra fuente que respete la interfaz. Una pausa o falta de aceptación no inserta ceros: los ceros del upsampler son muestras válidas y deben distinguirse de la ausencia de datos.

## Operaciones por bloque

Sean `h[0]…h[7]` los ocho coeficientes del RRC causal. Su fase de muestreo, tabla exacta y normalización comunes a ambas ramas se fijan en E02. Para un RRC de banda base convencional los coeficientes son reales y filtran la señal compleja I/Q. Hay que generar exactamente ocho taps, sin cambiar a nueve por conveniencia de una biblioteca.

| Operación | Definición |
|---|---|
| Tabla fija | `H[k] = DFT16([h[0],…,h[7],0,0,0,0,0,0,0,0])[k]`. |
| Ventana del bloque `b` | `w_b[r] = x[8b−8+r]`, para `r=0…15`. Las entradas fuera de la trama valen cero para el cálculo. |
| Transformada de entrada | `X_b = FFT16(w_b)`. |
| Multiplicación | `Y_b[k] = X_b[k] × H[k]`, para `k=0…15`. Son 16 productos por bloque, sin exigir 16 multiplicadores físicos en la versión inicial. |
| Transformada de salida | `v_b = IFFT16(Y_b)`. |
| Selección | Descartar `v_b[0…7]`; emitir `v_b[8…15]`, o solo las primeras `p` de estas posiciones en un bloque parcial. |
| Convención | FFT con exponente negativo sin escala; IFFT con exponente positivo y escala total `1/16`. Índices externos en orden natural; cualquier reordenamiento interno debe mantener alineados `X`, `H` y la salida. |

La tabla H puede ser compleja aunque h sea real. Redondeo, anchos de H y twiddles, escalado por etapas y saturación pertenecen a A04. La cuantización puede introducir error respecto del modelo flotante; la equivalencia matemática descrita aquí supone aritmética exacta.

### Ejemplo de ventanas

```text
Bloque 0: [0  0  0  0  0  0  0  0 | a0 0 a1 0 a2 0 a3 0]
Bloque 1: [a0 0 a1 0 a2 0 a3 0 | a4 0 a5 0 a6 0 a7 0]
```

Las ocho últimas entradas de una ventana pasan a ser el historial de la siguiente. Los ceros entre símbolos son parte del sobremuestreo, no relleno de FFT. Los ocho ceros añadidos a h solo se usan al precalcular H.

### Por qué funciona con ocho coeficientes

El FIR necesita siete muestras anteriores. Para las posiciones conservadas `r=8…15` y los taps `k=0…7`, se cumple `r−k≥1`; por tanto, no hay envolvimiento circular. La salida conservada coincide con `y[n]=Σ(k=0…7) h[k] x[n−k]`.

Las posiciones `0…6` pueden estar contaminadas por circularidad. La posición 7 también es válida, pero se descarta para mantener el avance regular de ocho: corresponde a la muestra anterior al tramo nuevo, ya emitida por el bloque previo (o anterior al inicio de la trama). Guardar ocho muestras de historial, aunque basten siete, cumple exactamente el 50 %.

FFT8 con avance cuatro no ofrece el historial necesario. FFT16 es la menor potencia de dos que admite este FIR con 50 % de superposición sin particionar el filtro.

## Tramas, pausas y salidas

- Una trama de **S símbolos produce 2S muestras de entrada al núcleo y 2S salidas**. Se omite la cola posterior en ambas ramas para comparar los mismos índices.
- Cada trama independiente comienza con historial cero. El procesamiento continuo conserva el historial hasta un fin de trama explícito o reset.
- Un bloque completo reúne ocho muestras nuevas. No se cierra por una pausa: se espera a completar el bloque o recibir fin de trama.
- Tras el último símbolo se incluye su cero de upsampling. Si quedan `p<8` muestras nuevas, se agregan `8−p` ceros de relleno y se emiten solo `v_b[8]…v_b[8+p−1]`. En la cadena QPSK 2×, `p` es 2, 4 o 6; el núcleo genérico puede admitir cualquier parcial de 1 a 7.
- Trama vacía: cero salidas. Longitud múltiplo de ocho muestras: no se agrega un bloque extra. El relleno no genera salidas adicionales ni se arrastra a otra trama independiente.
- No se compensa el retardo del pulso recortando muestras iniciales. La comparación directa y la FFT usan los mismos índices causales; la fase y el retardo del RRC se documentan con sus coeficientes en E02.

## Implementación inicial y latencia esperada

La versión inicial procesa un bloque a la vez: **capturar → FFT → productos → IFFT → emitir**. El control debe poder frenar la fuente mientras procesa o entrega resultados; el generador y el upsampler conservan su estado durante esas pausas. E03/C01 fijan las señales concretas y el calendario por ciclo.

La estimación estructural de la primera salida de un bloque completo es:

```text
L_primera = C_captura8 + C_FFT16 + C_productos16 + C_IFFT16 + C_hasta_primera_salida
```

`C_captura8` incluye reunir las ocho muestras posteriores al upsampler (cuatro símbolos). Con una muestra aceptada por ciclo, la fase de captura ocupa ocho ciclos; los intervalos desde el primer flanco aceptado deben contarse en C01 para evitar ambigüedad de un ciclo. Las pausas de fuente o destino agregan espera. Un bloque parcial puede iniciar el cómputo tras el fin de trama, completando el buffer con ceros.

Si `C_bloque` es el intervalo real entre inicios de bloques completos, la tasa sostenida es `8·f_clk/C_bloque` muestras/s, equivalente a `4·f_clk/C_bloque` símbolos/s. El retardo propio del pulso RRC y la latencia de procesamiento por bloques son conceptos distintos.

Como referencia para C01, radix-2 FFT16 requiere 32 butterflies y la IFFT otros 32, más 16 productos espectrales por bloque. Esto es un conteo de operaciones, no 80 ciclos garantizados: faltan latencias aritméticas, accesos a memoria y control. C01 determina esos valores para la arquitectura simple. C03/C04 estudian paralelismo y pipeline para cumplir el requisito posterior de rendimiento.

## Evidencia reproducible

```sh
python3 -m unittest tests.test_frequency_overlap_contract -v
make smoke
```

La [prueba](../../tests/test_frequency_overlap_contract.py) compara el [modelo flotante reutilizable](../../model/frequency.py), que representa FFT16/IFFT16 mediante DFT directa de biblioteca estándar, con una suma causal independiente de ocho taps. Incluye QPSK con semilla e upsampling 2×, tramas completas y parciales, trama vacía, impulso en los límites de bloque y retardos. El modelo procesa una trama completa por llamada y no conserva estado entre llamadas; el reinicio de historial del RTL se verifica en C02. El criterio es error absoluto por muestra menor que `1e−10` y longitud exacta de salida.

Los coeficientes de prueba incluyen un RRC ilustrativo de ocho taps y una tabla asimétrica para detectar errores de orden. El RRC ilustrativo no aprueba fase ni normalización de E02. La prueba demuestra la reconstrucción por bloques, no la calidad espectral del filtro definitivo, el SQNR en punto fijo, el protocolo RTL ni PPA.

Verificación local del 7/10/2026: las cinco pruebas de E01 y las nueve pruebas totales de `make smoke` pasan. `git diff --check` no reporta errores de whitespace. No hay RTL registrado; este resultado no es vector matching de hardware.

## Preparación del cierre de E01

| Criterio local | Evidencia / destino |
|---|---|
| Transformada, bloques y superposición | FFT16/IFFT16, historial ocho y avance ocho; decisiones confirmadas por Enzo. |
| Función y módulos | RRC8, beta 0,5, 2×; generador QPSK reutilizable separado; H constante. |
| Salidas y límites de trama | Índices y conteo 2S definidos arriba. |
| Latencia esperada | Expresión estructural, condiciones de captura y tasa; calendario por ciclos en C01. |
| Evidencia reproducible | Prueba de reconstrucción contra convolución directa y `make smoke`. |
| Revisión de equipo | Julián dejó «LGTM» en la PR #28; Andrés solicitó estas correcciones. Falta registrar el acuerdo sobre la versión corregida, conforme al [flujo de contratos](README.md). |
| Upsampling | 2× confirmado por Enzo el 7/10/2026; nombre del módulo: upsampler. Revisión conjunta del contrato pendiente. |
| Dependencia E00 y cierre en GitHub | E00 debe estar cerrada y debe vincularse el PR con evidencia o decisión revisada según E01. |

La tabla exacta de taps y el mapeo de bits pertenecen a E02/A01; anchos y SQNR a A04; interfaz y arquitectura por ciclos a E03/C01; RTL a C02; optimización a C03/C04.
