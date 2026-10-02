# Consigna original

Se implementará por separado dos tipos de filtros complejos. Uno en el dominio del tiempo y otro en la frecuencia. Será un filtro de 8  coeficientes y serán los del un RRCOS con roll off del 50% y con un oversampling de 2x. Los simbolos de entrada que transmitirá con QPSK.

La idea es cada grupo implemente alguna manera distinta de cada uno para poder discutir los resultados de la misma, agregando alguna técnica para mejorar alguno de los 3 ejes de optimización PPA. (Performance-time, Power, Area). Empezaremos por generar nuestro simulador en python del filtro en floating point. Luego lo llevaremos a fxp probando los numeros de bits para para medir su SQNR de manera de no tener menos de 40dB.

Una vez implementado en sus dos versiones, vamos a impementar la versión serial y hacer vector matching de ambas. Terminado esto se va a llevar la implementación de ambos a algunas de las aprendidas para mejorar alguno de los ejes de optimización. Las opciones serán paralela (unfolded), pipeline, sistólica, folded o una mezcla entre ellas. Para las versiones rapidas la frecuencia a la que se deberia llegar es 100MHz, mientas que en las lentas seria de unos 10MHz. Tratar de llegar a la mejor relacion PPA.

Deberán presentarse los resultados en filminas contrastando resultados entre las mismas y resaltando lo aprendido. Los grupos pueden ser de a 4 personas y pueden distribuirse el trabajo como mejor les parezca. Es también requerimiento del mismo hacer un Gantt con la subdivisión de todas las tareas y como se fueron distribuyendo. Se presentará el práctico en fecha acordada con el profesor antes de que termine el año.
