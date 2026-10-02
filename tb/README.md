# Testbenches

Cada variante RTL necesita un testbench que devuelva código de error (`$fatal`) si falla una comparación. El banco común futuro leerá los vectores deterministas de `vectors/`, alineará salidas por índice válido y reportará I/Q esperado y obtenido. Las reglas numéricas se fijan en el [contrato de verificación](../docs/contratos/verificacion-y-ppa.md).
