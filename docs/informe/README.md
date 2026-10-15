# Informe técnico (I02)

`main.tex` incluye una sección por archivo en `secciones/`, así cada uno edita la suya sin conflictos. Las secciones sin redactar usan `\pendiente{responsable}{qué va}`; al redactarlas, reemplazar el recuadro.

Compilar desde esta carpeta (requiere XeLaTeX o LuaLaTeX por `fontspec`):

```sh
tectonic main.tex        # o: latexmk -xelatex main.tex
```

Las cifras salen de los comandos del apéndice A; si cambia un modelo o un formato, regenerarlas y actualizar el texto.
