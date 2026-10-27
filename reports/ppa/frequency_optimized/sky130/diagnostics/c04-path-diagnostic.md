# Diagnóstico de caminos C04 (evidencia guardada)

Fuente: `build/ppa/frequency_optimized/20261024T232507221614Z-22dd3d09/runs/target/54-openroad-stapostpnr/`. Los tiempos están en ns. `max.rpt` y `min.rpt` listan el primer camino; `ws.max.rpt` y `ws.min.rpt` contienen el resumen de slack peor por corner.

| Corner / chequeo | Camino reportado | Slack del primer camino | Peor slack corner |
|---|---|---:|---:|
| `nom_tt_025C_1v80`, setup (`max.rpt`) | `rst` → `out_q[5]` | +2.330294 (MET) | +2.330294 (`ws.max.rpt`) |
| `nom_tt_025C_1v80`, hold (`min.rpt`) | `_80655_` → `_80655_` | +0.303278 (MET) | +0.303278 (`ws.min.rpt`) |
| `max_ss_100C_1v60`, setup (`max.rpt`) | `_78863_` → `_81410_` | −3.280996 (VIOLATED) | −3.280996 (`ws.max.rpt`) |
| `max_ss_100C_1v60`, hold (`min.rpt`) | `rst` → `_79914_` | −0.499415 (VIOLATED) | −0.499415 (`ws.min.rpt`) |

## Lectura del netlist final

En `runs/target/final/pnl/fir_frequency_optimized.pnl.v`, el registro `_78863_` es un `dfxtp_2` con `D=_00534_` y `Q=_00002_`. Su entrada `_00534_` es conducida por la salida `X` de la compuerta `_42112_` (`o21a_1`). `_81410_` es un `dfxtp_1` cuya salida está mapeada a `u_spectral.spectral_bins[15].u_product.aligned[1][19]`. La señal `_00002_` no muestra un nombre RTL preservado en el netlist: solo se puede concluir que es el Q de `_78863_`; inferir su función lógica más específica requeriría seguir la lógica y el contexto RTL correspondiente.

El destino `_79914_` es un `dfxtp_1` con Q mapeada a `u_control.fft_token[0][5]`. El inicio `rst` es un puerto de entrada, así que este camino de hold está asociado a la entrada/reset y sus restricciones/ruta hasta ese registro; no identifica por sí solo un defecto funcional del RTL.

El fallo SS reúne setup (−3.280996 ns) y hold (−0.499415 ns). El camino de hold comienza en `rst`, mientras que el camino de setup comienza en un registro interno cuya función RTL no quedó identificada y termina en un registro del datapath espectral. Estos reportes justifican revisar constraints, márgenes/derates y optimización física de ambos caminos; no justifican aplicar retiming automáticamente.

## Qué cambia en STA del escenario común

Los logs guardados muestran que el STA común no aplicó el SDC serializado del escenario target: en ambos escenarios el archivo leído se registra como OpenLane `base.sdc`, y sus valores efectivos vienen del entorno de cada corrida. En `_env_ThreadPoolExecutor-2_0.tcl` del escenario común, `CLOCK_PERIOD=100` y `IO_DELAY_CONSTRAINT=20`; en `_env_ThreadPoolExecutor-4_0.tcl` del target, son `10` y `20`, respectivamente. Los logs muestran delays de E/S efectivos de **20 ns en común** y **2 ns en target**, lo cual corresponde a la escala de 20% del período. Ambos logs reportan carga de salida `0.033442`, incertidumbre de reloj `0.25 ns`, transición de reloj `0.15 ns`, derate del 5%; el entorno limita transición máxima a `0.75 ns`. Los reportes usan árbol de reloj propagado.

Evidencia: `runs/common/01-openroad-stapostpnr/nom_tt_025C_1v80/sta.log` líneas 9–16 y `_env_ThreadPoolExecutor-2_0.tcl` líneas 39–55; target `runs/target/54-openroad-stapostpnr/nom_tt_025C_1v80/sta.log` líneas 9–16 y `_env_ThreadPoolExecutor-4_0.tcl` líneas 39–55. En particular, STA imprime `Reading design constraints file .../openlane/scripts/base.sdc`; común fija output/input delay 20, target 2. En común el camino nominal `rst`→`out_q[5]` tiene llegada 23.419706 ns y requerido 79.75 ns (slack +56.330292 ns); en target llega a 5.419706 ns y requiere 7.75 ns (slack +2.330294 ns). La diferencia de slack es exactamente 54 ns: el período aumenta 90 ns, mientras los márgenes de entrada y salida consumen 18 ns adicionales cada uno (+36 ns total), con incertidumbre constante.

La comparación SS también cambia de camino: target setup usa el FF→FF `_78863_`→`_81410_` y da −3.280996 ns; común setup usa `rst`→`out_q[5]` y da +53.313408 ns. En hold SS target el primer camino desde `rst` a `_79914_` da −0.499415 ns; común reporta primero `_80655_`→`_80655_` con +0.831592 ns. Por tanto, el PASS/FAIL entre target y common refleja un cambio de constraints y de camino crítico (incluida la demora de entrada), no una mejora lógica o un cambio de layout. El hold/reset negativo del target no queda invalidado por el slack positivo del camino mostrado en common.

Esto es distinto del SDC usado para estimar potencia común: `write_power_sdc` modifica únicamente el periodo de `create_clock` del SDC target de 10 a 100 ns, preservando sus delays E/S de 2 ns. Por ello, el STA físico de common (I/O delay 20 ns escalado por base.sdc) y la estimación de potencia common (I/O delay 2 ns del SDC target) no comparten el mismo conjunto completo de constraints.
