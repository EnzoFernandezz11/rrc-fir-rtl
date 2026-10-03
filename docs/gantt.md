# Gantt del proyecto

**Versión inicial:** 2026-10-02. **Revisión con dependencias:** 2026-10-03. **Responsables:** @andres332271 = modelos/precisión, @moreyrajulian = tiempo, @EnzoFernandezz11 = frecuencia. Las fechas son una estimación para organizar el trabajo en días corridos (incluye fines de semana); la presentación será en una fecha acordada con el profesor antes de fin de 2026. Los IDs y dependencias corresponden al [backlog](backlog.md).

## Plan

Cada tarea arranca con `after` sobre sus dependencias **para empezar**, de modo que no puede comenzar antes que ellas; al cambiar una duración, las tareas siguientes se corren solas. Las dependencias **para cerrar** no se dibujan: la duración de cada barra se eligió para terminar después de ellas, y `tests/test_plan.py` falla si alguna regla se rompe. En Mermaid el fin es exclusivo: una barra que termina el 07/10 libera a la siguiente ese mismo día.

```mermaid
gantt
    title Plan con dependencias (ajustar con datos reales)
    dateFormat YYYY-MM-DD
    axisFormat %d/%m
    section Contrato y planificación
    E00 Consigna             :e00, 2026-10-05, 1d
    E01 Método frecuencia    :e01, 2026-10-05, 2d
    E02 Coeficientes         :e02, 2026-10-05, 3d
    E03 Interfaz y PPA       :e03, after e02, 3d
    G01 Gantt                :g01, 2026-10-05, 32d
    section Modelos y precisión (@andres332271)
    A01 QPSK y RRCOS         :a01, 2026-10-05, 2d
    A02 Flotante tiempo      :a02, after a01, 2d
    A03 Flotante frecuencia  :a03, after a02, 3d
    A04 Punto fijo           :a04, after a02, 4d
    A05 Vectores             :a05, after a04, 2d
    A06 Banco común          :a06, after a05 e03, 5d
    A07 Tabla PPA            :a07, after e03, 22d
    section Filtro temporal (@moreyrajulian)
    B01 Diseño serial        :b01, after e02, 3d
    B02 RTL serial           :b02, after b01, 5d
    B03 Elegir optimización  :b03, after b02, 3d
    B04 RTL optimizado       :b04, after b03, 9d
    section Filtro en frecuencia (@EnzoFernandezz11)
    C01 Diseño serial        :c01, after e01, 5d
    C02 RTL serial           :c02, after c01, 8d
    C03 Elegir optimización  :c03, after c02, 2d
    C04 RTL optimizado       :c04, after c03, 11d
    section Integración y presentación
    I01 Comparación          :i01, after b04 c04 a07, 2d
    I02 Informe              :i02, 2026-10-14, 23d
    I03 Filminas borrador    :i03, after i01, 2d
```

G01, I02 e I03 terminan con la versión borrador para la presentación; se extienden cuando se confirme la fecha.

## Avance real

Esta tabla registra lo que efectivamente pasó y quién lo hizo, que es lo exigido para explicar el reparto real. Las fechas planificadas están solo en el diagrama: anotar aquí inicio y fin reales cuando ocurran, sin tocar el plan salvo para replanificar.

| ID | Responsable real | Inicio real | Fin real | Estado/notas |
|---|---|---|---|---|
| [E00](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/1) | — | — | — | — |
| [E01](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/2) | — | — | — | Consulta docente si hace falta. |
| [E02](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/3) | — | — | — | — |
| [E03](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/4) | — | — | — | — |
| [G01](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/5) | — | — | — | Actualizar semanalmente. |
| [A01](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/6) | — | — | — | — |
| [A02](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/7) | — | — | — | — |
| [A03](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/8) | — | — | — | — |
| [A04](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/9) | — | — | — | — |
| [A05](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/10) | — | — | — | Corte para cerrar B02/C02. |
| [B01](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/11) | — | — | — | — |
| [B02](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/12) | — | — | — | — |
| [C01](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/13) | — | — | — | — |
| [C02](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/14) | — | — | — | — |
| [A06](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/15) | — | — | — | — |
| [B03](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/16) | — | — | — | — |
| [B04](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/17) | — | — | — | — |
| [C03](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/18) | — | — | — | — |
| [C04](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/19) | — | — | — | Camino crítico hasta I01. |
| [A07](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/20) | — | — | — | Empieza con variantes disponibles. |
| [I01](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/21) | — | — | — | — |
| [I02](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/22) | — | — | — | Borrador temprano; conclusiones tras I01. |
| [I03](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/23) | — | — | — | Fecha final pendiente de acordar. |

## Corte del viernes 16/10

Meta: 18 de 23 tareas con evidencia de inicio (78 %). Es el máximo que permite el plan sin violar dependencias; la versión anterior apuntaba a 19 porque varias tareas empezaban antes que sus predecesoras. El avance real se comunica separado en tres cifras: **iniciadas**, **integradas** y **verificadas**. La cantidad de tarjetas movidas no sustituye el vector matching. Si E01 o C02 se retrasan, registrar la causa y ajustar fechas y responsable; no empezar C03 para mejorar el porcentaje.
