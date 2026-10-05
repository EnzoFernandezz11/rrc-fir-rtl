# Diagrama general del filtro en frecuencia — propuesta anterior

Este diagrama conserva el esquema discutido antes del cambio de [consigna](../consigna-original.md): RRC de ocho taps, nueve muestras nuevas por bloque, FFT/IFFT de 16 puntos y overlap-add. **Es una referencia histórica, no la arquitectura aprobada para la consigna actual.** El IIR de segundo orden y la superposición del 50 % obligan a revisar el método antes de implementarlo.

```mermaid
flowchart LR
    subgraph T0["Dominio del tiempo: preparación"]
        Q["Símbolos QPSK"] --> U["Sobremuestreo 2×<br/>símbolo, cero, símbolo, cero..."]
        U --> B["Reunir 9 muestras nuevas<br/>último bloque: completar con ceros"]
        B --> P["Agregar 7 ceros<br/>16 posiciones"]

        H["Los mismos 8 taps RRC<br/>h[0]...h[7]"] --> HP["Agregar 8 ceros<br/>16 posiciones"]
    end

    subgraph F["Dominio de la frecuencia"]
        P --> FX["FFT de 16 puntos<br/>X[0]...X[15]"]
        HP --> FH["FFT de 16 puntos<br/>calcular una vez"]
        FH --> ROM["Tabla de solo lectura<br/>H[0]...H[15]"]
        FX --> MUL["Multiplicar bin a bin<br/>Y[r] = X[r] × H[r]"]
        ROM --> MUL
    end

    subgraph T1["Dominio del tiempo: reconstrucción"]
        MUL --> INV["IFFT de 16 puntos<br/>escala 1/16"]
        INV --> SUM["Overlap-add<br/>sumar la cola anterior"]
        SUM --> OUT["Emitir 9 muestras<br/>por bloque completo"]
        INV --> TAIL["Guardar cola de 7 muestras"]
        TAIL -->|bloque siguiente| SUM
        TAIL --> END["Al terminar: vaciar la cola<br/>salida total S + 7 muestras"]
    end
```
