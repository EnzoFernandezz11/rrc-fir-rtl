# Backlog inicial para issues

Este listado enlaza las **23 issues creadas en GitHub**. Cada fila aporta título, responsable sugerido, dependencias y un criterio de cierre. **Para empezar** lista las tareas que deben estar cerradas antes de iniciar; **Para cerrar**, las que deben estarlo antes de dar la tarea por terminada. Así el trabajo avanza en paralelo sin cerrar nada sobre resultados que todavía no existen. Este archivo es la fuente de las dependencias: el [Gantt](gantt.md) las respeta y `tests/test_plan.py` lo comprueba. **A/B/C son roles**, no usuarios asignados; actualizar los responsables cuando los compañeros acepten la invitación. El estado de cada tarea se sigue en el [Project](https://github.com/users/EnzoFernandezz11/projects/4). Mantener los IDs para enlazar el [Gantt](gantt.md), el [contrato](contrato-tecnico.md) y los PR.

| ID y título sugerido | Responsable | Para empezar | Para cerrar | Criterio de cierre |
|---|---|---|---|---|
| **[E00 — Registrar consigna y requisitos](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/1)** | A; B/C revisan | — | — | Contrato técnico con requisitos confirmados, dudas y fuentes. |
| **[E01 — Definir filtro en frecuencia](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/2)** | C; A/B revisan | — | E00 | Transformada, bloques, solapamiento, salida y latencia documentados o consulta docente registrada. |
| **[E02 — Cerrar coeficientes y formato numérico](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/3)** | A; B/C revisan | — | E00, A01 | Tabla exacta de 8 coeficientes, normalización, mapeo QPSK/I-Q, anchos provisionales de interfaz y ejemplos. Los anchos internos y el redondeo los fija A04. |
| **[E03 — Cerrar interfaz RTL y medición PPA](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/4)** | B/C; A revisa | E02 | E01 | Puertos, `valid`, reloj, tecnología, constraints y métodos de medición definidos. |
| **[G01 — Mantener Gantt planificado y real](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/5)** | A; B/C actualizan | — | — | Tareas, responsables y fechas planificadas/reales actualizadas hasta la entrega. |
| **[A01 — Generar QPSK y RRCOS](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/6)** | A; B/C revisan | — | — | Generación reproducible con semilla, 8 coeficientes y respuesta al impulso. |
| **[A02 — Modelo flotante temporal](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/7)** | A; B revisa | A01 | — | Referencia Python con impulso, ceros y QPSK exportados con índices. |
| **[A03 — Modelo flotante en frecuencia](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/8)** | A; C revisa | A02 | E01 | Correspondencia con temporal para varias secuencias y bordes de bloque. |
| **[A04 — Elegir anchos de punto fijo](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/9)** | A; B/C revisan | A02 | A03 | Barrido reproducible y evidencia SQNR ≥ 40 dB sin overflow oculto. Fija anchos, redondeo y saturación de cada nodo y confirma o corrige los anchos de interfaz de E02. |
| **[A05 — Exportar vectores y formato de intercambio](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/10)** | A; B/C revisan | A04 | — | Archivo de entrada/salida y lector documentados, reproducibles sin edición manual. |
| **[B01 — Diseñar filtro temporal serial](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/11)** | B; A revisa | E02 | E03 | Diagrama de estados, recursos y cronograma de ciclos. |
| **[B02 — RTL y testbench temporal serial](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/12)** | B; A revisa | B01 | A05 | Simulación sintetizable con vector matching, impulso y bordes. |
| **[C01 — Diseñar filtro en frecuencia serial](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/13)** | C; A revisa | E01 | E03, A03 | Operaciones por bloque, buffers, recursos y latencia calculados. |
| **[C02 — RTL y testbench en frecuencia serial](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/14)** | C; A revisa | C01 | A05 | Vector matching con modelo fijo y manejo de bordes/solapamiento. |
| **[A06 — Banco común de verificación](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/15)** | A; B/C colaboran | A05, E03 | B02, C02 | Un comando corre ambas simulaciones y da PASS/FAIL con diagnóstico. |
| **[B03 — Elegir optimización temporal](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/16)** | B; A revisa | B01 | — | Se hace en paralelo con B02. Opción permitida y predicción de compromiso PPA documentadas. |
| **[B04 — RTL temporal optimizado](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/17)** | B; A/C revisan | B02, B03 | A06 | Mismos vectores, regresión y reporte de síntesis/timing reproducibles. |
| **[C03 — Elegir optimización en frecuencia](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/18)** | C; A revisa | C01 | — | Se hace en paralelo con C02. Opción permitida, memoria y compromiso PPA documentados. |
| **[C04 — RTL en frecuencia optimizado](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/19)** | C; A/B revisan | C02, C03 | A06 | Mismos vectores, regresión y reporte de síntesis/timing reproducibles. |
| **[A07 — Automatizar tabla PPA](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/20)** | A; B/C colaboran | E03 | B04, C04 | Script y tabla trazables a logs; se completa con B04/C04. |
| **[I01 — Comparar las cuatro variantes](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/21)** | Los tres; A integra | B04, C04, A07 | — | Tabla bajo mismas condiciones y conclusiones sobre PPA/SQNR. |
| **[I02 — Redactar informe técnico](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/22)** | A; B/C redactan secciones | A01 | B02, C02, I01 | Metodología, resultados, límites y comandos reproducibles. Puede empezar como borrador. |
| **[I03 — Preparar filminas y demo](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/23)** | Los tres | B02, C02 | I01, I02, G01 | Se arma con los resultados seriales y se completa con I01. Cada uno presenta su implementación; incluye Gantt y aprendizajes. |

## Etiquetas sugeridas

`spec`, `model`, `fixed-point`, `rtl-time`, `rtl-frequency`, `verification`, `ppa`, `docs`, `gantt`, `blocked`. Las etiquetas describen el área; el estado de trabajo corresponde al Project. Columnas sugeridas: **Pendiente → Listo → En curso → En revisión → Bloqueado → Hecho**.

## Hitos

1. **H0:** E00–E03 acordados y G01 iniciado.
2. **H1:** modelos flotantes/fijos y vectores listos (A01–A05).
3. **H2:** ambas versiones seriales con vector matching (B02, C02, A06).
4. **H3:** optimizaciones y PPA comparables (B04, C04, A07, I01).
5. **Entrega (30/10):** informe, filminas, demo y Gantt real (I02, I03, G01).

Meta tentativa del 16/10: **20/23 issues comenzadas con evidencia**, no 20 terminadas; es lo máximo que permite el plan sin violar dependencias. El registro de [Gantt](gantt.md) distingue tareas iniciadas, integradas y verificadas.
