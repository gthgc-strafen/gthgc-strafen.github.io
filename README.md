# GTHGC Strafenkasse

Öffentliche Übersicht der Mannschaftsstrafen der 1. Herren.
Die Seite ist reine Anzeige — eingetragen wird ausschließlich von der
Kapitänsrunde.

## Seite neu bauen

```bash
python3 build.py
```

Das Skript liest alles aus `data/`, prüft die Eingaben und schreibt
`index.html`. Bei Fehlern bricht es ab und ändert nichts.

## Neue Verstöße eintragen

Eine Zeile pro Verstoß an `data/verstoesse.csv` anhängen:

```
15.08.2026;Jan;1;6;
```

Datum, Name, Regelnummer, Menge (nur wo nötig), Notiz (optional).

## Danach

1. `python3 build.py`
2. Prüfbericht lesen — stimmt die Veränderung?
3. `index.html` im Browser öffnen und anschauen
4. Erst dann committen und pushen
