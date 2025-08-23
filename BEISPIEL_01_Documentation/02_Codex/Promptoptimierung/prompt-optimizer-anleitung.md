# Prompt Optimizer (API) – Anleitung & Beispiel (Python + UI)

**Stand:** 18.08.2025  
**Zielgruppe:** Entwickler:innen, die optimierte Prompts für OpenAI‑Modelle (z. B. `gpt-5`) **per API nutzbar** machen und lokal ein **UI** zum Optimieren & Testen verwenden möchten.

---

## Kurzfassung

- Es gibt **keinen separaten öffentlichen API‑Endpunkt** „Prompt Optimizer“.  
- Du kannst Prompts **in der OpenAI‑Konsole** optimieren und als **Prompt‑Objekt** speichern (→ Nutzung per `prompt_id`), **oder** du bildest das Optimieren **selbst** via **Responses‑API** (Meta‑Prompt) ab.  
- Dieses Repository zeigt eine **lokale PySide6‑UI** („Prompt Optimizer“) + **Testlauf** gegen ein frei wählbares **Zielmodell** (z. B. `gpt-5`, `gpt-4.1`, `gpt-4.1-mini`, `o3-mini`).

---

## Inhalte

1. [Architektur](#architektur)  
2. [Voraussetzungen](#voraussetzungen)  
3. [Installation](#installation)  
4. [Konfiguration](#konfiguration)  
5. [Start & Nutzung](#start--nutzung)  
6. [Beispielcode (PySide6-UI)](#beispielcode-pyside6-ui)  
7. [Optional: Gespeicherte Prompt-Objekte per `prompt_id`](#optional-gespeicherte-prompt-objekte-per-prompt_id)  
8. [Tipps zur Prompt-Qualität](#tipps-zur-prompt-qualität)  
9. [Troubleshooting](#troubleshooting)  
10. [Sicherheit & Kostenkontrolle](#sicherheit--kostenkontrolle)

---

## Architektur

- **Optimizer‑Phase (lokal):**  
  Ein *Meta‑Prompt* lässt ein OpenAI‑Modell (frei wählbar) deinen **Developer‑Prompt** + optionale **Few‑Shots** **prüfen & umschreiben**.  
  Rückgabe strikt als **JSON** (Schema validiert).

- **Test‑Phase (lokal):**  
  Der **optimierte Developer‑Prompt** wird gegen das **Zielmodell** getestet (freie Auswahl im UI).

- **Alternative (Konsole):**  
  In der **OpenAI‑Konsole** optimierte Prompts als **Prompt‑Objekt** speichern und später in API‑Calls über **`prompt_id`** referenzieren (Versionierung, Variablen).

---

## Voraussetzungen

- **Python** ≥ 3.10
- Pakete: `openai`, `PySide6`
- **OPENAI_API_KEY** als Umgebungsvariable

```bash
# Optional: venv
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

# Pakete
pip install --upgrade openai PySide6
```

---

## Konfiguration

Setze deinen API‑Key:
```bash
# Windows (PowerShell)
$Env:OPENAI_API_KEY="sk-..."
# Linux/macOS
export OPENAI_API_KEY="sk-..."
```

> **Hinweis:** Für produktive Setups den Key sicher in Secret‑Stores oder per `.env` verwalten – **niemals** im Code hardcoden.

---

## Start & Nutzung

1. Speichere die Datei **`prompt_optimizer_ui.py`** (siehe unten).  
2. Starte das UI:
   ```bash
   python prompt_optimizer_ui.py
   ```
3. **Optimierungs‑Modell** wählen (links oben).  
4. **Ziel‑Modell** wählen (rechts daneben).  
5. **Developer Prompt (roh)** einfügen, optional **Few‑Shots** (Notation `[user]`/`[assistant]`).  
6. **Optimieren** klicken → Ergebnispaneele füllen sich.  
7. **Mit Zielmodell testen** → Antwort erscheint im unteren Ausgabefeld.

---

## Beispielcode (PySide6-UI)

> Vollständiges, eigenständiges Beispiel. Beinhaltet:  
> - Strikte **JSON‑Response** mit Schema  
> - **Model‑Picker** für Optimizer & Zielmodell  
> - **Few‑Shot**‑Parser (`[user]` / `[assistant]`)  
> - **Fehlerbehandlung**

```python
# prompt_optimizer_ui.py
import os, json, sys, traceback
from typing import Dict, Any
from openai import OpenAI
from PySide6 import QtWidgets, QtCore

OPTIMIZER_SYSTEM = (
    "You are a rigorous Prompt Optimizer for OpenAI models. "
    "Given a developer prompt and optional few-shot examples, you must:\n"
    "1) Detect and fix contradictions, vague rules, and missing output-format specs.\n"
    "2) Align the prompt with the target OpenAI model's best practices.\n"
    "3) Preserve original intent; make minimal, explicit edits.\n"
    "4) If few-shot examples exist, ensure they comply with the developer rules.\n"
    "Return STRICT JSON only, matching the provided schema."
)

JSON_SCHEMA: Dict[str, Any] = {
    "name": "PromptOptimizationResult",
    "schema": {
        "type": "object",
        "properties": {
            "optimized_developer_message": {"type": "string"},
            "optimized_messages": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "role": {"type": "string", "enum": ["user", "assistant"]},
                        "content": {"type": "string"}
                    },
                    "required": ["role", "content"],
                    "additionalProperties": False
                }
            },
            "notes": {"type": "string"}
        },
        "required": ["optimized_developer_message", "optimized_messages"],
        "additionalProperties": False,
    },
    "strict": True,
}

DEFAULT_MODELS = [
    "gpt-5",
    "gpt-4.1",
    "gpt-4.1-mini",
    "o3-mini"
]

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenAI Prompt Optimizer (lokal per API)")
        self.resize(1100, 800)

        self.cboOptimizeModel = QtWidgets.QComboBox()
        self.cboOptimizeModel.addItems(DEFAULT_MODELS)
        self.cboOptimizeModel.setEditable(True)

        self.cboTargetModel = QtWidgets.QComboBox()
        self.cboTargetModel.addItems(DEFAULT_MODELS)
        self.cboTargetModel.setEditable(True)

        self.txtDevPrompt = QtWidgets.QTextEdit()
        self.txtDevPrompt.setPlaceholderText("Developer Prompt (roh) …")

        self.txtFewShots = QtWidgets.QTextEdit()
        self.txtFewShots.setPlaceholderText("Few-shot Beispiele (optional):\n"
                                            "FORMAT:\n[user] …\n[assistant] …\n[user] …\n…")

        self.btnOptimize = QtWidgets.QPushButton("Optimieren")
        self.btnOptimize.clicked.connect(self.optimize_prompt)

        self.txtOptimized = QtWidgets.QTextEdit()
        self.txtOptimized.setPlaceholderText("Optimierter Developer Prompt (Ergebnis)")
        self.txtOptimized.setReadOnly(False)

        self.txtOptimizedShots = QtWidgets.QTextEdit()
        self.txtOptimizedShots.setPlaceholderText("Optimierte Few-shots (Ergebnis)")
        self.txtOptimizedShots.setReadOnly(False)

        self.txtTestUser = QtWidgets.QTextEdit()
        self.txtTestUser.setPlaceholderText("Test-User-Eingabe (optional) …")

        self.btnTest = QtWidgets.QPushButton("Mit Zielmodell testen")
        self.btnTest.clicked.connect(self.test_target_model)

        self.txtModelAnswer = QtWidgets.QTextEdit()
        self.txtModelAnswer.setPlaceholderText("Antwort des Zielmodells")
        self.txtModelAnswer.setReadOnly(True)

        # Layouts
        topBar = QtWidgets.QWidget()
        topLay = QtWidgets.QHBoxLayout(topBar)
        topLay.addWidget(QtWidgets.QLabel("Optimierungs-Modell:"))
        topLay.addWidget(self.cboOptimizeModel, 1)
        topLay.addSpacing(16)
        topLay.addWidget(QtWidgets.QLabel("Ziel-Modell:"))
        topLay.addWidget(self.cboTargetModel, 1)
        topLay.addStretch()
        topLay.addWidget(self.btnOptimize)

        splitterTop = QtWidgets.QSplitter()
        splitterTop.setOrientation(QtCore.Qt.Orientation.Horizontal)
        left = QtWidgets.QWidget(); leftLay = QtWidgets.QVBoxLayout(left)
        leftLay.addWidget(QtWidgets.QLabel("Developer Prompt (roh)"))
        leftLay.addWidget(self.txtDevPrompt)
        right = QtWidgets.QWidget(); rightLay = QtWidgets.QVBoxLayout(right)
        rightLay.addWidget(QtWidgets.QLabel("Few-shots (optional)"))
        rightLay.addWidget(self.txtFewShots)
        splitterTop.addWidget(left)
        splitterTop.addWidget(right)
        splitterTop.setSizes([600, 500])

        splitterMid = QtWidgets.QSplitter()
        splitterMid.setOrientation(QtCore.Qt.Orientation.Horizontal)
        midLeft = QtWidgets.QWidget(); midLeftLay = QtWidgets.QVBoxLayout(midLeft)
        midLeftLay.addWidget(QtWidgets.QLabel("Optimierter Developer Prompt"))
        midLeftLay.addWidget(self.txtOptimized)
        midRight = QtWidgets.QWidget(); midRightLay = QtWidgets.QVBoxLayout(midRight)
        midRightLay.addWidget(QtWidgets.QLabel("Optimierte Few-shots"))
        midRightLay.addWidget(self.txtOptimizedShots)
        splitterMid.addWidget(midLeft)
        splitterMid.addWidget(midRight)
        splitterMid.setSizes([600, 500])

        bottomBar = QtWidgets.QWidget()
        bottomLay = QtWidgets.QHBoxLayout(bottomBar)
        bottomLay.addWidget(QtWidgets.QLabel("Test-User:"))
        bottomLay.addWidget(self.txtTestUser, 1)
        bottomLay.addWidget(self.btnTest)

        central = QtWidgets.QWidget()
        root = QtWidgets.QVBoxLayout(central)
        root.addWidget(topBar)
        root.addWidget(splitterTop, 2)
        root.addWidget(splitterMid, 2)
        root.addWidget(bottomBar)
        root.addWidget(self.txtModelAnswer, 1)
        self.setCentralWidget(central)

        if not os.getenv("OPENAI_API_KEY"):
            QtWidgets.QMessageBox.warning(self, "Hinweis",
                                          "OPENAI_API_KEY ist nicht gesetzt.")
        self.client = OpenAI()

    def _fewshots_to_list(self, text: str):
        """
        Konvertiert eine einfache [user]/[assistant] Notation in ein List[dict].
        """
        msgs = []
        cur_role, buf = None, []
        for line in text.splitlines():
            lt = line.strip()
            if lt.lower().startswith("[user]"):
                if cur_role and buf:
                    msgs.append({"role": cur_role, "content": "\n".join(buf).strip()})
                cur_role, buf = "user", [lt[6:].lstrip()]
            elif lt.lower().startswith("[assistant]"):
                if cur_role and buf:
                    msgs.append({"role": cur_role, "content": "\n".join(buf).strip() })
                cur_role, buf = "assistant", [lt[11:].lstrip()]
            else:
                buf.append(line)
        if cur_role and buf:
            msgs.append({"role": cur_role, "content": "\n".join(buf).strip()})
        return msgs

    def optimize_prompt(self):
        try:
            dev_raw = self.txtDevPrompt.toPlainText().strip()
            if not dev_raw:
                QtWidgets.QMessageBox.information(self, "Eingabe fehlt",
                                                  "Bitte einen Developer Prompt eingeben.")
                return

            few = self._fewshots_to_list(self.txtFewShots.toPlainText())
            target_model = self.cboTargetModel.currentText().strip()
            optimize_model = self.cboOptimizeModel.currentText().strip()

            payload = {
                "target_model": target_model,
                "developer_message": dev_raw,
                "messages": few
            }

            resp = self.client.responses.create(
                model=optimize_model,
                input=[
                    {"role": "developer", "content": [{"type": "input_text", "text": OPTIMIZER_SYSTEM}]},
                    {"role": "user", "content": [{"type": "input_text", "text": json.dumps(payload)}]},
                ],
                response_format={"type": "json_schema", "json_schema": JSON_SCHEMA},
                temperature=0.2,
            )

            # Primäre Abfrage (neuere SDKs)
            result_text = getattr(resp, "output_text", None)
            if not result_text:
                # Fallback für alternative SDK-Formate
                try:
                    result_text = resp.output[0].content[0].text
                except Exception:
                    result_text = str(resp)

            data = json.loads(result_text)
            self.txtOptimized.setPlainText(data.get("optimized_developer_message",""))
            shots = []
            for m in data.get("optimized_messages", []):
                shots.append(f"[{m['role']}] {m['content']}")
            self.txtOptimizedShots.setPlainText("\n".join(shots))

        except Exception as e:
            traceback.print_exc()
            QtWidgets.QMessageBox.critical(self, "Fehler", f"{e}")

    def test_target_model(self):
        try:
            dev_opt = self.txtOptimized.toPlainText().strip()
            user_test = self.txtTestUser.toPlainText().strip()
            target_model = self.cboTargetModel.currentText().strip()

            if not dev_opt:
                QtWidgets.QMessageBox.information(self, "Hinweis",
                                                  "Kein optimierter Developer Prompt vorhanden.")
                return
            if not user_test:
                user_test = "Kurzer Funktionstest: Beschreibe in 3 Bullet-Points die Vorteile dieses Optimizers."

            resp = self.client.responses.create(
                model=target_model,
                input=[
                    {"role": "developer", "content": [{"type": "input_text", "text": dev_opt}]},
                    {"role": "user", "content": [{"type": "input_text", "text": user_test}]},
                ],
                text={"format": {"type": "text"}, "verbosity": "medium"},
                temperature=0.3,
            )

            out_text = getattr(resp, "output_text", None)
            if not out_text:
                try:
                    out_text = resp.output[0].content[0].text
                except Exception:
                    out_text = str(resp)
            self.txtModelAnswer.setPlainText(out_text)

        except Exception as e:
            traceback.print_exc()
            QtWidgets.QMessageBox.critical(self, "Fehler", f"{e}")

def main():
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

---

## Optional: Gespeicherte Prompt-Objekte per `prompt_id`

Wenn du im **Optimize‑Bereich** der Konsole einen Prompt als Objekt speicherst, kannst du ihn per **`prompt_id`** in Calls wiederverwenden (inkl. Versionierung/Variablen).

> **Skizze (Beispiel):**
```python
from openai import OpenAI
client = OpenAI()

resp = client.responses.create(
    model="gpt-5",  # Zielmodell
    input={
        "prompt": {
            "prompt_id": "pmpt_123...",     # ID aus der Konsole
            "version": 3,                   # optional; sonst “latest”
            "variables": {"city": "Berlin"} # falls Platzhalter im Prompt
        }
    },
    text={"format": {"type": "text"}}
)
print(resp.output_text)
```

> **Wichtig:** Die konkrete `prompt_id` und das Variablen‑Schema ergeben sich aus dem in der Konsole gespeicherten Prompt‑Objekt.

---

## Tipps zur Prompt-Qualität

- **Ziele explizit** machen (Rollen, Grenzen, Output‑Format, Beispiele).  
- **Ambiguitäten eliminieren** (Begriffe definieren, Annahmen festschreiben).  
- **Strukturierte Ausgaben** (JSON‑Schema oder valide Markdown‑Sektionen).  
- **Deterministik erhöhen** (geeignete Temperatur/Seed, ggf. Tools/Tests).  
- **Evaluieren** (Gold‑Sätze, Regression‑Checks, automatische Evals).

---

## Troubleshooting

- **`OPENAI_API_KEY` fehlt:** In der UI erscheint ein Hinweis – Umgebungsvariable setzen und Programm neu starten.  
- **SDK‑Unterschiede:** Das Beispiel liest primär `resp.output_text`. Falls nicht vorhanden, greift ein **Fallback** auf strukturierte Felder.  
- **Modellnamen:** Trage deine tatsächlichen Modell‑Bezeichner in die Dropdowns ein (Feld ist editierbar).  
- **JSON‑Fehler:** Wenn das Modell kein valides JSON liefert, reduziere `temperature` und halte den **System‑Prompt** streng.

---

## Sicherheit & Kostenkontrolle

- **Secrets schützen** (keine Keys im Code; Least‑Privilege).  
- **Kosten limitieren** (Kontingente, Monitoring, kleinere Modelle zum Optimieren, Zielmodell nur für finalen Test).  
- **PII/Unternehmensdaten** nur nach Freigabe verarbeiten; ggf. **Redaction** vor dem Optimieren anwenden.

---

© 2025 – Referenzimplementierung für einen lokalen Prompt‑Optimizer mit OpenAI Responses‑API.
