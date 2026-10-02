# Contratos de trabajo entre A, B y C

La [consigna original](../consigna-original.md) es la fuente externa. El [contrato técnico](../contrato-tecnico.md) reúne requisitos confirmados y el registro de decisiones. Estos documentos detallan los acuerdos que permiten trabajar en paralelo:

1. [Señales, coeficientes y formatos](senales-y-formatos.md): A prepara; B/C revisan antes de tomar vectores como referencia.
2. [Método en frecuencia](frecuencia.md): C propone; A valida contra el modelo temporal y B revisa la comparación.
3. [Interfaz RTL](interfaz-rtl.md): B/C acuerdan puertos y ciclos; A valida que el banco común puede usarlos.
4. [Verificación y PPA](verificacion-y-ppa.md): A prepara métricas y vectores; B/C validan que se ejecutan igual en sus variantes.

Cada documento tiene estado **Abierto → Propuesto → Aprobado A/B/C**. No pasar a «Aprobado» hasta enlazar evidencia (respuesta del docente, ecuación, ejemplo numérico o prueba). Para cambiar un contrato aprobado: abrir issue/PR, explicar el impacto y actualizar `config/project.json`, modelos, vectores y RTL afectados en el mismo cambio o en PR dependientes declarados. No duplicar valores definitivos en varios archivos: la tabla técnica y la configuración deben apuntar a la misma decisión.
