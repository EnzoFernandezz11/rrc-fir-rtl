# Tabla PPA

Generada con `python3 -m scripts.ppa_table`; no editar a mano. Cada fila sale de `reports/ppa/<variante>/summary.tsv` (flujo Vivado de C02). SQNR mínima del modelo fijo de cada rama, semillas 0–4 × 1024 símbolos (A04), solo para variantes registradas en `config/rtl_targets.json` (coinciden palabra por palabra con ese modelo). La potencia estática es del dispositivo completo; la dinámica requiere revisar la cobertura SAIF de cada corrida.

| variante | commit | configuración | SQNR | área | Fmax | latencia | throughput | potencia | herramienta/log |
|---|---|---|---|---|---|---|---|---|---|
| time_serial | — | — | — | no medida | no medida | no medida | no medida | no medida | — |
| time_optimized | — | — | — | no medida | no medida | no medida | no medida | no medida | — |
| frequency_serial | — | — | — | no medida | no medida | no medida | no medida | no medida | — |
| frequency_optimized | — | — | — | no medida | no medida | no medida | no medida | no medida | — |
