# Filtros RRCOS complejos en RTL

Proyecto final: dos implementaciones de un filtro complejo de 8 coeficientes, una en el dominio del tiempo y otra en frecuencia. La entrada usa símbolos QPSK con sobremuestreo 2× y el RRCOS tiene roll-off de 50 %. El trabajo compara versiones seriales y optimizadas con foco en rendimiento, potencia y área (PPA).

## Estado actual

Este repositorio contiene el **andamiaje de trabajo**. Aún no hay coeficientes definitivos, modelo Python del filtro ni RTL. Esos resultados corresponden a las tareas del [backlog](docs/backlog.md). La [consigna actualizada](docs/consigna-actualizada.md) (6/10/2026) es la vigente; la [primera versión actualizada](docs/consigna-actualizada-v1.md) y la [consigna original](docs/consigna-original.md) se conservan tal como fueron recibidas. Los parámetros confirmados y las decisiones pendientes se registran en el [contrato técnico](docs/contrato-tecnico.md) y los [contratos de trabajo](docs/contratos/README.md); nadie debe deducir coeficientes o formatos a partir del nombre de un archivo.

Las [23 issues](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues) están en el [Project del equipo](https://github.com/users/EnzoFernandezz11/projects/4) con estados, responsables asignados y fechas previstas. [Andrés (@andres332271)](https://github.com/andres332271) lleva modelos y precisión; [Julián (@moreyrajulian)](https://github.com/moreyrajulian), el filtro temporal; y [Enzo (@EnzoFernandezz11)](https://github.com/EnzoFernandezz11), el filtro en frecuencia. Cada integrante puede filtrar sus tareas por asignado en las [issues](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues) o en la vista correspondiente del Project.

| Integrante | Issues asignadas | Vista del Project |
|---|---|---|
| @andres332271 | [Ver issues](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues?q=is%3Aissue+assignee%3Aandres332271) | [Andrés](https://github.com/users/EnzoFernandezz11/projects/4/views/5) |
| @moreyrajulian | [Ver issues](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues?q=is%3Aissue+assignee%3Amoreyrajulian) | [Julián](https://github.com/users/EnzoFernandezz11/projects/4/views/6) |
| @EnzoFernandezz11 | [Ver issues](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues?q=is%3Aissue+assignee%3AEnzoFernandezz11) | [Enzo](https://github.com/users/EnzoFernandezz11/projects/4/views/7) |

## Primeros pasos

1. Leer el [contrato técnico](docs/contrato-tecnico.md) y cerrar E00–E03 entre los tres. Registrar allí las respuestas del docente y los supuestos provisionales.
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

El registro de RTL está vacío mientras no exista una implementación. **Agregar una variante al registro en el mismo PR que incorpora su RTL y testbench.** Si una variante registrada falta o su simulación falla, `make smoke` falla; el mensaje inicial de «0 variantes» no cuenta como vector matching.

## Organización

| Ruta | Contenido |
|---|---|
| `config/` | Parámetros confirmados y registro de variantes para CI. |
| `model/` | Generador QPSK y modelos flotante/fijo. |
| `rtl/time/`, `rtl/frequency/`, `rtl/common/` | Implementaciones y bloques compartidos. |
| `tb/` | Testbenches y lectura de vectores. |
| `tests/` | Pruebas Python. |
| `vectors/` | Vectores pequeños y reproducibles. |
| `scripts/` | Validación, simulación y síntesis automatizada. |
| `constraints/` | Condiciones de reloj y tecnología para PPA. |
| `reports/` | Resultados finales y conclusiones trazables. |

La meta de precisión es **SQNR ≥ 40 dB**. Las variantes rápidas apuntan a **100 MHz** y las lentas a **10 MHz**. El método de cálculo del SQNR, la tecnología para timing y la metodología de potencia deben quedar acordados antes de publicar comparaciones.
