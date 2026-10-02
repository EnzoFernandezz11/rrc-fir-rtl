# Configuración pendiente en GitHub

Este archivo registra el estado de la configuración de GitHub. El [backlog](backlog.md) enlaza las 23 issues con sus ID y criterios de cierre.

## Issues y etiquetas

1. **Hecho:** etiquetas `spec`, `model`, `fixed-point`, `rtl-time`, `rtl-frequency`, `verification`, `ppa`, `docs`, `gantt` y `blocked`.
2. **Hecho:** una issue por ID del backlog, con responsable **A/B/C como rol** en el cuerpo. Asignar cuentas de GitHub cuando acepten la invitación.
3. **Hecho:** dependencias enlazadas por número en el cuerpo de cada issue; el backlog y Gantt enlazan las 23 issues.

## GitHub Project

**Hecho:** [RRC FIR RTL — Trabajo final](https://github.com/users/EnzoFernandezz11/projects/4) está vinculado al repo, es público y contiene las 23 issues. Tiene los estados `Pendiente`, `Listo`, `En curso`, `En revisión`, `Bloqueado` y `Hecho`; campos **Responsable (rol)**, **Inicio previsto** y **Fin previsto**; vistas **Kanban**, **Por persona**, **Cronograma** y **Todas las tareas**. Las fechas y roles del [Gantt](gantt.md) están cargados. El objetivo del 16/10 es 19 issues iniciadas con evidencia, no 19 cerradas.

**Ajuste visual pendiente:** en la vista **Por persona**, agrupar manualmente por `Responsable (rol)` si quieren columnas por A/B/C/Equipo. En **Cronograma**, comprobar que los ejes usan `Inicio previsto` y `Fin previsto`; las fechas ya están cargadas en las tarjetas. La API disponible creó las vistas y sus campos pero no expuso esa configuración visual. Asignar cuentas de GitHub cuando los compañeros se sumen.

## Reglas de `main`

- Requerir PR para integrar y una revisión de otra persona cuando ya haya colaboradores.
- Requerir solo el check `smoke` de `RTL CI` después de comprobar que el workflow corre en GitHub. El job `full` es informativo al integrar o al ejecutarlo manualmente.
- No configurar un check requerido con filtros por rutas: los PR de documentación también ejecutan un smoke corto.
- Evitar push directo o force push en `main` una vez configuradas las reglas.

## Condición previa para automatizarlo

El CLI ya tiene acceso al repositorio y a Projects. No guardar tokens en el repositorio. La regla que exige **una revisión de otra persona** se configura después de que al menos un compañero acepte la invitación, para no dejar a Enzo bloqueado trabajando solo. El job `smoke` ya terminó correctamente en el push inicial; puede marcarse como requerido cuando empiecen a colaborar.
