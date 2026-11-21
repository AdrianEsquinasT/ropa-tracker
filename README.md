# Cesta de deseos

Web estática (GitHub Pages) con tres apartados —ropa, relojes y perfumes— donde
guardas lo que te gusta: foto, precio, tienda, enlace directo y tu talla.
Selecciona varios artículos para ver el total, enviarte el informe por correo o
guardarlo en PDF.

Web: https://adrianesquinast.github.io/ropa-tracker/

## Añadir artículos desde el móvil

1. Pulsa **+ Añadir**, elige categoría y rellena nombre, tienda y precio.
2. Para la foto: en la web de la tienda mantén pulsada la imagen y elige
   *Copiar enlace de la imagen*; pégalo en el campo **Foto**.
3. Se guarda en ese dispositivo. Para tenerlo en todos, pulsa
   **Exportar añadidos** y pega el texto dentro de `items.json` (GitHub lo deja
   editar desde el navegador del móvil).

## Fotos y precios automáticos

`scripts/track.py` sabe leer precio, foto y tallas de la ficha del producto,
pero **Zara, Lefties, Pull&Bear y Bershka bloquean las IP de centro de datos**
(escudo anti-bot de Akamai). Desde GitHub Actions casi con seguridad fallará y
verás el precio de la etiqueta con el aviso *sin datos web*.

Alternativas, de menos a más trabajo:

- **Foto por enlace** (recomendado): pega la URL de la imagen en `items.json`
  (`"photo": "https://…jpg"`). Tu móvil la carga directamente desde la tienda.
- **Foto subida al repositorio**: sube el archivo a `docs/img/` y pon
  `"photo": "img/nombre.jpg"`.
- **Ejecutarlo en tu Mac**, cuya IP es doméstica y no suele estar bloqueada:

      python3 scripts/track.py && python3 -m http.server -d docs

## Avisos de bajada de precio por correo

Solo funcionan si `track.py` consigue leer el precio (ver el apartado anterior).
Hacen falta tres secretos en el repositorio:

1. Activa la verificación en dos pasos de Google en myaccount.google.com/security
2. Crea una contraseña de aplicación en myaccount.google.com/apppasswords
   (16 letras; no es la contraseña de tu Gmail).
3. En GitHub: *Settings → Secrets and variables → Actions → New repository secret*
   y crea los tres, uno a uno:

   | Nombre      | Valor                               |
   |-------------|-------------------------------------|
   | `SMTP_USER` | tu dirección de Gmail               |
   | `SMTP_PASS` | la contraseña de aplicación de 16 letras |
   | `EMAIL_TO`  | la dirección donde quieres el aviso |

Los secretos no se pueden volver a leer, ni siquiera tú: si lo pierdes, se borra
y se crea otro. Nunca los escribas en `items.json` ni en ningún archivo.

## Comprobación automática

`.github/workflows/track.yml` se ejecuta cada 6 horas y también a mano desde la
pestaña *Actions*. Guarda el histórico de precios en `docs/data.json`, así que
una bajada queda registrada aunque el correo falle.

## Pruebas

    python3 tests/test_track.py
