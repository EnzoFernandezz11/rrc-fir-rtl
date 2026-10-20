# Gantt del proyecto

**Versión inicial:** 2026-10-02. **Revisión con dependencias:** 2026-10-03. **Ajuste a la fecha límite:** 2026-10-05. **Avance real:** 2026-10-07, 2026-10-12, 2026-10-14 y 2026-10-17. **Responsables:** @andres332271 = modelos/precisión, @moreyrajulian = tiempo, @EnzoFernandezz11 = frecuencia. Las fechas son una estimación para organizar el trabajo en días corridos (incluye fines de semana); todo debe estar terminado antes del **30/10**, fecha límite de la presentación. Los IDs y dependencias corresponden al [backlog](backlog.md).

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
    G01 Gantt                :g01, 2026-10-05, 25d
    section Modelos y precisión (@andres332271)
    A01 QPSK y RRCOS         :a01, 2026-10-05, 2d
    A02 Flotante tiempo      :a02, after a01, 2d
    A03 Flotante frecuencia  :a03, after a02, 3d
    A04 Punto fijo           :a04, after a02, 4d
    A05 Vectores             :a05, after a04, 2d
    A06 Banco común          :a06, after a05 e03, 5d
    A07 Tabla PPA            :a07, after e03, 18d
    section Filtro temporal (@moreyrajulian)
    B01 Diseño serial        :b01, after e02, 3d
    B02 RTL serial           :b02, after b01, 5d
    B03 Elegir optimización  :b03, after b01, 3d
    B04 RTL optimizado       :b04, after b02 b03, 9d
    section Filtro en frecuencia (@EnzoFernandezz11)
    C01 Diseño serial        :c01, after e01, 5d
    C02 RTL serial           :c02, after c01, 8d
    C03 Elegir optimización  :c03, after c01, 2d
    C04 RTL optimizado       :c04, after c02 c03, 9d
    section Integración y presentación
    I01 Comparación          :i01, after b04 c04 a07, 1d
    I02 Informe              :i02, 2026-10-14, 16d
    I03 Filminas             :i03, after b02 c02, 10d
```

G01, I02 e I03 terminan el 29/10, el día anterior a la presentación. Para entrar en el plazo, B03 y C03 se hacen en paralelo con el serial, I03 arranca con los resultados seriales, I01 dura un día y C04 baja a 9 días. C04 queda en el camino crítico sin margen; B04 tiene 4 días de holgura.

**Corte de C04 (lunes 26/10):** si C04 no pasa el vector matching, se presenta C serial (C02) contra B optimizado (B04), C04 queda como trabajo futuro en el informe y se avisa al profesor.

## Avance real

Esta tabla registra lo que efectivamente pasó y quién lo hizo, que es lo exigido para explicar el reparto real. Las fechas planificadas están solo en el diagrama: anotar aquí inicio y fin reales cuando ocurran, sin tocar el plan salvo para replanificar.

**Al 17/10:** 19 de 23 tareas iniciadas (todas salvo B04, C04, I01 e I03), 14 integradas (E00–E03, A01–A05, B01–B03, C01 y C02) y 2 verificadas (B02 y C02: vector matching A05 integrado, también en el banco común de A06). Según el plan deberían haber empezado 20: falta B04 (plan 16/10). En revisión: A06 (#53), A07 (#52), C03 (#50, aprobada) y la corrección del flujo PPA (#51). Las fechas son locales; GitHub muestra UTC, y un PR abierto de noche puede figurar con el día siguiente.

Riesgos al 17/10:

- **Rama temporal:** B02 cerró el 14/10 y B03 el 16/10, 3 días después del plan. B04 no empezó (plan 16/10); si arranca el 18/10, sus 9 días terminan el 26/10 y la holgura hasta I01 (29/10) baja de 4 a 2 días.
- **Rama en frecuencia:** C02 se integró el 15/10, 4 días antes del plan, y C03 está aprobada. Si C04 arranca el 18/10, termina el 26/10, el mismo día del corte, y gana 2 días de holgura frente al plan (inicio 20/10). La propuesta de C03 estima ≈ 77 % de las LUT del xc7a35t, lo que deja poco margen; C04 debe sintetizar pronto las redes constantes.
- **Modelos e integración:** A06 y A07 tienen PR; la tabla PPA ya mide B02 y C02 en Vivado, y B04/C04 se suman con el mismo flujo. I03 puede empezar antes del 20/10 porque sus dependencias ya cerraron. Hay tres PR esperando revisión (#51, #52, #53).

| ID | Responsable real | Inicio real | Fin real | Estado/notas |
|---|---|---|---|---|
| [E00](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/1) | @andres332271 | 05/10 | 07/10 | Consigna actualizada en #27 y segunda versión en #29 (06/10). |
| [E01](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/2) | @EnzoFernandezz11 | 05/10 | 08/10 | #28 integrado. Plan: fin 06/10 (+2 días). |
| [E02](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/3) | @andres332271 | 07/10 | 08/10 | #33 integrado; D02/D03 siguen propuestos hasta la revisión conjunta. Plan: fin 07/10 (+1). |
| [E03](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/4) | @moreyrajulian | 09/10 | 09/10 | #38 integrado; D03, D05 y D06 siguen propuestos. Plan: fin 10/10 (−1). |
| [G01](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/5) | @andres332271 | 03/10 | — | #24, #27, #34, #43, #46 y este registro. Actualizar semanalmente. |
| [A01](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/6) | @andres332271 | 07/10 | 08/10 | #32 integrado. Plan: fin 06/10 (+2). |
| [A02](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/7) | @andres332271 | 07/10 | 09/10 | #35 integrado. Plan: fin 08/10 (+1). |
| [A03](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/8) | @andres332271 | 12/10 | 12/10 | #40 integrado; error máx. entre modelos flotantes < 2e-14. Plan: fin 11/10 (+1). |
| [A04](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/9) | @andres332271 | 12/10 | 12/10 | #41 integrado: salida Q2.7 (9 bits), SQNR 44,2/43,0 dB. Plan: fin 12/10. |
| [A05](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/10) | @andres332271 | 12/10 | 13/10 | #42 integrado. Plan: inicio 13/10, fin 14/10 (−1). |
| [B01](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/11) | @moreyrajulian | 12/10 | 13/10 | #44 integrado: `L = 9`, `II = 10`, 56 FF estimados. Plan: inicio 08/10, fin 10/10 (+3). |
| [B02](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/12) | @moreyrajulian | 14/10 | 14/10 | #45 integrado: vector matching, `L = 9`, `II = 10`, pausas y reset en medio de trama. Plan: fin 15/10 (−1). |
| [C01](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/13) | @EnzoFernandezz11 | 06/10 | 13/10 | #39 integrado tras quitar R01. Plan: fin 11/10 (+2). |
| [C02](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/14) | @EnzoFernandezz11 | 12/10 | 15/10 | #47 integrado: vector matching A05, `L = 559`, 575 ciclos por bloque, `run.tcl` parametrizado. Plan: fin 19/10 (−4). |
| [A06](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/15) | @andres332271 | 14/10 | — | #53 en revisión: `make regresion` pasa con B02 y C02 integrados (vector matching, reset en trama y pausas). Plan: inicio 15/10 (−1), fin 19/10. |
| [B03](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/16) | @moreyrajulian | 15/10 | 16/10 | #49 integrado: sistólica en forma transpuesta, `II = 1`, `L = 1`, 100 MHz; D08 temporal propuesto. Plan: inicio 11/10, fin 13/10 (+3). |
| [B04](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/17) | — | — | — | Plan: inicio 16/10, fin 24/10. Sus dependencias cerraron el 16/10. |
| [C03](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/18) | @EnzoFernandezz11 | 15/10 | — | #50 aprobado el 17/10: FFT/IFFT desplegadas, 16 productos espectrales con H fijo y redes CSD, 100 MHz. Falta pasar la base a `main` y registrar D08. Plan: inicio 12/10, fin 13/10 (+3). |
| [C04](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/19) | — | — | — | Plan: inicio 20/10. Camino crítico hasta I01; puede arrancar al integrarse C03. |
| [A07](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/20) | @andres332271 | 14/10 | — | #52 en revisión: tabla PPA desde Vivado con B02 y C02 a 10 y 100 MHz y banco PPA temporal; B04/C04 se agregan con `--import`. Incluye la corrección de #51. Plan: inicio 11/10 (+3), fin 28/10. |
| [I01](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/21) | — | — | — | — |
| [I02](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/22) | @andres332271 | 15/10 | — | #48 en borrador: secciones 1–6 y PPA serial redactadas; faltan 7–9 (Julián y Enzo), Gantt y conclusiones. Plan: inicio 14/10 (+1). |
| [I03](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/23) | — | — | — | Plan: inicio 20/10 (B02 y C02 ya integradas). Presentación 30/10. |

## Corte del viernes 16/10

Meta: 20 de 23 tareas con evidencia de inicio (87 %). Es el máximo que permite el plan sin violar dependencias; solo I01 y C04 (y por lo tanto el cierre de I03) dependen de resultados posteriores. El avance real se comunica separado en tres cifras: **iniciadas**, **integradas** y **verificadas**. La cantidad de tarjetas movidas no sustituye el vector matching. Si E01 o C02 se retrasan, registrar la causa y ajustar fechas y responsable; no empezar C04 sin C02 para mejorar el porcentaje.

**Resultado al 16/10:** 19 de 23 iniciadas (83 %); faltó B04, cuyas dependencias cerraron ese mismo día. Integradas: 14; verificadas: 2.
