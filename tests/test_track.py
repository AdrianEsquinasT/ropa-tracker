import json, sys, unittest
from datetime import date
from pathlib import Path
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import track

def page(price, sizes=None):
    offers = [{"@type": "Offer", "price": price, "size": s, "availability": "https://schema.org/" + ("InStock" if ok else "OutOfStock")} for s, ok in (sizes or {"M": True}).items()]
    ld = {"@context": "https://schema.org", "@type": "Product", "name": "Camiseta test", "image": ["https://x/i.jpg"], "offers": offers}
    return '<script type="application/ld+json">%s</script>' % json.dumps(ld)

ITEM = {"art": "1028/507/716", "type": "top", "label_price": 15.99, "url": "https://www.lefties.com/p"}

class T(unittest.TestCase):
    def test_parse(self):
        p = track.parse_product(page("12,99", {"M": True, "L": False}))
        self.assertEqual((p["price"], p["name"], p["image"], p["stock"]), (12.99, "Camiseta test", "https://x/i.jpg", {"M": True, "L": False}))
    def test_drop_alert_and_size(self):
        with mock.patch.object(track, "fetch", return_value=page("12.99", {"M": True, "L": False})):
            rec, alert = track.check_item(ITEM, None, date(2026, 11, 27))
        self.assertEqual(rec["price"], 12.99); self.assertEqual(rec["in_my_size"], ["M"])
        self.assertEqual(alert["old"], 15.99); self.assertEqual(len(rec["history"]), 2)
    def test_no_change_no_alert(self):
        with mock.patch.object(track, "fetch", return_value=page("15.99")):
            rec, alert = track.check_item(ITEM, None, date(2026, 11, 27))
        self.assertIsNone(alert); self.assertEqual(len(rec["history"]), 1)
    def test_rise_no_alert(self):
        with mock.patch.object(track, "fetch", return_value=page("19.99")):
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
    def test_image_downloaded(self):
        with mock.patch.object(track, "fetch", return_value=page("12.99")), \
             mock.patch.object(track, "download_image", return_value="img/x.jpg") as d:
            rec, _ = track.check_item(ITEM, None, date(2026, 11, 27))
        self.assertEqual(rec["image"], "img/x.jpg"); d.assert_called_once()
    def test_email(self):
        a = [{"name": "n", "old": 15.99, "new": 12.99, "url": "u", "art": "a", "in_my_size": ["M"]}]
        env = {"SMTP_USER": "u@x", "SMTP_PASS": "p", "EMAIL_TO": "t@x"}
        with mock.patch.dict("os.environ", env), mock.patch("smtplib.SMTP_SSL") as s:
            self.assertTrue(track.send_email(a, date(2026, 11, 27)))
            msg = s.return_value.__enter__.return_value.send_message.call_args[0][0]
        self.assertIn("[Black Friday]", msg["Subject"])
unittest.main() if __name__ == "__main__" else None
