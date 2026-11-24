import json, sys, unittest
from datetime import date
from pathlib import Path
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import track

def page(price, sizes=None, _final="https://www.lefties.com/p"):
    offers = [{"@type": "Offer", "price": price, "size": s, "availability": "https://schema.org/" + ("InStock" if ok else "OutOfStock")} for s, ok in (sizes or {"M": True}).items()]
    ld = {"@context": "https://schema.org", "@type": "Product", "name": "Camiseta test", "image": ["https://x/i.jpg"], "offers": offers}
    return '<script type="application/ld+json">%s</script>' % json.dumps(ld)


def resp(price, sizes=None):
    """fetch(url, with_url=True) devuelve (html, url_final)."""
    return (page(price, sizes), "https://www.lefties.com/p")

ITEM = {"art": "1028/507/716", "type": "top", "label_price": 15.99, "url": "https://www.lefties.com/p"}

class T(unittest.TestCase):
    def test_parse(self):
        p = track.parse_product(page("12,99", {"M": True, "L": False}))
        self.assertEqual((p["price"], p["name"], p["image"], p["stock"]), (12.99, "Camiseta test", "https://x/i.jpg", {"M": True, "L": False}))
    def test_drop_alert_and_size(self):
        with mock.patch.object(track, "fetch", return_value=resp("12.99", {"M": True, "L": False})):
            rec, alert = track.check_item(ITEM, None, date(2026, 11, 27))
        self.assertEqual(rec["price"], 12.99); self.assertEqual(rec["in_my_size"], ["M"])
        self.assertEqual(alert["old"], 15.99); self.assertEqual(len(rec["history"]), 2)
    def test_no_change_no_alert(self):
        with mock.patch.object(track, "fetch", return_value=resp("15.99")):
            rec, alert = track.check_item(ITEM, None, date(2026, 11, 27))
        self.assertIsNone(alert); self.assertEqual(len(rec["history"]), 1)
    def test_rise_no_alert(self):
        with mock.patch.object(track, "fetch", return_value=resp("19.99")):
            rec, alert = track.check_item(ITEM, None, date(2026, 11, 27))
        self.assertIsNone(alert); self.assertEqual(rec["price"], 19.99)
    def test_failure_keeps_label_price(self):
        with mock.patch.object(track, "fetch", side_effect=OSError("403")):
            rec, alert = track.check_item(ITEM, None, date(2026, 11, 27))
        self.assertTrue(rec["status"].startswith("error")); self.assertEqual(rec["price"], 15.99)
    def test_no_url(self):
        with mock.patch.object(track, "find_url", return_value=None):
            rec, _ = track.check_item({**ITEM, "url": ""}, None, date(2026, 11, 27))
        self.assertIn("sin URL", rec["status"])
    def test_final_url_recorded(self):
        with mock.patch.object(track, "fetch", return_value=(page("12.99"), "https://www.pullandbear.com/es/prenda-p123.html")):
            rec, _ = track.check_item(ITEM, None, date(2026, 11, 27))
        self.assertEqual(rec["final_url"], "https://www.pullandbear.com/es/prenda-p123.html")
    def test_image_downloaded(self):
        with mock.patch.object(track, "fetch", return_value=resp("12.99")), \
             mock.patch.object(track, "download_image", return_value="img/x.jpg") as d:
            rec, _ = track.check_item(ITEM, None, date(2026, 11, 27))
        self.assertEqual(rec["image"], "img/x.jpg"); d.assert_called_once()
    def test_app_fields_pass_through(self):
        it = {"art": "m1x", "noref": True, "type": "top", "label_price": 25.99, "label_original": 39.99,
              "url": "", "wanted": ["M", "L"], "in_my_size": ["M"], "sizes": [["M", True], ["L", False]], "category": "ropa"}
        rec, _ = track.check_item(it, None, date(2026, 11, 27))
        self.assertTrue(rec["noref"]); self.assertEqual(rec["in_my_size"], ["M"])
        self.assertEqual(rec["original_price"], 39.99); self.assertEqual(rec["sizes"][1], ["L", False])
    def test_manual_price_once_no_flipflop(self):
        it = {**ITEM, "url": "", "manual_price": 19.99}
        rec, _ = track.check_item(it, None, date(2026, 11, 27))
        self.assertEqual(rec["price"], 19.99)
        # siguiente ejecución: la web dice otra cosa; el precio manual no se vuelve a apuntar
        with mock.patch.object(track, "fetch", return_value=resp("15.99")):
            rec2, _ = track.check_item({**ITEM, "manual_price": 19.99}, json.loads(json.dumps(rec)), date(2026, 11, 28))
        rec3, _ = track.check_item({**it}, json.loads(json.dumps(rec2)), date(2026, 11, 29))
        self.assertEqual([h["source"] for h in rec3["history"]].count("manual"), 1)
    def test_supabase_mode(self):
        rows = [{"id": "r1", "art": "7210/538/104", "price": 27.99, "status": "manual",
                 "history": [{"date": "2026-11-20", "price": 27.99, "source": "alta"}],
                 "data": {"name": "Polo rugby", "type": "top", "url": "https://www.pullandbear.com/es/-l07210538",
                          "wanted": ["M", "L"], "label_price": 27.99, "category": "ropa"}},
                {"id": "r2", "art": "m1x", "price": 79, "status": "manual", "history": [],
                 "data": {"name": "Sauvage", "type": "perfume", "url": "", "wanted": [], "category": "perfumes"}}]
        calls = []
        def fake_sb(method, path, body=None):
            calls.append((method, path, body)); return rows if method == "GET" else None
        with mock.patch.object(track, "sb", fake_sb), \
             mock.patch.object(track, "fetch", return_value=(page("21.99", {"M": True, "L": False}), "https://www.pullandbear.com/es/polo-l07210538")), \
             mock.patch.object(track, "send_email") as se:
            track.main_supabase()
        patches = {p.split("eq.")[1]: b for m, p, b in calls if m == "PATCH"}
        self.assertEqual(patches["r1"]["price"], 21.99)                      # bajada guardada
        self.assertEqual(patches["r1"]["data"]["in_my_size"], ["M"])          # tu talla leída
        self.assertEqual(patches["r1"]["data"]["name"], "Polo rugby")         # no pisa tus datos
        self.assertEqual(patches["r2"]["price"], 79)                          # sin URL: conserva precio
        se.assert_called_once()                                               # aviso por correo de la bajada
    def test_email(self):
        a = [{"name": "n", "old": 15.99, "new": 12.99, "url": "u", "art": "a", "in_my_size": ["M"]}]
        env = {"SMTP_USER": "u@x", "SMTP_PASS": "p", "EMAIL_TO": "t@x"}
        with mock.patch.dict("os.environ", env), mock.patch("smtplib.SMTP_SSL") as s:
            self.assertTrue(track.send_email(a, date(2026, 11, 27)))
            msg = s.return_value.__enter__.return_value.send_message.call_args[0][0]
        self.assertIn("[Black Friday]", msg["Subject"])
unittest.main() if __name__ == "__main__" else None
