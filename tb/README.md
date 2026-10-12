# Testbenches

Cada variante RTL necesita un testbench que devuelva código de error (`$fatal`) si falla una comparación. El banco común futuro leerá los vectores deterministas de `vectors/`, alineará salidas por índice válido y reportará I/Q esperado y obtenido. Las reglas numéricas se fijan en el [contrato de verificación](../docs/contratos/verificacion-y-ppa.md).

`frequency/tb_fir_frequency_serial.sv` genera y compara en SystemVerilog los vectores del perfil provisional C02, usando los taps de `config/project.json`. `make smoke` lo ejecuta con Icarus; incluye timeout, comparación por palabra, protocolo, reset y tiempos. `vvp build/frequency_serial.out +dump_constants` muestra las tablas calculadas. Esta referencia local no sustituye el modelo fijo definitivo ni los vectores A05.
