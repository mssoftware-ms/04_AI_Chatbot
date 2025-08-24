# AGENTS.md

## Ziel
Dieses Repository stellt Werkzeuge und eine GUI für Git- und Coding-Workflows bereit.  
Alle beteiligten Agents sollen konsistente Qualität sicherstellen und sich an die
folgenden Regeln halten.

## Arbeitsablauf
1. **Analysephase**  
   - Lies zunächst die vorhandenen READMEs und Code-Dateien, um das Problem zu
     verstehen.  
   - Erstelle einen Plan oder Pseudocode für die Lösung und fasse die Schritte
     kurz zusammen.

2. **Critic-Überprüfung**  
   - Vor jeder Codeänderung prüft der *Critic* den Plan.  
   - Der Critic kontrolliert:
     - Verständlichkeit und Vollständigkeit des Lösungswegs.
     - Einhaltung des Codestils (PEP‑8) und bestehender Konventionen.
     - Mögliche Fehlerquellen oder Seiteneffekte.
   - Erst nach der Freigabe durch den Critic wird der Code implementiert.

3. **Implementierung**  
   - Schreibe sauberen, gut dokumentierten Code.  
   - Achte auf aussagekräftige Kommentare und Docstrings in deutscher Sprache.
   - Wenn möglich, füge Tests oder Beispielaufrufe hinzu.

4. **Iterative Verfeinerung**  
   - Nach jeder Änderung startet erneut die Critic-Prüfung.  
   - Iteriere, bis keine Beanstandungen mehr vorliegen.

5. **Zusammenfassung und Commit**  
   - Fasse alle Änderungen prägnant zusammen.  
   - Committe den Code mit einer klaren Commit-Nachricht.

6. **kipj Projektdatei umgang**
  - Lies dir die coding-ki.kipj vor den änderungen durch, darin findet sich eine Projektdoku, ignoriere "# Bekannte Probleme" und die "# To-Do Liste". Wichtig ist der Projekttree!
  - Wenn du am Projekttree Änderungen durchführst, wie z.b. neue def's, neue Dateien... oder gelöschte defs oder Dateien, dann aktualisiere den Tree in der Projektdatei!

## Stilregeln
- Python: PEP‑8 einhalten, Zeilenlänge 120 Zeichen.
- GUI-Elemente mit PySide6 nach Möglichkeit in separaten Modulen kapseln.
- Dokumentation nach Möglichkeit ebenfalls in Deutsch.
- Keine Umlaute verwenden, sonst kommt git damit nicht klar: "The head ref may contain hidden characters". Dies gilt auch fuer die Bennung der Pull Requests!!!
- Erstelle keine Bilddateien!
