# Cesta de deseos

Web estática (GitHub Pages) con tres apartados —ropa, relojes y perfumes— donde
guardas lo que te gusta: foto, precio, tienda, enlace directo y tu talla.
Selecciona varios artículos para ver el total, enviarte el informe por correo o
guardarlo en PDF.

Web: https://adrianesquinast.github.io/ropa-tracker/

## Añadir desde la tienda, con todo relleno

Pegar solo la URL en la app no puede traer precio ni tallas: el navegador
impide que una web lea las páginas de otra (CORS), y las tiendas de Inditex
bloquean los servidores. Por eso existe el botón **＋ A mi cesta**
(`docs/bookmarklet.js`, instalación en `instalar.html`):

1. Abre la ficha del producto en el navegador.
2. Pulsa el marcador **＋ A mi cesta**.
3. Se añade solo a la cesta con nombre, precio (y el anterior si está rebajado),
   foto, tienda, referencia, tallas disponibles, ml o mm. El aviso ofrece Editar y Deshacer.

Solo lee lo que la página ya muestra; no hace peticiones extra a la tienda
ni envía nada a terceros. Los datos viajan en el fragmento `#` del enlace,
que no llega a ningún servidor.

## Sincronizar entre dispositivos (opcional, recomendado)

Sin esto, lo que añades se queda en el navegador donde lo añadiste. Con esto, cada
alta, edición o borrado se guarda en `items.json` del repositorio: aparece en todos
tus dispositivos y entra en el seguimiento de precios.

1. En la app, pulsa el icono de la nube (arriba) o "Sincronizar".
2. Crea una clave *fine-grained* en GitHub con acceso **solo a este repositorio** y
   el permiso **Contents: Read and write** (la app explica los pasos).
3. Pégala y pulsa "Guardar y probar". Repite en cada dispositivo.

La clave se guarda solo en ese navegador, nunca en el repositorio. Si no hay
conexión, los cambios esperan en cola y se suben solos al volver. Si dos
dispositivos guardan a la vez, se reintenta sin perder nada.

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
