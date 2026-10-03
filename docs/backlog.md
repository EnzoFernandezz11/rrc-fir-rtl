# Backlog inicial para issues

Este listado enlaza las **23 issues creadas en GitHub**. Cada fila aporta título, responsable sugerido, dependencias y un criterio de cierre. **Para empezar** lista las tareas que deben estar cerradas antes de iniciar; **Para cerrar**, las que deben estarlo antes de dar la tarea por terminada. Así el trabajo avanza en paralelo sin cerrar nada sobre resultados que todavía no existen. Este archivo es la fuente de las dependencias: el [Gantt](gantt.md) las respeta y `tests/test_plan.py` lo comprueba. Los responsables son @andres332271 (modelos y precisión), @moreyrajulian (filtro temporal) y @EnzoFernandezz11 (filtro en frecuencia); las issues están asignadas a sus cuentas. El estado de cada tarea se sigue en el [Project](https://github.com/users/EnzoFernandezz11/projects/4). Mantener los IDs para enlazar el [Gantt](gantt.md), el [contrato](contrato-tecnico.md) y los PR.

| ID y título sugerido | Responsable | Para empezar | Para cerrar | Criterio de cierre |
|---|---|---|---|---|
| **[E00 — Registrar consigna y requisitos](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/1)** | @andres332271; @moreyrajulian y @EnzoFernandezz11 revisan | — | — | Contrato técnico con requisitos confirmados, dudas y fuentes. |
| **[E01 — Definir filtro en frecuencia](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/2)** | @EnzoFernandezz11; @andres332271 y @moreyrajulian revisan | — | E00 | Transformada, bloques, solapamiento, salida y latencia documentados o consulta docente registrada. |
| **[E02 — Cerrar coeficientes y formato numérico](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/3)** | @andres332271; @moreyrajulian y @EnzoFernandezz11 revisan | — | E00, A01 | Tabla exacta de 8 coeficientes, normalización, mapeo QPSK/I-Q, anchos provisionales de interfaz y ejemplos. Los anchos internos y el redondeo los fija A04. |
| **[E03 — Cerrar interfaz RTL y medición PPA](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/4)** | @moreyrajulian y @EnzoFernandezz11; @andres332271 revisa | E02 | E01 | Puertos, `valid`, reloj, tecnología, constraints y métodos de medición definidos. |
| **[G01 — Mantener Gantt planificado y real](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/5)** | @andres332271; @moreyrajulian y @EnzoFernandezz11 actualizan | — | — | Tareas, responsables y fechas planificadas/reales actualizadas hasta la entrega. |
| **[A01 — Generar QPSK y RRCOS](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/6)** | @andres332271; @moreyrajulian y @EnzoFernandezz11 revisan | — | — | Generación reproducible con semilla, 8 coeficientes y respuesta al impulso. |
| **[A02 — Modelo flotante temporal](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/7)** | @andres332271; @moreyrajulian revisa | A01 | — | Referencia Python con impulso, ceros y QPSK exportados con índices. |
| **[A03 — Modelo flotante en frecuencia](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/8)** | @andres332271; @EnzoFernandezz11 revisa | A02 | E01 | Correspondencia con temporal para varias secuencias y bordes de bloque. |
| **[A04 — Elegir anchos de punto fijo](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/9)** | @andres332271; @moreyrajulian y @EnzoFernandezz11 revisan | A02 | A03 | Barrido reproducible y evidencia SQNR ≥ 40 dB sin overflow oculto. Fija anchos, redondeo y saturación de cada nodo y confirma o corrige los anchos de interfaz de E02. |
| **[A05 — Exportar vectores y formato de intercambio](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/10)** | @andres332271; @moreyrajulian y @EnzoFernandezz11 revisan | A04 | — | Archivo de entrada/salida y lector documentados, reproducibles sin edición manual. |
| **[B01 — Diseñar filtro temporal serial](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/11)** | @moreyrajulian; @andres332271 revisa | E02 | E03 | Diagrama de estados, recursos y cronograma de ciclos. |
| **[B02 — RTL y testbench temporal serial](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/12)** | @moreyrajulian; @andres332271 revisa | B01 | A05 | Simulación sintetizable con vector matching, impulso y bordes. |
| **[C01 — Diseñar filtro en frecuencia serial](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/13)** | @EnzoFernandezz11; @andres332271 revisa | E01 | E03, A03 | Operaciones por bloque, buffers, recursos y latencia calculados. |
| **[C02 — RTL y testbench en frecuencia serial](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/14)** | @EnzoFernandezz11; @andres332271 revisa | C01 | A05 | Vector matching con modelo fijo y manejo de bordes/solapamiento. |
| **[A06 — Banco común de verificación](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/15)** | @andres332271; @moreyrajulian y @EnzoFernandezz11 colaboran | A05, E03 | B02, C02 | Un comando corre ambas simulaciones y da PASS/FAIL con diagnóstico. |
| **[B03 — Elegir optimización temporal](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/16)** | @moreyrajulian; @andres332271 revisa | B02 | — | Opción permitida y predicción de compromiso PPA documentadas. |
| **[B04 — RTL temporal optimizado](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/17)** | @moreyrajulian; @andres332271 y @EnzoFernandezz11 revisan | B03 | A06 | Mismos vectores, regresión y reporte de síntesis/timing reproducibles. |
| **[C03 — Elegir optimización en frecuencia](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/18)** | @EnzoFernandezz11; @andres332271 revisa | C02 | — | Opción permitida, memoria y compromiso PPA documentados. |
| **[C04 — RTL en frecuencia optimizado](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/19)** | @EnzoFernandezz11; @andres332271 y @moreyrajulian revisan | C03 | A06 | Mismos vectores, regresión y reporte de síntesis/timing reproducibles. |
| **[A07 — Automatizar tabla PPA](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/20)** | @andres332271; @moreyrajulian y @EnzoFernandezz11 colaboran | E03 | B04, C04 | Script y tabla trazables a logs; se completa con B04/C04. |
| **[I01 — Comparar las cuatro variantes](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/21)** | @andres332271, @moreyrajulian y @EnzoFernandezz11; @andres332271 integra | B04, C04, A07 | — | Tabla bajo mismas condiciones y conclusiones sobre PPA/SQNR. |
| **[I02 — Redactar informe técnico](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/22)** | @andres332271; @moreyrajulian y @EnzoFernandezz11 redactan secciones | A01 | B02, C02, I01 | Metodología, resultados, límites y comandos reproducibles. Puede empezar como borrador. |
| **[I03 — Preparar filminas y demo](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/23)** | @andres332271, @moreyrajulian y @EnzoFernandezz11 | I01 | I02, G01 | Cada uno presenta su implementación; incluye Gantt y aprendizajes. |

## Etiquetas sugeridas

`spec`, `model`, `fixed-point`, `rtl-time`, `rtl-frequency`, `verification`, `ppa`, `docs`, `gantt`, `blocked`. Las etiquetas describen el área; el estado de trabajo corresponde al Project. Columnas sugeridas: **Pendiente → Listo → En curso → En revisión → Bloqueado → Hecho**.

## Hitos

1. **H0:** E00–E03 acordados y G01 iniciado.
2. **H1:** modelos flotantes/fijos y vectores listos (A01–A05).
3. **H2:** ambas versiones seriales con vector matching (B02, C02, A06).
4. **H3:** optimizaciones y PPA comparables (B04, C04, A07, I01).
5. **Entrega:** informe, filminas, demo y Gantt real (I02, I03, G01).

Meta tentativa del 16/10: **18/23 issues comenzadas con evidencia**, no 18 terminadas; es lo máximo que permite el plan sin violar dependencias. El registro de [Gantt](gantt.md) distingue tareas iniciadas, integradas y verificadas.
