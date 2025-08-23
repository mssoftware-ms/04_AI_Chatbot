"""
PyQt6 Integration für claude-flow v2.0.0-alpha.90
Nutzt Claude Web Abo (kein API Key nötig!)
"""

import subprocess
import json
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal
from typing import List, Dict, Optional

class ClaudeFlowV90Launcher(QThread):
    """
    Thread-safe Launcher für claude-flow v90 mit Ihrem Setup
    """
    
    # Signals für GUI Updates
    output_received = pyqtSignal(str)
    status_changed = pyqtSignal(str, str)  # status, color
    command_generated = pyqtSignal(str)
    
    def __init__(self, project_path: str = "/mnt/d/03_Git/02_Python/01_AI_Coding_Station"):
        super().__init__()
        self.project_path = Path(project_path)
        self.process = None
        
        # Ihre 10 Agenten
        self.available_agents = [
            "queen", "backend-dev", "frontend-dev", "system-architect",
            "tester", "performance-tester", "security-tester",
            "devops-engineer", "api-documenter", "pentester"
        ]
        
        # Verifiziere Versionen
        self.claude_version = self.get_claude_version()
        self.flow_version = self.get_flow_version()
        
    def get_claude_version(self) -> str:
        """Holt Claude Code Version"""
        try:
            result = subprocess.run(['claude', '--version'], 
                                  capture_output=True, text=True)
            return result.stdout.strip()
        except:
            return "Not installed"
            
    def get_flow_version(self) -> str:
        """Holt claude-flow Version"""
        try:
            result = subprocess.run(['npx', 'claude-flow@alpha', '--version'], 
                                  capture_output=True, text=True)
            return result.stdout.strip()
        except:
            return "Not installed"
            
    def build_command(self, 
                      task: str,
                      agents: List[str],
                      options: Dict = None) -> str:
        """
        Baut den claude-flow Command
        
        Args:
            task: Die Aufgabe
            agents: Liste der zu verwendenden Agenten
            options: Zusätzliche Optionen
        """
        
        # Basis Command
        cmd_parts = [
            'npx', 'claude-flow@alpha', 'hive-mind', 'spawn',
            f'"{task}"'
        ]
        
        # Agenten hinzufügen
        if agents:
            cmd_parts.append(f'--agents {",".join(agents)}')
            
        # Standard-Optionen für Web-Abo
        cmd_parts.extend([
            '--claude',  # WICHTIG: Nutzt Claude Code CLI (kein API Key!)
            '--verbose'
        ])
        
        # Weitere Optionen
        if options:
            if options.get('memory', True):
                cmd_parts.append('--memory persistent')
            if options.get('parallel', True):
                cmd_parts.append('--parallel')
            if options.get('neural', False):
                cmd_parts.append('--neural-enabled')
            if options.get('mcp', True):
                cmd_parts.append('--mcp-enabled')
            if options.get('telemetry', False):
                cmd_parts.append('--telemetry enabled')
            if options.get('topology'):
                cmd_parts.append(f'--topology {options["topology"]}')
                
        # Modelle (Ihre Konfiguration)
        cmd_parts.append('--queen-model claude-3-opus-20240229')
        cmd_parts.append('--worker-model claude-3-sonnet-20240229')
        
        command = ' '.join(cmd_parts)
        self.command_generated.emit(command)
        return command
        
    def launch_quick_task(self, task: str):
        """
        Schnell-Launch mit Standard-Agenten
        """
        agents = ["queen", "backend-dev", "tester"]
        command = self.build_command(task, agents)
        return self.execute_command(command)
        
    def launch_python_development(self, task: str):
        """
        Python-Entwicklung Preset
        """
        agents = ["queen", "backend-dev", "tester", "api-documenter", "devops-engineer"]
        options = {
            'memory': True,
            'parallel': True,
            'mcp': True,
            'topology': 'hierarchical'
        }
        command = self.build_command(task, agents, options)
        return self.execute_command(command)
        
    def launch_security_audit(self, task: str):
        """
        Security Audit Preset
        """
        agents = ["queen", "security-tester", "pentester", "system-architect"]
        options = {
            'memory': True,
            'parallel': False,  # Sequential für Security
            'topology': 'mesh',
            'sandboxed': True
        }
        command = self.build_command(task, agents, options)
        return self.execute_command(command)
        
    def launch_full_team(self, task: str):
        """
        Alle 10 Agenten
        """
        command = self.build_command(task, self.available_agents)
        return self.execute_command(command)
        
    def execute_command(self, command: str) -> bool:
        """
        Führt Command aus mit Live-Output
        """
        try:
            self.status_changed.emit("🚀 Starting claude-flow...", "green")
            
            # Change to project directory
            import os
            os.chdir(self.project_path)
            
            # Execute with live output
            self.process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            # Stream output
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    self.output_received.emit(line.strip())
                    
            self.process.wait()
            
            if self.process.returncode == 0:
                self.status_changed.emit("✅ Task completed successfully", "green")
                return True
            else:
                self.status_changed.emit(f"❌ Task failed (code: {self.process.returncode})", "red")
                return False
                
        except Exception as e:
            self.status_changed.emit(f"❌ Error: {str(e)}", "red")
            return False
            
    def stop(self):
        """Stoppt laufenden Prozess"""
        if self.process:
            self.process.terminate()
            self.status_changed.emit("⏹ Process stopped", "orange")


class ClaudeFlowWidget(QWidget):
    """
    GUI Widget für Ihre PyQt6 App
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.launcher = ClaudeFlowV90Launcher()
        self.init_ui()
        
    def init_ui(self):
        from PyQt6.QtWidgets import (
            QVBoxLayout, QHBoxLayout, QTextEdit, 
            QPushButton, QComboBox, QLabel, QCheckBox
        )
        
        layout = QVBoxLayout()
        
        # Version Info
        version_label = QLabel(
            f"Claude: {self.launcher.claude_version} | "
            f"Flow: {self.launcher.flow_version}"
        )
        layout.addWidget(version_label)
        
        # Task Input
        self.task_input = QTextEdit()
        self.task_input.setPlaceholderText("Enter your task...")
        self.task_input.setMaximumHeight(100)
        layout.addWidget(QLabel("Task:"))
        layout.addWidget(self.task_input)
        
        # Preset Selection
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "Quick (3 agents)",
            "Python Development (5 agents)",
            "Security Audit (4 agents)",
            "Full Team (10 agents)",
            "Custom Selection"
        ])
        layout.addWidget(QLabel("Preset:"))
        layout.addWidget(self.preset_combo)
        
        # Options
        options_layout = QHBoxLayout()
        self.memory_check = QCheckBox("Persistent Memory")
        self.memory_check.setChecked(True)
        self.parallel_check = QCheckBox("Parallel Execution")
        self.parallel_check.setChecked(True)
        self.mcp_check = QCheckBox("MCP Tools")
        self.mcp_check.setChecked(True)
        
        options_layout.addWidget(self.memory_check)
        options_layout.addWidget(self.parallel_check)
        options_layout.addWidget(self.mcp_check)
        layout.addLayout(options_layout)
        
        # Launch Buttons
        button_layout = QHBoxLayout()
        
        self.launch_btn = QPushButton("🚀 Launch Hive Mind")
        self.launch_btn.clicked.connect(self.launch_task)
        button_layout.addWidget(self.launch_btn)
        
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.clicked.connect(self.launcher.stop)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)
        
        layout.addLayout(button_layout)
        
        # Output
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        layout.addWidget(QLabel("Output:"))
        layout.addWidget(self.output_text)
        
        # Status
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
        # Connect signals
        self.launcher.output_received.connect(self.append_output)
        self.launcher.status_changed.connect(self.update_status)
        self.launcher.command_generated.connect(self.show_command)
        
    def launch_task(self):
        """Startet Task basierend auf Preset"""
        task = self.task_input.toPlainText().strip()
        if not task:
            self.update_status("Please enter a task", "red")
            return
            
        preset = self.preset_combo.currentText()
        
        # Disable launch, enable stop
        self.launch_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
        # Clear output
        self.output_text.clear()
        
        # Launch based on preset
        if "Quick" in preset:
            self.launcher.launch_quick_task(task)
        elif "Python Development" in preset:
            self.launcher.launch_python_development(task)
        elif "Security Audit" in preset:
            self.launcher.launch_security_audit(task)
        elif "Full Team" in preset:
            self.launcher.launch_full_team(task)
        else:
            # Custom selection
            self.launcher.launch_quick_task(task)
            
    def append_output(self, text):
        """Fügt Output hinzu"""
        self.output_text.append(text)
        
    def update_status(self, text, color):
        """Update Status Label"""
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color};")
        
        # Re-enable buttons wenn fertig
        if "completed" in text.lower() or "failed" in text.lower():
            self.launch_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            
    def show_command(self, command):
        """Zeigt generierten Command"""
        self.output_text.append(f"📝 Command: {command}\n")


# Integration in Ihre bestehende App:
def integrate_into_your_app(main_window):
    """
    So fügen Sie es zu Ihrer App hinzu:
    
    from claude_flow_v90_integration import ClaudeFlowWidget
    
    # In Ihrer main_app.py:
    self.claude_flow_widget = ClaudeFlowWidget(self)
    self.tab_widget.addTab(self.claude_flow_widget, "🚀 Claude-Flow v90")
    """
    pass


# Standalone Test
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication, QMainWindow
    import sys
    
    app = QApplication(sys.argv)
    
    window = QMainWindow()
    window.setWindowTitle("Claude-Flow v90 Launcher")
    
    widget = ClaudeFlowWidget()
    window.setCentralWidget(widget)
    
    window.resize(800, 600)
    window.show()
    
    sys.exit(app.exec())