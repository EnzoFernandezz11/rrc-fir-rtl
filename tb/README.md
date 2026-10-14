# Testbenches

Cada variante RTL necesita un testbench que devuelva código de error (`$fatal`) si falla una comparación. El banco común futuro leerá los vectores deterministas de `vectors/`, alineará salidas por índice válido y reportará I/Q esperado y obtenido. Las reglas numéricas se fijan en el [contrato de verificación](../docs/contratos/verificacion-y-ppa.md).

- `time/tb_fir_time_serial.sv` (B02): corre cada vector smoke dos veces, ideal (comprueba `L = 9` e `II = 10`) y con burbujas y `out_ready = 0` pseudoaleatorios (semilla 1), y compara contra `yt`. Con `vvp build/time_serial.out +regresion` agrega `build/vectors/qpsk_s1.txt`, que se genera con `python3 -m model.vectors`.
