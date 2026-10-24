# Filtros RRCOS complejos en RTL

Proyecto final: dos implementaciones de un filtro complejo de 8 coeficientes, una en el dominio del tiempo y otra en frecuencia. La entrada usa símbolos QPSK y un upsampler 2×, confirmado por Enzo el 7/10/2026 para ambas cadenas; el RRCOS tiene roll-off de 50 %. El trabajo compara versiones seriales y optimizadas con foco en rendimiento, potencia y área (PPA).

## Estado actual

Este repositorio contiene modelos flotantes y fijos, [vectores comunes A05](vectors/README.md), la variante RTL temporal serial y dos variantes en frecuencia registradas en CI. `make smoke` comprueba las tres variantes actualmente habilitadas en el registro; frecuencia serial incluye A05 y la regresión extendida A03/A04, y frecuencia optimizada incluye 837 tramas A04/A05 con pausas, backpressure y reset. La optimización en frecuencia C04 está integrada. El flujo local de medición lógica SKY130 HD está documentado, sin implicar timing, ruteo ni potencia físicos; ver la [guía PPA](docs/frecuencia/ppa.md). La comparación PPA continúa en las tareas del [backlog](docs/backlog.md). La [consigna vigente](docs/consigna-actualizada.md), confirmada el 7/10/2026, es la única copia en el árbol de trabajo: se retiraron las versiones reemplazadas para evitar contexto contradictorio; el historial permanece en Git. Los requisitos y las decisiones se registran en el [contrato técnico](docs/contrato-tecnico.md) y sus [contratos de trabajo](docs/contrato-tecnico.md#3-detalle-por-tema). Para el contexto teórico general (RRC, FFT, punto fijo, PPA) está la [guía de Enzo](docs/Guia_integral_RRCOS_RTL.md), que es una referencia y no se mantiene al día.

Las [23 issues](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues) están en el [Project del equipo](https://github.com/users/EnzoFernandezz11/projects/4) con estados, responsables asignados y fechas previstas. [Andrés (@andres332271)](https://github.com/andres332271) lleva modelos y precisión; [Julián (@moreyrajulian)](https://github.com/moreyrajulian), el filtro temporal; y [Enzo (@EnzoFernandezz11)](https://github.com/EnzoFernandezz11), el filtro en frecuencia. Cada integrante puede filtrar sus tareas por asignado en las [issues](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues) o en la vista correspondiente del Project.

| Integrante | Issues asignadas | Vista del Project |
|---|---|---|
| @andres332271 | [Ver issues](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues?q=is%3Aissue+assignee%3Aandres332271) | [Andrés](https://github.com/users/EnzoFernandezz11/projects/4/views/5) |
| @moreyrajulian | [Ver issues](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues?q=is%3Aissue+assignee%3Amoreyrajulian) | [Julián](https://github.com/users/EnzoFernandezz11/projects/4/views/6) |
| @EnzoFernandezz11 | [Ver issues](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues?q=is%3Aissue+assignee%3AEnzoFernandezz11) | [Enzo](https://github.com/users/EnzoFernandezz11/projects/4/views/7) |

## Primeros pasos

1. Leer el [contrato técnico](docs/contrato-tecnico.md). E00–E03 tienen sus issues cerradas; revisar allí qué decisiones siguen propuestas y registrar las respuestas del docente.
2. Seguir el [Gantt](docs/gantt.md) y tomar una tarea del [backlog](docs/backlog.md).
3. Crear una rama corta por tarea y abrir un PR con la [guía de contribución](CONTRIBUTING.md).
4. Instalar dependencias con `pip install -r requirements.txt` y ejecutar `make smoke` localmente antes del PR. El comando valida el contrato y ejecuta los testbenches que estén registrados en `config/rtl_targets.json`.

## Comandos

| Comando | Función |
|---|---|
| `make check-contract` | Valida estructura y parámetros confirmados de `config/project.json`. |
| `make smoke` | Valida contrato, ejecuta pruebas Python y simula los RTL registrados con Icarus Verilog. |
| `make full` | Ejecuta síntesis Yosys de los RTL registrados que tengan script de síntesis. |
| `make verify` | Ejecuta `smoke` y `full` localmente. |

Requisitos actuales: Python 3.12 o compatible; `iverilog` y `vvp` cuando se registre el primer RTL; `yosys` para `make full`. Las salidas se escriben en `build/` y no se versionan. La [CI](.github/workflows/rtl-ci.yml) corre `smoke` en cada PR y `full` después de integrar en `main` o manualmente.

Las variantes registradas están en `config/rtl_targets.json`. **Agregar una variante al registro en el mismo PR que incorpora su RTL y testbench.** Si una variante registrada falta o su simulación falla, `make smoke` falla; el mensaje inicial de «0 variantes» no cuenta como vector matching.

Para PPA físico de C02/C04 se añadió OpenLane 2 fijado mediante Nix:

~~~sh
sh scripts/ppa/openlane/run.sh --target frequency_serial
sh scripts/ppa/openlane/run.sh --target frequency_optimized
python3 scripts/ppa.py compare --c02 RUTA_CORRIDA_C02 --c04 RUTA_CORRIDA_C04 --render
~~~

La [guía PPA](docs/frecuencia/ppa.md) describe los requisitos, STA post-SPEF,
potencia con actividad y gráficos Mermaid/SVG. La automatización no implica
que una corrida física ya haya terminado; el [informe](reports/ppa/frequency.md)
identifica el nivel de evidencia de cada medición.

## Organización

La [arquitectura RTL serial de B01](docs/arquitectura-rtl-tiempo-serial.md) define el diseño temporal que implementa `rtl/time/fir_time_serial.sv` (B02), y la [arquitectura optimizada de B03](docs/arquitectura-rtl-tiempo-optimizada.md) elige la variante sistólica que implementará B04. La [arquitectura RTL serial de C01](docs/frecuencia/arquitectura-rtl-frecuencia-serial.md) reúne las decisiones de C02; el [contrato C04](docs/frecuencia/c04-implementacion.md) documenta la implementación optimizada en frecuencia y sus límites de evidencia PPA.

| Ruta | Contenido |
|---|---|
| `config/` | Parámetros confirmados y registro de variantes para CI. |
| `model/` | Generador QPSK y modelos flotante/fijo. |
| `rtl/time/`, `rtl/frequency/`, `rtl/frequency_optimized/` | Núcleos independientes; los testbenches inyectan vectores Python. |
| `tb/` | Testbenches y lectura de vectores. |
| `tests/` | Pruebas Python. |
| `vectors/` | Vectores pequeños y reproducibles. |
| `scripts/` | Validación, simulación y síntesis automatizada. |
| `constraints/` | Condiciones de reloj y tecnología para PPA. |
| `reports/` | Resultados finales y conclusiones trazables. |

Los mínimos del proyecto, confirmados por Enzo el 7/10/2026, son **SQNR ≥ 40 dB**, frecuencia de reloj **≥ 100 MHz para las variantes rápidas** y **≥ 10 MHz para las lentas**. El método de cálculo del SQNR, la tecnología para timing y la metodología de potencia deben quedar acordados antes de publicar comparaciones.
