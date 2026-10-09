# Variantes rápidas: reloj mínimo 100 MHz (contrato técnico, mínimos confirmados el 7/10/2026).
# Síntesis e implementación out-of-context del núcleo (docs/contratos/verificacion-y-ppa.md#ppa).
create_clock -name clk -period 10.000 [get_ports clk]
