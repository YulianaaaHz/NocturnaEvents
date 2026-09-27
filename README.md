# Nocturna Events PRO — versión corregida

## Render

Build:
`pip install -r requirements.txt`

Start:
`gunicorn app:app`

## Panel

`/login`

Usuario inicial:
`admin`

Contraseña inicial:
`cambia-esta-clave`

Cámbiala desde el panel después del primer acceso.

## Galería

La galería funciona por álbum/sección:

- Crear una fiesta con un nombre, por ejemplo `Summer Night 2026`.
- Pegar una URL de imagen por línea.
- Si después vuelves a usar `Summer Night 2026`, las nuevas fotos se agregan al mismo álbum.
- Las fotos anteriores no se reemplazan.
- Una foto solamente se elimina si el administrador pulsa `Eliminar`.

## Posición del texto de inicio

En `Panel → Diseño` puedes mover el bloque de texto del inicio con:

- Horizontal
- Vertical
- Ancho máximo
- Tamaño del bloque
- Alineación

Los cambios se guardan desde el panel y no requieren editar CSS.

## Persistencia en Render

La base de datos es SQLite. Para conservarla entre nuevos deploys/reinicios que eliminen el filesystem, configura `DATA_DIR` apuntando a un almacenamiento persistente disponible en tu servicio de Render. Si no tienes almacenamiento persistente, el código seguirá funcionando, pero ningún programa que guarde SQLite solamente en el filesystem local puede garantizar los datos después de que el proveedor destruya ese filesystem.

## Cambios importantes de esta versión

- Corregidas las referencias `url_for` que causaban el error 500 (`del_gallery`, `del_event`, `del_quote`).
- Añadida la ruta que faltaba para eliminar cotizaciones.
- La galería usa `INSERT` y nunca reemplaza las fotos al agregar nuevas.
- La portada ya no limita artificialmente la consulta de la galería.
- Migración segura de nuevos ajustes: no borra la configuración existente.
- Se eliminaron inconsistencias entre los nombres de campos del panel y los textos realmente usados por la web.
- Render/Gunicorn usa el puerto de `PORT` y `debug=False`.
