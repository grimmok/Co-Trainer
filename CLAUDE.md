# FM-Scout

Liest einen Football-Manager-27-Spielstand (`.fm`) und erzeugt `FM-Scout.html`. Projektstand, Format-Details und offene Punkte stehen in [HANDOFF.md](HANDOFF.md). Lies diese Datei zuerst.

## Feste Regeln

- **CA, PA und versteckte Attribute** (Cons, Dirt, ImpM, InjPr, Vers) erscheinen nie in der Oberfläche und nie im JSON von `FM-Scout.html`. Sie dürfen nur intern gerechnet werden.
- **Potenzial** wird nur als Text angezeigt, z. B. „Kann sich zu einem guten Zweitliga-Spieler entwickeln“, niemals als Zahl.
- **Spielstände nur lesen**, nie schreiben oder verändern.
- **Geld** steht im Spielstand in GBP. Angezeigt wird in EUR: Faktor **1,1641**.
- **Attributblock zuordnen nur über `Block-ID (u32 bei −43) = Personen-ID − 1`.** Der Block liegt *vor* dem Personenkopf. Niemals „nächster Personenkopf“ verwenden.
- **Neue Rollen-Fingerabdrücke** (`ROLE_FP` in `extract.py`) nur eintragen, wenn der Nutzer die Rolle bestätigt hat (Liste oder Screenshot). Nicht raten.
- **Neu dekodierte Werte** (Finanzen, Verträge, Rollen) mit Screenshots des Nutzers abgleichen, bevor sie als korrekt gelten.
- **Oberfläche und Texte auf Deutsch**, mit den deutschen FM27-Begriffen (Rollennamen siehe `lang_db`, IDs 1800–1884).
- **Was nicht im Spielstand steht** (Trainerprofil, Teamanweisungen), kommt aus `config.json`. Werte aus dem Spielstand haben Vorrang vor `config.json`.

## Arbeitsweise

- Ausgabe neu erzeugen: `python extract.py [Pfad.fm]`. Ohne Pfad wird der neueste Spielstand genommen. Zum Prüfen einzelner Spieler die Umgebungsvariable `FMS_DEBUG=Name1,Name2` setzen. Dann werden Rohwerte inkl. CA/PA in die Konsole geschrieben; diese Werte nur zur Kontrolle verwenden, nie in die Oberfläche übernehmen.
- Änderungen im Browser prüfen. Die Vorschau „fmscout“ (`.claude/launch.json`) liefert diesen Ordner auf Port 8765 aus. Beim Laden `?v=<irgendwas>` anhängen, sonst kommt eine gecachte Seite. Danach die Konsole auf Fehler prüfen.
- `app.html` ist die Vorlage, `FM-Scout.html` die erzeugte Ausgabe. Änderungen an der Oberfläche immer in `app.html` vornehmen, nie in `FM-Scout.html`.
- Erkundungsskripte und entpackte Spielstand-Teile gehören in das Scratchpad, nicht in diesen Ordner.
- Nutzerpfade:
  - Spielstände: `%USERPROFILE%\Documents\Sports Interactive\Football Manager 26\games\`
  - Spiel: `G:\SteamLibrary\steamapps\common\Football Manager 27`
