# Constraints PPA

Guardar aquí constraints de reloj y tecnología para las cuatro variantes. No comparar Fmax, área o potencia si cambian biblioteca/FPGA, corner, actividad o constraints sin indicarlo. El método se acuerda en el [contrato PPA](../docs/contratos/verificacion-y-ppa.md).

| Archivo | Uso |
|---|---|
| `clk_100mhz.xdc` | Variantes rápidas: período 10 ns. |
| `clk_10mhz.xdc` | Variantes lentas: período 100 ns. |

Las dos fijan solo el reloj del puerto `clk`, porque el núcleo se implementa out-of-context en Vivado (propuesta E03). Cada reporte en `reports/` indica qué archivo usó.
