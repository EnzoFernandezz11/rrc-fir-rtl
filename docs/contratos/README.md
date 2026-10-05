# Contratos de trabajo entre @andres332271, @moreyrajulian y @EnzoFernandezz11

La [consigna actualizada](../consigna-actualizada.md) es la fuente externa vigente. Por indicación de Enzo, el [contrato de frecuencia](frecuencia.md) documenta una lectura conjunta con la [consigna original](../consigna-original.md): conserva RRC8, beta 0,5 y 2× en frecuencia y aplica IIR de segundo orden en tiempo. La interpretación queda pendiente de revisión del equipo. El [contrato técnico](../contrato-tecnico.md) y otros acuerdos aún requieren reconciliar ese cambio en sus tareas correspondientes. Estos documentos detallan los acuerdos que permiten trabajar en paralelo:

1. [Señales, coeficientes y formatos](senales-y-formatos.md): @andres332271 prepara; @moreyrajulian y @EnzoFernandezz11 revisan antes de tomar vectores como referencia.
2. [Método en frecuencia](frecuencia.md): @EnzoFernandezz11 propone; @andres332271 valida el procesamiento por bloques contra una referencia directa independiente y @moreyrajulian revisa la comparación. La respuesta del filtro en frecuencia es propia, distinta de la del IIR temporal.
3. [Interfaz RTL](interfaz-rtl.md): @moreyrajulian y @EnzoFernandezz11 acuerdan puertos y ciclos; @andres332271 valida que el banco común puede usarlos.
4. [Verificación y PPA](verificacion-y-ppa.md): @andres332271 prepara métricas y vectores; @moreyrajulian y @EnzoFernandezz11 validan que se ejecutan igual en sus variantes.

Cada documento tiene estado **Abierto → Propuesto → Aprobado por @andres332271, @moreyrajulian y @EnzoFernandezz11**. No pasar a «Aprobado» hasta enlazar evidencia (respuesta del docente, ecuación, ejemplo numérico o prueba). Para cambiar un contrato aprobado: abrir issue/PR, explicar el impacto y actualizar `config/project.json`, modelos, vectores y RTL afectados en el mismo cambio o en PR dependientes declarados. No duplicar valores definitivos en varios archivos: la tabla técnica y la configuración deben apuntar a la misma decisión.
