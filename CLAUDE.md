# GTHGC Strafenkasse — Arbeitsanweisung

Dieses Repository erzeugt eine öffentlich erreichbare Seite mit Namen und
Geldbeträgen. Der Nutzer (MG) ist kein Programmierer. Erkläre in normaler
Sprache, was du tust, und nutze keine Fachbegriffe ohne kurze Erklärung.

## Sicherheitsregeln — gelten immer

1. **Niemals `git push` ohne ausdrückliche Zustimmung.** Zeige vorher den
   Prüfbericht von `build.py` und frage: "Soll ich das jetzt
   veröffentlichen?" Erst bei einem klaren Ja pushen.
2. **Niemals einen Spieler aus `data/spieler.json` entfernen, ohne vorher zu
   fragen.** Auch dann nicht, wenn der Nutzer es beiläufig erwähnt. Nachfragen,
   ob der offene Betrag verfällt oder umgebucht wird.
3. **Niemals `index.html` von Hand bearbeiten.** Sie wird von `build.py`
   erzeugt und bei jedem Lauf überschrieben. Änderungen am Aussehen gehören in
   `template.html`, Änderungen an Daten in `data/`.
4. **Niemals `git push --force`, `git reset --hard` oder `git rebase`.** Diese
   Befehle können veröffentlichte Stände zerstören. Wenn etwas rückgängig
   gemacht werden muss: `git revert`, und vorher erklären, was passiert.
5. **Nichts Privates ins Repository.** Keine Klarnamen zusätzlich zu den
   Spitznamen, keine Adressen, Telefonnummern, Kontodaten oder Screenshots von
   Zahlungseingängen. Das Repository ist öffentlich, und Git vergisst nichts —
   auch später gelöschte Inhalte bleiben in der Historie.
6. **Bei einem Fehler nicht raten.** Lieber sagen, was unklar ist, und fragen.

## Normaler Ablauf

Der Nutzer schickt neue Verstöße, meist so:

> 15.08. Jan Nr. 1, 6 Min · 17.08. Klaudi Nr. 11 · 17.08. Levi Nr. 15, 2 Teile

Dann:

1. Zeilen an `data/verstoesse.csv` anhängen, Format
   `datum;name;regel;menge;notiz`, Datum vierstellig als `TT.MM.JJJJ`.
   Ist die Jahreszahl nicht genannt, das laufende Jahr annehmen und es
   im Bericht erwähnen.
2. `python3 build.py` ausführen.
3. Den Prüfbericht vollständig zeigen und in einem Satz einordnen
   ("+80,50 €, plausibel für fünf Verstöße").
4. Nach Zustimmung: `git add -A`, `git commit` mit sprechender Nachricht
   (z. B. "Verstöße August 2026"), `git push`.
5. Den Link zur Seite nennen und darauf hinweisen, dass die Aktualisierung
   ein bis zwei Minuten dauert.

Bricht `build.py` mit Fehlern ab, wird `index.html` nicht verändert. Die
Fehlermeldungen nennen Zeilennummer und Grund — zusammen mit dem Nutzer
korrigieren, nicht eigenmächtig Namen oder Regeln "passend machen".

## Wer hat bezahlt

Zahlungen trägt der Nutzer über `data/spieler.json` ein: `"bezahlt": true`.
Der Betrag bleibt dann sichtbar, rutscht aber ausgegraut ans Listenende.
Beim Start einer neuen Saison werden die Überträge neu gesetzt und
`verstoesse.csv` geleert — das ist eine bewusste Entscheidung des Nutzers,
nicht automatisch machen.

## Dateien

| Datei | Zweck |
|---|---|
| `data/verstoesse.csv` | laufendes Log, hier kommen neue Verstöße rein |
| `data/spieler.json` | Spielerstamm, Überträge, Zahlungsstatus |
| `data/katalog.json` | die 21 Regeln, DE + EN, und ihre Beträge |
| `data/stand.json` | letzter Stand, nur für den Vergleich im Prüfbericht |
| `template.html` | Layout, ändert sich selten |
| `build.py` | erzeugt `index.html` aus den Daten |
| `index.html` | **erzeugt** — nicht von Hand ändern |
| `assets/wappen.png` | Vereinswappen, wird beim Bauen eingebettet |

## Fachliches

- Ein Strafenpunkt sind 0,50 €. Steht in `katalog.json` unter `satz_euro`.
- Regel 2 rechnet auf angefangene 5 Minuten auf, Regel 12 (Rote Karte) erzeugt
  keinen Geldbetrag, sondern einen Hinweis "Grillen für die Mannschaft".
- Regel `15b` ist der Sonderfall "Kleidungsstück komplett vergessen",
  30 Strafen pro Teil. Sie steht nicht in der Katalogansicht, ist aber buchbar.
- Regel 16 (10 Strafen pro Monat für unbezahlte Strafen) läuft **nicht**
  automatisch. Sie wird nur gebucht, wenn der Nutzer es ausdrücklich sagt.
- "Bench" ist ein Gemeinschaftskonto, kein Spieler.
