# Ankündigung Co-Trainer 1.0

Text zum Posten (z. B. Discord), dazu das Vorschaubild `vorschau-1.0.png`. Der Download-Link funktioniert erst, wenn das Repository öffentlich ist.

---

**Co-Trainer 1.0.0 ist da! ⚽**

Co-Trainer liest deinen **Football-Manager-27-Spielstand** und hilft dir bei Kader, Transfers, Taktik und Training. Herunterladen, doppelklicken, Spielstand wählen, fertig. Python oder andere Installationen brauchst du nicht.

**Was schon funktioniert:**
- **Kaderanalyse:** deine beste Startelf für deine Taktik, Stärken und Lücken je Position, Finanzen auf einen Blick
- **Transfervorschläge:** passende Spieler für deine schwächsten Positionen, mit geschätzter Wechselchance und Marktwert, gefiltert nach deinem Scoutinggebiet
- **Taktik:** zeigt, wo deine Taktik schwächelt, wer dafür verantwortlich ist und was hilft (andere Rolle, Training oder Transfer)
- **Training:** eine Trainingswoche mit den echten FM27-Einheiten, abgestimmt auf deinen Spielstil
- **Kaderliste:** alle Spieler mit Positionen, Vertrag und Gehalt
- **Spoilerschutz:** Standardmäßig zeigt Co-Trainer über fremde Spieler nur, was du im Spiel auch ohne Scouting siehst. Mehr Infos schaltest du bewusst dazu.
- Spielstände werden **nur gelesen**, nie verändert. Keine Internetverbindung, keine Datensammlung.

**Download:** https://github.com/grimmok/Co-Trainer/releases/latest
Beim ersten Start meldet Windows „Der Computer wurde durch Windows geschützt“, weil das Programm nicht signiert ist. Dann auf **Weitere Informationen** und **Trotzdem ausführen** klicken.

**Was noch geplant ist:**
- weitere Rollen erkennen (bisher erscheinen unbekannte Rollen mit „?“)
- Teamanweisungen aus dem Spielstand lesen
- schnelleres Einlesen (zurzeit rund zwei Minuten)
- bessere Vorschläge bei „Kein Scouting“ und für gerade gewechselte Spieler

Läuft vorerst nur unter Windows und auf Deutsch. Feedback ist willkommen!

---

## Vorschaubild neu erzeugen

`vorschau-1.0.html` (2000×1125) zeigt `kaderanalyse-hell.png`, ein Bildschirmfoto der Kaderanalyse im hellen Schema (Entwicklermodus mit `dev-data.json`, Fenster 1280×1100, Skalierung 2). Rendern zum Beispiel mit Edge:

```powershell
& "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --headless=new --hide-scrollbars --window-size=2000,1125 --screenshot="$PWD\vorschau-1.0.png" "$PWD\vorschau-1.0.html"
```
