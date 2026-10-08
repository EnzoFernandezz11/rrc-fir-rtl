# Guía integral para diseñar y verificar los filtros RRCOS en RTL

> **Referencia teórica sin mantenimiento.** Resumen de estudio de @EnzoFernandezz11 para dar contexto general; puede quedar desactualizado. Las decisiones vigentes están en el [contrato técnico](contrato-tecnico.md) y sus contratos de trabajo.
>
> **Propósito.** Leer antes de comenzar y consultar mientras se construyen los modelos, el RTL y la comparación PPA del trabajo final. Esta guía enseña la teoría y propone una forma de comprobar cada paso. **No aprueba decisiones pendientes:** la fuente de requisitos es la [consigna](consigna-actualizada.md), y el estado de cada acuerdo vive en el [contrato técnico](contrato-tecnico.md) y en [config/project.json](../config/project.json).
>
> **Lectura rápida:** §§ 1–3 antes del modelo; §§ 4–6 antes del RTL; §§ 7–9 durante verificación y PPA; § 10 para dudas frecuentes. Las referencias del § 11 permiten volver a las clases y a los libros. “Página” de un libro significa **página del PDF**, que puede diferir de la numeración impresa.

## Índice

1. [Qué exige el proyecto y qué falta acordar](#1-qué-exige-el-proyecto-y-qué-falta-acordar)
2. [De QPSK al filtro discreto](#2-de-qpsk-al-filtro-discreto)
3. [RC, RRC y los ocho coeficientes](#3-rc-rrc-y-los-ocho-coeficientes)
4. [Modelo en tiempo y arquitectura serial](#4-modelo-en-tiempo-y-arquitectura-serial)
5. [Modelo y arquitectura en frecuencia](#5-modelo-y-arquitectura-en-frecuencia)
6. [Punto fijo y presupuesto de precisión](#6-punto-fijo-y-presupuesto-de-precisión)
7. [Interfaz RTL, planificación y optimizaciones](#7-interfaz-rtl-planificación-y-optimizaciones)
8. [Verificación funcional y vector matching](#8-verificación-funcional-y-vector-matching)
9. [Comparación PPA y herramientas](#9-comparación-ppa-y-herramientas)
10. [Recorrido de trabajo, errores y consultas rápidas](#10-recorrido-de-trabajo-errores-y-consultas-rápidas)
11. [Mapa de fuentes](#11-mapa-de-fuentes)

---

## 1. Qué exige el proyecto y qué falta acordar

### 1.1 Requisitos que sí están confirmados

La consigna pide **dos filtros complejos implementados por separado**: un FIR temporal **RRCOS de 8 taps**, roll-off $\beta=0{,}5$, y una implementación en frecuencia basada en FFT con **50 % de superposición**. Deben verificarse la correspondencia de sus resultados y las diferencias entre flotante y punto fijo; luego de la interfaz serie se requiere una implementación paralela, con énfasis en FFT, productos e IFFT. También exige diagrama de bloques, descripción de etapas y Gantt con aportes individuales. Como aclaración adicional, Enzo confirmó el 7/10/2026 los mínimos **SQNR ≥ 40 dB**, **reloj ≥ 100 MHz en variantes rápidas** y **≥ 10 MHz en lentas**; se registran en el [contrato técnico](contrato-tecnico.md). Enzo también confirmó el upsampling $L=2$ el 7/10/2026: ambas cadenas usan un upsampler separado del generador. El proyecto incluye la comparación PPA. [Fuente: consigna](consigna-actualizada.md).

Una frecuencia de reloj objetivo no equivale a tasa de muestras. Si una arquitectura acepta una muestra cada $II$ ciclos, su tasa sostenida ideal es $f_{\mathrm{clk}}/II$, siempre que no haya paradas adicionales. Un diseño a 100 MHz con $II=16$ entrega menos muestras por segundo que uno a 10 MHz con $II=1$. Medir ambos números.

### 1.2 La cadena completa

~~~text
bits QPSK → símbolos complejos a[m]
          → sobremuestreo 2×: u[n]
          → filtro RRC h[k] (tiempo o frecuencia)
          → muestras complejas y[n]
          → cuantización/control de flujo RTL
          → vectores comparados → SQNR y PPA
~~~

El modelo flotante fija el significado matemático. El modelo fijo fija lo que debe hacer la aritmética digital **bit a bit**. Los testbenches comprueban que el RTL produce esas palabras en los índices correctos. La síntesis y el análisis temporal muestran el costo de hacerlo. No se debe usar la salida del propio RTL como referencia para validar el RTL. Fuentes: Módulo 1, diap. 6–7 y 37–41; [contrato de verificación](contratos/verificacion-y-ppa.md).

### 1.3 Decisiones que siguen abiertas

La tabla es una brújula de trabajo, no permiso para rellenar valores arbitrarios. El contrato del repo manda si cambia después de escribir esta guía.

| ID | Pregunta que hay que responder | Consecuencia práctica |
|---|---|---|
| D01 | ¿Qué transformada, longitud $N$, método de bloques, solapamiento y latencia definen “filtro en frecuencia”? | Define modelo, buffers, FFT/IFFT y test de bordes. |
| D02 | ¿Cuáles son $h[0]\ldots h[7]$, fase, orden, escala y normalización? | Define todos los resultados esperados. |
| D03 | ¿Cómo se representan QPSK, I/Q, reset, valid/ready y límites de bloque? | Define puertos y alineación del banco. |
| D04 | ¿Cuántos bits hay en cada nodo y cómo redondear/saturar? | Define modelo fijo, RTL y SQNR. |
| D05–D06 | ¿Cuál es la plataforma y cómo medir timing, área y potencia? | Evita comparar números incompatibles. |
| D07 | ¿Cuál es la referencia y el tramo exacto para SQNR? | Evita una cifra “40 dB” irreproducible. |
| D08 | ¿Qué optimización se elige en cada dominio y qué métrica intenta mejorar? | Da sentido a la comparación. |

**Regla de trazabilidad.** Para cada acuerdo anotar valor, estado, fuente, ejemplo numérico y PR en el [contrato técnico](contrato-tecnico.md). Actualizar [config/project.json](../config/project.json) solo con los valores que usarán scripts y modelos. El roll-off $\beta=0{,}5$ de la consigna y el upsampling $L=2$ confirmado por Enzo no determinan una tabla única de ocho coeficientes.

### 1.4 Reparto y dependencias

El [backlog](backlog.md) y el [Gantt](gantt.md) contienen 24 tareas, incluida R01 para módulos RTL comunes. Andrés lleva principalmente generador, modelos, precisión y vectores; Julián, el filtro temporal; Enzo, el filtro en frecuencia. Se cierra primero el contrato E00–E03; luego A01–A05; después B02/C02 con banco A06; más tarde B04/C04 y PPA A07; finalmente comparación I01 e informe/presentación I02/I03. El Gantt distingue dependencias **para comenzar** de las necesarias **para cerrar**. El porcentaje de issues movidas no sustituye una prueba de equivalencia.

---

## 2. De QPSK al filtro discreto

### 2.1 Símbolos complejos y convenciones

QPSK transmite dos bits por símbolo mediante cuatro puntos del plano I/Q. Una convención didáctica es $a[m]\in\{(\pm1\pm j)/\sqrt{2}\}$, de energía $|a[m]|^2=1$. Otra usa $\pm1\pm j$, de energía 2. El mapeo de pares de bits, el orden I/Q y la amplitud son parte de **D03**: no hay que elegir uno silenciosamente. El notebook previo Tarea1 usa una convención concreta que puede servir de ejemplo, pero no fija el contrato nuevo. Fuentes teóricas: Proakis y Salehi, PDF pp. 137–146; [contrato de señales](contratos/senales-y-formatos.md).

Para $L=2$, la secuencia ideal a la salida del upsampler y antes del filtro RRC se obtiene insertando un cero complejo entre símbolos:

$$
u[2m]=a[m],\qquad u[2m+1]=0.
$$

“Dos muestras por símbolo” no significa repetir cada símbolo dos veces. Repetir produce otro pulso y otra respuesta espectral. Si el diseño recibe ya las muestras $u[n]$ en vez de recibir símbolos $a[m]$, el contrato debe decirlo expresamente. También debe decir si la interfaz recibe I y Q en puertos separados, qué muestra llega primero y qué ocurre al terminar un bloque.

**Ejemplo orientativo, no vector oficial.** Para $a=[1+j,\,-1+j,\,1-j]$, la inserción de ceros produce $u=[1+j,\,0,\,-1+j,\,0,\,1-j,\,0]$. El cero final pertenece a la trama y produce su salida correspondiente; el contrato E01 omite la cola posterior del FIR. La señalización de fin de trama se acuerda con la interfaz.

### 2.2 FIR complejo y condiciones iniciales

Un FIR causal de $M=8$ taps calcula

$$
y[n]=\sum_{k=0}^{7}h[k]\,u[n-k].
$$

Para un arranque en reposo se define $u[n]=0$ si $n<0$. Si los coeficientes RRC elegidos son **reales**, las dos ramas I/Q usan los mismos coeficientes:

$$
y_I[n]=\sum_k h[k]u_I[n-k],\qquad
y_Q[n]=\sum_k h[k]u_Q[n-k].
$$

El dato sigue siendo complejo, aunque el impulso de cada rama sea real. Si se aprueban coeficientes complejos, la multiplicación pasa a ser

$$
(a+jb)(c+jd)=(ac-bd)+j(ad+bc),
$$

y el modelo y los recursos cambian. No asumir cuatro multiplicadores reales por tap si la tabla $h[k]$ resulta real. Fuentes: Módulo 7, diap. 7–12; Módulo 10, diap. 9–11.

La **respuesta al impulso** es la mejor primera prueba: con $u[0]=1$ y el resto cero, la salida ideal causal es $h[0],\ldots,h[7]$, seguida de ceros. Un impulso solo en Q comprueba la otra rama y el orden I/Q. Dos impulsos separados comprueban la superposición y el vaciado de la línea de retardos.

### 2.3 Pulso de transmisión, receptor y criterio de Nyquist

En comunicaciones, un RRC suele dividir el conformado entre transmisión y recepción. Dos respuestas RRC ideales y conjugadas en la configuración adecuada producen una respuesta **raised cosine** (RC) total. El criterio de Nyquist de cero ISI se aplica a la respuesta total **en los instantes de decisión**; un RRC aislado no tiene por qué valer cero en todos los tiempos de símbolo ajenos al central. El filtro adaptado invierte temporalmente y conjuga el pulso del transmisor. Aquí el enunciado exige implementar un filtro RRCOS; no especifica una cadena TX + canal + RX completa. Fuentes: Barry, Lee y Messerschmitt, PDF pp. 146–152 y 170–171; Proakis y Salehi, PDF pp. 693–698.

El RRC ideal es de duración infinita. Recortarlo a ocho muestras altera la respuesta y, en general, impide afirmar cero ISI exacto. La convolución de dos secuencias RRC **recortadas** se parece al RC ideal pero no coincide exactamente. La normalización cambia la amplitud; no corrige por sí sola el ISI. Comparar siempre la curva y los valores en los instantes pertinentes.

### 2.4 Qué mirar en tiempo y frecuencia

En tiempo, mirar simetría, signos, lóbulo central, extremos del soporte y retardo de grupo. En frecuencia, mirar magnitud, banda de transición, fuga por truncamiento y escala. El roll-off $\beta$ controla el exceso de ancho de banda del pulso RC ideal: aumentar $\beta$ ensancha la transición y suele concentrar más la respuesta temporal. Una FFT de los ocho taps es **una visualización de su respuesta discreta**, no automáticamente el algoritmo de filtrado por bloques. Fuentes: TP1 previo; Proakis y Salehi, PDF pp. 626–628 y 693–698.

---

## 3. RC, RRC y los ocho coeficientes

### 3.1 Variable normalizada y fórmula

Sea $T$ el período de símbolo, $F_s=L/T$ y $u=t/T$. Una expresión habitual para el RRC ideal, antes de escoger escala global, es

$$
g_{\mathrm{RRC}}(u)=
\frac{\sin\!\bigl(\pi(1-\beta)u\bigr)+4\beta u\cos\!\bigl(\pi(1+\beta)u\bigr)}
     {\pi u\,[1-(4\beta u)^2]}.
$$

En $u=0$ y $u=\pm1/(4\beta)$ el cociente aparece como $0/0$, pero los límites son finitos:

$$
g_{\mathrm{RRC}}(0)=1-\beta+\frac{4\beta}{\pi},
$$

$$
g_{\mathrm{RRC}}\!\left(\pm\frac{1}{4\beta}\right)
=\frac{\beta}{\sqrt{2}}
\left[\left(1+\frac{2}{\pi}\right)\sin\!\left(\frac{\pi}{4\beta}\right)
+\left(1-\frac{2}{\pi}\right)\cos\!\left(\frac{\pi}{4\beta}\right)\right].
$$

Se debe evaluar esos puntos mediante límites explícitos, no con un pequeño cambio artificial de $\beta$ o de $u$. Para $\beta=0{,}5$, las singularidades aparentes distintas del origen están en $u=\pm0{,}5$. TP1 previo, celda de RRC; Proakis y Salehi, PDF pp. 693–698.

Para contrastar, una forma del **RC** ideal es

$$
g_{\mathrm{RC}}(u)=\frac{\sin(\pi u)}{\pi u}
\frac{\cos(\pi\beta u)}{1-(2\beta u)^2},
$$

con sus límites propios en $u=0$ y $u=\pm1/(2\beta)$. **No usar la fórmula RC para producir los ocho taps RRC.**

### 3.2 El detalle decisivo: ocho es par

Una ventana simétrica de **ocho** muestras, con fase centrada entre muestras, usa

$$
u_k=\frac{k-(M-1)/2}{L}
=\frac{k-3{,}5}{2},\qquad k=0,\ldots,7.
$$

Así $u_k=(-1{,}75,\,-1{,}25,\,-0{,}75,\,-0{,}25,\,+0{,}25,\,+0{,}75,\,+1{,}25,\,+1{,}75)$. Su retardo de grupo, si $h[k]=h[7-k]$, es $3{,}5$ muestras, es decir, $1{,}75$ símbolos a 2×. **Ningún tap cae exactamente en $u=0$**; tampoco en $\pm0{,}5$ con esta fase. Esto no es un error: es una consecuencia de un FIR simétrico de longitud par.

También podrían proponerse ocho muestras con otra fase, por ejemplo $u_k=(k-3)/2$. Eso incluye $u=0$, pero la ventana temporal deja de ser simétrica alrededor del centro entre taps y la latencia/fase cambia. **D02 debe fijar cuál es la opción correcta** según el objetivo docente y los ejemplos de referencia. El TP1 anterior convierte una cantidad par de taps en impar; copiar su función sin cambiarla daría nueve taps y violaría la consigna.

### 3.3 Escala y cuantización: orden recomendado de decisiones

1. Fijar $M=8$, $L=2$, $\beta=0{,}5$, convención temporal $u_k$, orden $h[0]\ldots h[7]$ y representación causal.
2. Evaluar la fórmula con límites exactos donde corresponda; guardar valores de suficiente precisión para regenerar la tabla.
3. Elegir **una** normalización justificada: por ejemplo energía discreta $\sum_k|h[k]|^2=1$, ganancia en DC $\sum_k h[k]=1$, o una escala exigida por el docente. No son equivalentes. Registrar cuál se usó y cómo afecta la amplitud.
4. Generar respuesta al impulso, curva de frecuencia y una secuencia QPSK corta para inspección.
5. Recién entonces cuantizar los coeficientes, definir el formato de hardware y evaluar el SQNR sobre la misma escala.

La normalización por suma del TP1 previo es una decisión de aquel ejercicio; no es una ley universal del RRC. No mezclar una referencia flotante normalizada de una manera con un RTL cuyos coeficientes se normalizaron de otra. Registrar al menos el script generador, fase, fórmula, tabla, escala, versión y semilla de vectores. [Fuente: contrato de señales](contratos/senales-y-formatos.md).

### 3.4 Comprobaciones numéricas mínimas del generador

- Coeficientes finitos: ningún NaN o infinito, incluso en límites de la fórmula.
- Simetría $h[k]\approx h[7-k]$ si se aprobó la fase simétrica.
- Impulso causal con exactamente ocho muestras no nulas salvo que algún tap sea cero por construcción.
- Resultado reproducible: misma configuración, mismos ocho números.
- Verificación cruzada: evaluar el RRC con una implementación independiente o con alta precisión y comparar cada tap.
- Comparar el RRC truncado con un RRC largo solo como **control teórico**, sin usar el largo como sustituto de los ocho taps.
- No inferir “cero ISI exacto” de una gráfica poco detallada.


---

## 4. Modelo en tiempo y arquitectura serial

### 4.1 Modelo flotante de referencia

El modelo más simple mantiene un historial de ocho muestras complejas. Por cada muestra aceptada, coloca la nueva en la posición 0, desplaza las anteriores y calcula el producto escalar con $h[0]\ldots h[7]$. Una implementación con convolución de biblioteca es útil como **segunda referencia**, siempre que se comprueben modo, longitud, orientación de taps y condiciones iniciales.

~~~text
hist = [0j] × 8
por cada u[n] aceptada:
    hist = [u[n]] + hist[0:7]
    y[n] = suma(h[k] × hist[k] para k=0..7)
~~~

Con $u$ de longitud $S$ y $h$ de longitud 8, la convolución lineal completa tiene $S+7$ muestras. Un sistema que emite solo $S$ salidas o que se reinicia entre bloques puede ser válido, pero debe declararlo. El modelo flotante, el fijo y el testbench deben usar **la misma política de cola y reset**. Fuentes: Módulo 7, diap. 7–12; [modelo previsto](../model/README.md).

### 4.2 Datapath serial: qué se comparte

Una arquitectura serial típica dispone de un multiplicador y acumulador (**MAC**) por rama I/Q, o de un multiplicador complejo si $h[k]$ es complejo. Guarda ocho muestras, un índice de tap y la suma parcial. Para una muestra $n$, recorre $k=0\ldots7$; al terminar entrega $y[n]$ con su índice válido. Si las ramas I y Q comparten el mismo multiplicador real, harán falta todavía más ciclos.

No prometer “ocho ciclos por salida” sin dibujar el schedule. Los registros de operandos, la latencia del multiplicador, la carga/limpieza del acumulador y el protocolo de entrada/salida pueden añadir ciclos. Escribir una tabla **por flanco de reloj** con: estado, entrada aceptada, tap, producto calculado, acumulador antes/después y valid de salida. Fuentes: Módulo 2, diap. 10–16 y 20; Módulo 6, diap. 5–15 y 37–41.

**Esqueleto conceptual, sin fijar interfaz:**

| Fase | Operación | Comprobación |
|---|---|---|
| Espera | Señalar capacidad de aceptar una muestra. | Una burbuja no cambia el historial. |
| Aceptación | Guardar I/Q; definir el índice de salida asociado. | No perder ni duplicar una muestra. |
| MAC | Leer tap y muestra histórica alineados; acumular. | El primer producto usa $h[0]u[n]$. |
| Salida | Redondear/saturar en el punto pactado; activar valid. | Una salida válida por muestra aceptada. |
| Nueva muestra | Volver a espera o iniciar operación siguiente. | $II$ medido, no supuesto. |

El histórico debe actualizarse **una vez por muestra aceptada**, no una vez por tap. El acumulador debe comenzar limpio para cada nueva salida. En SystemVerilog, un registro asignado con `<=` se actualiza al final del paso temporal; razonar explícitamente si una MAC lee el valor viejo o el nuevo del historial. Fuentes: Módulo 2, diap. 20 y 25–26; [contrato de interfaz](contratos/interfaz-rtl.md).

### 4.3 Rendimiento mínimo que hay que calcular

Definir **latencia** como ciclos desde la aceptación de una muestra hasta el flanco donde su salida es válida. Definir **intervalo de iniciación** $II$ como ciclos mínimos entre muestras aceptadas en régimen estable. Definir **throughput** con la frecuencia y $II$, y también en símbolos/s cuando hay dos muestras/símbolo. Para un diseño serial que necesita $C$ ciclos no solapables por muestra, $II\ge C$. Si hay buffering o varias operaciones en vuelo, documentar exactamente qué se solapa.

**Pregunta de viabilidad:** si el flujo exige una nueva muestra cada $T_s$, ¿la arquitectura serial puede aceptarla, o se requiere backpressure y buffering? Una variante puede cumplir 100 MHz de reloj y aun así no alcanzar la tasa de muestras exigida. Como la consigna no fija aún esa tasa ni el protocolo, registrar la respuesta en D03 y D08.

### 4.4 Puntos donde fallan las primeras implementaciones

1. Invertir el orden de taps: $h[0]$ debe multiplicar la muestra presente en la convención de arriba.
2. Actualizar la línea de retardos durante los ocho pasos MAC.
3. Conservar un acumulador anterior al empezar otra salida.
4. Cambiar la cuantización entre modelo y RTL.
5. Marcar valid antes de que el resultado registrado tenga el valor final.
6. Suponer que una salida “se ve” en el mismo flanco en que se aceptó la entrada.
7. Aplicar reset a mitad de una transacción sin definir qué pasa con la salida pendiente.

**Prueba de banco:** dibujar a mano los dos primeros resultados de un impulso; repetir con una muestra negativa solo en Q. Si la tabla de flancos y el modelo no coinciden ahí, no tiene sentido ejecutar una regresión larga.

---

## 5. Modelo y arquitectura en frecuencia

### 5.1 Lo que representa la transformación

Para secuencias discretas, la transformada convierte una convolución **circular de longitud $N$** en un producto bin a bin:

$$
Y_N[r]=X_N[r]H_N[r],\qquad
y_N[n]=\operatorname{IDFT}_N\{Y_N[r]\}.
$$

La salida de la IDFT de $N$ puntos es circular: términos cuyo índice excede $N-1$ reaparecen al comienzo. El FIR en tiempo calcula una **convolución lineal**. Para que ambas salidas coincidan, hay que dejar espacio suficiente para evitar aliasing circular en cada bloque y reconstruir el flujo. Éste es el centro técnico de D01. Fuentes: Oppenheim, *Tratamiento de señales en tiempo discreto*, PDF pp. 669–686; Módulo 7, diap. 24–30; [contrato de frecuencia](contratos/frecuencia.md).

La FFT es un algoritmo eficiente para calcular una DFT; no transforma mágicamente el FIR en una multiplicación por un solo coeficiente. Hay que almacenar un bloque, transformar las muestras, multiplicar **todos los bins**, invertir la transformación y tratar bordes. Para ocho taps, ese costo puede superar al FIR directo. La implementación en frecuencia sigue siendo parte de la consigna y debe medirse, no justificarse con una supuesta ventaja automática.

### 5.2 Overlap-add: una opción concreta para evaluar

Si se eligen $B$ muestras nuevas por bloque y $M=8$ taps, el tamaño de transformada debe satisfacer

$$
N\ge B+M-1=B+7.
$$

Cada bloque de entrada se rellena con ceros hasta $N$; también se rellena $h$ hasta $N$. Se precomputa $H_N=\operatorname{DFT}_N(h)$ con la **misma escala y orden** que el datapath. Tras la IDFT, cada bloque contiene $B+7$ muestras de convolución lineal. Las muestras que sobresalen de cada bloque se **suman** en sus índices globales. Si $B<7$, la cola puede alcanzar más de un bloque posterior; la implementación debe conservar esas sumas hasta emitirlas.

**Ejemplo de juguete, separado del diseño de ocho taps.** Para $h=[1,1]$, $x=[1,2,3,4]$, $B=3$, $N=4$: el primer bloque $[1,2,3]$ produce $[1,3,5,3]$; el segundo $[4]$ produce $[4,4]$, ubicado desde el índice 3. Al sumar la zona superpuesta se obtiene $[1,3,5,7,4]$, exactamente la convolución lineal. Si se descarta el valor 3 del borde, el resultado es incorrecto.

Con $M=8$, una FFT de 16 puntos permite como máximo $B=9$ muestras nuevas por bloque en esta versión simple. No significa que 16 sea la elección definitiva: memoria, tasa requerida, uso del núcleo FFT, cuantización y latencia pueden cambiar D01.

### 5.3 Overlap-save: otra opción concreta

Se procesan bloques de $N$ muestras que incluyen las $M-1=7$ muestras anteriores y $K=N-M+1=N-7$ muestras nuevas. El producto FFT–IFFT genera $N$ valores circulares; **se descartan las primeras siete** y se conservan las $K$ salidas siguientes. En el primer bloque, el historial previo es cero si se eligió arranque en reposo. Para bloques incompletos hay que definir relleno y cantidad de salidas válidas.

Una FFT de 8 puntos daría solo $K=1$ muestra útil por bloque; ésta es una forma rápida de detectar una propuesta poco eficiente. Comparar $N$, buffers y ciclos reales con la opción overlap-add. No mezclar ambos métodos: cambian la posición de las muestras válidas y el manejo del historial. Fuentes: Oppenheim, PDF pp. 669–686; [contrato de frecuencia](contratos/frecuencia.md).

**Propuesta vigente del proyecto:** E01 elige $N=16$, ocho muestras de historial y avance $K=8$ para cumplir exactamente el 50 % de superposición. Descarta posiciones 0…7 y conserva 8…15. La posición 7 también es válida, pero pertenece al tramo anterior. El máximo convencional $N-7=9$ describe otra organización y no es el avance de C01.

### 5.4 Escala de FFT y número de bits

Una DFT común usa

$$
X[r]=\sum_{n=0}^{N-1}x[n]e^{-j2\pi rn/N},
\quad
x[n]=\frac{1}{N}\sum_{r=0}^{N-1}X[r]e^{j2\pi rn/N}.
$$

Algunas bibliotecas y núcleos RTL distribuyen el factor $1/N$ entre etapas o lo aplican en otra posición. Comparar FFT Python y hardware requiere **registrar esa convención**. Cada butterfly puede aumentar el rango; se necesitan bits de guarda o escalado por etapas. Los twiddles cuantizados, redondeos y saturaciones pueden producir una salida distinta de la convolución fija temporal aun cuando ambas aproximen el mismo filtro flotante. Declarar tolerancia y analizar SQNR por variante; no esconder un error de bloque detrás de una tolerancia amplia. Fuentes: Módulo 7, diap. 25–30 y 40–46; [contrato de verificación](contratos/verificacion-y-ppa.md).

Si $h[k]$ es real y simétrico, su DFT tiene relaciones útiles, pero el pipeline sigue tratando datos complejos QPSK y debe preservar el orden de bins. Comprobar por separado las partes real e imaginaria de la multiplicación espectral. Una rotación compleja por twiddle puede implementarse con multiplicadores o, en algunas arquitecturas, CORDIC; la Unidad 5, diap. 5 y 13–19 explica el compromiso. CORDIC **no es requisito** ni necesariamente conveniente para $N$ pequeño y twiddles constantes.

### 5.5 Qué debe contener el diseño serial en frecuencia

Antes de escribir RTL, dibujar un diagrama con: buffer de entrada, historial/solapamiento, transformada, memoria de coeficientes $H_N$, multiplicador espectral, inversa, selector de salidas válidas y buffer de salida. Luego construir una tabla por ciclo con ocupación de memorias, operaciones y estados. Si FFT, producto e IFFT comparten hardware, contar recargas, lectura/escritura y conflictos de puertos. Si se usan núcleos separados, contar recursos replicados.

Calcular explícitamente:

$$
\text{throughput sostenido}=
\frac{K f_{\mathrm{clk}}}{\text{intervalo entre bloques, en ciclos}}
$$

donde $K$ es el avance real: $B$ en overlap-add, $N-7$ en overlap-save con historial mínimo, y **ocho en la propuesta FFT16 al 50 % de E01/C01**. El denominador es el intervalo entre inicios de bloques en régimen, tras incluir operaciones, transferencias y esperas. Si no se solapan bloques, ese intervalo equivale a los ciclos totales de procesamiento del bloque. La latencia de la primera salida incluye reunir el bloque y procesarlo. Acordar si hay salida continua, ráfagas o backpressure. Fuentes: Módulo 6, diap. 6–15 y 37–41; Módulo 7, diap. 24–30.

### 5.6 Prueba matemática obligatoria antes de RTL

Con los mismos $h[k]$ y entrada, el modelo flotante temporal y el modelo flotante por bloques deben concordar, tras alinear índices, en:

- impulso al comienzo y justo antes de un límite de bloque;
- ceros, una secuencia corta conocida y QPSK con semilla fija;
- respuesta de los ocho taps dentro de la trama y último bloque parcial; con el recorte sin cola de E01, extender la entrada con ceros válidos si se quiere observar la respuesta completa de un impulso próximo al final;
- muestras negativas en I y Q;
- más de dos bloques, para exponer errores de solapamiento acumulado.

Para una implementación FFT en coma flotante basta una tolerancia numérica pequeña declarada; un error grande o concentrado en los bordes señala índices, escala o solapamiento incorrectos. Registrar la **primera muestra válida**, cuántas se descartan y el retardo. El contrato advierte que una FFT multiplicada por coeficientes **sin método de bloques acordado** no garantiza equivalencia. [Fuente: contrato de frecuencia](contratos/frecuencia.md).

---

## 6. Punto fijo y presupuesto de precisión

### 6.1 Qué significa un formato Q

En esta guía, un entero con signo de $W$ bits y $F$ bits fraccionarios representa $v=q\,2^{-F}$. Su rango es

$$
-2^{W-F-1}\le v\le 2^{W-F-1}-2^{-F}.
$$

La notación “Qm.n” cambia entre autores: algunos cuentan el bit de signo dentro de $m$ y otros no. En el contrato escribir siempre **$W$ total, $F$ fraccional y signo**; eso elimina la ambigüedad. Ejemplo: $W=8,F=7$ cubre $[-1,\,1-2^{-7}]$ con paso $2^{-7}$. Fuentes: Módulo 3, diap. 7–23; resumen del módulo 3.

### 6.2 Suma, producto y acumulación

Para sumar exactamente dos cantidades con el mismo $F$, alinear puntos binarios y extender signo. Una suma puede necesitar un bit entero adicional si se quiere evitar overflow. Un producto completo de operandos signados $W_x,F_x$ y $W_h,F_h$ tiene hasta $W_x+W_h$ bits y $F_x+F_h$ bits fraccionarios. El acumulador de **ocho productos** suele reservar al menos $\lceil\log_2 8\rceil=3$ bits de guarda sobre el ancho del producto cuando se desea soportar la suma peor caso de magnitudes sin saturación interna; ajustar con el rango real y los signos. Los formatos de FFT y multiplicación compleja pueden exigir todavía más.

**Ejemplo con signo.** En $W=8,F=7$, $+0{,}75$ se codifica como $q_x=96$ y $-0{,}5$ como $q_h=-64$. El producto entero completo es $-6144$; interpretado con $F=14$, vale $-0{,}375$. Para volver a $F=7$, el entero es $-48$. Si el resultado no fuera múltiplo exacto de $2^7$, habría que aplicar el redondeo acordado. Un desplazamiento aritmético a la derecha de un número negativo implementa una política concreta de truncado; no sustituye automáticamente “redondeo al más próximo”. Fuentes: Módulo 3, diap. 17–23; Módulo 4, diap. 15–27.

### 6.3 Definir cada recorte, no solo la salida

Una ficha de formato para cada nodo debe incluir: nombre, $W$, $F$, signo, rango máximo esperado, ancho de operación, punto donde se eliminan bits, modo de redondeo y política de overflow. Distinguir:

- **Wrap-around:** el resultado se interpreta módulo $2^W$; un overflow puede cambiar abruptamente signo y valor.
- **Saturación:** limita al extremo representable; requiere lógica y puede introducir distorsión.
- **Truncado/redondeo:** afectan el error aun sin overflow.
- **Cuantización de coeficientes:** cambia la función de transferencia misma.

Comprobar numéricamente tanto el peor caso razonable como estímulos que provoquen extremos. “No observé overflow en una prueba aleatoria” no demuestra que sea imposible. En un FIR sin realimentación, un análisis de $\sum_k|h[k]|$ con límite de entrada da una cota útil: $|y[n]|\le \max|u[n]|\sum_k|h[k]|$. Para I/Q y coeficientes complejos, tratar magnitudes y componentes con cuidado. Fuentes: Módulo 3, diap. 21–26; Módulo 7, diap. 40–47.

### 6.4 SQNR reproducible

Una definición candidata para revisar en D07 es

$$
\mathrm{SQNR}=10\log_{10}
\frac{\sum_{n\in V}|y_{\mathrm{ref}}[n]|^2}
{\sum_{n\in V}|y_{\mathrm{fxp}}[n]-y_{\mathrm{ref}}[n]|^2}
\quad\text{dB},
\qquad |z|^2=(\Re z)^2+(\Im z)^2.
$$

$V$ es el conjunto **de muestras válidas y alineadas**. Fijar si la referencia es el FIR temporal flotante para ambas variantes o una referencia por dominio; escala, longitud de secuencia, semilla, tratamiento de colas, transitorio, saturaciones y tolerancia. Si el error es cero, la razón formal tiende a infinito; informar “coincidencia exacta bajo esta muestra de prueba”, no un número arbitrario. Si la energía de referencia es cero, la fórmula no define SQNR útil: usar otros vectores para la métrica y conservar el vector de ceros como prueba funcional. [Fuente: contrato de verificación](contratos/verificacion-y-ppa.md).

No aplicar sin más la regla aproximada de 6 dB por bit: depende de señal, escala, distribución del error y arquitectura. La meta de 40 dB se **mide** sobre casos acordados. Separar errores: primero referencia float contra modelo con coeficientes cuantizados; luego agregar recortes internos y redondeos; finalmente comparar RTL contra el modelo fijo, donde se espera coincidencia exacta o una tolerancia explícita según contrato.

### 6.5 Barrido de bits sin engañarse

Para cada candidato de formatos, guardar $W,F$ de entrada, coeficiente, producto, acumulador, salida y nodos FFT; método de redondeo; número de overflows; SQNR de cada caso; costo estimado de multiplicadores, sumadores y memorias. Empezar con anchos generosos para establecer una referencia fija casi exacta. Reducir uno o pocos anchos por vez; ejecutar **los mismos vectores**; localizar qué nodo introduce el error dominante. Seleccionar la configuración más barata que mantenga margen sobre 40 dB en el conjunto acordado, sin overflow oculto. Una única semilla favorable no es evidencia suficiente.

El valor exacto de la configuración elegida debe pasar al [contrato de señales](contratos/senales-y-formatos.md), al modelo fijo, a los vectores y al RTL de manera controlada. Si dos dominios usan distintas etapas de cuantización, documentar las diferencias sin cambiar la referencia funcional a conveniencia.


---

## 7. Interfaz RTL, planificación y optimizaciones

### 7.1 Una interfaz compartida necesita semántica, no solo nombres

Antes de conectar testbenches, E03 debe especificar: reloj y reset; anchos y orden de I/Q; significado de entrada válida y aceptación; posibilidad de backpressure de salida; inicialización de historia; límites y tamaño de bloque; alineación entre muestras y salidas; latencia/throughput por variante. Dos módulos pueden tener puertos parecidos y ser incompatibles si discrepan en el flanco donde aceptan el dato. [Fuentes: contrato de interfaz](contratos/interfaz-rtl.md); Módulo 2, diap. 15–16 y 35.

Si se acuerda un protocolo valid/ready, la transferencia ocurre en el flanco donde **ambas** señales valen 1. Valid sin ready no garantiza que el receptor haya aceptado el dato. Mientras valid=1 y ready=0, el emisor debe conservar dato y marcadores, según el contrato adoptado. Si no se admite backpressure, documentar la capacidad de recepción y qué hace el sistema si se excede; no tirar muestras silenciosamente. El banco común puede adaptar latencias distintas mediante una cola de resultados etiquetados por índice de muestra.

**Tabla de ciclos obligatoria para el contrato:** reset; primera muestra presentada y aceptada; burbuja; primera salida válida; bloqueo de salida si aplica; fin de bloque; reset durante una operación. Hacerla por separado para serial temporal y serial en frecuencia y luego comprobar que el banco común sabe asociar cada salida con una entrada.

### 7.2 Separar algoritmo, schedule y circuito físico

Un **DFG** o grafo de flujo de datos muestra operaciones y dependencias. El **schedule** asigna operaciones a ciclos y recursos; el **RTL** materializa registros, multiplexores, memoria, FSM y datapath; el análisis de timing comprueba retrasos físicos. Un schedule correcto puede fallar timing si el camino combinacional de un ciclo es demasiado largo. Una buena frecuencia de reloj puede no bastar si $II$ es grande. Fuentes: Módulo 6, diap. 6–15 y 41; resumen del módulo 6.

Para cada variante dibujar:

1. Entradas y salidas con formatos y validez.
2. Operaciones del grafo: ocho productos y acumulación en tiempo; FFT/producto/IFFT y solapamiento en frecuencia.
3. Recursos físicos y número de puertos de memorias.
4. Registros que separan etapas y estado mínimo necesario.
5. Tabla de ciclos y $II$ previsto.
6. Camino combinacional sospechoso y constraint de reloj objetivo.

### 7.3 Técnicas que se vieron en clase y qué cambian

| Técnica | Mecanismo | Beneficio potencial | Costo o riesgo a verificar |
|---|---|---|---|
| Serial / folded | Reutilizar uno o pocos operadores en distintos ciclos. | Menos multiplicadores y a menudo menos área. | Más ciclos por muestra, control, muxes y memoria; la potencia total debe medirse. |
| Paralela / unfolded | Replicar operadores o procesar varias muestras simultáneas. | Mayor throughput. | Más recursos, buses, actividad y ruteo. |
| Pipeline | Insertar registros para acortar caminos combinacionales. | Mayor frecuencia o $II$ menor tras el llenado. | Más registros, latencia y necesidad de alinear valid y ramas. |
| Retiming | Redistribuir registros conservando equivalencia secuencial bajo las condiciones apropiadas. | Balancear etapas sin replicar necesariamente toda la lógica. | Cuidado con reset, latencia observable y restricciones de equivalencia. |
| Sistólica | Red regular de elementos de procesamiento con datos que avanzan por etapas. | Flujo local y alto throughput en problemas adecuados. | Registro y ancho de banda internos; justificar que el mapa de 8 taps o FFT conviene. |
| Multiplicación por constantes | Aprovechar coeficientes fijos, simetría o codificación CSD. | Menos multiplicadores o lógica más simple. | Controlar signo, rango y la cuantización real de los taps. |

Fuentes: Módulo 3, diap. 28–29; Módulo 6, diap. 17–28 y 37–40; Módulo 7, diap. 8–14, 23 y 38; resumen del módulo 7.

**Elegir D08 con hipótesis comprobable.** Ejemplo de formulación: “Pipelinar la suma temporal para intentar subir Fmax, conservando los mismos taps y reduciendo $II$ a uno; esperamos más FF y latencia”. O “compartir un multiplicador espectral para reducir área, aceptando más ciclos por bloque”. La decisión definitiva depende de las versiones seriales medidas. No llamar “optimización” a un cambio que solo altera la escala o descarta salidas.

### 7.4 Simetría y recursos: cuándo ayuda

Si se aprueba $h[k]=h[7-k]$, el FIR en tiempo puede reagruparse:

$$
y[n]=\sum_{k=0}^{3}h[k]\{u[n-k]+u[n-(7-k)]\}.
$$

Esto reduce de ocho a cuatro **multiplicaciones por muestra** en una implementación totalmente paralela, a cambio de pre-sumas y posibles bits de guarda. En una arquitectura serial también puede reducir ciclos MAC, pero la pre-suma cambia el punto de cuantización. Para equivalencia **bit a bit**, el modelo fijo debe reflejar el nuevo orden de operaciones, o debe justificarse una tolerancia funcional. No aplicar la simetría si los coeficientes cuantizados no conservan exactamente la igualdad par a par.

### 7.5 RTL sintetizable y control de signos

Usar lógica combinacional con asignaciones completas y lógica secuencial con asignaciones no bloqueantes. Declarar anchos, signo y extensión de cada producto/suma; las reglas implícitas de tamaños de SystemVerilog pueden truncar antes de que el resultado llegue al acumulador. Evitar latches accidentales en FSM o multiplexores. Definir reset de estado, índices, valid y buffers; no hace falta inicializar con reset cada bit de datapath si el protocolo invalida su contenido y el objetivo de síntesis lo justifica, pero la elección debe ser explícita.

Separar señales de “dato físicamente presente” de “dato válido”. Tras reset o durante llenado de pipeline, los registros pueden contener cualquier patrón: el testbench compara solo salidas válidas y también verifica que valid aparezca en el ciclo correcto. Fuentes: Módulo 2, diap. 18–26 y 35; Módulo 7, diap. 50.

### 7.6 Timing, constraints y CDC en este trabajo

Para reloj de 100 MHz, el período nominal es **10 ns**; para 10 MHz es **100 ns**. Esos valores se plasman en constraints una vez elegida la plataforma y se acompañan de incertidumbre, condiciones de entrada/salida y tecnología coherentes. El camino crítico de registro a registro requiere que retardo de lógica, ruteo y setup quepan en el período con el margen de reloj correspondiente. Revisar también hold. **No declarar multicycle o false path para hacer desaparecer una violación que sí afecta una transferencia real.** Fuentes: Módulo 9, diap. 10–15 y 23–31; resumen del módulo 9.

La consigna actual no establece más de un dominio de reloj. Si las cuatro variantes operan con **un solo reloj** y señales síncronas, no hace falta añadir CDC artificial. Si luego se conectan relojes distintos o reset asíncrono, aplicar las reglas de sincronización apropiadas: un doble FF sirve para un control de un bit bajo sus condiciones, **no** para un bus multibit arbitrario ni para todos los pulsos fast→slow. Fuente: Módulo 9, diap. 36–59.

---

## 8. Verificación funcional y vector matching

### 8.1 Tres niveles de referencia

1. **Modelo flotante temporal:** define la convolución ideal con la tabla RRC aprobada.
2. **Modelo flotante en frecuencia:** demuestra que el método de bloques elegido representa la misma operación, con tolerancia de cálculo flotante y política de bordes declaradas.
3. **Modelo fijo por arquitectura:** reproduce formatos, redondeos, escalas y saturaciones en el orden del hardware. El testbench del RTL compara contra esta referencia **por índice de salida válida**, no por número bruto de ciclo.

El SQNR compara una salida cuantizada con una referencia flotante acordada. El vector matching comprueba una salida RTL contra el modelo fijo acordado. Son preguntas diferentes: un RTL puede coincidir exactamente con un modelo fijo cuyo SQNR es insuficiente. [Contrato de verificación](contratos/verificacion-y-ppa.md); Módulo 2, diap. 35.

### 8.2 Matriz de pruebas mínima

| Caso | Qué debe exponer |
|---|---|
| Reset y ceros | Estado conocido, ausencia de valid espurio, respuesta nula. |
| Impulso en I y luego en Q | Orden de taps, longitud, signos y mezcla accidental I/Q. |
| Dos impulsos espaciados | Historia y superposición. |
| QPSK con semilla fija | Flujo típico y precisión. |
| Valores extremos positivos/negativos | Signo, saturación, overflow y redondeo. |
| Burbujas de entrada | Avance de historia solo cuando se acepta la muestra. |
| Salida detenida, si hay ready | Conservación de dato válido sin pérdidas. |
| Reset a mitad de operación | Cancelación o vaciado definido por el contrato. |
| Cruce y final de bloque | Overlap-add/save, relleno, descarte y salida final. |
| Dos o más bloques seguidos | Estado persistente y falta de duplicaciones. |

Para cada falla informar: variante, semilla, configuración, índice lógico de muestra, ciclo, I/Q esperado y recibido, y formato numérico. Una onda VCD ayuda a depurar, pero un mensaje de testbench debe permitir localizar el error sin abrirla. [Fuentes: contrato de verificación](contratos/verificacion-y-ppa.md); [testbenches previstos](../tb/README.md).

### 8.3 Alineación correcta

Mantener una cola de **salidas esperadas asociadas a cada entrada aceptada**. Con `valid/ready`, extraer la siguiente salida esperada y comparar únicamente cuando `out_valid && out_ready`; bajo pausa, verificar además que datos y metadatos permanezcan estables. Si la interfaz aprobada solo tiene `valid`, comparar en cada ciclo válido. Si el filtro en frecuencia emite por ráfagas, la cola conserva el orden sin imponer que su latencia coincida con la temporal. Los marcadores de bloque y los índices permiten detectar una salida que falta o sobra. Al terminar, verificar también el conteo: mismas entradas aceptadas y mismas salidas esperadas según la política de cola. Comparar por ciclos sin consultar la aceptación produce falsos fallos; ignorar los conteos permite falsos PASS.

Una tolerancia de punto fijo debe justificarse por un cambio real de orden de operaciones o de escalado. Si el modelo fijo reproduce la microarquitectura, preferir comparación exacta de palabras. Nunca aumentar tolerancia hasta que pase un error de solapamiento. Para Python flotante vs FFT flotante, usar una tolerancia absoluta/relativa declarada y reportar error máximo por muestra y error RMS.

### 8.4 Vectores reproducibles

El generador debe guardar versión de configuración, semilla, número de símbolos, mapeo QPSK, coeficientes y formatos. Versionar un conjunto **pequeño** para smoke; generar regresiones grandes en build. La referencia se regenera desde código, no se edita a mano. Un vector debe dejar claro si cada fila representa símbolo, muestra sobremuestreada, entrada aceptada o salida válida, y cómo se emparejan I y Q. [Vectores previstos](../vectors/README.md); [contrato de señales](contratos/senales-y-formatos.md).

### 8.5 Qué prueba hoy la automatización del repo

[make smoke](../Makefile) llama a [scripts/ci.py](../scripts/ci.py): valida configuración, compila Python y ejecuta tests. Para cada variante registrada en [config/rtl_targets.json](../config/rtl_targets.json), compila testbench con Icarus Verilog y lo simula con vvp. El testbench debe terminar con error —por ejemplo `$fatal`— si algo falla. El registro está vacío en la etapa documentada por el repo: “smoke verde” todavía **no** demuestra vector matching. En el PR que agrega RTL hay que registrar la variante junto con su testbench.

Los tests Python actuales comprueban requisitos del andamiaje, ausencia de RTL registrado faltante/duplicado y coherencia de dependencias entre backlog y Gantt. Al crecer el proyecto, agregar pruebas que cubran las **ecuaciones y casos difíciles**, no pruebas que solo repitan una línea de la implementación. [Tests del andamiaje](../tests/test_scaffold.py), [test del plan](../tests/test_plan.py), [CI](../.github/workflows/rtl-ci.yml).

### 8.6 Puertas de aceptación por fase

- **A01–A03:** generador determinista; tablas y modelos flotantes temporal/frecuencia coinciden en casos de borde.
- **A04–A05:** formatos y vectores regenerables; SQNR ≥40 dB según D07; overflow observado o descartado con evidencia.
- **B02/C02:** cada serial registrada; testbench falla cuando se altera un tap o se pierde una salida; smoke demuestra comparación efectiva.
- **B04/C04:** mismos vectores y casos de protocolo; equivalencia funcional con latencia/throughput actualizados; reporte de síntesis y timing reproducible.
- **I01:** tabla con las cuatro variantes bajo condiciones comparables y vínculos a configuración, commit y logs.

---

## 9. Comparación PPA y herramientas

### 9.1 Qué significan las métricas

**Performance:** reportar $f_{\mathrm{max}}$ **medido bajo una tecnología y constraints**, latencia en ciclos y tiempo, $II$, muestras/s y símbolos/s. El cumplimiento de reloj ≥ 100 MHz en variantes rápidas o ≥ 10 MHz en lentas se verifica con análisis temporal a la frecuencia de operación elegida, no con una simulación funcional. Distinguir timing tras síntesis, tras placement y tras routing si existen datos: cambian la precisión del interconnect. Fuentes: Módulo 8, diap. 8–15 y 20–30; Módulo 9, diap. 23–31.

**Área:** en FPGA, LUT/FF/DSP/BRAM y familia de dispositivo; en ASIC, área de celdas bajo la misma biblioteca, corner y constraints, además de memorias/macros si corresponde. El recuento genérico de celdas de Yosys permite una comparación limitada de lógica, pero **no es área física final**. No poner un número FPGA frente a $\mu m^2$ ASIC como si fueran la misma unidad. Fuente: Módulo 8, diap. 12–17 y 30.

**Potencia:** para CMOS, una aproximación de la parte dinámica es $P_{\mathrm{dyn}}\approx \alpha C V^2 f$; además existe potencia estática. $\alpha$ depende de los datos y de las conmutaciones internas. Por eso se requieren tecnología, tensión, corner, reloj, estímulos y actividad (por ejemplo VCD/SAIF si la herramienta lo admite). Indicar si se reporta potencia media, energía por muestra o por símbolo. Una arquitectura de menor potencia instantánea puede consumir más energía por muestra si necesita muchos ciclos. Fuente: Módulo 10, diap. 3–14 y 32–36.

### 9.2 Condiciones de comparación justa

Mantener iguales la función, los ocho taps, escala objetivo, vectores, definición de SQNR, tecnología, biblioteca/dispositivo, corner, restricciones y método de extracción. Las arquitecturas pueden tener distintas latencias y $II$; reportarlos en lugar de ocultarlos. Si una variante corre a otra frecuencia, además del consumo en ese punto operativo comparar energía por muestra o explicar por qué la comparación directa de potencia no es equivalente. Registrar versión de herramienta y commit.

**Plantilla de tabla final:**

| Variante | Commit y config | SQNR dB | Área y unidad | Fmax MHz | Latencia ciclos/ns | II; muestras/s | Potencia mW; energía/muestra | Herramienta, tecnología, corner, log |
|---|---|---:|---:|---:|---:|---:|---:|---|
| Tiempo serial | pendiente | — | — | — | — | — | — | — |
| Tiempo optimizado | pendiente | — | — | — | — | — | — | — |
| Frecuencia serial | pendiente | — | — | — | — | — | — | — |
| Frecuencia optimizado | pendiente | — | — | — | — | — | — | — |

Un campo sin medición se marca **“no medido”**, con motivo. Nunca completar potencia a partir de intuición ni Fmax a partir del período solicitado. [Fuente: contrato de verificación y PPA](contratos/verificacion-y-ppa.md).

### 9.3 Qué automatiza la CI y qué falta

[make full](../Makefile) ejecuta Yosys solo para las variantes del registro que poseen script de síntesis. Puede pasar sin sintetizar nada si aún no hay scripts. En GitHub Actions, **smoke** corre para cada PR y **full** después de integrar en main o manualmente; full es informativo según la guía de colaboración. Los logs quedan como artefactos. No existe despliegue continuo de hardware. [Workflow de CI](../.github/workflows/rtl-ci.yml); [guía de contribución](../CONTRIBUTING.md).

La automatización futura de A07 debe leer resultados reales de herramientas, etiquetarlos con commit/configuración y generar la tabla. Para timing y potencia faltan plataforma, constraints y método en D05–D06. Un reporte Yosys de mapeo genérico no cumple por sí solo la comparación PPA completa.

### 9.4 Ideas de bajo consumo aplicables con cautela

Reducir conmutación innecesaria cuando valid=0, compartir recursos, usar coeficientes constantes/simétricos y elegir anchos adecuados pueden ayudar. Una celda integrada de clock gating requiere flujo de tecnología y checks de timing; no crear un reloj derivado combinacional con una compuerta para “ahorrar potencia”. Operand isolation y clock enable pueden probarse cuando la medición de actividad permita verificar su efecto. Power gating, DVFS, multi-Vt y UPF aparecen en el Módulo 10, diap. 15–47, pero solo entran al proyecto si la plataforma elegida soporta medirlos y el esfuerzo se justifica. Mantener primero una base funcional y comparable.


---

## 10. Recorrido de trabajo, errores y consultas rápidas

### 10.1 Antes de empezar una tarea

1. Leer la issue correspondiente en el [backlog](backlog.md): objetivo, responsable, dependencias **para empezar** y **para cerrar**.
2. Leer la decisión D01–D08 y el contrato particular que afecta la tarea. Si sigue abierta, trabajar con una hipótesis marcada **provisional** y registrar su impacto; no presentarla como requisito de la consigna.
3. Dibujar una prueba manual pequeña: impulso y dos o tres muestras QPSK. Anotar entradas, salidas y ciclos esperados.
4. Fijar el criterio de PASS antes de escribir implementación: ecuación, vector, número de muestras y mensaje de fallo.
5. Tomar una rama corta por tarea; incluir en el PR configuración, semilla, comandos y evidencia. El [CONTRIBUTING](../CONTRIBUTING.md) pide revisión cruzada y smoke verde.

### 10.2 Checklist por hito

**H0 — contrato.** ¿Hay respuesta documentada sobre coeficientes y fase? ¿El filtro en frecuencia especifica transformada, bloques, convolución y bordes? ¿Puertos, formato de datos y método SQNR/PPA permiten construir un testbench común? ¿Los tres revisaron los contratos? [Contratos](contrato-tecnico.md#3-detalle-por-tema).

**H1 — modelos.** ¿El generador QPSK reproduce símbolos con la misma semilla? ¿Hay exactamente ocho taps finitos? ¿El modelo temporal responde al impulso con esos taps? ¿El modelo por bloques coincide con el temporal en límites y cola? ¿El barrido de punto fijo demuestra 40 dB o más bajo la definición pactada? ¿Se detectan saturaciones y overflows? [Backlog A01–A05](backlog.md).

**H2 — seriales.** ¿Se conoce el flanco exacto de aceptación y salida? ¿Cada salida válida corresponde al índice correcto? ¿Se registró la variante junto con testbench en el manifiesto? ¿El testbench falla de forma deliberada si se cambia un tap o se pierde una muestra? ¿El smoke ya ejecuta vector matching real? [Manifiesto](../config/rtl_targets.json).

**H3 — optimizaciones.** ¿Se escribió la hipótesis PPA antes de cambiar RTL? ¿Los mismos vectores siguen pasando? ¿Se midieron latencia, $II$, recursos y timing con condiciones rastreables? ¿Se separa una diferencia numérica pactada de un bug? [Contrato PPA](contratos/verificacion-y-ppa.md).

**Entrega.** ¿Las cuatro filas de la tabla usan una base comparable? ¿Cada gráfico señala herramienta, tecnología, frecuencia y versión? ¿El informe enseña limitaciones y decisiones abiertas? ¿El Gantt muestra inicio y fin **reales** además del plan? ¿Cada integrante puede explicar su implementación y al menos un compromiso PPA? [Gantt](gantt.md).

### 10.3 Ejercicio guiado para probar la teoría antes del RTL

Esta receta genera una **opción de ventana simétrica**, sin normalización ni cuantización. Sirve para detectar índices y singularidades. **No convierte esta opción en la decisión D02.**

~~~python
import numpy as np

def rrc_raw_even_8(beta=0.5, samples_per_symbol=2):
    if not 0 < beta <= 1:
        raise ValueError("Este ejemplo supone 0 < beta <= 1")
    if samples_per_symbol <= 0:
        raise ValueError("samples_per_symbol debe ser positivo")

    k = np.arange(8, dtype=float)
    u = (k - 3.5) / samples_per_symbol
    out = np.empty(8, dtype=float)

    for i, t in enumerate(u):
        if np.isclose(t, 0.0, atol=1e-14, rtol=0):
            out[i] = 1 - beta + 4 * beta / np.pi
        elif np.isclose(abs(t), 1 / (4 * beta), atol=1e-14, rtol=0):
            out[i] = beta / np.sqrt(2) * (
                (1 + 2 / np.pi) * np.sin(np.pi / (4 * beta))
                + (1 - 2 / np.pi) * np.cos(np.pi / (4 * beta))
            )
        else:
            out[i] = (
                np.sin(np.pi * (1 - beta) * t)
                + 4 * beta * t * np.cos(np.pi * (1 + beta) * t)
            ) / (np.pi * t * (1 - (4 * beta * t) ** 2))

    assert np.isfinite(out).all()
    assert np.allclose(out, out[::-1])
    return u, out

u, h = rrc_raw_even_8()
assert len(h) == 8
assert np.allclose(u, -u[::-1])
~~~

Luego crear una entrada de impulso complejo y comparar $\operatorname{convolve}(u,h)$ con la fórmula FIR calculada por un bucle. Repetir con tres símbolos QPSK sobremuestreados. Para ensayar frecuencia, elegir provisionalmente $N=16$, bloques $B=9$ y overlap-add: cada bloque devuelve su convolución de 16 muestras y las últimas siete se suman al bloque siguiente. Comparar todas las muestras con la convolución lineal Python, incluido el final. Finalmente cuantizar **una sola etapa** y observar cuánto cambia el resultado antes de seguir reduciendo bits.

### 10.4 Tabla de síntomas y causas probables

| Síntoma | Primeras comprobaciones |
|---|---|
| El impulso sale invertido | Convención $h[k]$, orden de memoria, índice del MAC. |
| Todo coincide salvo una escala constante | Normalización de $h$; factor $1/N$ de IFFT; punto binario de salida. |
| Error solo alrededor de límites de bloque | Longitud $N$, siete muestras de solapamiento, sumas/descartes, último bloque. |
| I correcto y Q errado | Mapeo de símbolos, signo de multiplicación compleja, orden de puertos. |
| Valores pequeños bien y extremos mal | Extensión de signo, ancho de producto, overflow, saturación. |
| Error de un ciclo o de una muestra | Flanco de aceptación, valid, llenado de pipeline, índice de cola. |
| SQNR bajo sin grandes errores puntuales | Coeficientes cuantizados, demasiados recortes, escala o referencia desalineada. |
| SQNR “infinito” en solo ceros | Denominador y numerador nulos; usar un caso con energía. |
| Simulación pasa y timing falla | Camino combinacional, constraints y tecnología; pipeline/retiming si procede. |
| Área aparentemente muy baja en Yosys | Revisar que el top y las fuentes correctas se sintetizaron; distinguir celdas genéricas de área física. |
| Potencia “mejora” al bajar frecuencia | Comparar también tasa y energía por muestra bajo estímulos iguales. |

### 10.5 Preguntas para la revisión entre compañeros

- **Modelo:** ¿Puedo reproducir los ocho taps desde una fórmula y configuración sin mirar el RTL? ¿Qué hace la referencia con las últimas siete muestras?
- **Tiempo:** ¿En qué flanco entra una muestra y cuándo sale su resultado? ¿La historia se mueve exactamente una vez por muestra aceptada?
- **Frecuencia:** ¿Qué $N$ se usa? ¿Cuántas salidas útiles hay por bloque? ¿Dónde se corrige la circularidad y dónde se aplica $1/N$?
- **Punto fijo:** ¿Cada nodo tiene $W,F$, signo y política de recorte? ¿Qué vector activa el peor caso observado?
- **Verificación:** Si cambio un bit de coeficiente o elimino una salida válida, ¿falla la prueba? ¿El mensaje me dice qué índice se rompió?
- **PPA:** ¿La cifra viene de una herramienta, una tecnología y un log identificables? ¿Se comparan el mismo flujo de muestras y las mismas condiciones?
- **Contrato:** ¿El valor que acabo de usar está aprobado o es una hipótesis? ¿Dónde consta la fuente?

### 10.6 Glosario compacto

| Término | Significado en este trabajo |
|---|---|
| Tap | Un coeficiente $h[k]$ y la muestra histórica con la que se multiplica. |
| RRC / RRCOS | Pulso raíz coseno alzado; no confundir con RC ni con una ventana de “coseno alzado”. |
| Roll-off $\beta$ | Parámetro de exceso de ancho de banda del conformado ideal. |
| Sobremuestreo 2× | Dos instantes de muestra por período de símbolo; el upsampler ideal inserta un cero entre símbolos antes del filtro. |
| I/Q | Componentes real e imaginaria de la señal compleja. |
| Convolución lineal | FIR causal ordinario; longitud $S+M-1$ para secuencias finitas completas. |
| Convolución circular | Operación natural de DFT/IDFT de longitud $N$; requiere método de bloques para reproducir la lineal. |
| Overlap-add/save | Métodos distintos para recomponer una convolución lineal por bloques FFT. |
| $II$ | Ciclos entre entradas aceptadas o trabajos iniciados en régimen. |
| Latencia | Ciclos desde una entrada aceptada hasta su salida válida. |
| SQNR | Relación energía de referencia / energía de error de cuantización bajo un conjunto de muestras definido. |
| PPA | Power, Performance, Area; exige métricas y condiciones comparables. |
| STA | Análisis estático de timing bajo constraints y tecnología. |
| CDC | Cruce entre dominios de reloj distintos; solo aplica si realmente existen. |

---

## 11. Mapa de fuentes

### 11.1 Orden de autoridad

1. **Requisitos del trabajo:** [consigna vigente](consigna-actualizada.md).
2. **Decisiones aprobadas o abiertas:** [contrato técnico](contrato-tecnico.md), [contratos de trabajo](contrato-tecnico.md#3-detalle-por-tema) y [configuración consumida por scripts](../config/project.json).
3. **Implementación y avance:** [backlog](backlog.md), [Gantt](gantt.md), [guía de contribución](../CONTRIBUTING.md), [CI](../.github/workflows/rtl-ci.yml).
4. **Fundamento técnico:** libros de comunicaciones y DSP; módulos del curso. Un ejemplo de clase muestra una técnica, pero no cambia la consigna.

### 11.2 Los diez módulos del curso y su uso aquí

| Material | Partes útiles para este proyecto | Prioridad |
|---|---|---|
| Módulo 1 | Flujo algoritmo→RTL→verificación→PPA; alcance. | Directa. |
| Módulo 2 | Registros, FSM, valid/ready, SystemVerilog y testbench. | Directa. |
| Módulo 3 y resumen | Formatos con signo, cuantización, overflow y constantes. | Directa. |
| Módulo 4, resumen, ejercicios | MAC, sumadores, multiplicadores y costo de compartirlos. | Directa al elegir datapath. |
| Módulo 5 y resumen | CORDIC y arquitecturas iterativas; twiddles si se propone usarlos. | Condicional. |
| Módulo 6 y resumen | DFG, scheduling, pipeline, retiming, folding/unfolding. | Directa. |
| Módulo 7 y resumen | FIR serial/paralelo/sistólico, FFT, SQNR y trade-offs. | Central. |
| Módulo 8 | Síntesis, mapeo, reportes, FPGA/ASIC y limitaciones de PPA temprano. | Directa. |
| Módulo 9 y resumen | Constraints, setup/hold, STA; CDC solo si aparecen varios relojes. | Directa/condicional. |
| Módulo 10 | Potencia, actividad, energía por operación y técnicas low power. | Directa para PPA; técnicas avanzadas condicionales. |

Las diapositivas contienen también ejemplos **distintos** de la consigna, como FIR de cuatro taps o un FIR simétrico ilustrativo de ocho taps en el Módulo 8. Usarlos para aprender arquitectura, **no como coeficientes RRC oficiales**.

### 11.3 Material anterior de comunicaciones

- TP1.ipynb: ejercicios de RC/RRC, variación de $\beta$, espectro y convolución RRC∗RRC. Es una fuente práctica de orientación. Usa 4× y fuerza taps impares; su código necesita adaptación matemática para los ocho taps pares y 2× actuales. La normalización por suma es una elección de ese TP.
- Tarea1.ipynb: ejemplo de símbolos y mapeo QPSK. La nueva interfaz aún debe acordar su propio mapeo y escala.
- Proakis y Salehi, *Digital Communications*, 5.ª ed.: QPSK en PDF pp. 137–146; conformado/raised cosine y RRC en pp. 623–641 y 693–698; filtro adaptado en pp. 197–198.
- Barry, Lee y Messerschmitt, *Digital Communication*: criterio de Nyquist y conformado en PDF pp. 146–152; filtro adaptado en pp. 170–171; convolución circular en pp. 248–251.
- Oppenheim, *Tratamiento de señales en tiempo discreto*: convolución lineal y circular mediante DFT en PDF pp. 669–686. En otras páginas aparece “coseno alzado” como **ventana** de análisis espectral; esa ventana no es el pulso RC/RRC del sistema de comunicaciones.
- Los apuntes escaneados de clases ópticas y el TP de ecualización tratan otros problemas de canal. Solo conviene consultarlos si una duda concreta conecta con filtrado discreto; no trasladar parámetros de fibra, BER o ecualizadores adaptativos al RRC RTL por semejanza de vocabulario.

### 11.4 Cómo mantener viva esta guía

**Estado del repositorio consultado: 2026-10-04.** El repo todavía describe un andamiaje sin coeficientes definitivos ni variantes RTL registradas. Cuando se apruebe un contrato, actualizar la tabla de decisiones del § 1 y reemplazar ejemplos provisionales por enlaces al generador y a los resultados **sin duplicar valores definitivos en múltiples lugares**. Esta guía debe seguir señalando al contrato como fuente de verdad y conservar la explicación de por qué se eligió cada método.
