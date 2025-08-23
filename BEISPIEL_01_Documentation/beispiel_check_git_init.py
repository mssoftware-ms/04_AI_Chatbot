#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Tuple, Optional

class GitInitializer:
    def __init__(self, directory: str = None):
        """
        Initialisiert den GitInitializer
        
        Args:
            directory: Zielverzeichnis (Standard: aktuelles Verzeichnis)
        """
        self.directory = Path(directory) if directory else Path.cwd()
        self.git_dir = self.directory / '.git'
        
    def check_git_exists(self) -> bool:
        """Prüft ob .git Verzeichnis existiert"""
        return self.git_dir.exists() and self.git_dir.is_dir()
    
    def check_branch_exists(self) -> Tuple[bool, Optional[str]]:
        """
        Prüft ob ein Branch existiert
        
        Returns:
            Tuple: (branch_exists: bool, branch_name: Optional[str])
        """
        if not self.check_git_exists():
            return False, None
            
        try:
            # Versuche aktuellen Branch zu ermitteln
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=self.directory,
                capture_output=True,
                text=True,
                check=False
            )
            
            # Wenn Ausgabe leer ist, gibt es noch keinen Branch
            branch_name = result.stdout.strip()
            if branch_name:
                return True, branch_name
                
            # Prüfe ob überhaupt Branches existieren
            result = subprocess.run(
                ['git', 'branch', '-a'],
                cwd=self.directory,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.stdout.strip():
                # Es gibt Branches, aber wir sind in detached HEAD state
                return True, "detached HEAD"
            else:
                # Keine Branches vorhanden (leeres Repository)
                return False, None
                
        except subprocess.SubprocessError:
            return False, None
    
    def get_status(self) -> Dict:
        """
        Ermittelt den vollständigen Git-Status
        
        Returns:
            Dict mit Status-Informationen
        """
        git_exists = self.check_git_exists()
        branch_exists, branch_name = self.check_branch_exists()
        
        status = {
            'git_initialized': git_exists,
            'branch_exists': branch_exists,
            'branch_name': branch_name,
            'can_initialize': False,
            'message': '',
            'action_needed': None
        }
        
        if not git_exists:
            status['can_initialize'] = True
            status['message'] = 'Kein Git Repository vorhanden - kann initialisiert werden'
            status['action_needed'] = 'full_init'
        elif git_exists and not branch_exists:
            status['can_initialize'] = True
            status['message'] = 'Git Repository vorhanden aber KEIN Branch - Initialisierung erforderlich'
            status['action_needed'] = 'create_branch'
        else:
            status['message'] = f'Git Repository vollständig initialisiert (Branch: {branch_name})'
            status['action_needed'] = None
            
        return status
    
    def initialize(self, branch_name: str = 'main') -> Dict:
        """
        Führt Git-Initialisierung durch
        
        Args:
            branch_name: Name des Hauptbranches (Standard: 'main')
            
        Returns:
            Dict mit Ergebnis der Initialisierung
        """
        status = self.get_status()
        
        if not status['can_initialize']:
            return {
                'success': False,
                'message': f"Initialisierung nicht möglich: {status['message']}"
            }
        
        try:
            os.chdir(self.directory)
            
            if status['action_needed'] == 'full_init':
                # Vollständige Initialisierung
                print("📁 Initialisiere neues Git Repository...")
                
                # Git init mit konfiguriertem default branch
                subprocess.run(
                    ['git', 'config', '--global', 'init.defaultBranch', branch_name],
                    check=True,
                    capture_output=True
                )
                subprocess.run(['git', 'init'], check=True, capture_output=True)
                
                # Branch wird automatisch mit dem ersten Commit erstellt
                self._create_initial_files()
                self._make_initial_commit(branch_name)
                
            elif status['action_needed'] == 'create_branch':
                # Nur Branch und Initial Commit erstellen
                print("🌿 Git existiert, erstelle Branch und Initial Commit...")
                
                # Erstelle erste Dateien falls noch nicht vorhanden
                self._create_initial_files()
                
                # Erstelle Branch mit erstem Commit
                self._make_initial_commit(branch_name)
            
            # Finaler Status
            final_status = self.get_status()
            return {
                'success': True,
                'message': f"✅ Erfolgreich initialisiert! Branch: {final_status['branch_name']}",
                'branch': final_status['branch_name']
            }
            
        except subprocess.CalledProcessError as e:
            return {
                'success': False,
                'message': f"❌ Fehler bei Git-Operation: {e}"
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"❌ Unerwarteter Fehler: {e}"
            }
    
    def _create_initial_files(self):
        """Erstellt initiale Dateien (README, .gitignore)"""
        # README.md
        readme_path = self.directory / 'README.md'
        if not readme_path.exists():
            project_name = self.directory.name
            readme_content = f"""# {project_name}

## Beschreibung
Projekt initialisiert am {subprocess.run(['date'], capture_output=True, text=True).stdout.strip()}

## Setup
```bash
git clone <repository-url>
cd {project_name}