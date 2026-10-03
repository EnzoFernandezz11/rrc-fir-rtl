# Guía de trabajo

Somos tres personas: @andres332271 lleva modelos, precisión, vectores y automatización; @moreyrajulian lleva el filtro temporal; @EnzoFernandezz11 lleva el filtro en frecuencia. Cada persona revisa trabajo de las otras. La [lista de tareas](docs/backlog.md) define entregables y dependencias.

## Ramas e issues

- `main` debe poder ejecutar `make smoke` en todo momento. Una rama sale de `main`, cubre una issue y vuelve por PR. Ejemplos: `spec/e02-formatos`, `andres332271/a05-vectores`, `moreyrajulian/b02-serial-tiempo`, `EnzoFernandezz11/c02-serial-frecuencia`.
- Usar el ID del backlog en título de rama, PR y commits cuando sea útil. Abrir un PR en borrador temprano si hay una decisión que afecte a otra persona.
- Mantener una tarea técnica principal en curso por persona. Los PR pequeños facilitan revisión; separar contrato/modelo, RTL, testbench y PPA si son cambios independientes.
- Una tarea puede empezar cuando están cerradas sus dependencias **para empezar** del [backlog](docs/backlog.md), y solo se cierra cuando también lo están las de **para cerrar**. Si cambian dependencias o duraciones, actualizar backlog y [Gantt](docs/gantt.md) en el mismo PR; `make smoke` comprueba que sigan siendo consistentes.
- Antes de avanzar una tarea dependiente, verificar que la decisión de la que depende esté registrada en `docs/contrato-tecnico.md`.

## Contrato compartido

`docs/contrato-tecnico.md` explica las decisiones; `config/project.json` guarda los valores que consumen scripts. Si cambian coeficientes, escala, interfaz o método en frecuencia, actualizar ambos en el mismo PR y enumerar qué vectores/modelos/RTL se ven afectados. Una decisión provisional no se vuelve confirmada por usarla en código. E00–E03 requieren revisión de @andres332271, @moreyrajulian y @EnzoFernandezz11.

## Qué presentar en un PR

- Issue vinculada, objetivo y dependencias.
- Cambios en función, precisión, latencia, throughput o recursos, cuando correspondan.
- Comando para reproducir la prueba, semilla/configuración y evidencia PASS/FAIL.
- Para optimizaciones, comparación con la versión serial en las mismas condiciones y fuente del dato PPA.
- Preguntas concretas para el revisor y riesgos conocidos.

Una aprobación de otro integrante alcanza para cambios ordinarios. Los cambios del contrato numérico o del algoritmo requieren acuerdo de los tres. No integrar si falla `smoke`; si el problema es de la CI, corregirlo en un PR. No aceptar una prueba que pase por omitir silenciosamente una variante registrada.

## Reglas de `main`

- Integrar solo por PR, con una revisión de otra persona cuando ya haya colaboradores.
- El check requerido es `smoke` de `RTL CI`, sin filtros por rutas: los PR de documentación también lo ejecutan. El job `full` es informativo al integrar o al ejecutarlo manualmente.
- Sin push directo ni force push a `main` una vez configuradas las reglas. No guardar tokens en el repositorio.

## Archivos generados

No versionar binarios de simulación, VCD grandes, logs temporales, entornos Python ni archivos de `build/`. Versionar scripts, constraints, semillas, configuraciones y tablas finales pequeñas. El Gantt en `docs/gantt.md` se actualiza semanalmente con inicio y fin reales, para poder mostrar la distribución de trabajo en la presentación.
