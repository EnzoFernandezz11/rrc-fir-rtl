# Backlog inicial para issues

Este es el listado de tareas listo para trasladar a GitHub Issues. Cada fila aporta título, responsable sugerido, dependencias y un criterio de cierre. **A/B/C son roles**, no usuarios asignados; actualizar los responsables cuando los compañeros acepten la invitación. La columna de estado vive luego en GitHub Projects. Mantener los IDs al crear issues para poder enlazar el [Gantt](gantt.md), el [contrato](contrato-tecnico.md) y los PR.

| ID y título sugerido | Responsable | Depende de | Criterio de cierre |
|---|---|---|---|
| **E00 — Registrar consigna y requisitos** | A; B/C revisan | — | Contrato técnico con requisitos confirmados, dudas y fuentes. |
| **E01 — Definir filtro en frecuencia** | C; A/B revisan | E00 | Transformada, bloques, solapamiento, salida y latencia documentados o consulta docente registrada. |
| **E02 — Cerrar coeficientes y formato numérico** | A; B/C revisan | E00 | Tabla exacta de 8 coeficientes, normalización, QPSK, I/Q, redondeo y ejemplos. |
| **E03 — Cerrar interfaz RTL y medición PPA** | B/C; A revisa | E01, E02 | Puertos, `valid`, reloj, tecnología, constraints y métodos de medición definidos. |
| **G01 — Mantener Gantt planificado y real** | A; B/C actualizan | E00 | Tareas, responsables y fechas planificadas/reales actualizadas hasta la entrega. |
| **A01 — Generar QPSK y RRCOS** | A; B/C revisan | E02 | Generación reproducible con semilla, 8 coeficientes y respuesta al impulso. |
| **A02 — Modelo flotante temporal** | A; B revisa | A01 | Referencia Python con impulso, ceros y QPSK exportados con índices. |
| **A03 — Modelo flotante en frecuencia** | A; C revisa | E01, A02 | Correspondencia con temporal para varias secuencias y bordes de bloque. |
| **A04 — Elegir anchos de punto fijo** | A; B/C revisan | A02, A03 | Barrido reproducible y evidencia SQNR ≥ 40 dB sin overflow oculto. |
| **A05 — Exportar vectores y formato de intercambio** | A; B/C revisan | A04 | Archivo de entrada/salida y lector documentados, reproducibles sin edición manual. |
| **B01 — Diseñar filtro temporal serial** | B; A revisa | E02, E03 | Diagrama de estados, recursos y cronograma de ciclos. |
| **B02 — RTL y testbench temporal serial** | B; A revisa | B01, A05 | Simulación sintetizable con vector matching, impulso y bordes. |
| **C01 — Diseñar filtro en frecuencia serial** | C; A revisa | E01, E03, A03 | Operaciones por bloque, buffers, recursos y latencia calculados. |
| **C02 — RTL y testbench en frecuencia serial** | C; A revisa | C01, A05 | Vector matching con modelo fijo y manejo de bordes/solapamiento. |
| **A06 — Banco común de verificación** | A; B/C colaboran | A05, B02, C02 | Un comando corre ambas simulaciones y da PASS/FAIL con diagnóstico. |
| **B03 — Elegir optimización temporal** | B; A revisa | B02 | Opción permitida y predicción de compromiso PPA documentadas. |
| **B04 — RTL temporal optimizado** | B; A/C revisan | B03, A06 | Mismos vectores, regresión y reporte de síntesis/timing reproducibles. |
| **C03 — Elegir optimización en frecuencia** | C; A revisa | C02 | Opción permitida, memoria y compromiso PPA documentados. |
| **C04 — RTL en frecuencia optimizado** | C; A/B revisan | C03, A06 | Mismos vectores, regresión y reporte de síntesis/timing reproducibles. |
| **A07 — Automatizar tabla PPA** | A; B/C colaboran | E03, B02, C02 | Script y tabla trazables a logs; se completa con B04/C04. |
| **I01 — Comparar las cuatro variantes** | Los tres; A integra | B04, C04, A07 | Tabla bajo mismas condiciones y conclusiones sobre PPA/SQNR. |
| **I02 — Redactar informe técnico** | A; B/C redactan secciones | A01, B02, C02, I01 | Metodología, resultados, límites y comandos reproducibles. Puede empezar como borrador. |
| **I03 — Preparar filminas y demo** | Los tres | I01, I02, G01 | Cada uno presenta su implementación; incluye Gantt y aprendizajes. |

## Etiquetas sugeridas

`spec`, `model`, `fixed-point`, `rtl-time`, `rtl-frequency`, `verification`, `ppa`, `docs`, `gantt`, `blocked`. Las etiquetas describen el área; el estado de trabajo corresponde al Project. Columnas sugeridas: **Pendiente → Listo → En curso → En revisión → Bloqueado → Hecho**.

## Hitos

1. **H0:** E00–E03 acordados y G01 iniciado.
2. **H1:** modelos flotantes/fijos y vectores listos (A01–A05).
3. **H2:** ambas versiones seriales con vector matching (B02, C02, A06).
4. **H3:** optimizaciones y PPA comparables (B04, C04, A07, I01).
5. **Entrega:** informe, filminas, demo y Gantt real (I02, I03, G01).

Meta tentativa del 16/10: **19/23 issues comenzadas con evidencia**, no 19 terminadas. El registro de [Gantt](gantt.md) distingue tareas iniciadas, integradas y verificadas.
