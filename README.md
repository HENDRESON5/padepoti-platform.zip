# PADEPOTI E-Ticket System

Album launch, Sunday 8 November 2026, 1PM - 5PM, Alliance Francaise Blantyre (Jacaranda).
Standard ticket: K5,000.

Each ticket gets its own number (PADEPOTI-0001, 0002...) and its own QR code.
The QR carries a secret signature, so nobody can make up or edit a code.

## Step 1: Set up (once, about 10 minutes)

1. Install Python 3 from python.org. On Windows, tick "Add Python to PATH".
2. Put this whole folder on your laptop (for example `Documents/padepoti-eticket`).
3. Open a terminal in the folder (Windows: type `cmd` in the folder's address bar).
4. Run: `pip install -r requirements.txt`

Keep `template.png` in the folder. It is your ticket design.

## Step 2: Sell a ticket

1. The buyer pays K5,000 to your Airtel Money / Mpamba number.
2. CHECK that the money really arrived (look at your own phone, not their screenshot).
3. Run:

       python eticket.py sell --name "Chikondi Banda" --phone 0999123456

4. The ticket image appears in the `tickets` folder (for example `tickets/PADEPOTI-0001.png`).
5. Send that image to the buyer on WhatsApp or SMS. They show it on their phone at the door.

Every sale is saved automatically in `guests.csv` (open it in Excel).

## Optional: pre-make tickets

To make 50 blank tickets in advance: `python eticket.py batch --count 50`
When one is sold: `python eticket.py paid PADEPOTI-0007 --name "Name" --phone 099...`
That re-makes the ticket with the buyer's name. Only tickets marked paid are accepted at the door.

## Step 3: Keep track

`python eticket.py list` shows tickets sold, people arrived and income so far.

## Step 4: At the door (8 November)

1. Open a terminal on the laptop and run: `python eticket.py checkin`
2. For each guest, scan their QR with a phone scanner app (or a USB barcode scanner).
   Copy or type the code it shows into the laptop (a USB scanner types it for you).
3. The screen tells you what to do:
   - `OK WELCOME <name>`: let them in. The ticket is now marked used.
   - `ALREADY USED at <time>`: the ticket was shown before. Do not admit.
   - `FAKE / INVALID CODE`: do not admit.
   - `NOT PAID`: the ticket was never marked paid.

## Rules to keep it safe

- NEVER share `secret.key`. It is created on first run. Anyone who has it can make real-looking tickets.
- Back up `guests.csv` and `secret.key` (copy to a flash disk or email yourself).
  If you lose `secret.key`, old tickets stop validating.
- Do not delete or rename `guests.csv` while selling.
- Run check-in on ONE laptop only, so a ticket cannot be used twice on two devices.

## Files

- `eticket.py`: the program (selling, QR tickets, check-in)
- `template.png`: ticket design (edit it to change the look)
- `requirements.txt`: the two libraries needed
- `tickets/`: created automatically, holds the ticket images
- `guests.csv`: created automatically, your guest list
