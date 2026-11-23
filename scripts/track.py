#!/usr/bin/env python3
"""Comprueba precios de items.json, actualiza docs/data.json y avisa por email si bajan."""
import json, os, re, smtplib, sys, urllib.parse, urllib.request
from datetime import date, datetime, timezone
from email.message import EmailMessage
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ITEMS = ROOT / "items.json"
DATA = ROOT / "docs" / "data.json"
WANTED = {"top": ["M", "L"], "bottom": ["40", "42"], "shoe": ["40.5", "41", "41.5", "42"],
          "watch": [], "perfume": []}
CATEGORIES = ("ropa", "relojes", "perfumes")
BLACK_FRIDAY = (date(2026, 11, 20), date(2026, 12, 1))
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


def fetch(url, with_url=False):
    """Descarga la página. with_url devuelve también la URL final tras los redirects."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "es-ES,es;q=0.9"})
    with urllib.request.urlopen(req, timeout=30) as r:
        html = r.read().decode("utf-8", "replace")
        return (html, r.geturl()) if with_url else html


def download_image(url, art, referer):
    """Guarda la foto en docs/img/ (evita hotlinking bloqueado). Devuelve ruta relativa o None."""
    slug = re.sub(r"\W+", "-", art).strip("-")
    img_dir = ROOT / "docs" / "img"
    for f in img_dir.glob(slug + ".*"):
        return "img/" + f.name
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": referer})
        with urllib.request.urlopen(req, timeout=30) as r:
            ctype, data = r.headers.get("Content-Type", ""), r.read(3_000_000)
        ext = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}.get(ctype.split(";")[0])
        if not ext or len(data) < 500:
            return None
        img_dir.mkdir(parents=True, exist_ok=True)
        (img_dir / (slug + ext)).write_bytes(data)
        return "img/" + slug + ext
    except Exception:
        return None


def _walk(o):
    if isinstance(o, dict):
        yield o
        for v in o.values():
            yield from _walk(v)
    elif isinstance(o, list):
        for v in o:
            yield from _walk(v)


def _num(x):
    try:
        return float(str(x).replace(",", "."))
    except (TypeError, ValueError):
        return None


def parse_product(html):
    """Extrae nombre, imagen, precio y tallas de JSON-LD (schema.org/Product) u og:."""
    out = {"name": None, "image": None, "price": None, "stock": None}
    for blk in re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', html, re.S | re.I):
        try:
            data = json.loads(blk)
        except ValueError:
            continue
        for o in _walk(data):
            t = o.get("@type")
            if t == "Product" or (isinstance(t, list) and "Product" in t):
                out["name"] = out["name"] or o.get("name")
                img = o.get("image")
                if isinstance(img, list):
                    img = img[0] if img else None
                if isinstance(img, dict):
                    img = img.get("url")
                out["image"] = out["image"] or img
                offers = o.get("offers")
                offers = offers if isinstance(offers, list) else [offers] if offers else []
                prices, stock = [], {}
                for of in offers:
                    p = _num(of.get("price") or of.get("lowPrice"))
                    if p is not None:
                        prices.append(p)
                    size = of.get("size") or (of.get("itemOffered") or {}).get("size")
                    if size:
                        stock[str(size).upper()] = str(of.get("availability", "")).endswith("InStock")
                if prices:
                    out["price"] = min(prices)
                if stock:
                    out["stock"] = stock
    if not out["image"]:
        m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', html)
        out["image"] = m.group(1) if m else None
    if not out["name"]:
        m = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)', html)
        out["name"] = m.group(1) if m else None
    if out["price"] is None:
        m = re.search(r'product:price:amount["\'][^>]+content=["\']([\d.,]+)', html)
        out["price"] = _num(m.group(1)) if m else None
    return out


DOMAINS = {"Lefties": "lefties.com", "Zara": "zara.com", "Bershka": "bershka.com", "Pull&Bear": "pullandbear.com"}


def find_url(art, store="Lefties"):
    """EXPERIMENTAL: intenta localizar la URL buscando por referencia. Lo fiable es rellenar 'url'."""
    dom = DOMAINS.get(store)
    if not dom:
        return None
    ref = "".join(art.split("/")[:2])
    base = "https://www." + dom
    html = fetch(base + "/es/search?term=" + urllib.parse.quote(ref))
    m = re.search(r'href=["\'](https://www\.[^"\']*%s[^"\']*)' % ref, html) or \
        re.search(r'href=["\'](/es/[^"\']*%s[^"\']*)' % ref, html)
    return urllib.parse.urljoin(base, m.group(1)) if m else None


def in_my_size(stock, wanted):
    if not stock:
        return None
    return [s for s in wanted if stock.get(s.upper())]


def build_record(item, prev, today):
    rec = prev or {
        "art": item["art"], "history": [{"date": today.isoformat(), "price": item["label_price"], "source": "etiqueta"}],
    }
    rec.update({
        "type": item["type"], "store": item.get("store", "Lefties"),
        "category": item.get("category", "ropa"),
        "original_price": item.get("label_original"), "label_size": item.get("label_size"),
        "wanted": item.get("wanted", WANTED.get(item["type"], [])),
        "desc": item.get("desc", ""),
        "name": item.get("name") or rec.get("name") or "Ref. " + item["art"],
        "url": item.get("url") or rec.get("url") or "",
        "image": item.get("photo") or rec.get("image") or "",
        "noref": bool(item.get("noref")),
    })
    # datos que la app ya leyó de la tienda: se conservan mientras el scraper no consiga otros
    if item.get("sizes"):
        rec["sizes"] = item["sizes"]
    if "in_my_size" in item and rec.get("in_my_size") is None:
        rec["in_my_size"] = item["in_my_size"]
    # precio corregido a mano desde la app: se apunta una sola vez (sin alternar con el de la web)
    mp = item.get("manual_price")
    if mp is not None:
        last_manual = next((h["price"] for h in reversed(rec["history"]) if h.get("source") == "manual"), None)
        if last_manual != mp and rec["history"][-1]["price"] != mp:
            rec["history"].append({"date": today.isoformat(), "price": mp, "source": "manual"})
    return rec


def check_item(item, prev, today):
    rec = build_record(item, prev, today)
    alert = None
    try:
        url = rec["url"] or find_url(item["art"], item.get("store", "Lefties"))
        if not url:
            raise RuntimeError("sin URL: añádela en items.json")
        rec["url"] = url
        html, final = fetch(url, with_url=True)
        rec["final_url"] = final
        info = parse_product(html)
        if info["price"] is None:
            raise RuntimeError("no se encontró precio en la página")
        if info["name"] and not item.get("name"):
            rec["name"] = info["name"]
        if info["image"] and not item.get("photo"):
            img = urllib.parse.urljoin(final, info["image"])
            rec["image"] = download_image(img, item["art"], final) or img
        rec["stock"] = info["stock"]
        rec["in_my_size"] = in_my_size(info["stock"], rec["wanted"])
        last = rec["history"][-1]["price"]
        if info["price"] != last:
            rec["history"].append({"date": today.isoformat(), "price": info["price"], "source": "web"})
            if info["price"] < last:
                alert = {"name": rec["name"], "old": last, "new": info["price"], "url": url, "art": item["art"],
                         "in_my_size": rec["in_my_size"]}
        rec["status"] = "ok"
    except Exception as e:  # un fallo no debe tumbar al resto
        rec["status"] = "error: %s" % e
    if not rec["wanted"]:                      # relojes y perfumes no tienen talla
        rec["in_my_size"] = None
    elif "in_my_size" not in rec:
        rec["in_my_size"] = item.get("in_my_size")
    rec["price"] = rec["history"][-1]["price"]
    rec["last_checked"] = datetime.now(timezone.utc).isoformat(timespec="minutes")
    return rec, alert


def send_email(alerts, today):
    user, pwd, to = os.getenv("SMTP_USER"), os.getenv("SMTP_PASS"), os.getenv("EMAIL_TO")
    if not (user and pwd and to):
        print("Email no configurado; alertas:", alerts)
        return False
    bf = BLACK_FRIDAY[0] <= today <= BLACK_FRIDAY[1]
    lines = []
    for a in alerts:
        talla = "" if a["in_my_size"] is None else (" | tu talla: " + (", ".join(a["in_my_size"]) or "agotada"))
        lines.append("%s (%s): %.2f € -> %.2f €%s\n%s" % (a["name"], a["art"], a["old"], a["new"], talla, a["url"]))
    msg = EmailMessage()
    msg["Subject"] = "%sLefties: bajada de precio (%d)" % ("[Black Friday] " if bf else "", len(alerts))
    msg["From"], msg["To"] = user, to
    msg.set_content("\n\n".join(lines))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(user, pwd)
        s.send_message(msg)
    return True


def main():
    today = date.today()
    items = json.loads(ITEMS.read_text("utf-8"))
    prev = {r["art"]: r for r in json.loads(DATA.read_text("utf-8")).get("items", [])} if DATA.exists() else {}
    records, alerts = [], []
    for it in items:
        rec, alert = check_item(it, prev.get(it["art"]), today)
        records.append(rec)
        print(it["art"], rec["status"], rec["price"])
        if alert:
            alerts.append(alert)
    DATA.write_text(json.dumps({"updated": datetime.now(timezone.utc).isoformat(timespec="minutes"), "items": records},
                               ensure_ascii=False, indent=1), "utf-8")
    if alerts:
        send_email(alerts, today)


if __name__ == "__main__":
    sys.exit(main())
