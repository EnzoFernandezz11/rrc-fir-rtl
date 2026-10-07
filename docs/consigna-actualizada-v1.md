# Consigna actualizada (v1, reemplazada)

Primera versión actualizada por el profesor, recibida el 5/10/2026. Reemplazada el 6/10/2026 por la [consigna actualizada](consigna-actualizada.md), que corrige el filtro en tiempo (FIR RRC de 8 taps en lugar de IIR de segundo orden). Se conserva como historial. Texto transcripto sin cambios.

Se deberán implementar por separado dos tipos de filtros complejos: uno en el dominio del tiempo y otro en el dominio de la frecuencia.

El filtro en el dominio del tiempo deberá ser un filtro IIR de segundo orden. Por su parte, el filtro en el dominio de la frecuencia deberá implementarse mediante la técnica de procesamiento por bloques con una superposición del 50 %. Las señales de entrada utilizadas para las pruebas serán simbolos QPSK(+/-1) .

La documentación del proyecto deberá incluir un diagrama de bloques completo, acompañado por una descripción detallada de cada una de las etapas del sistema. Asimismo, se deberá realizar una comparación entre una implementación en punto flotante y otra en punto fijo, evaluando el comportamiento de ambas alternativas mediante pruebas con distintos conjuntos de datos.

Una vez implementadas las dos versiones, será necesario completar la interfaz serie y verificar la correspondencia de resultados entre ambas. Posteriormente, se llevará a cabo una implementación paralela utilizando alguna de las alternativas disponibles ( pipeline, sistólica, folded u otra equivalente), con el objetivo de analizar las mejoras obtenidas en términos de desempeño.

Para la implementación en el dominio de la frecuencia, la etapa de procesamiento basada en FFT deberá alcanzar el mayor grado de paralelización posible. Se evaluará especialmente el diseño y la optimización de las operaciones de FFT, multiplicación espectral e IFFT. Los distintos grupos podrán definir la estrategia de implementación que consideren más adecuada para cumplir este requisito.

Finalmente, se solicita elaborar un diagrama de Gantt que contemple la distribución de tareas entre los integrantes del equipo. Dicho cronograma deberá evidenciar el aporte individual de cada participante y servir como respaldo de la planificación y seguimiento del proyecto.

La presentación y defensa del trabajo práctico se realizará en la fecha acordada.
