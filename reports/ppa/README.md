# Registro PPA en frecuencia

[Resultados y análisis de las corridas seriales y optimizadas](frequency.md).

El informe muestra, por variante, solo la última corrida local exitosa. Cada nueva corrida exitosa reemplaza la anterior aunque sea equivalente; sus artefactos quedan en `build/ppa/`. La historia de Vivado C02 se conserva en su sección histórica y no se reemplaza con la medición local SKY130.

Las instrucciones y limitaciones están en la [guía PPA](../../docs/frecuencia/ppa.md). La medición local usa SKY130 HD; `package` añade un ZIP para una referencia FPGA posterior con Vivado y no sustituye esa medición ASIC.
