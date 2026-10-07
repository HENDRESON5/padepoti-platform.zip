"""
PADEPOTI e-ticket system  -  Album Launch, Sunday 8 November 2026
Alliance Francaise Blantyre (Jacaranda), 1PM - 5PM

Commands
  python eticket.py sell  --name "Chikondi Banda" --phone 0999123456
  python eticket.py batch --count 50
  python eticket.py list
  python eticket.py checkin          (door scanning, see README)

Every ticket gets a unique number (PADEPOTI-0001) and a QR code that carries
the number plus a secret signature, so a made-up or edited code is rejected.
"""
import argparse, csv, hashlib, hmac, os, secrets, sys
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from reportlab.graphics.barcode.qrencoder import QRCode, QRErrorCorrectLevel

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "template.png")
OUT_DIR = os.path.join(HERE, "tickets")
GUESTS = os.path.join(HERE, "guests.csv")
KEYFILE = os.path.join(HERE, "secret.key")      # KEEP PRIVATE, do not share
PREFIX = "PADEPOTI"
FIELDS = ["ticket_no", "code", "buyer_name", "phone", "paid",
          "sold_at", "arrived", "arrived_at"]

# Right-hand white panel of the template (where the old barcode was)
PANEL = (1580, 0, 1981, 648)

# ---------- secret + signing ----------
def secret():
    if not os.path.exists(KEYFILE):
        with open(KEYFILE, "w") as f:
            f.write(secrets.token_hex(32))
    return open(KEYFILE).read().strip().encode()

def sign(ticket_no):
    return hmac.new(secret(), ticket_no.encode(), hashlib.sha256).hexdigest()[:10].upper()

def make_code(n):
    ticket_no = f"{PREFIX}-{n:04d}"
    return ticket_no, f"{ticket_no}-{sign(ticket_no)}"

def verify(code):
    """Return ticket_no if the code is genuine, else None."""
    code = code.strip().upper()
    parts = code.rsplit("-", 1)
    if len(parts) != 2:
        return None
    ticket_no, sig = parts
    return ticket_no if hmac.compare_digest(sig, sign(ticket_no)) else None

# ---------- guest list ----------
def read_guests():
    if not os.path.exists(GUESTS):
        return []
    with open(GUESTS, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write_guests(rows):
    with open(GUESTS, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

# ---------- QR + ticket image ----------
def qr_image(text, size):
    # find the smallest version that fits the text
    for version in range(1, 11):
        try:
            qr = QRCode(version, QRErrorCorrectLevel.M)
            qr.addData(text)
            qr.make()
            break
        except Exception:
            continue
    n = qr.getModuleCount()
    border = 2
    scale = max(1, size // (n + 2 * border))
    side = (n + 2 * border) * scale
    img = Image.new("RGB", (side, side), "white")
    px = ImageDraw.Draw(img)
    for r in range(n):
        for c in range(n):
            if qr.isDark(r, c):
                x, y = (c + border) * scale, (r + border) * scale
                px.rectangle([x, y, x + scale - 1, y + scale - 1], fill="black")
    return img

def font(name, size):
    for p in (f"/usr/share/fonts/truetype/google-fonts/Poppins-{name}.ttf",
              "C:/Windows/Fonts/arialbd.ttf" if name == "Bold" else "C:/Windows/Fonts/arial.ttf",
              "/System/Library/Fonts/Helvetica.ttc",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if name == "Bold"
              else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def build_ticket(ticket_no, code, buyer=""):
    im = Image.open(TEMPLATE).convert("RGB")
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = PANEL
    d.rectangle([x0 + 4, y0, x1, y1], fill="white")          # clear old barcode
    qr = qr_image(code, 300)
    cx = (x0 + 4 + x1) // 2
    im.paste(qr, (cx - qr.size[0] // 2, 70))
    def centred(text, y, f, fill):
        w = d.textlength(text, font=f)
        d.text((cx - w / 2, y), text, font=f, fill=fill)
    centred(ticket_no, 70 + qr.size[1] + 14, font("Bold", 30), (20, 20, 50))
    centred("Scan at the entrance", 70 + qr.size[1] + 56, font("Regular", 20), (90, 90, 90))
    if buyer:
        centred(buyer[:26], 70 + qr.size[1] + 88, font("Regular", 20), (20, 20, 50))
    return im

def save_ticket(ticket_no, code, buyer=""):
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, f"{ticket_no}.png")
    build_ticket(ticket_no, code, buyer).save(path)
    return path

# ---------- commands ----------
def next_number(rows):
    return max((int(r["ticket_no"].split("-")[1]) for r in rows), default=0) + 1

def cmd_sell(a):
    rows = read_guests()
    n = next_number(rows)
    ticket_no, code = make_code(n)
    rows.append(dict(ticket_no=ticket_no, code=code, buyer_name=a.name, phone=a.phone,
                     paid="yes", sold_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
                     arrived="no", arrived_at=""))
    write_guests(rows)
    print("Ticket created:", save_ticket(ticket_no, code, a.name))
    print("Send this image to the buyer on WhatsApp / SMS.")

def cmd_batch(a):
    rows = read_guests()
    n = next_number(rows)
    for i in range(a.count):
        ticket_no, code = make_code(n + i)
        rows.append(dict(ticket_no=ticket_no, code=code, buyer_name="", phone="",
                         paid="no", sold_at="", arrived="no", arrived_at=""))
        save_ticket(ticket_no, code)
    write_guests(rows)
    print(f"{a.count} blank tickets saved in {OUT_DIR}.")
    print("Mark each as sold with:  python eticket.py paid PADEPOTI-0001 --name 'X' --phone 099...")

def cmd_paid(a):
    rows = read_guests()
    for r in rows:
        if r["ticket_no"] == a.ticket_no.upper():
            r.update(paid="yes", buyer_name=a.name, phone=a.phone,
                     sold_at=datetime.now().strftime("%Y-%m-%d %H:%M"))
            write_guests(rows)
            print("Ticket created:", save_ticket(r["ticket_no"], r["code"], a.name))
            return
    print("No such ticket.")

def cmd_list(_):
    rows = read_guests()
    sold = sum(r["paid"] == "yes" for r in rows)
    arrived = sum(r["arrived"] == "yes" for r in rows)
    print(f"Tickets: {len(rows)} | sold: {sold} | arrived: {arrived} | income: K{sold*5000:,}")
    for r in rows:
        print(f'{r["ticket_no"]}  paid={r["paid"]:<3}  arrived={r["arrived"]:<3}  {r["buyer_name"]}  {r["phone"]}')

def cmd_checkin(_):
    print("PADEPOTI door check-in. Scan a QR (or type the code). Ctrl+C to stop.\n")
    while True:
        try:
            code = input("Scan > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nDone."); return
        if not code:
            continue
        ticket_no = verify(code)
        if not ticket_no:
            print("  X  FAKE / INVALID CODE - do not admit\n"); continue
        rows = read_guests()
        row = next((r for r in rows if r["ticket_no"] == ticket_no), None)
        if not row:
            print("  X  Ticket not in guest list\n"); continue
        if row["paid"] != "yes":
            print(f"  X  {ticket_no} is NOT PAID\n"); continue
        if row["arrived"] == "yes":
            print(f"  X  ALREADY USED at {row['arrived_at']} ({row['buyer_name']})\n"); continue
        row["arrived"] = "yes"
        row["arrived_at"] = datetime.now().strftime("%H:%M")
        write_guests(rows)
        print(f"  OK  WELCOME {row['buyer_name']}  ({ticket_no})\n")

def main():
    p = argparse.ArgumentParser(description="PADEPOTI e-ticket system")
    s = p.add_subparsers(dest="cmd", required=True)
    x = s.add_parser("sell");  x.add_argument("--name", required=True); x.add_argument("--phone", default=""); x.set_defaults(f=cmd_sell)
    x = s.add_parser("batch"); x.add_argument("--count", type=int, required=True); x.set_defaults(f=cmd_batch)
    x = s.add_parser("paid");  x.add_argument("ticket_no"); x.add_argument("--name", required=True); x.add_argument("--phone", default=""); x.set_defaults(f=cmd_paid)
    x = s.add_parser("list");  x.set_defaults(f=cmd_list)
    x = s.add_parser("checkin"); x.set_defaults(f=cmd_checkin)
    a = p.parse_args()
    a.f(a)

if __name__ == "__main__":
    main()
