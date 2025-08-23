#!/usr/bin/env python3
"""
Agent Migration Tool: claude-flow to Codex CLI
Automatisches Portierungstool mit grafischer Benutzeroberfläche
"""

import json
import os
import sys
import toml
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import subprocess
import shutil
import re

class AgentMigrationTool:
    """Hauptklasse für das Migrations-Tool"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Agent Migration Tool - claude-flow → Codex CLI")
        self.root.geometry("1200x800")
        
        # Dunkles Theme
        self.setup_theme()
        
        # Migrationsdaten
        self.claude_flow_config = {}
        self.codex_config = {}
        self.agents_mapping = {}
        self.migration_report = []
        
        # UI Setup
        self.setup_ui()
        
    def setup_theme(self):
        """Konfiguriert ein modernes dunkles Theme"""
        self.colors = {
            'bg': '#1e1e1e',
            'fg': '#ffffff',
            'accent': '#007acc',
            'success': '#4caf50',
            'warning': '#ff9800',
            'error': '#f44336',
            'secondary_bg': '#2d2d2d',
            'border': '#3c3c3c'
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # TTK Style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TLabel', background=self.colors['bg'], foreground=self.colors['fg'])
        self.style.configure('TButton', background=self.colors['accent'], foreground=self.colors['fg'])
        self.style.configure('TFrame', background=self.colors['bg'])
        
    def setup_ui(self):
        """Erstellt die Benutzeroberfläche"""
        # Header
        header_frame = tk.Frame(self.root, bg=self.colors['accent'], height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="🔄 Agent Migration Tool",
            font=('Arial', 18, 'bold'),
            bg=self.colors['accent'],
            fg=self.colors['fg']
        )
        title_label.pack(pady=15)
        
        # Main Container
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Left Panel - Source (claude-flow)
        left_panel = self.create_panel(main_container, "claude-flow (Quelle)", 0, 0)
        self.claude_flow_text = self.create_text_area(left_panel)
        
        # Middle Panel - Controls
        middle_panel = tk.Frame(main_container, bg=self.colors['bg'], width=200)
        middle_panel.grid(row=0, column=1, padx=10, sticky='ns')
        self.create_control_buttons(middle_panel)
        
        # Right Panel - Target (Codex CLI)
        right_panel = self.create_panel(main_container, "Codex CLI (Ziel)", 0, 2)
        self.codex_text = self.create_text_area(right_panel)
        
        # Bottom Panel - Status & Logs
        bottom_panel = tk.Frame(self.root, bg=self.colors['secondary_bg'], height=200)
        bottom_panel.pack(fill=tk.X, side=tk.BOTTOM)
        bottom_panel.pack_propagate(False)
        
        self.create_status_panel(bottom_panel)
        
        # Configure grid weights
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_columnconfigure(2, weight=1)
        
    def create_panel(self, parent, title, row, column):
        """Erstellt ein Panel mit Titel"""
        frame = tk.LabelFrame(
            parent,
            text=title,
            font=('Arial', 12, 'bold'),
            bg=self.colors['secondary_bg'],
            fg=self.colors['fg'],
            relief=tk.FLAT,
            borderwidth=2
        )
        frame.grid(row=row, column=column, sticky='nsew', padx=5, pady=5)
        return frame
    
    def create_text_area(self, parent):
        """Erstellt einen scrollbaren Textbereich"""
        text_area = scrolledtext.ScrolledText(
            parent,
            wrap=tk.WORD,
            width=40,
            height=20,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            insertbackground=self.colors['fg'],
            font=('Consolas', 10)
        )
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        return text_area
    
    def create_control_buttons(self, parent):
        """Erstellt die Steuerungsbuttons"""
        # Load Button
        load_btn = tk.Button(
            parent,
            text="📁 Projekt laden",
            command=self.load_claude_flow_project,
            bg=self.colors['accent'],
            fg=self.colors['fg'],
            font=('Arial', 10, 'bold'),
            width=20,
            height=2
        )
        load_btn.pack(pady=10)
        
        # Analyze Button
        analyze_btn = tk.Button(
            parent,
            text="🔍 Analysieren",
            command=self.analyze_configuration,
            bg=self.colors['warning'],
            fg=self.colors['fg'],
            font=('Arial', 10, 'bold'),
            width=20,
            height=2
        )
        analyze_btn.pack(pady=10)
        
        # Migrate Button
        migrate_btn = tk.Button(
            parent,
            text="⚡ Migrieren",
            command=self.perform_migration,
            bg=self.colors['success'],
            fg=self.colors['fg'],
            font=('Arial', 10, 'bold'),
            width=20,
            height=2
        )
        migrate_btn.pack(pady=10)
        
        # Export Button
        export_btn = tk.Button(
            parent,
            text="💾 Exportieren",
            command=self.export_configuration,
            bg=self.colors['accent'],
            fg=self.colors['fg'],
            font=('Arial', 10, 'bold'),
            width=20,
            height=2
        )
        export_btn.pack(pady=10)
        
        # Separator
        separator = tk.Frame(parent, height=2, bg=self.colors['border'])
        separator.pack(fill=tk.X, pady=20)
        
        # Options
        self.create_options(parent)
        
    def create_options(self, parent):
        """Erstellt Optionen für die Migration"""
        options_label = tk.Label(
            parent,
            text="Migrationsoptionen",
            font=('Arial', 11, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['fg']
        )
        options_label.pack(pady=5)
        
        # Checkboxes
        self.migrate_tools = tk.BooleanVar(value=True)
        tools_cb = tk.Checkbutton(
            parent,
            text="MCP-Server migrieren",
            variable=self.migrate_tools,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            selectcolor=self.colors['secondary_bg']
        )
        tools_cb.pack(anchor='w', padx=20)
        
        self.create_scripts = tk.BooleanVar(value=True)
        scripts_cb = tk.Checkbutton(
            parent,
            text="Workflow-Scripts erstellen",
            variable=self.create_scripts,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            selectcolor=self.colors['secondary_bg']
        )
        scripts_cb.pack(anchor='w', padx=20)
        
        self.preserve_structure = tk.BooleanVar(value=True)
        structure_cb = tk.Checkbutton(
            parent,
            text="Struktur beibehalten",
            variable=self.preserve_structure,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            selectcolor=self.colors['secondary_bg']
        )
        structure_cb.pack(anchor='w', padx=20)
        
    def create_status_panel(self, parent):
        """Erstellt das Status- und Log-Panel"""
        # Status Bar
        status_frame = tk.Frame(parent, bg=self.colors['border'], height=30)
        status_frame.pack(fill=tk.X)
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(
            status_frame,
            text="Bereit",
            bg=self.colors['border'],
            fg=self.colors['fg'],
            anchor='w'
        )
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        # Progress Bar
        self.progress = ttk.Progressbar(
            status_frame,
            length=200,
            mode='determinate'
        )
        self.progress.pack(side=tk.RIGHT, padx=10, pady=5)
        
        # Log Area
        log_label = tk.Label(
            parent,
            text="Migrations-Log",
            font=('Arial', 10, 'bold'),
            bg=self.colors['secondary_bg'],
            fg=self.colors['fg']
        )
        log_label.pack(anchor='w', padx=10, pady=(10, 5))
        
        self.log_text = scrolledtext.ScrolledText(
            parent,
            wrap=tk.WORD,
            height=8,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=('Consolas', 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
    def log(self, message, level='INFO'):
        """Fügt eine Nachricht zum Log hinzu"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # Farbcodes basierend auf Level
        color_tags = {
            'INFO': self.colors['fg'],
            'SUCCESS': self.colors['success'],
            'WARNING': self.colors['warning'],
            'ERROR': self.colors['error']
        }
        
        self.log_text.insert(tk.END, f"[{timestamp}] [{level}] {message}\n")
        
        # Scroll zum Ende
        self.log_text.see(tk.END)
        
        # Update Status
        self.status_label.config(text=message[:50] + '...' if len(message) > 50 else message)
        self.root.update()
        
    def load_claude_flow_project(self):
        """Lädt ein claude-flow Projekt"""
        folder = filedialog.askdirectory(title="Wählen Sie das claude-flow Projektverzeichnis")
        
        if not folder:
            return
        
        self.log("Lade claude-flow Projekt...", "INFO")
        self.progress['value'] = 0
        
        try:
            # Suche nach Konfigurationsdateien
            config_files = {
                'claude-flow.config.json': None,
                '.claude/settings.json': None,
                '.swarm/agents.json': None,
                '.hive-mind/config.json': None
            }
            
            total_files = len(config_files)
            current = 0
            
            for config_file in config_files.keys():
                current += 1
                self.progress['value'] = (current / total_files) * 50
                
                file_path = Path(folder) / config_file
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        config_files[config_file] = json.load(f)
                        self.log(f"Gefunden: {config_file}", "SUCCESS")
                else:
                    self.log(f"Nicht gefunden: {config_file}", "WARNING")
            
            # Merge Konfigurationen
            self.claude_flow_config = self.merge_configs(config_files)
            
            # Zeige Konfiguration im Textfeld
            self.claude_flow_text.delete(1.0, tk.END)
            self.claude_flow_text.insert(1.0, json.dumps(self.claude_flow_config, indent=2))
            
            self.log("claude-flow Projekt erfolgreich geladen", "SUCCESS")
            self.progress['value'] = 100
            
        except Exception as e:
            self.log(f"Fehler beim Laden: {str(e)}", "ERROR")
            messagebox.showerror("Fehler", f"Fehler beim Laden des Projekts:\n{str(e)}")
            
    def merge_configs(self, configs: Dict[str, Any]) -> Dict[str, Any]:
        """Kombiniert mehrere Konfigurationsdateien"""
        merged = {
            'agents': [],
            'hooks': [],
            'permissions': {'allow': [], 'deny': []},
            'mcpServers': {},
            'workflows': [],
            'settings': {}
        }
        
        for filename, config in configs.items():
            if config is None:
                continue
                
            if 'agents' in config:
                merged['agents'].extend(config['agents'])
            if 'hooks' in config:
                merged['hooks'].extend(config['hooks'])
            if 'permissions' in config:
                merged['permissions']['allow'].extend(config.get('permissions', {}).get('allow', []))
                merged['permissions']['deny'].extend(config.get('permissions', {}).get('deny', []))
            if 'mcpServers' in config:
                merged['mcpServers'].update(config.get('mcpServers', {}))
            if 'workflows' in config:
                merged['workflows'].extend(config.get('workflows', []))
                
        return merged
    
    def analyze_configuration(self):
        """Analysiert die claude-flow Konfiguration"""
        if not self.claude_flow_config:
            messagebox.showwarning("Warnung", "Bitte laden Sie zuerst ein claude-flow Projekt")
            return
        
        self.log("Analysiere Konfiguration...", "INFO")
        self.progress['value'] = 0
        
        analysis = {
            'agent_types': self.extract_agent_types(),
            'tools': self.extract_tools(),
            'workflows': self.extract_workflows(),
            'permissions': self.claude_flow_config.get('permissions', {}),
            'complexity': self.calculate_complexity()
        }
        
        # Zeige Analyse
        self.show_analysis_dialog(analysis)
        
        self.log("Analyse abgeschlossen", "SUCCESS")
        self.progress['value'] = 100
        
    def extract_agent_types(self) -> List[str]:
        """Extrahiert die verschiedenen Agententypen"""
        agent_types = set()
        
        # Standard claude-flow Agenten
        standard_agents = ['Queen', 'Architect', 'Coder', 'TDD', 'Security', 'DevOps', 'Reviewer']
        
        # Suche nach benutzerdefinierten Agenten
        if 'agents' in self.claude_flow_config:
            for agent in self.claude_flow_config['agents']:
                if isinstance(agent, dict) and 'type' in agent:
                    agent_types.add(agent['type'])
                    
        # Füge Standard-Agenten hinzu wenn keine gefunden
        if not agent_types:
            agent_types.update(standard_agents)
            
        return list(agent_types)
    
    def extract_tools(self) -> Dict[str, Any]:
        """Extrahiert verwendete Tools und MCP-Server"""
        tools = {}
        
        if 'mcpServers' in self.claude_flow_config:
            tools['mcp_servers'] = self.claude_flow_config['mcpServers']
            
        if 'hooks' in self.claude_flow_config:
            tools['hooks'] = []
            for hook in self.claude_flow_config['hooks']:
                if isinstance(hook, dict) and 'command' in hook:
                    tools['hooks'].append(hook['command'])
                    
        return tools
    
    def extract_workflows(self) -> List[str]:
        """Extrahiert definierte Workflows"""
        workflows = []
        
        if 'workflows' in self.claude_flow_config:
            workflows = self.claude_flow_config['workflows']
        else:
            # Standard SPARC Workflow
            workflows = ['Specify', 'Pseudocode', 'Architect', 'Review', 'Code']
            
        return workflows
    
    def calculate_complexity(self) -> str:
        """Berechnet die Komplexität der Migration"""
        score = 0
        
        # Anzahl der Agenten
        agent_count = len(self.extract_agent_types())
        score += agent_count * 10
        
        # Anzahl der Tools
        tools = self.extract_tools()
        if 'mcp_servers' in tools:
            score += len(tools['mcp_servers']) * 5
            
        # Workflows
        workflow_count = len(self.extract_workflows())
        score += workflow_count * 8
        
        if score < 30:
            return "Einfach"
        elif score < 60:
            return "Mittel"
        else:
            return "Komplex"
            
    def show_analysis_dialog(self, analysis: Dict[str, Any]):
        """Zeigt die Analyse in einem Dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Konfigurationsanalyse")
        dialog.geometry("600x500")
        dialog.configure(bg=self.colors['bg'])
        
        # Title
        title = tk.Label(
            dialog,
            text="📊 Analyse-Ergebnis",
            font=('Arial', 14, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['fg']
        )
        title.pack(pady=10)
        
        # Analysis Text
        text_widget = scrolledtext.ScrolledText(
            dialog,
            wrap=tk.WORD,
            width=70,
            height=25,
            bg=self.colors['secondary_bg'],
            fg=self.colors['fg'],
            font=('Consolas', 10)
        )
        text_widget.pack(padx=20, pady=10)
        
        # Format Analysis
        analysis_text = f"""
=== KONFIGURATIONSANALYSE ===

📦 AGENTENTYPEN ({len(analysis['agent_types'])}):
{chr(10).join(f'  • {agent}' for agent in analysis['agent_types'])}

🛠️ TOOLS & MCP-SERVER:
{self.format_tools(analysis['tools'])}

🔄 WORKFLOWS ({len(analysis['workflows'])}):
{chr(10).join(f'  {i+1}. {workflow}' for i, workflow in enumerate(analysis['workflows']))}

🔐 BERECHTIGUNGEN:
  Erlaubt: {', '.join(analysis['permissions'].get('allow', []))}
  Verweigert: {', '.join(analysis['permissions'].get('deny', []))}

📊 MIGRATIONSKOMPLEXITÄT: {analysis['complexity']}

💡 EMPFEHLUNGEN:
{self.generate_recommendations(analysis)}
        """
        
        text_widget.insert(1.0, analysis_text)
        text_widget.config(state='disabled')
        
        # Close Button
        close_btn = tk.Button(
            dialog,
            text="Schließen",
            command=dialog.destroy,
            bg=self.colors['accent'],
            fg=self.colors['fg'],
            font=('Arial', 10, 'bold')
        )
        close_btn.pack(pady=10)
        
    def format_tools(self, tools: Dict[str, Any]) -> str:
        """Formatiert die Tools-Ausgabe"""
        output = []
        
        if 'mcp_servers' in tools:
            output.append("  MCP-Server:")
            for name, config in tools['mcp_servers'].items():
                output.append(f"    - {name}: {config.get('command', 'N/A')}")
                
        if 'hooks' in tools:
            output.append("  Hooks:")
            for hook in tools['hooks']:
                output.append(f"    - {hook}")
                
        return '\n'.join(output) if output else "  Keine Tools konfiguriert"
    
    def generate_recommendations(self, analysis: Dict[str, Any]) -> str:
        """Generiert Empfehlungen basierend auf der Analyse"""
        recommendations = []
        
        if analysis['complexity'] == "Komplex":
            recommendations.append("• Erwägen Sie eine schrittweise Migration")
            recommendations.append("• Erstellen Sie Backup aller Konfigurationen")
            recommendations.append("• Testen Sie jeden migrierten Agenten einzeln")
            
        if len(analysis['agent_types']) > 5:
            recommendations.append("• Konsolidieren Sie ähnliche Agenten für Codex CLI")
            recommendations.append("• Nutzen Sie Profile für verschiedene Agenten-Sets")
            
        if 'mcp_servers' in analysis['tools'] and len(analysis['tools']['mcp_servers']) > 0:
            recommendations.append("• Verifizieren Sie MCP-Server Kompatibilität mit Codex CLI")
            
        return '\n'.join(recommendations) if recommendations else "• Direkte Migration möglich"
    
    def perform_migration(self):
        """Führt die eigentliche Migration durch"""
        if not self.claude_flow_config:
            messagebox.showwarning("Warnung", "Bitte laden Sie zuerst ein claude-flow Projekt")
            return
        
        self.log("Starte Migration...", "INFO")
        self.progress['value'] = 0
        
        try:
            # 1. Erstelle Codex CLI Konfiguration
            self.log("Erstelle Codex CLI config.toml...", "INFO")
            self.progress['value'] = 20
            codex_toml = self.create_codex_config()
            
            # 2. Erstelle AGENTS.md
            self.log("Generiere AGENTS.md Dateien...", "INFO")
            self.progress['value'] = 40
            agents_md = self.create_agents_md()
            
            # 3. Erstelle Workflow-Scripts
            if self.create_scripts.get():
                self.log("Erstelle Workflow-Scripts...", "INFO")
                self.progress['value'] = 60
                scripts = self.create_workflow_scripts()
            
            # 4. Erstelle Migrations-Mapping
            self.log("Erstelle Mapping-Datei...", "INFO")
            self.progress['value'] = 80
            mapping = self.create_migration_mapping()
            
            # Zeige Ergebnisse
            self.show_migration_results(codex_toml, agents_md)
            
            self.log("Migration erfolgreich abgeschlossen!", "SUCCESS")
            self.progress['value'] = 100
            
        except Exception as e:
            self.log(f"Migrationsfehler: {str(e)}", "ERROR")
            messagebox.showerror("Fehler", f"Migration fehlgeschlagen:\n{str(e)}")
            
    def create_codex_config(self) -> Dict[str, Any]:
        """Erstellt die Codex CLI config.toml Konfiguration"""
        config = {
            'model': 'o4-mini',
            'model_provider': 'openai',
            'approval_policy': 'suggest',
            'sandbox_mode': 'workspace-write',
            'profiles': {},
            'mcp_servers': {}
        }
        
        # Migriere MCP-Server
        if self.migrate_tools.get() and 'mcpServers' in self.claude_flow_config:
            for name, server_config in self.claude_flow_config['mcpServers'].items():
                config['mcp_servers'][name] = {
                    'command': server_config.get('command', ''),
                    'args': server_config.get('args', [])
                }
        
        # Erstelle Profile für verschiedene Agententypen
        agent_types = self.extract_agent_types()
        for agent_type in agent_types:
            profile_name = agent_type.lower()
            config['profiles'][profile_name] = {
                'approval_policy': self.map_approval_policy(agent_type),
                'sandbox_mode': self.map_sandbox_mode(agent_type)
            }
            
        return config
    
    def map_approval_policy(self, agent_type: str) -> str:
        """Mappt Agententyp zu Approval Policy"""
        policy_map = {
            'Queen': 'on-request',
            'Architect': 'suggest',
            'Coder': 'suggest',
            'TDD': 'on-request',
            'Security': 'always',
            'DevOps': 'suggest',
            'Reviewer': 'always'
        }
        return policy_map.get(agent_type, 'suggest')
    
    def map_sandbox_mode(self, agent_type: str) -> str:
        """Mappt Agententyp zu Sandbox Mode"""
        mode_map = {
            'Queen': 'workspace-write',
            'Architect': 'read-only',
            'Coder': 'workspace-write',
            'TDD': 'workspace-write',
            'Security': 'read-only',
            'DevOps': 'workspace-write',
            'Reviewer': 'read-only'
        }
        return mode_map.get(agent_type, 'workspace-write')
    
    def create_agents_md(self) -> str:
        """Erstellt die AGENTS.md Datei"""
        agent_types = self.extract_agent_types()
        workflows = self.extract_workflows()
        
        md_content = """# Codex CLI Agent Configuration
*Automatisch migriert von claude-flow*

## System Overview
Diese Konfiguration wurde automatisch aus einem claude-flow Multi-Agent-System migriert.
Die ursprünglichen spezialisierten Agenten wurden in natürlichsprachliche Instruktionen übersetzt.

---

"""
        
        # Füge Instruktionen für jeden Agententyp hinzu
        for agent_type in agent_types:
            md_content += self.generate_agent_instructions(agent_type)
            md_content += "\n---\n\n"
        
        # Füge Workflow-Instruktionen hinzu
        md_content += "## Workflow Integration\n\n"
        md_content += self.generate_workflow_instructions(workflows)
        
        # Füge Permissions und Hooks hinzu
        if 'permissions' in self.claude_flow_config:
            md_content += "\n## Security & Permissions\n\n"
            md_content += self.generate_permissions_instructions()
        
        return md_content
    
    def generate_agent_instructions(self, agent_type: str) -> str:
        """Generiert Instruktionen für einen spezifischen Agententyp"""
        instructions_map = {
            'Queen': """## Queen Agent - Orchestration Leader

### Core Responsibilities
- Coordinate all development activities across the project
- Make high-level architectural decisions
- Delegate tasks to appropriate specialized functions
- Ensure quality standards are maintained throughout

### Decision Framework
When presented with a task:
1. Analyze requirements comprehensively
2. Break down into subtasks
3. Determine optimal execution order
4. Monitor progress and adjust as needed

### Quality Standards
- All code must pass review before integration
- Documentation must be complete and clear
- Test coverage must exceed 80%
- Security considerations must be addressed upfront""",

            'Architect': """## Architect Agent - System Design

### Core Responsibilities
- Design system architecture with scalability in mind
- Create detailed technical specifications
- Define API contracts and data models
- Establish coding standards and patterns

### Architecture Principles
- Follow SOLID principles religiously
- Implement clean architecture patterns
- Design for testability and maintainability
- Minimize coupling, maximize cohesion

### Documentation Requirements
- Create comprehensive ADRs for major decisions
- Maintain up-to-date system diagrams
- Document all API endpoints thoroughly
- Include performance considerations""",

            'Coder': """## Coder Agent - Implementation Specialist

### Core Responsibilities
- Implement features according to specifications
- Write clean, efficient, and maintainable code
- Follow established coding standards
- Optimize for performance and readability

### Coding Standards
- Use meaningful variable and function names
- Keep functions small and focused
- Implement proper error handling
- Add inline comments for complex logic

### Best Practices
- Write code that is self-documenting
- Refactor regularly to improve quality
- Use appropriate design patterns
- Consider edge cases and error scenarios""",

            'TDD': """## TDD Agent - Test-Driven Development

### Core Responsibilities
- Write comprehensive test suites
- Implement test-first development approach
- Ensure high code coverage
- Create both unit and integration tests

### Testing Strategy
- Write failing tests before implementation
- Test edge cases and error conditions
- Use appropriate mocking and stubbing
- Maintain test documentation

### Coverage Requirements
- Minimum 80% code coverage
- 100% coverage for critical paths
- Include performance tests where relevant
- Implement regression test suites""",

            'Security': """## Security Agent - Vulnerability Analysis

### Core Responsibilities
- Perform security audits on all code
- Identify potential vulnerabilities
- Implement security best practices
- Review authentication and authorization

### Security Checklist
- Check for SQL injection vulnerabilities
- Validate all user inputs
- Implement proper encryption
- Review API security measures
- Check for XSS vulnerabilities
- Audit dependency vulnerabilities

### Compliance Requirements
- Follow OWASP guidelines
- Implement proper logging
- Ensure data privacy compliance
- Regular security updates""",

            'DevOps': """## DevOps Agent - Infrastructure & Deployment

### Core Responsibilities
- Configure CI/CD pipelines
- Manage deployment processes
- Monitor system performance
- Implement infrastructure as code

### Deployment Strategy
- Automate all deployment steps
- Implement blue-green deployments
- Configure proper monitoring
- Set up automated rollback

### Infrastructure Requirements
- Use containerization (Docker)
- Implement Kubernetes for orchestration
- Configure proper logging and monitoring
- Set up automated backups""",

            'Reviewer': """## Reviewer Agent - Code Quality Assurance

### Core Responsibilities
- Review all code changes thoroughly
- Ensure coding standards compliance
- Verify test coverage
- Check documentation completeness

### Review Criteria
- Code readability and maintainability
- Performance implications
- Security considerations
- Architectural alignment

### Feedback Guidelines
- Provide constructive criticism
- Suggest specific improvements
- Highlight both issues and good practices
- Ensure knowledge sharing"""
        }
        
        return instructions_map.get(agent_type, f"""## {agent_type} Agent

### Core Responsibilities
- Perform specialized tasks related to {agent_type}
- Maintain high quality standards
- Collaborate with other system components
- Document all activities thoroughly

### Best Practices
- Follow established patterns and conventions
- Prioritize code quality and maintainability
- Consider performance implications
- Ensure comprehensive testing""")
    
    def generate_workflow_instructions(self, workflows: List[str]) -> str:
        """Generiert Workflow-Instruktionen"""
        instructions = "### Workflow Execution Order\n\n"
        
        if workflows:
            instructions += "Follow this workflow sequence for all major features:\n\n"
            for i, workflow in enumerate(workflows, 1):
                instructions += f"{i}. **{workflow}**: "
                instructions += self.get_workflow_description(workflow) + "\n"
        else:
            instructions += """Use the standard development workflow:
1. **Requirements Analysis**: Understand the problem thoroughly
2. **Design**: Create architectural plans
3. **Implementation**: Write clean code
4. **Testing**: Ensure quality through tests
5. **Review**: Validate all changes
6. **Deployment**: Ship with confidence
"""
        
        return instructions
    
    def get_workflow_description(self, workflow: str) -> str:
        """Gibt eine Beschreibung für einen Workflow-Schritt zurück"""
        descriptions = {
            'Specify': 'Define clear requirements and acceptance criteria',
            'Pseudocode': 'Create high-level algorithmic representation',
            'Architect': 'Design system components and interactions',
            'Review': 'Validate design decisions and approaches',
            'Code': 'Implement the actual solution',
            'Test': 'Verify functionality and edge cases',
            'Deploy': 'Release to production environment'
        }
        return descriptions.get(workflow, f'Execute {workflow} phase')
    
    def generate_permissions_instructions(self) -> str:
        """Generiert Permissions-Instruktionen"""
        permissions = self.claude_flow_config.get('permissions', {})
        allowed = permissions.get('allow', [])
        denied = permissions.get('deny', [])
        
        instructions = "### Permissions & Restrictions\n\n"
        
        if allowed:
            instructions += "**Allowed Operations:**\n"
            for perm in allowed:
                instructions += f"- {perm}\n"
            instructions += "\n"
        
        if denied:
            instructions += "**Restricted Operations:**\n"
            for perm in denied:
                instructions += f"- Never perform {perm} without explicit approval\n"
        
        return instructions
    
    def create_workflow_scripts(self) -> List[Dict[str, str]]:
        """Erstellt Workflow-Automatisierungs-Scripts"""
        scripts = []
        workflows = self.extract_workflows()
        
        # Hauptworkflow-Script
        main_script = {
            'name': 'claude_flow_workflow.sh',
            'content': self.generate_main_workflow_script(workflows)
        }
        scripts.append(main_script)
        
        # Agent-spezifische Scripts
        for agent_type in self.extract_agent_types():
            agent_script = {
                'name': f'{agent_type.lower()}_agent.sh',
                'content': self.generate_agent_script(agent_type)
            }
            scripts.append(agent_script)
        
        return scripts
    
    def generate_main_workflow_script(self, workflows: List[str]) -> str:
        """Generiert das Haupt-Workflow-Script"""
        script = """#!/bin/bash
# claude-flow to Codex CLI Workflow Automation
# Auto-generated migration script

set -e

echo "🚀 Starting claude-flow compatible workflow..."

# Configuration
PROJECT_DIR=$(pwd)
CODEX_CONFIG="$HOME/.codex/config.toml"

"""
        
        # Füge Workflow-Schritte hinzu
        for i, workflow in enumerate(workflows, 1):
            script += f"""
# Step {i}: {workflow}
echo "📋 Executing {workflow} phase..."
codex exec --profile {workflow.lower()} "Execute the {workflow} phase for the current task"
if [ $? -ne 0 ]; then
    echo "❌ {workflow} phase failed"
    exit 1
fi
echo "✅ {workflow} phase completed"
"""
        
        script += """
echo "✨ Workflow completed successfully!"
"""
        
        return script
    
    def generate_agent_script(self, agent_type: str) -> str:
        """Generiert ein Agent-spezifisches Script"""
        return f"""#!/bin/bash
# {agent_type} Agent Simulation for Codex CLI
# Auto-generated from claude-flow configuration

AGENT_TYPE="{agent_type}"
PROFILE="{agent_type.lower()}"

echo "🤖 Activating $AGENT_TYPE agent mode..."

# Load agent-specific configuration
codex exec --profile $PROFILE \\
    "You are now operating as the $AGENT_TYPE agent. \\
     Follow the instructions in AGENTS.md for the $AGENT_TYPE role. \\
     Current task: $1"

# Log agent activity
echo "[$AGENT_TYPE] Task completed: $1" >> .codex/agent.log
"""
    
    def create_migration_mapping(self) -> Dict[str, Any]:
        """Erstellt eine Mapping-Datei für die Migration"""
        mapping = {
            'migration_date': datetime.now().isoformat(),
            'source_system': 'claude-flow',
            'target_system': 'codex-cli',
            'agent_mapping': {},
            'tool_mapping': {},
            'workflow_mapping': {}
        }
        
        # Agent Mapping
        for agent in self.extract_agent_types():
            mapping['agent_mapping'][agent] = {
                'profile': agent.lower(),
                'agents_md_section': f'{agent} Agent',
                'script': f'{agent.lower()}_agent.sh'
            }
        
        # Tool Mapping
        if 'mcpServers' in self.claude_flow_config:
            for server_name in self.claude_flow_config['mcpServers']:
                mapping['tool_mapping'][server_name] = {
                    'type': 'mcp_server',
                    'codex_config_section': f'mcp_servers.{server_name}'
                }
        
        # Workflow Mapping
        for i, workflow in enumerate(self.extract_workflows()):
            mapping['workflow_mapping'][workflow] = {
                'order': i + 1,
                'profile': workflow.lower()
            }
        
        self.migration_report = mapping
        return mapping
    
    def show_migration_results(self, codex_toml: Dict[str, Any], agents_md: str):
        """Zeigt die Migrationsergebnisse an"""
        # Update Codex Text Area
        self.codex_text.delete(1.0, tk.END)
        
        # Formatiere TOML
        toml_content = toml.dumps(codex_toml)
        
        # Kombiniere Ausgabe
        output = f"""# config.toml
{toml_content}

# ==========================================

# AGENTS.md
{agents_md}
"""
        
        self.codex_text.insert(1.0, output)
        
        # Zeige Erfolgs-Dialog
        self.show_success_dialog()
    
    def show_success_dialog(self):
        """Zeigt einen Erfolgs-Dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Migration erfolgreich!")
        dialog.geometry("500x300")
        dialog.configure(bg=self.colors['bg'])
        
        # Success Icon and Message
        success_label = tk.Label(
            dialog,
            text="✅ Migration erfolgreich abgeschlossen!",
            font=('Arial', 14, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['success']
        )
        success_label.pack(pady=20)
        
        # Statistics
        stats_text = f"""
Migrierte Komponenten:
• {len(self.extract_agent_types())} Agententypen
• {len(self.extract_tools().get('mcp_servers', {}))} MCP-Server
• {len(self.extract_workflows())} Workflow-Schritte

Die Konfiguration wurde erfolgreich für Codex CLI vorbereitet.
Sie können die Dateien nun exportieren und in Ihrem
Codex CLI Projekt verwenden.
        """
        
        stats_label = tk.Label(
            dialog,
            text=stats_text,
            font=('Arial', 10),
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            justify=tk.LEFT
        )
        stats_label.pack(pady=10, padx=20)
        
        # Buttons
        button_frame = tk.Frame(dialog, bg=self.colors['bg'])
        button_frame.pack(pady=20)
        
        export_btn = tk.Button(
            button_frame,
            text="Exportieren",
            command=lambda: [self.export_configuration(), dialog.destroy()],
            bg=self.colors['success'],
            fg=self.colors['fg'],
            font=('Arial', 10, 'bold'),
            width=15
        )
        export_btn.pack(side=tk.LEFT, padx=10)
        
        close_btn = tk.Button(
            button_frame,
            text="Schließen",
            command=dialog.destroy,
            bg=self.colors['accent'],
            fg=self.colors['fg'],
            font=('Arial', 10, 'bold'),
            width=15
        )
        close_btn.pack(side=tk.LEFT, padx=10)
    
    def export_configuration(self):
        """Exportiert die migrierte Konfiguration"""
        export_dir = filedialog.askdirectory(title="Wählen Sie das Export-Verzeichnis")
        
        if not export_dir:
            return
        
        try:
            export_path = Path(export_dir)
            
            # Erstelle Codex-Verzeichnisstruktur
            codex_dir = export_path / 'codex-migration'
            codex_dir.mkdir(exist_ok=True)
            
            # Exportiere config.toml
            config_file = codex_dir / 'config.toml'
            codex_config = self.create_codex_config()
            with open(config_file, 'w', encoding='utf-8') as f:
                toml.dump(codex_config, f)
            self.log(f"Exportiert: config.toml", "SUCCESS")
            
            # Exportiere AGENTS.md
            agents_file = codex_dir / 'AGENTS.md'
            agents_content = self.create_agents_md()
            with open(agents_file, 'w', encoding='utf-8') as f:
                f.write(agents_content)
            self.log(f"Exportiert: AGENTS.md", "SUCCESS")
            
            # Exportiere Workflow-Scripts
            if self.create_scripts.get():
                scripts_dir = codex_dir / 'scripts'
                scripts_dir.mkdir(exist_ok=True)
                
                for script in self.create_workflow_scripts():
                    script_file = scripts_dir / script['name']
                    with open(script_file, 'w', encoding='utf-8') as f:
                        f.write(script['content'])
                    # Mache Script ausführbar auf Unix-Systemen
                    if os.name != 'nt':
                        os.chmod(script_file, 0o755)
                    self.log(f"Exportiert: {script['name']}", "SUCCESS")
            
            # Exportiere Migrations-Mapping
            mapping_file = codex_dir / 'migration_mapping.json'
            with open(mapping_file, 'w', encoding='utf-8') as f:
                json.dump(self.migration_report, f, indent=2)
            self.log(f"Exportiert: migration_mapping.json", "SUCCESS")
            
            # Erstelle README
            readme_file = codex_dir / 'README.md'
            with open(readme_file, 'w', encoding='utf-8') as f:
                f.write(self.generate_readme())
            self.log(f"Exportiert: README.md", "SUCCESS")
            
            messagebox.showinfo("Export erfolgreich", 
                              f"Konfiguration wurde exportiert nach:\n{codex_dir}")
            
        except Exception as e:
            self.log(f"Export-Fehler: {str(e)}", "ERROR")
            messagebox.showerror("Export-Fehler", f"Fehler beim Export:\n{str(e)}")
    
    def generate_readme(self) -> str:
        """Generiert eine README für die exportierte Konfiguration"""
        return f"""# Codex CLI Migration von claude-flow

## 📋 Übersicht
Diese Konfiguration wurde automatisch vom Agent Migration Tool erstellt.
Migrationsdatum: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🚀 Installation

1. **Codex CLI installieren:**
   ```bash
   npm install -g @openai/codex
   ```

2. **Konfiguration kopieren:**
   ```bash
   cp config.toml ~/.codex/config.toml
   cp AGENTS.md ~/your-project/AGENTS.md
   ```

3. **Scripts ausführbar machen:**
   ```bash
   chmod +x scripts/*.sh
   ```

## 📁 Dateistruktur

- `config.toml` - Hauptkonfiguration für Codex CLI
- `AGENTS.md` - Agenten-Instruktionen
- `scripts/` - Workflow-Automatisierungs-Scripts
- `migration_mapping.json` - Mapping zwischen claude-flow und Codex CLI

## 🔧 Verwendung

### Mit Profilen arbeiten:
```bash
codex exec --profile architect "Design the system architecture"
```

### Workflow ausführen:
```bash
./scripts/claude_flow_workflow.sh
```

### Spezifischen Agenten aktivieren:
```bash
./scripts/coder_agent.sh "Implement user authentication"
```

## ⚠️ Wichtige Hinweise

- Die Migration übersetzt Multi-Agent-Orchestrierung in Single-Agent-Instruktionen
- Manche claude-flow Features haben keine direkte Entsprechung in Codex CLI
- Testen Sie die migrierten Workflows gründlich
- Passen Sie die AGENTS.md nach Bedarf an Ihre spezifischen Anforderungen an

## 📚 Weitere Ressourcen

- [Codex CLI Dokumentation](https://help.openai.com/en/articles/11096431-openai-codex-cli-getting-started)
- [AGENTS.md Best Practices](https://agentsmd.net/)
- [Migration Mapping Details](migration_mapping.json)

---
*Generiert vom Agent Migration Tool v1.0*
"""
    
    def run(self):
        """Startet die Anwendung"""
        self.log("Agent Migration Tool gestartet", "INFO")
        self.root.mainloop()


# Hauptprogramm
if __name__ == "__main__":
    app = AgentMigrationTool()
    app.run()
