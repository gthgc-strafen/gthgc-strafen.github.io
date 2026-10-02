#!/usr/bin/env python3
"""
Baut index.html aus den Dateien in data/.

Aufruf:  python3 build.py

Das Skript schreibt index.html NUR, wenn alle Pruefungen bestanden sind.
Am Ende steht ein Pruefbericht mit alter und neuer Summe.
"""

import base64
import csv
import json
import math
import sys
from datetime import datetime
from pathlib import Path

HIER = Path(__file__).parent
DATA = HIER / "data"
STAND_DATEI = DATA / "stand.json"

fehler = []
warnungen = []


def euro(strafen, satz):
    return f"{strafen * satz:.2f} €".replace(".", ",")


# ---------------------------------------------------------------- einlesen
def lade_json(pfad):
    try:
        return json.loads(pfad.read_text(encoding="utf-8"))
    except FileNotFoundError:
        sys.exit(f"ABBRUCH: Datei fehlt: {pfad}")
    except json.JSONDecodeError as e:
        sys.exit(f"ABBRUCH: {pfad.name} ist kaputt (Zeile {e.lineno}): {e.msg}\n"
                 f"Meist ein fehlendes Komma oder eine Klammer zu viel.")


katalog = lade_json(DATA / "katalog.json")
stamm = lade_json(DATA / "spieler.json")

SATZ = katalog["satz_euro"]
REGELN = {r["nr"]: r for r in katalog["regeln"]}
SPIELER = {s["name"]: s for s in stamm["spieler"]}


# ----------------------------------------------------- Verstoesse einlesen
def lies_verstoesse():
    pfad = DATA / "verstoesse.csv"
    if not pfad.exists():
        sys.exit(f"ABBRUCH: Datei fehlt: {pfad}")

    zeilen = []
    for nr, roh in enumerate(pfad.read_text(encoding="utf-8").splitlines(), start=1):
        text = roh.strip()
        if not text or text.startswith("#") or text.startswith("datum;"):
            continue
        teile = next(csv.reader([text], delimiter=";"))
        teile += [""] * (5 - len(teile))
        datum, name, regel, menge, notiz = (t.strip() for t in teile[:5])

        if not datum or not name or not regel:
            fehler.append(f"Zeile {nr}: Datum, Name oder Regel fehlt → {text!r}")
            continue
        try:
            datetime.strptime(datum, "%d.%m.%Y")
        except ValueError:
            fehler.append(f"Zeile {nr}: Datum '{datum}' nicht im Format TT.MM.JJJJ")
            continue
        if name not in SPIELER:
            aehnlich = [s for s in SPIELER if s.lower().startswith(name[:3].lower())]
            tipp = f" Meintest du: {', '.join(aehnlich)}?" if aehnlich else ""
            fehler.append(f"Zeile {nr}: '{name}' steht nicht in spieler.json.{tipp}")
            continue
        if regel not in REGELN:
            fehler.append(f"Zeile {nr}: Regel '{regel}' gibt es im Katalog nicht.")
            continue

        r = REGELN[regel]
        if r["formel"] in ("pro_menge", "pro_5min"):
            if not menge:
                fehler.append(f"Zeile {nr}: Regel {regel} braucht eine Menge ({r['einheit']}).")
                continue
            try:
                menge_zahl = float(menge.replace(",", "."))
            except ValueError:
                fehler.append(f"Zeile {nr}: Menge '{menge}' ist keine Zahl.")
                continue
            if menge_zahl <= 0:
                fehler.append(f"Zeile {nr}: Menge muss groesser als 0 sein.")
                continue
        else:
            menge_zahl = 1
            if menge:
                warnungen.append(f"Zeile {nr}: Regel {regel} hat einen festen Satz – "
                                 f"die Menge '{menge}' wird ignoriert.")

        # Strafen berechnen
        if r["formel"] == "fest":
            strafen = r["strafen"]
        elif r["formel"] == "pro_menge":
            strafen = int(round(r["strafen"] * menge_zahl))
        elif r["formel"] == "pro_5min":
            strafen = r["strafen"] * math.ceil(menge_zahl / 5)
        else:  # sachleistung
            strafen = 0

        if r["formel"] == "pro_5min":
            beschreibung = f"Nr. {regel} · {r['de']['text']} ({menge_zahl:g} Min.)"
        elif r["formel"] == "pro_menge":
            beschreibung = f"Nr. {regel} · {r['de']['text']} ({menge_zahl:g} {r['einheit']})"
        else:
            beschreibung = f"Nr. {regel} · {r['de']['text']}"

        zeilen.append({
            "datum": datum, "name": name, "regel": regel,
            "strafen": strafen, "karte": r.get("karte", ""),
            "text": beschreibung,
            "sachleistung": r["formel"] == "sachleistung",
            "sach_text": r["de"]["strafe"] if r["formel"] == "sachleistung" else "",
        })
    return zeilen


verstoesse = lies_verstoesse()

if fehler:
    print("\n  ABBRUCH – index.html wurde NICHT geaendert.\n")
    print("  Bitte in data/verstoesse.csv korrigieren:\n")
    for f in fehler:
        print("   ✗", f)
    print()
    sys.exit(1)


# ----------------------------------------------------- Spieler zusammenbauen
ausgabe = []
for s in stamm["spieler"]:
    posten = []
    if s.get("uebertrag", 0) > 0:
        posten.append({
            "datum": stamm.get("uebertrag_label", "Übertrag"),
            "text": "Übertrag Strafen", "strafen": s["uebertrag"], "karte": "",
        })
    sach = []
    for v in sorted((v for v in verstoesse if v["name"] == s["name"]),
                    key=lambda v: datetime.strptime(v["datum"], "%d.%m.%Y")):
        if v["sachleistung"]:
            sach.append(f"{v['sach_text']} ({v['datum']})")
        posten.append({"datum": v["datum"], "text": v["text"],
                       "strafen": v["strafen"], "karte": v["karte"]})

    hinweis = s.get("hinweis", "")
    if sach:
        hinweis = (hinweis + " " if hinweis else "") + "Offen: " + "; ".join(sach) + "."

    eintrag = {"name": s["name"], "bezahlt": bool(s.get("bezahlt")),
               "hinweis": hinweis, "posten": posten}
    if s.get("typ"):
        eintrag["typ"] = s["typ"]
    ausgabe.append(eintrag)


# ----------------------------------------------------- Katalog fuer Anzeige
def katalog_fuer_anzeige(sprache):
    regeln = [[r["nr"], r[sprache]["text"], r[sprache]["strafe"], r.get("karte", "")]
              for r in katalog["regeln"] if not r.get("versteckt")]
    return {"satz": katalog["satz_text"][sprache], "regeln": regeln,
            "creed": katalog["creed"][sprache], "remarks": katalog["remarks"][sprache]}


# ----------------------------------------------------- rendern
stand_datum = datetime.now().strftime("%d.%m.%Y")
summe_offen = sum(sum(p["strafen"] for p in s["posten"])
                  for s in ausgabe if not s["bezahlt"])

daten = (
    f'const STAND = {json.dumps(stand_datum, ensure_ascii=False)};\n\n'
    f'const SPIELER = {json.dumps(ausgabe, ensure_ascii=False, indent=2)};\n\n'
    f'const KATALOG = {json.dumps({"de": katalog_fuer_anzeige("de"), "en": katalog_fuer_anzeige("en")}, ensure_ascii=False, indent=2)};'
)

vorlage = (HIER / "template.html").read_text(encoding="utf-8")
wappen = base64.b64encode((HIER / "assets" / "wappen.png").read_bytes()).decode()
seite = vorlage.replace("__DATEN__", daten).replace(
    "__WAPPEN__", "data:image/png;base64," + wappen)

if "__DATEN__" in seite or "__WAPPEN__" in seite:
    sys.exit("ABBRUCH: Platzhalter in template.html nicht gefunden.")


# ----------------------------------------------------- Pruefbericht
alt = {}
if STAND_DATEI.exists():
    alt = json.loads(STAND_DATEI.read_text(encoding="utf-8"))

alt_summe = alt.get("strafen_offen")
alt_anzahl = alt.get("spieler")

print()
print("  ┌─ PRÜFBERICHT " + "─" * 46)
print(f"  │ Spieler im Stamm   {len(ausgabe)}" +
      (f"   (vorher {alt_anzahl})" if alt_anzahl is not None and alt_anzahl != len(ausgabe) else ""))
print(f"  │ Verstöße im Log    {len(verstoesse)}")
print(f"  │ Offen gesamt       {euro(summe_offen, SATZ)}   ({summe_offen} Strafen)")

if alt_summe is not None:
    diff = summe_offen - alt_summe
    zeichen = "+" if diff > 0 else ""
    print(f"  │ Vorheriger Stand   {euro(alt_summe, SATZ)}")
    print(f"  │ Veränderung        {zeichen}{euro(diff, SATZ)}")
    if diff < 0:
        print("  │")
        print("  │ ⚠  Die Summe ist GESUNKEN. Das ist nur richtig, wenn jemand")
        print("  │    bezahlt hat oder du bewusst etwas gestrichen hast.")
if alt_anzahl is not None and len(ausgabe) < alt_anzahl:
    print("  │")
    print(f"  │ ⚠  Es sind {alt_anzahl - len(ausgabe)} Spieler WENIGER als beim letzten Mal.")
    print("  │    Bitte prüfen, ob das Absicht war.")

if warnungen:
    print("  │")
    for w in warnungen:
        print("  │ ⚠ ", w)

print("  │")
print("  │ Top 3 offen:")
for s in sorted((s for s in ausgabe if not s["bezahlt"]),
                key=lambda s: -sum(p["strafen"] for p in s["posten"]))[:3]:
    t = sum(p["strafen"] for p in s["posten"])
    print(f"  │   {s['name']:<14} {euro(t, SATZ):>10}")
print("  └" + "─" * 60)

(HIER / "index.html").write_text(seite, encoding="utf-8")
STAND_DATEI.write_text(json.dumps(
    {"datum": stand_datum, "strafen_offen": summe_offen, "spieler": len(ausgabe)},
    ensure_ascii=False, indent=2), encoding="utf-8")

print()
print(f"  index.html geschrieben ({round(len(seite.encode())/1024)} KB).")
print("  Jetzt im Browser öffnen und anschauen, BEVOR du pushst:")
print(f"     open {HIER / 'index.html'}")
print()
