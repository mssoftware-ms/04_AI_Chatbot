# 🌐 WSL Browser Installation - Commands zum Ausführen

## 🚀 Schritt 1: Browser installieren

Führe diese Commands in deinem WSL Terminal aus:

```bash
# Package list aktualisieren:
sudo apt update

# Chromium Browser installieren (empfohlen):
sudo apt install -y chromium-browser

# ODER falls Chromium nicht verfügbar, Firefox:
sudo apt install -y firefox
```

## 🔍 Schritt 2: Installation prüfen

```bash
# Prüfen ob Browser installiert ist:
which chromium-browser || which firefox

# Display-Support prüfen:
echo "Display: $DISPLAY"
echo "Wayland: $WAYLAND_DISPLAY"
```

## 🚀 Schritt 3: App mit Browser testen

```bash
# Virtual environment aktivieren:
source venv/bin/activate

# App mit Browser-Detection starten:
python start_with_browser.py
```

## 🎯 Erwartetes Ergebnis:

```
🐧 WSL detected: True
🌐 Browser found: chromium-browser
🖥️  Display available: True
🚀 Using native WSL browser: chromium-browser

✅ Backend started successfully
🌐 Backend API: http://localhost:8000
🖥️  UI App: http://localhost:8550

[Browser öffnet sich automatisch!] 🎉
```

## 💡 Troubleshooting

Falls Browser nicht öffnet:
```bash
# Manual test:
chromium-browser http://localhost:8550

# Oder mit Firefox:
firefox http://localhost:8550
```

Führe diese Commands aus und ich schaue dann, wie es läuft! 🚀