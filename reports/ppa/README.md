# Registro PPA en frecuencia

[Resultados y análisis de las corridas seriales y optimizadas](frequency.md).

`make ppa-local` y `make ppa-package` registran las nuevas medidas en el historial serial sin duplicar ejecuciones equivalentes. El informe conserva configuración, revisión, medidas, análisis y evidencias de cada corrida. Los resultados de Vivado se incorporan a la entrada correspondiente o a una entrada vinculada a su corrida local; las corridas anteriores se conservan.

Las instrucciones están en la [guía PPA](../../docs/frecuencia/ppa.md). Los artefactos pesados y resúmenes originales quedan en `build/ppa/` o en una ubicación externa identificada. Los valores no medidos se indican como pendientes.
