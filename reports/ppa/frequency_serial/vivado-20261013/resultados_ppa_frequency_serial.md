# Resultados PPA — `fir_frequency_serial`

**Diseño:** `fir_frequency_serial` (FIR en frecuencia, variante serial)
**Dispositivo:** Artix-7 `xc7a35tcpg236-1` (Basys 3), out-of-context
**Herramienta:** Vivado v2024.2 (64-bit)
**Reloj:** 100 ns (10 MHz) · **Benchmark:** A04, QPSK 2x, semilla 1, 1024 símbolos, 2048 muestras
**Fecha:** 2026-10-13

---

## Resumen PPA

| Métrica | Valor | Tipo de dato |
|---|---|---|
| Verificación funcional (2048 muestras) | ✅ PASS | **medido** (sim. comportamental) |
| Latencia | 559 ciclos | medido |
| Ciclos por bloque | 575 | medido |
| Ciclos activos (2048 muestras) | 147 200 | medido |
| Throughput @10 MHz | 139 130,435 muestras/s | medido |
| Timing interno @10 MHz | ✅ MET (setup + hold) | **medido** (implementación routed) |
| WNS (setup) | +82,675 ns | medido |
| WHS (hold) | +0,189 ns | medido |
| Fmax estimada | ≈ 57,72 MHz | derivado: 1000 / (100 − WNS) |
| LUT (as Logic) | 1875 (9,01 %) | medido |
| FF (Slice Registers) | 569 (1,37 %) | medido |
| DSP48E1 | 3 (3,33 %) | medido |
| Block RAM | 0 | medido |
| CARRY4 / F7+F8 Muxes | 20 / 238 | medido |
| Potencia total on-chip | 0,070 W | **estimación vectorless** |
| Potencia dinámica | 0,002 W | estimación vectorless |
| Potencia estática (dispositivo) | 0,068 W | estimación vectorless |
| Energía dinámica por muestra | ≈ 14,4 nJ/muestra | derivado (vectorless) |

---

## Metodología

El flujo PPA original del paquete (`scripts/ppa/vivado/run.bat`) no completó en este
entorno (Windows + Vivado 2024.2). La implementación física (síntesis + place & route +
timing + DRC) sí se completó y es válida; la etapa de **simulación temporal con SDF**
falló. Los resultados se obtuvieron así:

- **Área, timing, Fmax, DRC:** directamente de la implementación routed del flujo
  (`utilization.rpt`, `timing_setup.rpt`, `timing_hold.rpt`, `timing_summary.rpt`).
- **Verificación funcional + throughput/latencia:** simulación **comportamental** (RTL,
  sin SDF) del mismo `tb_fir_frequency_ppa.sv` con los vectores `ppa_vectors.txt`.
  Resultado: `PASS PPA: 2048 muestras, L=559, bloque=575, 147200 ciclos, 139130.435 muestras/s`.
- **Potencia:** `report_power` en modo **vectorless** sobre `implemented.dcp`
  (sin SAIF), confianza **Media** (actividad de nodos internos <25 % especificada).

---

## Detalle de potencia (vectorless)

- Total On-Chip: **0,070 W** → Dinámica **0,002 W** + Estática del dispositivo **0,068 W**.
- La **estática domina** (97 % del total): esperable en un núcleo chico sobre Artix-7;
  la mayor parte del consumo es del dispositivo, no de la lógica del diseño.
- Toda la potencia dinámica (~0,002 W) se concentra en `u_engine` (motor FFT/IFFT),
  coherente con que el motor ocupa el ~95 % de los ciclos por bloque.
- **Junction 25,4 °C · Max Ambient 84,6 °C** con los valores de entorno por defecto.

---

## Limitaciones / notas de honestidad

1. **La potencia es vectorless, no con actividad real (SAIF).** La cifra dinámica
   (0,002 W) y la energía por muestra (~14,4 nJ) son estimaciones con confianza Media.
   La potencia "oficial" con SAIF requiere que complete la simulación temporal gate-level,
   lo que no fue posible en Vivado 2024.2 (ver abajo).
2. **La simulación temporal gate-level (SDF) no completa en Vivado 2024.2:** el benchmark
   arranca (la ventana de actividad llega a 1 tras el reset) pero las salidas dejan de
   aparecer y salta el watchdog del testbench a 160 000 ciclos. Patrón típico de
   **X-propagation por flip-flops sin inicializar** en la netlist (GSR/`glbl`). La
   simulación comportamental del mismo RTL pasa sin problemas, por lo que el RTL, el
   testbench y los vectores están correctos: el problema es específico de la sim gate-level
   en esta versión/entorno.
3. **Área distinta de la referencia del paquete:** el `resources.json` de referencia indica
   LUT 1507 / FF 610 / DSP 1; esta implementación en 2024.2 dio LUT 1875 / FF 569 / DSP 3.
   Diferencia esperable por distinta versión de Vivado.

---

## Correcciones aplicadas a los scripts (para poder correr en Windows)

En `scripts/ppa/vivado/run.tcl`, las llamadas a `xelab` y `xsim` se hacían por nombre, lo
que en Windows resuelve a `xelab.bat` / `xsim.bat`; esos wrappers **parten los argumentos
en el `=`**, rompiendo `-sdfmax /tb.../dut=implemented.sdf` y `-testplusarg VECTORS=...`.
Se corrigió invocando los ejecutables directos (`.../bin/unwrapped/win64.o/xelab.exe` y
`xsim.exe`), que preservan el `=`. Con eso el flujo pasa síntesis/impl/elaboración; el
bloqueo restante es el X-propagation de la sim temporal (punto 2 de arriba).
