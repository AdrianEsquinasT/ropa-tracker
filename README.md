# Lefties tracker

Web estática (GitHub Pages) + GitHub Actions que comprueba precios cada 6 h y envía email si bajan.

## Puesta en marcha
1. Crea un repo **público** en GitHub (Pages gratis no funciona con repos privados en plan Free) y sube esta carpeta.
2. Settings → Pages → Source: *Deploy from a branch* → `main` / carpeta `/docs`.
3. Settings → Secrets and variables → Actions → New secret: `SMTP_USER` (tu Gmail), `SMTP_PASS` (contraseña de aplicación de Google, requiere verificación en 2 pasos), `EMAIL_TO` (destino).
4. En `items.json` pega la `url` de cada prenda (abre la prenda en lefties.com y copia el enlace). Opcional: `name` y `photo`.
5. Actions → track → *Run workflow*. Mira la web en `https://<usuario>.github.io/<repo>/` (en el móvil, "Añadir a pantalla de inicio").

## Probar en local (Mac)
    python3 tests/test_track.py && python3 scripts/track.py && python3 -m http.server -d docs
