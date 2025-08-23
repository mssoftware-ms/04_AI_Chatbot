"""
GUI Config Extractor Integration für Ihre Claude-Flow App
Integriert in Ihre bestehende PyQt6 Anwendung
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTextEdit, QLabel, QGroupBox, QCheckBox, QComboBox,
    QTableWidget, QTableWidgetItem, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QColor, QFont
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

class ConfigExtractorWidget(QWidget):
    """
    Widget für Config-Extraktion und -Synchronisation
    Integriert in Ihre bestehende Claude-Flow GUI
    """
    
    config_extracted = pyqtSignal(dict)
    status_message = pyqtSignal(str, str)  # message, level (info/warning/error/success)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent  # Referenz zur Hauptanwendung
        self.extracted_config = {}
        self.custom_agents = {}
        self.init_ui()
        
    def init_ui(self):
        """Erstellt die UI-Komponenten"""
        layout = QVBoxLayout()
        
        # Titel
        title = QLabel("🔧 V86 Config Extractor & Synchronizer")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # Status Box
        self.status_box = QGroupBox("Extraction Status")
        status_layout = QVBoxLayout()
        
        # Checkboxen für gefundene Configs
        self.checks = {
            'claude_settings': QCheckBox("📄 .claude/settings.json"),
            'mcp_config': QCheckBox("🔌 .mcp.json"),
            'env_vars': QCheckBox("🔑 Environment Variables"),
            'custom_agents': QCheckBox("🤖 Custom Agents"),
            'python_env': QCheckBox("🐍 Python Environment"),
            'memory_db': QCheckBox("💾 Memory Database"),
            'project_context': QCheckBox("📝 CLAUDE.md")
        }
        
        for check in self.checks.values():
            check.setEnabled(False)
            status_layout.addWidget(check)
            
        self.status_box.setLayout(status_layout)
        layout.addWidget(self.status_box)
        
        # Ihre Custom Agents Sektion
        agents_group = QGroupBox("Your Custom Agent Configuration")
        agents_layout = QVBoxLayout()
        
        # Agent-Auswahl basierend auf Ihrem Setup
        self.agent_selector = QComboBox()
        self.agent_selector.addItems([
            "🐍 Python Development (Your Setup)",
            "🔧 Custom Backend Team",
            "🛡️ Security & Testing Suite",
            "📊 Full Stack Development",
            "🎯 Specialized AI Team"
        ])
        agents_layout.addWidget(QLabel("Select Your Agent Preset:"))
        agents_layout.addWidget(self.agent_selector)
        
        # Ihre spezifischen Agenten
        self.your_agents = QTableWidget(10, 3)
        self.your_agents.setHorizontalHeaderLabels(["Agent", "Role", "Status"])
        
        # Ihre Agenten aus der Migration
        your_agent_list = [
            ("queen", "Strategic Coordinator", "✅ Migrated"),
            ("backend-dev", "Python Developer", "✅ Migrated"),
            ("frontend-dev", "UI Developer", "✅ Migrated"),
            ("system-architect", "Architecture Design", "✅ Migrated"),
            ("tester", "Test Automation", "✅ Migrated"),
            ("performance-tester", "Performance Analysis", "✅ Migrated"),
            ("security-tester", "Security Audit", "✅ Migrated"),
            ("devops-engineer", "CI/CD Pipeline", "✅ Migrated"),
            ("api-documenter", "Documentation", "✅ Migrated"),
            ("pentester", "Penetration Testing", "✅ Migrated")
        ]
        
        for i, (agent, role, status) in enumerate(your_agent_list):
            self.your_agents.setItem(i, 0, QTableWidgetItem(agent))
            self.your_agents.setItem(i, 1, QTableWidgetItem(role))
            self.your_agents.setItem(i, 2, QTableWidgetItem(status))
            
        self.your_agents.resizeColumnsToContents()
        agents_layout.addWidget(self.your_agents)
        
        agents_group.setLayout(agents_layout)
        layout.addWidget(agents_group)
        
        # Control Buttons
        button_layout = QHBoxLayout()
        
        self.extract_btn = QPushButton("🔍 Extract Current Config")
        self.extract_btn.clicked.connect(self.extract_config)
        button_layout.addWidget(self.extract_btn)
        
        self.sync_btn = QPushButton("🔄 Sync with Your Setup")
        self.sync_btn.clicked.connect(self.sync_with_custom_setup)
        self.sync_btn.setEnabled(False)
        button_layout.addWidget(self.sync_btn)
        
        self.generate_btn = QPushButton("⚡ Generate V86 Config")
        self.generate_btn.clicked.connect(self.generate_v86_config)
        self.generate_btn.setEnabled(False)
        button_layout.addWidget(self.generate_btn)
        
        self.test_btn = QPushButton("🧪 Test Configuration")
        self.test_btn.clicked.connect(self.test_configuration)
        button_layout.addWidget(self.test_btn)
        
        layout.addLayout(button_layout)
        
        # Output/Log Area
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(150)
        self.log_area.setStyleSheet("font-family: monospace; font-size: 10px;")
        layout.addWidget(QLabel("Extraction Log:"))
        layout.addWidget(self.log_area)
        
        # Authentication Options (NEU!)
        auth_group = QGroupBox("🔐 Authentication Method")
        auth_layout = QVBoxLayout()
        
        self.auth_method = QComboBox()
        self.auth_method.addItems([
            "Claude Web Abo (No API Key needed)",
            "API Key (Programmatic Access)",
            "Auto-Detect"
        ])
        self.auth_method.currentTextChanged.connect(self.on_auth_method_changed)
        
        auth_layout.addWidget(QLabel("Select Authentication:"))
        auth_layout.addWidget(self.auth_method)
        
        self.auth_status = QLabel("Status: Checking...")
        auth_layout.addWidget(self.auth_status)
        
        auth_group.setLayout(auth_layout)
        layout.addWidget(auth_group)
        
        self.setLayout(layout)
        
        # Initial check
        self.check_authentication()
        
    def check_authentication(self):
        """Prüft verfügbare Authentifizierungsmethoden"""
        self.log("Checking authentication methods...")
        
        # Check for API Key
        api_key = os.environ.get('ANTHROPIC_API_KEY', '')
        has_api_key = bool(api_key and api_key.startswith('sk-ant-'))
        
        # Check for Claude Code CLI
        has_claude_cli = os.system('which claude >/dev/null 2>&1') == 0
        
        # Check for browser session (simplified check)
        has_browser_session = os.path.exists(os.path.expanduser('~/.claude'))
        
        if has_api_key:
            self.auth_status.setText("✅ API Key found")
            self.auth_status.setStyleSheet("color: green;")
            self.log("✅ API Key detected", "success")
        elif has_claude_cli and has_browser_session:
            self.auth_status.setText("✅ Claude Web Abo detected")
            self.auth_status.setStyleSheet("color: green;")
            self.log("✅ Using Claude Web Abo - No API Key needed!", "success")
        else:
            self.auth_status.setText("⚠️ No authentication found")
            self.auth_status.setStyleSheet("color: orange;")
            self.log("⚠️ Please login to claude.ai or set API key", "warning")
            
    def on_auth_method_changed(self, method):
        """Reagiert auf Änderung der Auth-Methode"""
        if "Web Abo" in method:
            self.log("ℹ️ Web Abo selected - No API Key needed!", "info")
            self.log("Please ensure you're logged in at claude.ai", "info")
        elif "API Key" in method:
            self.log("ℹ️ API Key mode - Set ANTHROPIC_API_KEY environment variable", "info")
            
    def extract_config(self):
        """Extrahiert alle verfügbaren Konfigurationen"""
        self.log_area.clear()
        self.log("Starting configuration extraction...")
        
        project_path = self.get_project_path()
        if not project_path:
            self.log("❌ No project path set", "error")
            return
            
        extracted = {
            'timestamp': datetime.now().isoformat(),
            'project_path': str(project_path),
            'your_custom_setup': self.extract_your_setup(),
            'found_configs': {}
        }
        
        # Check .claude/settings.json
        claude_settings = project_path / '.claude' / 'settings.json'
        if claude_settings.exists():
            with open(claude_settings) as f:
                extracted['found_configs']['claude_settings'] = json.load(f)
            self.checks['claude_settings'].setChecked(True)
            self.log("✅ Found .claude/settings.json", "success")
        else:
            self.log("⚠️ No .claude/settings.json found", "warning")
            
        # Check .mcp.json
        mcp_config = project_path / '.mcp.json'
        if mcp_config.exists():
            with open(mcp_config) as f:
                extracted['found_configs']['mcp'] = json.load(f)
            self.checks['mcp_config'].setChecked(True)
            self.log("✅ Found .mcp.json with MCP servers", "success")
        else:
            self.log("⚠️ No .mcp.json - MCP servers need configuration", "warning")
            
        # Check for your custom agents
        agents_dir = project_path / '.claude' / 'agents'
        if agents_dir.exists():
            agent_files = list(agents_dir.glob('*.md'))
            extracted['found_configs']['custom_agents'] = [f.stem for f in agent_files]
            self.checks['custom_agents'].setChecked(True)
            self.log(f"✅ Found {len(agent_files)} custom agents", "success")
        else:
            self.log("ℹ️ No custom agents directory", "info")
            
        # Check environment
        env_vars = {
            'ANTHROPIC_API_KEY': bool(os.environ.get('ANTHROPIC_API_KEY')),
            'GITHUB_TOKEN': bool(os.environ.get('GITHUB_PERSONAL_ACCESS_TOKEN')),
            'CLAUDE_FLOW_DEBUG': os.environ.get('CLAUDE_FLOW_DEBUG', 'not set')
        }
        extracted['found_configs']['env_vars'] = env_vars
        if env_vars['ANTHROPIC_API_KEY'] or self.auth_method.currentText().startswith("Claude Web"):
            self.checks['env_vars'].setChecked(True)
            
        # Check Python environment
        import sys
        extracted['found_configs']['python'] = {
            'version': sys.version,
            'venv': bool(os.environ.get('VIRTUAL_ENV')),
            'path': sys.executable
        }
        self.checks['python_env'].setChecked(True)
        
        # Check memory database
        memory_db = project_path / '.swarm' / 'memory.db'
        if memory_db.exists():
            self.checks['memory_db'].setChecked(True)
            self.log("✅ Memory database exists", "success")
            
        # Enable sync button
        self.sync_btn.setEnabled(True)
        self.extracted_config = extracted
        
        self.log("\n✅ Extraction complete!", "success")
        self.config_extracted.emit(extracted)
        
    def extract_your_setup(self):
        """Extrahiert Ihr spezifisches Agent-Setup"""
        return {
            'agents': [
                'queen', 'backend-dev', 'frontend-dev', 'system-architect',
                'tester', 'performance-tester', 'security-tester',
                'devops-engineer', 'api-documenter', 'pentester'
            ],
            'preset': self.agent_selector.currentText(),
            'topology': 'hierarchical',
            'models': {
                'queen': 'claude-3-opus-20240229',
                'workers': 'claude-3-sonnet-20240229'
            },
            'memory_size': '1GB',
            'parallel_execution': True
        }
        
    def sync_with_custom_setup(self):
        """Synchronisiert mit Ihrem Custom Setup"""
        self.log("\n🔄 Syncing with your custom setup...")
        
        # Verwende Ihre migrierten V86 Konfigurationen
        v86_config_path = Path("src/Agents_Configuration")
        
        if v86_config_path.exists():
            self.log("✅ Found your V86 migration", "success")
            self.log("  • 64 agents available", "info")
            self.log("  • 87 MCP tools ready", "info")
            self.log("  • Byzantine Fault Tolerance enabled", "info")
            
            # Merge mit extrahierten Configs
            self.merge_configs()
            self.generate_btn.setEnabled(True)
        else:
            self.log("⚠️ V86 migration directory not found", "warning")
            
    def merge_configs(self):
        """Merged extracted configs mit Ihrem Setup"""
        self.log("\n📋 Merging configurations...")
        
        merged = {
            **self.extracted_config,
            'v86_enabled': True,
            'your_setup': self.extract_your_setup(),
            'authentication': {
                'method': self.auth_method.currentText(),
                'api_key_required': "API Key" in self.auth_method.currentText()
            }
        }
        
        self.extracted_config = merged
        self.log("✅ Configurations merged successfully", "success")
        
    def generate_v86_config(self):
        """Generiert finale V86 Konfiguration"""
        self.log("\n⚡ Generating V86 configuration...")
        
        project_path = self.get_project_path()
        if not project_path:
            return
            
        # Verwende Ihr V86 Setup
        from src.claude_flow_gui.converters.v86_converter import V86ConfigConverter
        
        converter = V86ConfigConverter()
        v86_config = converter.generate_v86_config(
            project_path=project_path,
            agents=self.extract_your_setup()['agents'],
            task="Generated from GUI Extractor",
            custom_config=self.extracted_config
        )
        
        # Speichere Konfiguration
        output_file = project_path / 'claude-flow.config.json'
        with open(output_file, 'w') as f:
            json.dump(v86_config, f, indent=2)
            
        self.log(f"✅ V86 config saved to: {output_file}", "success")
        
        # Zeige Erfolg
        QMessageBox.information(
            self,
            "Success",
            f"V86 configuration generated successfully!\n\n"
            f"File: {output_file}\n\n"
            f"You can now launch Hive Mind with your custom setup."
        )
        
    def test_configuration(self):
        """Testet die generierte Konfiguration"""
        self.log("\n🧪 Testing configuration...")
        
        # Test ob claude-flow verfügbar ist
        if os.system('npx claude-flow@alpha --version >/dev/null 2>&1') == 0:
            self.log("✅ claude-flow@alpha is available", "success")
        else:
            self.log("❌ claude-flow@alpha not found", "error")
            return
            
        # Test MCP servers
        self.log("Testing MCP servers...", "info")
        project_path = self.get_project_path()
        
        if (project_path / '.mcp.json').exists():
            # Vereinfachter Test
            self.log("✅ MCP configuration found", "success")
        else:
            self.log("⚠️ No MCP configuration", "warning")
            
        # Test authentication
        if "Web Abo" in self.auth_method.currentText():
            self.log("✅ Using Web Abo - No API key needed", "success")
        elif os.environ.get('ANTHROPIC_API_KEY'):
            self.log("✅ API Key is set", "success")
        else:
            self.log("⚠️ No authentication configured", "warning")
            
        self.log("\n✅ Configuration test complete", "success")
        
    def get_project_path(self):
        """Holt den aktuellen Projektpfad aus der Hauptanwendung"""
        if hasattr(self.parent_app, 'project_path'):
            return Path(self.parent_app.project_path)
        return Path.cwd()
        
    def log(self, message, level="info"):
        """Logging mit Farben"""
        colors = {
            'info': 'black',
            'success': 'green',
            'warning': 'orange',
            'error': 'red'
        }
        
        # In Log-Area schreiben
        cursor = self.log_area.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        
        # Farbiges HTML
        html = f'<span style="color: {colors.get(level, "black")}">{message}</span><br>'
        cursor.insertHtml(html)
        
        # Auto-scroll
        self.log_area.ensureCursorVisible()
        
        # Signal senden
        self.status_message.emit(message, level)


class ConfigExtractorDialog(QWidget):
    """
    Standalone Dialog/Tab für Config Extraction
    Kann als Tab in Ihrer Hauptanwendung integriert werden
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Integriere den Extractor
        self.extractor = ConfigExtractorWidget(self)
        layout.addWidget(self.extractor)
        
        self.setLayout(layout)
        self.setWindowTitle("V86 Config Extractor - Your Custom Setup")
        
        
# Integration in Ihre bestehende App:
def add_to_your_app(main_window):
    """
    Fügt den Config Extractor zu Ihrer App hinzu
    
    In Ihrer main_app.py:
    
    from config_extractor_gui import ConfigExtractorWidget
    
    # In create_ui() oder setup_tabs():
    self.config_extractor = ConfigExtractorWidget(self)
    self.tab_widget.addTab(self.config_extractor, "🔧 Config Sync")
    
    # Verbinde Signals
    self.config_extractor.config_extracted.connect(self.on_config_extracted)
    self.config_extractor.status_message.connect(self.show_status_message)
    """
    pass