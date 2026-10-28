# Experimentos de cierre temporal C04 en SS

El 27/10/2026 se investigó el cierre a 100 MHz manteniendo la interfaz, la
latencia de 26 ciclos y el intervalo de ocho ciclos por bloque. La referencia
es la corrida publicada en `reports/ppa/frequency.md`: setup −3,281 ns y hold
−0,499 ns en `max_ss_100C_1v60`. Los experimentos usaron OpenLane 2.3.10,
SKY130 HD y STA post-ruteo con SPEF, sin alterar los delays de E/S del flujo.

| Experimento | Setup peor SS (ns) | Hold peor SS (ns) | Resultado |
| --- | ---: | ---: | --- |
| Referencia: TT, AREA 0 | −3,281 | −0,499 | FAIL |
| Optimización SS, AREA 0 | −3,489 | −0,417 | FAIL |
| Optimización SS, DELAY 0 | −2,612 | −0,626 | FAIL |
| DELAY 0 y reparación post-GRT, margen hold 0,2 ns | −2,501 | −0,336 | FAIL |
| Lo anterior y selector de salida experimental | −2,466 | −0,430 | FAIL |
| Lo anterior y selector one-hot experimental | −2,024 | −0,247 | FAIL |
| One-hot y marcador de último slot por banco | −1,905 | −0,296 | FAIL; 25 violaciones de ruteo |
| One-hot y registro espectral antes del CSD | −2,125 | −0,287 | FAIL; 0 violaciones de ruteo |

La reparación post-GRT partió del estado de la corrida DELAY 0 anterior al
STA intermedio posterior a ruteo global; no repitió la reparación post-CTS.
El selector experimental reemplazó el part-select variable de las salidas por
un `case` de slices fijos, sin cambiar el control ni agregar registros. Pasó
160.000 comparaciones del selector y la simulación RTL de 2048 muestras con
latencia 26 e intervalo 8. Su mejora de setup fue pequeña y empeoró hold frente
al experimento anterior, por lo que no se incorporó al RTL.

Una segunda variante usa un puntero one-hot de ocho posiciones para seleccionar
la salida. Lo reinicia al finalizar cada bloque y lo avanza únicamente con el
handshake. Pasó 160.000 comparaciones del selector y la regresión RTL de 837
tramas, incluidos bloques parciales, pausas y reset; conservó latencia 26 e
intervalo 8. Sus fuentes y hashes se conservaron antes de la corrida física.
Mejoró setup y hold frente a los otros experimentos, pero ambos permanecen
negativos. No se incorporó al RTL ni se publicó como medición final.

Una variante posterior agregó un marcador one-hot del último slot por banco
para simplificar `emit_finish` y `out_last`. Pasó la regresión RTL de 837
tramas y el banco común, manteniendo latencia 26 e intervalo 8. La corrida
post-ruteo del 28/10/2026 mejoró setup, pero empeoró hold respecto de la
variante one-hot y terminó con 25 violaciones de ruteo y 79 violaciones de
antena reportadas. No constituye cierre físico ni se adoptó en el RTL. Los
snapshots, hashes, configuración y reportes están en
`build/ppa/experiments/onehot-last-marker/`.

El 28/10/2026 se ensayó mover el registro espectral de productos antes del
árbol CSD, manteniendo el número de etapas. La variante pasó la regresión RTL
de 837 tramas, con latencia 26 e intervalo 8, pero el STA post-ruteo reportó
setup −2,125 ns y hold −0,287 ns en el peor caso. El ruteador terminó con cero
violaciones, aunque persistieron 94 redes con violaciones de antena. No se
validaron netlist ni potencia. Frente al one-hot anterior empeoró ambos slacks,
por lo que no se adoptó. Fuentes y evidencia local bajo
`build/ppa/experiments/C04-max-ss-delay0/selector-retime-inputreg/`.

Las corridas experimentales terminaron en STA post-PnR; el ruteador informó
25 violaciones en la variante de último slot y cero en la variante de registro
espectral. No se ejecutaron la simulación de la
netlist final ni el análisis de potencia de estos experimentos, y el DRC del
ruteador no equivale a signoff de fabricación. No sustituyen la evidencia PPA
publicada. Los directorios completos, configuraciones y logs quedan localmente
bajo `build/ppa/experiments/`, que no se versiona.

Ninguna configuración cerró SS. La variante one-hot redujo el déficit de
setup y hold, pero mantiene violaciones de ambos y
violaciones eléctricas. El siguiente paso es investigar los caminos críticos
de registro a registro y de entrada/salida en el RTL y su mapeo, y medir
nuevas alternativas sin cambiar el contrato. No declarar PASS sin verificar
setup y hold en los nueve corners y volver a validar la netlist final.

En la variante one-hot, el peor setup es `rst` → `out_last` (−2,023 ns);
también fallan caminos de `rst` a las salidas de datos y a `out_valid`. El
peor hold va de `rst` a un registro de la IFFT (−0,247 ns). Evitar la
comparación del índice de salida podría reducir parte de la demora de
`out_last`, pero no resolvería por sí solo los demás caminos de reset. Las
restricciones o la semántica de reset no deben relajarse para ocultar estos
fallos.

## Diagnóstico de la variante one-hot

En los reportes post-PnR con SPEF de `max_ss_100C_1v60`, el camino de setup
`rst` → `out_last` tiene slack −2,023451 ns. Ocho etapas de distribución de
reset aportan aproximadamente 5,24 ns de demora de celdas y 0,12 ns de redes;
las etapas individuales tienen fanout entre 4 y 10. El resto de la lógica
hacia la salida aporta aproximadamente 2,49 ns. El peor hold, `rst` →
`u_ifft.stage_i[3][188]`, tiene slack −0,246914 ns: la llegada de datos es
3,748 ns y la del reloj de captura 3,817 ns, con incertidumbre de 0,25 ns.
Por ello, acelerar indiscriminadamente reset puede agravar hold.

También hay hold negativo desde `in_last` (−0,137951 ns) y `out_ready`
(−0,115088 ns); el peor camino registro a registro de hold reportado es
positivo (+1,086299 ns). En setup, un camino registro a registro hacia
`u_spectral.spectral_bins[3].u_product.aligned[3][17]` tiene slack
−1,757492 ns. Su origen no conserva un alias RTL identificable en el netlist;
la distribución inicial ocupa aproximadamente 2,2 ns y la lógica posterior
7,9 ns. El peor camino de reset a registro observado tiene slack −0,333411 ns.
Entre los 1000 caminos de setup reportados no aparece una entrada distinta de
reset hacia un registro, por lo que esos datos no establecen su peor slack.

Fuentes: `build/ppa/experiments/C04-max-ss-delay0/runs/`
`C04-max-ss-delay0-fifth-selector-onehot-grt-hold0p2-20261027/`
`55-openroad-stapostpnr/max_ss_100C_1v60/{max,min}.rpt`. Estos valores
describen la referencia existente; no son una nueva corrida ni demuestran cierre.

## Experimentos en curso

Se inició una corrida aislada desde el placement de la variante one-hot,
reduciendo el tamaño máximo del cluster de CTS de 25 a 12 sinks y su diámetro
de 50 a 30 µm. Los demás parámetros y constraints conservan los de la
referencia. El CTS insertó 1.772 buffers frente a 1.178 de la referencia;
el efecto sobre setup, hold y ruteo requiere el STA post-SPEF. Configuración,
hashes del estado y fuentes, logs y monitor de memoria están en
`build/ppa/experiments/onehot-cts-cluster12/`.
En el STA intermedio inmediatamente después de CTS, antes de reparar timing,
el peor slack SS fue −3,242 ns de setup y −0,329 ns de hold, frente a
−3,173 ns y −0,376 ns en la misma etapa de la referencia. Son estimaciones
intermedias, no resultados post-ruteo.
Tras la reparación post-CTS, el STA intermedio SS reportó −0,788 ns de setup
y +0,536 ns de hold; en la referencia fueron −0,329 ns y +0,151 ns. La
reparación insertó 4.560 buffers de hold (4.420 en la referencia). El
ruteo y el STA post-SPEF siguen siendo necesarios para comparar los resultados.
Después de la reparación post-GRT, el STA intermedio SS dio −0,669 ns de
setup y +0,534 ns de hold, frente a −0,457 ns y +0,561 ns de la referencia
en la misma etapa. Ambos empeoraron en esta estimación; no sustituye SPEF.

También se preparó una variante aislada en la que los registros de productos
se actualizan en cada ciclo y los bits de validez conservan su reset. Pasó la
aritmética exhaustiva, seis pruebas de aritmética/FFT/espectro, el banco común
y la regresión C04 de 837 tramas con latencia 26 e intervalo 8. Esta evidencia
no mide el efecto físico ni la potencia: actualizar datos inválidos puede
aumentar la actividad de conmutación. Fuentes, hashes y logs están en
`build/ppa/experiments/onehot-product-unconditional/`; no se adoptó en el RTL
principal.

Una segunda variante independiente actualiza en cada ciclo los registros de
alineación de mariposas y los registros de datos entre etapas FFT, dejando el
reset de los tokens de validez. Pasó las mismas seis pruebas unitarias, el
banco común y la regresión de 837 tramas con latencia 26 e intervalo 8. No se
ha medido físicamente; su actividad y potencia también pueden aumentar.
Fuentes, configuración, hashes y logs están en
`build/ppa/experiments/onehot-fft-data-free/`.

La corrida `onehot-cts-cluster12` sí llegó a STA post-ruteo con SPEF. Al
reanudar el paso de STA se completaron los nueve corners. Frente a la
referencia, el peor setup pasó de −2,023 a −1,975 ns y el peor hold de −0,247
a −0,211 ns: mejora modesta, todavía falla. En `min_ss` el hold bajó de
+0,040 a −0,013 ns. El chequeo final de antenas reporta 83 violaciones de red
y 93 de pin; el DRC del ruteo detallado quedó en cero. Este CTS no se adopta
como solución, pero queda como base para medir la siguiente hipótesis.

| Corner | Setup cluster12 (ns) | Hold cluster12 (ns) |
| --- | ---: | ---: |
| `nom_tt_025C_1v80` | +1,700 | +0,434 |
| `nom_ss_100C_1v60` | −1,646 | −0,120 |
| `nom_ff_n40C_1v95` | +3,094 | +0,179 |
| `min_tt_025C_1v80` | +1,909 | +0,441 |
| `min_ss_100C_1v60` | −1,319 | −0,013 |
| `min_ff_n40C_1v95` | +3,230 | +0,183 |
| `max_tt_025C_1v80` | +1,533 | +0,429 |
| `max_ss_100C_1v60` | −1,975 | −0,211 |
| `max_ff_n40C_1v95` | +2,973 | +0,174 |

Los reportes completos están en `build/ppa/experiments/onehot-cts-cluster12-sta-resume/`.

La hipótesis siguiente está aislada en
`build/ppa/experiments/onehot-reset-output-branch/`: `out_valid` y `out_last`
usan una rama invertida de reset marcada `keep`; el reset síncrono de estados
y datapath queda igual. Su log confirma la prueba aritmética exhaustiva y el
banco común con regresión QPSK, pausas y protocolo; no confirma una regresión
de 837 tramas para esta variante. La primera corrida física con CTS 12/30 se
completó hasta el checker de conectividad, como se detalla más abajo.
El STA SS previo a la reparación post-CTS dio setup −3,011 ns y hold −0,484 ns;
el crítico de setup ya es registro a registro (`_93650_` → `_95925_`) y el de
hold es entrada `in_q[0]` → registro. Son valores intermedios sin reparación.
Después de reparar timing post-CTS, el STA SS intermedio quedó en setup
−0,462 ns y hold +0,541 ns (cluster12 sin la rama: −0,788 ns y +0,536 ns).
Esto confirma una mejora provisional de setup sin perder el margen de hold;
GRT, DRT, antenas y STA post-SPEF aún deciden el resultado.
Tras GRT y su reparación, el STA SS quedó en setup −0,476 ns y hold +0,519 ns.
El chequeo de antenas bajó de 206 redes/254 pines a 45/7 después de RepairAntennas.
El ruteo detallado sigue ejecutándose; estos datos no sustituyen STA post-SPEF.
El ruteo detallado terminó con cero DRC, pero el checker encontró el reloj
`_96007_/CLK` desconectado desde CTS. Por ello los STA intermedios de esta
variante son incompletos y no permiten compararla como candidata válida. El
chequeo posterior al ruteo reportó 107 redes y 119 pines con antenas. Se debe
repetir CTS y verificar conectividad antes de continuar.

El reensayo CTS con cluster 13 también dejó desconectado ese mismo pin. En una
copia del ODB se conectó a `clknet_leaf_1473_clk`, rama del registro vecino
`_96006_` a 10 µm, con cinco terminales previamente conectados. El STA de
control posterior ya no reporta registros sin reloj ni ese endpoint sin
restricción. La reconstrucción, parámetros y procedencia están en
`build/ppa/experiments/onehot-reset-output-cts13/`; la corrida física desde el
estado corregido se ejecutó hasta STA post-ruteo.
Después de reparar timing post-GRT en esa copia, `_96007_/CLK` sigue conectado
y el STA SS intermedio reporta setup −0,476 ns y hold +0,519 ns. El ruteo
detallado se ejecutó a continuación.
La corrida corregida completó STA post-ruteo con SPEF en los nueve corners:
el peor `max_ss` dio setup −1,600220 ns y hold −0,285578 ns; `nom_ss` dio
−1,353222/−0,177960 ns y `min_ss` −1,056727/−0,033118 ns. Los otros seis
corners pasaron ambos chequeos. DRC del ruteador y pines desconectados: cero;
antenas: 99 redes y 110 pines. Por tanto no hay cierre ni PASS físico.
Reportes: `runs/reset-cts13-connected-physical/20-openroad-stapostpnr/`.

Como siguiente hipótesis se preparó `onehot-csd-balanced-tree`: compacta los
dígitos positivos y negativos del CSD en árboles balanceados y combina ambos
con una resta, conservando el registro de productos. Está aislada en
`build/ppa/experiments/onehot-csd-balanced-tree/` con hashes de fuentes; aún
requiere pruebas aritméticas, regresión y medición física antes de evaluarla.

El análisis del netlist post-GRT confirmó que `_93650_` es una copia de
`spectral_source`: su D tiene los mismos operandos que el registro original.
La distribución desde su Q hasta el primer gate del mux cuesta 2,229 ns en
el camino a `spectral_bins[3].u_product.aligned[3][18]`. La variante aislada
`build/ppa/experiments/C04-spectral-bank-per-bin/` replica el selector por bin
y mueve el mux de bancos a cada bin, sin cambiar su flanco de actualización.
Faltan verificar que las 16 copias sobrevivan síntesis y medir setup/hold
post-SPEF. Sus comandos y salida quedan en `run_validation.py` y
`validation.log` dentro de su directorio.
La validación terminó con éxito: siete pruebas unitarias de aritmética, FFT y
espectro, CSD exhaustivo, regresión de 837 tramas con latencia 26 e intervalo
8, y banco común. Se necesita medición física antes de atribuirle una mejora
de timing.
La síntesis de esa variante conservó solo un FF de selección y creó buffers
para las otras 15 señales: las marcas del vector no evitaron la fusión. No se
debe atribuir a esa versión una reducción de fanout de FF; se está ajustando
la implementación. En una copia integrada también se reduce la salida por banco
antes del mux final y se aplica reset al final. Por pedido del usuario, para
esta copia se hará una prueba dirigida y una sola regresión completa.
La copia integrada `C04-spectral-bank-per-bin-output-finalmux` reduce por
banco antes del mux de salida y aplica reset directamente a los datos. Usa
instancias de selector por bin con jerarquía preservada para evitar la fusión
observada. Pasó la prueba dirigida de salida y la regresión de 837 tramas
con L=26 e II=8; aún no tiene resultado físico.
La síntesis de la copia integrada conservó 16 instancias del módulo de selección,
cada una con un `dfxtp_2`; la corrida continuó hacia CTS y ruteo.
El proceso `continue_after_cts.py` espera el fin exitoso de CTS y su STA de
control, detiene la continuación si hay registros sin reloj y, si el chequeo
pasa, inicia automáticamente el flujo desde reparación post-CTS hasta SPEF.
La corrida integrada terminó: en `max_ss` el STA post-SPEF da setup −1,675305
ns y hold −0,167011 ns; `nom_ss` −1,343698/−0,032645 ns y `min_ss`
−1,012328/+0,120405 ns. Los demás corners pasan ambos chequeos. El ruteador
reporta cero DRC, y el checker cero pines desconectados; antenas reporta 78
redes y 94 pines. La corrida no cierra timing ni cumple antenas. Reportes en
`runs/integrated-postcts/20-openroad-stapostpnr/`.
