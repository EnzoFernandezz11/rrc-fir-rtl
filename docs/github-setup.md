# Configuración pendiente en GitHub

Este archivo registra las tareas de GitHub que no dependen de invitar todavía a B y C. El [backlog](backlog.md) contiene 23 issues sugeridas con sus ID y criterios de cierre.

## Issues y etiquetas

1. Crear etiquetas `spec`, `model`, `fixed-point`, `rtl-time`, `rtl-frequency`, `verification`, `ppa`, `docs`, `gantt` y `blocked`.
2. Crear una issue por ID del backlog, con responsable **A/B/C como rol** en el cuerpo. Asignar cuentas de GitHub cuando acepten la invitación.
3. Enlazar dependencias con números de issue una vez creadas. Mantener el ID estable en título, Gantt y PR.

## GitHub Project

Crear un Project llamado **RRC FIR RTL — Trabajo final** con estados `Pendiente`, `Listo`, `En curso`, `En revisión`, `Bloqueado` y `Hecho`. Añadir vistas **Kanban**, **Por persona** y **Cronograma**. Incorporar las 23 issues y filtrar por responsable cuando los compañeros se sumen. El objetivo del 16/10 es 19 issues iniciadas con evidencia, no 19 cerradas.

## Reglas de `main`

- Requerir PR para integrar y una revisión de otra persona cuando ya haya colaboradores.
- Requerir solo el check `smoke` de `RTL CI` después de comprobar que el workflow corre en GitHub. El job `full` es informativo al integrar o al ejecutarlo manualmente.
- No configurar un check requerido con filtros por rutas: los PR de documentación también ejecutan un smoke corto.
- Evitar push directo o force push en `main` una vez configuradas las reglas.

## Condición previa para automatizarlo

El CLI debe mostrar una sesión válida con `gh auth status` y permisos sobre `EnzoFernandezz11/rrc-fir-rtl`. Para Projects puede requerirse autorización adicional de `gh` para el scope de Projects. No guardar tokens en el repositorio. Hasta que la sesión esté disponible para este entorno, los archivos locales son la fuente preparada para crear issues, Project y reglas en la interfaz o con `gh`.
