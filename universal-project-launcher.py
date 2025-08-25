#!/usr/bin/env python3
"""
Universal Windows Project Launcher
Automatisiert die Einrichtung und den Start von Python-Projekten unter Windows
"""

import os
import sys
import subprocess
import json
import shutil
import hashlib
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import filedialog
import time
import ctypes
import colorama
from colorama import Fore, Back, Style

# Initialisiere colorama für Windows
colorama.init()

# Setze UTF-8 Encoding für Windows Console
if sys.platform == "win32":
    # Aktiviere ANSI Escape Sequences in Windows Terminal
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    # Setze Console auf UTF-8
    os.system("chcp 65001 > nul")


class ProjectLauncher:
    def __init__(self):
        self.project_root = Path.cwd()
        self.venv_path = self.project_root / "venv"
        self.config_dir = self.project_root / "02_Configuration" / "Log"
        self.requirements_log = self.config_dir / "requirements.json"
        self.requirements_file = self.project_root / "requirements.txt"
        self.python_version = "3.12"
        self.main_file = None
        self.fast_mode = False  # Schnellstart wenn alles ok ist
        
    def log(self, message, level="info"):
        """Gibt farbige Log-Nachrichten aus"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if level == "success":
            print(f"{Fore.GREEN}✅ [{timestamp}] {message}{Style.RESET_ALL}")
        elif level == "error":
            print(f"{Fore.RED}❌ [{timestamp}] {message}{Style.RESET_ALL}")
        elif level == "warning":
            print(f"{Fore.YELLOW}⚠️  [{timestamp}] {message}{Style.RESET_ALL}")
        elif level == "info":
            print(f"{Fore.CYAN}ℹ️  [{timestamp}] {message}{Style.RESET_ALL}")
        elif level == "process":
            print(f"{Fore.MAGENTA}🔄 [{timestamp}] {message}{Style.RESET_ALL}")
        else:
            print(f"   [{timestamp}] {message}")
    
    def print_header(self):
        """Zeigt einen schönen Header an"""
        print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}🚀 Universal Windows Project Launcher{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Projekt: {self.project_root.name}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Pfad: {self.project_root}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")
        
    def find_main_file(self):
        """Sucht die Hauptdatei der Anwendung"""
        self.log("Suche nach Hauptdatei...", "process")
        
        # Cache für Hauptdatei
        cache_file = self.config_dir / "main_file_cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached = json.load(f)
                    cached_path = Path(cached["main_file"])
                    if cached_path.exists():
                        self.main_file = cached_path
                        self.log(f"Hauptdatei aus Cache: {self.main_file.name}", "success")
                        return True
            except:
                pass
        
        # Typische Namen für Hauptdateien
        common_names = [
            "main.py", "app.py", "run.py", "start.py", 
            "__main__.py", "application.py", "server.py",
            "manage.py", "launch.py", "index.py", "bot.py"
        ]
        
        # Suche in Projektwurzel
        for name in common_names:
            if name == "launch.py":  # Überspringe diese Datei selbst
                continue
            file_path = self.project_root / name
            if file_path.exists():
                self.main_file = file_path
                self.log(f"Hauptdatei gefunden: {name}", "success")
                self.save_main_file_cache()
                return True
        
        # Suche in src/ oder app/ Ordnern
        for folder in ["src", "app", "source"]:
            folder_path = self.project_root / folder
            if folder_path.exists():
                for name in common_names:
                    file_path = folder_path / name
                    if file_path.exists():
                        self.main_file = file_path
                        self.log(f"Hauptdatei gefunden: {folder}/{name}", "success")
                        self.save_main_file_cache()
                        return True
        
        # Suche nach Dateien mit if __name__ == "__main__":
        self.log("Suche nach Python-Dateien mit main-Block...", "process")
        for py_file in self.project_root.rglob("*.py"):
            if py_file.parent.name == "venv" or py_file.name == "launch.py":
                continue
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'if __name__ == "__main__":' in content or 'if __name__ == \'__main__\':' in content:
                        self.main_file = py_file
                        self.log(f"Hauptdatei mit main-Block: {py_file.relative_to(self.project_root)}", "success")
                        self.save_main_file_cache()
                        return True
            except Exception:
                continue
        
        # Dateiauswahldialog wenn automatische Suche fehlschlägt
        self.log("Keine Hauptdatei automatisch gefunden", "warning")
        return self.select_main_file()
    
    def save_main_file_cache(self):
        """Speichert die gefundene Hauptdatei im Cache"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        cache_file = self.config_dir / "main_file_cache.json"
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump({"main_file": str(self.main_file)}, f)
        except:
            pass
    
    def select_main_file(self):
        """Öffnet einen Dateiauswahldialog"""
        self.log("Öffne Dateiauswahldialog...", "info")
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        file_path = filedialog.askopenfilename(
            title="Wählen Sie die Hauptdatei der Anwendung",
            initialdir=self.project_root,
            filetypes=[("Python Dateien", "*.py"), ("Alle Dateien", "*.*")]
        )
        
        root.destroy()
        
        if file_path:
            self.main_file = Path(file_path)
            self.log(f"Datei ausgewählt: {self.main_file.relative_to(self.project_root)}", "success")
            self.save_main_file_cache()
            return True
        else:
            self.log("Keine Datei ausgewählt", "error")
            return False
    
    def check_python_version(self):
        """Überprüft die Python-Version im venv"""
        if not self.venv_path.exists():
            return False
        
        python_exe = self.venv_path / "Scripts" / "python.exe"
        
        if not python_exe.exists():
            return False
        
        try:
            result = subprocess.run(
                [str(python_exe), "--version"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            version_str = result.stdout.strip()
            version_parts = version_str.split()[1].split('.')
            major_minor = f"{version_parts[0]}.{version_parts[1]}"
            
            if major_minor == self.python_version:
                self.log(f"venv Python-Version OK: {version_str}", "success")
                return True
            else:
                self.log(f"venv Python-Version inkompatibel: {version_str}", "warning")
                return False
        except Exception as e:
            self.log(f"Fehler beim Prüfen der Python-Version: {e}", "error")
            return False
    
    def remove_venv(self):
        """Entfernt das bestehende venv"""
        if self.venv_path.exists():
            self.log("Entferne bestehendes venv...", "process")
            try:
                # Mehrere Versuche falls Dateien gesperrt sind
                for attempt in range(3):
                    try:
                        shutil.rmtree(self.venv_path)
                        self.log("venv erfolgreich entfernt", "success")
                        return
                    except Exception:
                        if attempt < 2:
                            time.sleep(1)
                        else:
                            raise
            except Exception as e:
                self.log(f"Fehler beim Entfernen des venv: {e}", "error")
                sys.exit(1)
    
    def create_venv(self):
        """Erstellt ein neues venv mit Python 3.12"""
        self.log(f"Erstelle neues venv mit Python {self.python_version}...", "process")
        
        # Versuche Python 3.12 zu finden
        python_exe = None
        possible_commands = [
            f"python{self.python_version}",
            "python3.12",
            "python",
            "py",
            r"C:\Python312\python.exe",
            r"C:\Program Files\Python312\python.exe",
            r"C:\Program Files (x86)\Python312\python.exe"
        ]
        
        for cmd in possible_commands:
            try:
                # Bei 'py' verwende spezielle Syntax für Version
                if cmd == "py":
                    test_cmd = ["py", f"-{self.python_version}", "--version"]
                else:
                    test_cmd = [cmd, "--version"]
                    
                result = subprocess.run(
                    test_cmd,
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                if self.python_version in result.stdout:
                    python_exe = cmd
                    self.log(f"Python gefunden: {cmd}", "success")
                    break
            except:
                continue
        
        if not python_exe:
            self.log(f"Python {self.python_version} nicht gefunden!", "error")
            self.log("Bitte installieren Sie Python 3.12 von python.org", "info")
            input("\nDrücken Sie Enter zum Beenden...")
            sys.exit(1)
        
        try:
            # Erstelle venv
            if python_exe == "py":
                create_cmd = ["py", f"-{self.python_version}", "-m", "venv", str(self.venv_path)]
            else:
                create_cmd = [python_exe, "-m", "venv", str(self.venv_path)]
            
            self.log("Führe aus: " + " ".join(create_cmd), "info")
            
            process = subprocess.Popen(
                create_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # Zeige Fortschritt
            while process.poll() is None:
                print(".", end="", flush=True)
                time.sleep(0.5)
            
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, create_cmd, stderr)
            
            print()  # Neue Zeile nach den Punkten
            self.log("venv erfolgreich erstellt", "success")
        except subprocess.CalledProcessError as e:
            self.log(f"Fehler beim Erstellen des venv: {e}", "error")
            if e.stderr:
                self.log(f"Fehlerdetails: {e.stderr}", "error")
            sys.exit(1)
    
    def get_venv_python(self):
        """Gibt den Pfad zum Python-Interpreter im venv zurück"""
        return str(self.venv_path / "Scripts" / "python.exe")
    
    def get_venv_pip(self):
        """Gibt den Pfad zu pip im venv zurück"""
        return str(self.venv_path / "Scripts" / "pip.exe")
    
    def run_pip_command(self, args, description):
        """Führt pip-Befehle mit sichtbarem Output aus"""
        self.log(description, "process")
        try:
            process = subprocess.Popen(
                [self.get_venv_python(), "-m", "pip"] + args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # Zeige Live-Output
            for line in process.stdout:
                line = line.strip()
                if line:
                    print(f"  {Fore.WHITE}│ {line}{Style.RESET_ALL}")
            
            process.wait()
            
            if process.returncode == 0:
                self.log(f"{description} - Erfolgreich", "success")
                return True
            else:
                self.log(f"{description} - Fehlgeschlagen", "error")
                return False
                
        except Exception as e:
            self.log(f"Fehler: {e}", "error")
            return False
    
    def upgrade_pip(self):
        """Aktualisiert pip auf die neueste Version"""
        return self.run_pip_command(
            ["install", "--upgrade", "pip"],
            "Aktualisiere pip"
        )
    
    def install_pipreqs(self):
        """Installiert pipreqs"""
        # Prüfe ob pipreqs bereits installiert ist
        try:
            result = subprocess.run(
                [self.get_venv_python(), "-m", "pip", "show", "pipreqs"],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.returncode == 0:
                self.log("pipreqs bereits installiert", "success")
                return True
        except:
            pass
        
        return self.run_pip_command(
            ["install", "pipreqs"],
            "Installiere pipreqs"
        )
    
    def calculate_requirements_hash(self):
        """Berechnet einen Hash der requirements.txt"""
        if not self.requirements_file.exists():
            return None
        
        try:
            with open(self.requirements_file, 'rb') as f:
                content = f.read()
                return hashlib.sha256(content).hexdigest()
        except Exception:
            return None
    
    def load_requirements_log(self):
        """Lädt das Log der letzten requirements"""
        if not self.requirements_log.exists():
            return None
        
        try:
            with open(self.requirements_log, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    
    def save_requirements_log(self):
        """Speichert das aktuelle requirements Log"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "size": self.requirements_file.stat().st_size if self.requirements_file.exists() else 0,
            "hash": self.calculate_requirements_hash(),
            "modified": self.requirements_file.stat().st_mtime if self.requirements_file.exists() else 0
        }
        
        try:
            with open(self.requirements_log, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2)
            self.log("Requirements-Log gespeichert", "success")
        except Exception as e:
            self.log(f"Konnte Requirements-Log nicht speichern: {e}", "warning")
    
    def requirements_changed(self):
        """Überprüft ob sich die requirements geändert haben"""
        if not self.requirements_file.exists():
            self.log("requirements.txt existiert nicht", "warning")
            return True
        
        current_hash = self.calculate_requirements_hash()
        last_log = self.load_requirements_log()
        
        if not last_log:
            self.log("Kein vorheriges Requirements-Log gefunden", "info")
            return True
        
        if current_hash != last_log.get("hash"):
            self.log("Requirements haben sich geändert", "warning")
            return True
        
        self.log("Requirements sind unverändert", "success")
        return False
    
    def generate_requirements(self):
        """Generiert requirements.txt mit pipreqs"""
        self.log("Generiere requirements.txt mit pipreqs...", "process")
        try:
            pipreqs_cmd = str(self.venv_path / "Scripts" / "pipreqs.exe")
            
            process = subprocess.Popen(
                [pipreqs_cmd, str(self.project_root), "--force", "--encoding", "utf-8"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            output, _ = process.communicate()
            
            if process.returncode == 0:
                self.log("requirements.txt erfolgreich generiert", "success")
                # Zeige gefundene Pakete
                if self.requirements_file.exists():
                    with open(self.requirements_file, 'r', encoding='utf-8') as f:
                        reqs = f.read().strip()
                        if reqs:
                            self.log("Gefundene Abhängigkeiten:", "info")
                            for line in reqs.split('\n'):
                                if line.strip():
                                    print(f"  {Fore.WHITE}• {line}{Style.RESET_ALL}")
            else:
                self.log("pipreqs Warnung (nicht kritisch)", "warning")
                # Erstelle leere requirements.txt wenn pipreqs fehlschlägt
                if not self.requirements_file.exists():
                    self.requirements_file.touch()
                    
        except Exception as e:
            self.log(f"Fehler beim Generieren: {e}", "warning")
            self.requirements_file.touch()
    
    def install_requirements(self):
        """Installiert alle Pakete aus requirements.txt"""
        if not self.requirements_file.exists():
            self.log("Keine requirements.txt gefunden", "warning")
            return
        
        # Prüfe ob requirements.txt leer ist
        with open(self.requirements_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            
        if not content:
            self.log("requirements.txt ist leer", "info")
            return
        
        # Zeige zu installierende Pakete
        self.log("Zu installierende Pakete:", "info")
        for line in content.split('\n'):
            if line.strip() and not line.startswith('#'):
                print(f"  {Fore.WHITE}• {line}{Style.RESET_ALL}")
        
        return self.run_pip_command(
            ["install", "-r", str(self.requirements_file)],
            "Installiere Pakete aus requirements.txt"
        )
    
    def update_gitignore(self):
        """Fügt venv und Log-Dateien zu .gitignore hinzu"""
        gitignore_path = self.project_root / ".gitignore"
        entries_to_add = [
            "venv/",
            "02_Configuration/Log/",
            "*.pyc",
            "__pycache__/",
            ".env",
            "*.log",
            ".vscode/",
            ".idea/",
            "*.egg-info/",
            "dist/",
            "build/"
        ]
        
        existing_entries = set()
        if gitignore_path.exists():
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                existing_entries = set(line.strip() for line in f if line.strip())
        
        new_entries = []
        for entry in entries_to_add:
            if entry not in existing_entries:
                new_entries.append(entry)
        
        if new_entries:
            with open(gitignore_path, 'a', encoding='utf-8') as f:
                if existing_entries:
                    f.write("\n")
                f.write("# Automatisch hinzugefügt von ProjectLauncher\n")
                for entry in new_entries:
                    f.write(f"{entry}\n")
            self.log(f".gitignore aktualisiert ({len(new_entries)} neue Einträge)", "success")
    
    def check_fast_start(self):
        """Prüft ob ein Schnellstart möglich ist"""
        # Prüfe ob venv existiert
        if not self.venv_path.exists():
            return False
        
        # Prüfe Python-Version
        if not self.check_python_version():
            return False
        
        # Prüfe ob requirements unverändert sind
        if self.requirements_changed():
            return False
        
        # Prüfe ob Hauptdatei im Cache ist
        cache_file = self.config_dir / "main_file_cache.json"
        if not cache_file.exists():
            return False
        
        self.log("✨ Schnellstart möglich - Überspringe Setup", "success")
        return True
    
    def start_application(self):
        """Startet die Hauptanwendung in einem neuen CMD-Fenster"""
        if not self.main_file:
            self.log("Keine Hauptdatei definiert", "error")
            sys.exit(1)
        
        print(f"\n{Fore.GREEN}{'='*70}{Style.RESET_ALL}")
        self.log(f"Starte Anwendung: {self.main_file.name}", "success")
        print(f"{Fore.GREEN}{'='*70}{Style.RESET_ALL}\n")
        
        # Erstelle Batch-Datei für Aktivierung und Start
        batch_content = f'''@echo off
chcp 65001 > nul
echo ========================================
echo Aktiviere Virtual Environment...
echo ========================================
call "{self.venv_path}\\Scripts\\activate.bat"
echo.
echo ========================================
echo Starte {self.main_file.name}...
echo ========================================
echo.
cd /d "{self.project_root}"
python "{self.main_file}"
echo.
echo ========================================
echo Anwendung beendet.
echo ========================================
pause
'''
        
        batch_file = self.project_root / "temp_launcher.bat"
        try:
            with open(batch_file, 'w', encoding='utf-8') as f:
                f.write(batch_content)
            
            # Starte in neuem CMD-Fenster
            subprocess.Popen(
                f'start "Python App - {self.main_file.name}" cmd /k "{batch_file}"',
                shell=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            
            self.log("Anwendung wurde in neuem Fenster gestartet", "success")
            time.sleep(2)  # Kurz warten damit Batch-Datei gelesen werden kann
            
            # Lösche temporäre Batch-Datei
            try:
                batch_file.unlink()
            except:
                pass
                
        except Exception as e:
            self.log(f"Fehler beim Starten: {e}", "error")
            sys.exit(1)
    
    def run(self):
        """Hauptablauf des Launchers"""
        try:
            self.print_header()
            
            # Prüfe ob Schnellstart möglich ist
            if self.check_fast_start():
                self.fast_mode = True
                # Lade Hauptdatei aus Cache
                cache_file = self.config_dir / "main_file_cache.json"
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached = json.load(f)
                    self.main_file = Path(cached["main_file"])
                
                self.log("🚀 SCHNELLSTART-MODUS", "success")
                time.sleep(1)
            else:
                self.log("Vollständige Initialisierung erforderlich", "info")
                
                # 1. Hauptdatei finden
                if not self.find_main_file():
                    input("\nDrücken Sie Enter zum Beenden...")
                    sys.exit(1)
                
                # 2. venv überprüfen und ggf. neu erstellen
                if self.venv_path.exists():
                    if not self.check_python_version():
                        self.remove_venv()
                        self.create_venv()
                else:
                    self.log("Kein venv gefunden", "info")
                    self.create_venv()
                
                # 3. pip aktualisieren
                self.upgrade_pip()
                
                # 4. pipreqs installieren
                self.install_pipreqs()
                
                # 5. requirements.txt generieren wenn nötig
                if self.requirements_changed() or not self.requirements_file.exists():
                    self.generate_requirements()
                
                # 6. requirements installieren wenn nötig
                if self.requirements_changed():
                    self.install_requirements()
                    self.save_requirements_log()
                
                # 7. .gitignore aktualisieren
                self.update_gitignore()
                
                print(f"\n{Fore.GREEN}✅ Setup abgeschlossen!{Style.RESET_ALL}\n")
            
            # 8. Anwendung starten
            self.start_application()
            
            print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
            self.log("Launcher beendet sich in 3 Sekunden...", "info")
            print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
            time.sleep(3)
            
        except KeyboardInterrupt:
            print(f"\n\n{Fore.YELLOW}⚠️  Abbruch durch Benutzer (Ctrl+C){Style.RESET_ALL}")
            input("\nDrücken Sie Enter zum Beenden...")
            sys.exit(0)
        except Exception as e:
            print(f"\n{Fore.RED}❌ Unerwarteter Fehler: {e}{Style.RESET_ALL}")
            import traceback
            traceback.print_exc()
            input("\nDrücken Sie Enter zum Beenden...")
            sys.exit(1)


if __name__ == "__main__":
    # Stelle sicher dass wir in Windows CMD laufen, nicht WSL
    if sys.platform != "win32":
        print("❌ Dieses Skript ist nur für Windows vorgesehen!")
        print("Bitte führen Sie es in der Windows-Eingabeaufforderung aus, nicht in WSL.")
        sys.exit(1)
    
    launcher = ProjectLauncher()
    launcher.run()