# Tabla PPA

Generada con `python3 -m scripts.ppa_table`; no editar a mano. Cada fila sale de `reports/ppa/<variante>/<reloj>mhz/summary.tsv` (flujo Vivado de C02). El reloj oficial es 10 MHz para las seriales y 100 MHz para las optimizadas; las seriales a 100 MHz son un dato adicional para separar la mejora de la arquitectura de la del reloj (#49). SQNR mínima del modelo fijo de cada rama, semillas 0–4 × 1024 símbolos (A04), solo para variantes registradas en `config/rtl_targets.json` (coinciden palabra por palabra con ese modelo). La potencia estática es del dispositivo completo. Vivado informa la dinámica con resolución de 1 mW, así que la energía por muestra de corridas con pocos mW de dinámica no distingue diferencias menores a ±0,5 mW; además, la cobertura SAIF es parcial (redes anotadas / total).

| variante | commit | configuración | SQNR | área | Fmax | latencia | throughput | potencia | herramienta/log |
|---|---|---|---|---|---|---|---|---|---|
| time_serial @ 10 MHz | — | — | 44.2 dB | no medida | no medida | no medida | no medida | no medida | — |
| time_serial @ 100 MHz | — | — | 44.2 dB | no medida | no medida | no medida | no medida | no medida | — |
| time_optimized @ 100 MHz | — | — | — | no medida | no medida | no medida | no medida | no medida | — |
| frequency_serial @ 10 MHz | `efb57125` | xc7a35tcpg236-1, OOC, 10 MHz, timing PASS | 43.0 dB | 1875 LUT / 569 FF / 3 DSP / 0 BRAM | 57.7 MHz (WNS 82.675 ns) | 559 ciclos | 0.1391 Mmuestras/s | 0.002 W din. / 0.068 W est. / 14.4 nJ/muestra (SAIF 2696 / 4391 redes) | Vivado v2024.2 (64-bit); [corrida](frequency_serial/10mhz/) |
| frequency_serial @ 100 MHz | `efb57125` | xc7a35tcpg236-1, OOC, 100 MHz, timing PASS | 43.0 dB | 1874 LUT / 569 FF / 3 DSP / 0 BRAM | 109.9 MHz (WNS 0.901 ns) | 559 ciclos | 1.391 Mmuestras/s | 0.015 W din. / 0.068 W est. / 10.8 nJ/muestra (SAIF 2696 / 4391 redes) | Vivado v2024.2 (64-bit); [corrida](frequency_serial/100mhz/) |
| frequency_optimized @ 100 MHz | — | — | — | no medida | no medida | no medida | no medida | no medida | — |
