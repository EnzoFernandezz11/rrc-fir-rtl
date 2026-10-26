# PPA de los núcleos temporales (SKY130)

Procedimiento para medir B02 (`time_serial`) y B04 (`time_optimized`) con
OpenLane 2 y la biblioteca **SKY130 HD**. Es el mismo método que usa la rama en
frecuencia para C02/C04 ([`docs/frecuencia/ppa.md`](frecuencia/ppa.md), rama
`e/c04-rtl-optimized`, commit `f1fe770`): mismas herramientas fijadas, biblioteca,
corners, benchmark, cálculo de potencia y criterios de PASS/FAIL. Los scripts
temporales son copias adaptadas; cuando se mergeen B04 y C04 conviene unificarlos.

**Estado de la decisión:** el 26/10/2026 los tres integrantes acordaron que la
tabla PPA común (`reports/ppa/tabla.md`) se hace con SKY130 para las cuatro
variantes (D05/D06; ver el historial de `docs/contrato-tecnico.md`). Las
corridas Vivado / Artix-7 ya medidas quedan como referencia FPGA en un anexo del
informe, no en la tabla principal.

## Qué cambia respecto del flujo de frecuencia

| Tema | Frecuencia (C02/C04) | Tiempo (B02/B04) |
|---|---|---|
| Script | `scripts/ppa.py`, `ppa_physical.py`, `ppa_compare.py` | `scripts/ppa_time.py`, `ppa_time_physical.py`, `ppa_time_compare.py` |
| Lanzador | `scripts/ppa/openlane/run.sh` | `scripts/ppa/openlane/run_time.sh` (solo cambia el script que llama) |
| Bancos | `tb_fir_frequency_ppa`, `tb_fir_frequency_optimized_ppa` | `tb_fir_time_ppa` (A07), `tb_fir_time_systolic_ppa` (B04) |
| Síntesis Yosys | `scripts/synth/frequency_*_sky130.ys` | `scripts/synth/time_*_sky130.ys` |
| Vectores | `scripts.ppa_vectors --domain frequency` | `scripts.ppa_vectors --domain time` |
| Throughput sostenido | 8 muestras por bloque: `8e9 / (ciclos_bloque · T)` | 1 muestra por II: `1e9 / (II · T)` |
| Reporte | `reports/ppa/frequency.md` | `reports/ppa/time.md` |

Los relojes objetivo son los del contrato: **100 ns (10 MHz) para B02** y
**10 ns (100 MHz) para B04**. El escenario `common` repite STA y potencia de
cada layout a 10 MHz para comparar las dos variantes al mismo reloj.

## Requisitos

- Checkout de OpenLane 2 limpio en `~/openlane2`, commit `a7b0e6d` (2.3.10).
- PDK Volare `0fe599b2afb6708d281543108caf8310912f54af` (sky130A).
- Nix con el caché FOSSi (ver `scripts/ppa/openlane/nix-cache.conf` y la guía de
  frecuencia).
- `.venv` del proyecto con numpy (Python 3.12) e Icarus/Yosys locales.
- GNU time en `/usr/bin/time` (control de recursos de las simulaciones y de OpenSTA).

## Comandos

Desde la raíz, de a una corrida por vez:

```sh
PPA_PYTHON=$PWD/.venv/bin/python3 sh scripts/ppa/openlane/run_time.sh --target time_serial
PPA_PYTHON=$PWD/.venv/bin/python3 sh scripts/ppa/openlane/run_time.sh --target time_optimized
```

Cada corrida:

1. Valida el ejemplo SPM de OpenLane en `build/ppa/openlane-preflight/` (solo
   la primera vez o si cambian herramientas, PDK o perfil Nix).
2. Corre `make smoke`, el benchmark RTL de 2048 muestras, la síntesis lógica
   SKY130 y la simulación funcional de `mapped.v` (igual que `local`).
3. Corre OpenLane Classic hasta `OpenROAD.STAPostPNR`: síntesis, floorplan,
   placement, CTS, ruteo, SPEF y STA en 9 corners (TT/SS/FF × RC nom/min/max).
4. Simula la netlist final con las mismas 2048 muestras y exige las mismas
   métricas que el RTL.
5. Calcula potencia con OpenSTA (TT, SPEF nominal) con la actividad VCD de toda
   la ventana activa, dividida en hasta 64 segmentos.
6. Repite STA y potencia a 10 MHz (`common`) sobre el mismo layout. B02 ya está
   a 10 MHz, así que `common` reutiliza `target`.

Solo para la parte lógica, sin OpenLane:

```sh
.venv/bin/python3 scripts/ppa_time.py local --target time_serial
.venv/bin/python3 scripts/ppa_time.py local --target time_optimized
```

Comparación de las dos últimas corridas publicadas (lee los JSON, no el Markdown):

```sh
.venv/bin/python3 scripts/ppa_time.py compare \
    --b02 build/ppa/time_serial/CORRIDA --b04 build/ppa/time_optimized/CORRIDA
```

Con `--render` además exporta los gráficos a SVG con Mermaid CLI (requiere npm).

## Cómo leer el veredicto de timing

El resumen separa tres estados por escenario:

- **Setup/hold:** slacks ≥ 0 y cero violaciones en los 9 corners.
- **Restricciones eléctricas:** cero violaciones de slew, capacitancia y fanout,
  sin advertencias de restricciones ni redes sin parasíticos.
- **Timing global:** PASS solo si pasan los dos anteriores.

Un FAIL eléctrico con setup/hold en PASS significa que la frecuencia cierra, pero
el layout no está limpio para fabricar. En B02 y B04 el caso típico es el fanout
de los buffers del árbol de reloj que inserta CTS.

**Fmax** se estima de los caminos registro a registro. En los núcleos temporales,
todos los registros dependen de la habilitación de entrada, así que OpenLane
puede no informar un camino registro a registro (`timing__setup_r2r__ws` = inf).
En ese caso la Fmax se lee de `clock.rpt` (`fmax`/`period_min` de OpenSTA). No es
un barrido de frecuencia ni demuestra el timing de E/S.

## Evidencia

Cada corrida completa queda en `build/ppa/<target>/<corrida>/`, que **no se
versiona** (`build/` está en `.gitignore`): estados de OpenLane (netlist, SPEF,
SDF, ODB, SDC resuelto), VCD, logs y archivos de consumo `*.resource.txt` /
`*.monitor.jsonl`. Pesa del orden de 100–170 MB por corrida.

Para que los enlaces del reporte funcionen para todo el equipo, al publicar una
corrida se copia un subconjunto liviano (≈ 0,5–0,8 MB) a
`reports/ppa/<target>/sky130/`, que sí se versiona, junto a las carpetas Vivado
`10mhz/` y `100mhz/`:

- `manifest.json`, `physical_metrics.json`, `local_metrics.json`,
  `gate_metrics.json`, `resources.json`, `cells.json`, `synthesis.ys`,
  `openlane-*.json`, `first_blocks.vcd` y los logs de benchmark.
- Por escenario (`target/`, `common/`): `metrics.json`, `power.sdc` y `power.log`.
- `runs/<escenario>/*-openroad-stapostpnr/`: `summary.rpt` y, por corner, los
  reportes chicos de STA (checks, clock, power, violator_list, ws/wns/tns, skew).
- `evidence.json`: nombre de la corrida de origen y SHA256 de cada archivo copiado.

Quedan afuera VCD completos, netlists, SPEF, SDF, ODB, la Liberty y los reportes
de caminos `max.rpt`/`min.rpt`; se regeneran con los comandos de arriba. Cada
publicación reemplaza la copia anterior de esa variante. La comparación B02/B04
y sus fuentes Mermaid quedan en `reports/ppa/time_comparison/`.

`reports/ppa/time.md` guarda solo la última corrida exitosa de cada variante y
la comparación.

La potencia es funcional, sin retardos: no incluye todos los glitches. No se
corre signoff de fabricación (GDS, DRC, LVS).
