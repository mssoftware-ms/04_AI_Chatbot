"""
Angepasster Workflow für Ihr spezifisches Agent-Setup
Basierend auf Ihrer V86 Migration und Custom Agents
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List

class CustomWorkflowManager:
    """
    Workflow-Manager für Ihr spezifisches Setup
    """
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        
        # Ihre spezifischen Agenten aus der Migration
        self.your_agents = {
            "queen": {
                "model": "claude-3-opus-20240229",
                "role": "Strategic Coordinator",
                "priority": "critical"
            },
            "backend-dev": {
                "model": "claude-3-sonnet-20240229",
                "role": "Python Development",
                "capabilities": ["Django", "FastAPI", "SQLAlchemy"]
            },
            "frontend-dev": {
                "model": "claude-3-sonnet-20240229",
                "role": "UI Development",
                "capabilities": ["React", "Vue", "TypeScript"]
            },
            "system-architect": {
                "model": "claude-3-sonnet-20240229",
                "role": "Architecture Design"
            },
            "tester": {
                "model": "claude-3-sonnet-20240229",
                "role": "Test Automation",
                "tools": ["pytest", "unittest", "selenium"]
            },
            "performance-tester": {
                "model": "claude-3-sonnet-20240229",
                "role": "Performance Analysis"
            },
            "security-tester": {
                "model": "claude-3-sonnet-20240229",
                "role": "Security Audit",
                "priority": "high"
            },
            "devops-engineer": {
                "model": "claude-3-sonnet-20240229",
                "role": "CI/CD Pipeline"
            },
            "api-documenter": {
                "model": "claude-3-sonnet-20240229",
                "role": "Documentation"
            },
            "pentester": {
                "model": "claude-3-sonnet-20240229",
                "role": "Penetration Testing",
                "restricted": True
            }
        }
        
        # Authentifizierungs-Methode
        self.auth_method = self.detect_auth_method()
        
    def detect_auth_method(self) -> str:
        """
        Erkennt verfügbare Authentifizierungsmethode
        """
        # Check für API Key
        if os.environ.get('ANTHROPIC_API_KEY'):
            return "api_key"
            
        # Check für Claude CLI (Web Abo)
        if os.system('which claude >/dev/null 2>&1') == 0:
            return "web_abo"
            
        # Check für Browser Session
        if os.path.exists(os.path.expanduser('~/.claude')):
            return "browser_session"
            
        return "none"
        
    def prepare_launch_command(self, task: str, selected_agents: List[str]) -> str:
        """
        Bereitet den Launch-Command basierend auf Auth-Methode vor
        """
        
        # Basis-Command
        cmd = "npx claude-flow@alpha hive-mind spawn"
        
        # Task hinzufügen
        cmd += f" '{task}'"
        
        # Config-Datei
        config_file = self.generate_config_for_task(task, selected_agents)
        cmd += f" --config '{config_file}'"
        
        # Auth-spezifische Parameter
        if self.auth_method == "web_abo":
            # Für Web-Abo Nutzer
            cmd += " --claude"  # Nutzt Claude Code CLI
            print("ℹ️ Using Claude Web Abo - No API Key needed!")
            print("Please ensure you're logged in at claude.ai")
            
        elif self.auth_method == "api_key":
            # Für API Key Nutzer
            cmd += " --api-key"
            
        else:
            print("⚠️ No authentication detected!")
            print("Please either:")
            print("1. Login to claude.ai (for Web Abo)")
            print("2. Set ANTHROPIC_API_KEY environment variable")
            return None
            
        # Ihre spezifischen Optionen
        cmd += " --verbose"
        cmd += " --memory-enabled"
        cmd += " --parallel-execution"
        cmd += " --topology hierarchical"
        
        # Modelle basierend auf Ihrem Setup
        cmd += " --queen-model claude-3-opus-20240229"
        cmd += " --worker-model claude-3-sonnet-20240229"
        
        return cmd
        
    def generate_config_for_task(self, task: str, selected_agents: List[str]) -> str:
        """
        Generiert V86 Config für spezifische Task
        """
        config = {
            "name": f"Task: {task[:50]}...",
            "version": "2.0.0-alpha.86",
            "timestamp": datetime.now().isoformat(),
            "authentication": {
                "method": self.auth_method,
                "api_key_required": self.auth_method == "api_key"
            },
            "project": {
                "path": str(self.project_path),
                "name": "01_AI_Coding_Station - Python Development"
            },
            "agents": {
                "selected": selected_agents,
                "specifications": {
                    agent: self.your_agents[agent]
                    for agent in selected_agents
                    if agent in self.your_agents
                }
            },
            "orchestrator": {
                "maxAgents": len(selected_agents),
                "topology": "hierarchical",
                "memoryEnabled": True
            },
            "mcp": {
                "enabled": True,
                "servers": self.get_mcp_servers()
            }
        }
        
        # Speichere Config
        output_file = self.project_path / f".claude-flow/configs/task_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(config, f, indent=2)
            
        return str(output_file)
        
    def get_mcp_servers(self) -> Dict:
        """
        Holt MCP Server Config (falls vorhanden)
        """
        mcp_file = self.project_path / '.mcp.json'
        if mcp_file.exists():
            with open(mcp_file) as f:
                data = json.load(f)
                return data.get('mcpServers', {})
        return {}
        
    def execute_workflow(self, task: str, agent_preset: str = "default"):
        """
        Führt Ihren angepassten Workflow aus
        """
        print("="*60)
        print("🚀 Starting Your Custom Workflow")
        print("="*60)
        
        # Wähle Agenten basierend auf Preset
        if agent_preset == "python_development":
            selected_agents = [
                "queen", "backend-dev", "tester", 
                "api-documenter", "devops-engineer"
            ]
        elif agent_preset == "security_audit":
            selected_agents = [
                "queen", "security-tester", "pentester",
                "system-architect"
            ]
        elif agent_preset == "full_stack":
            selected_agents = list(self.your_agents.keys())
        else:
            selected_agents = ["queen", "backend-dev", "tester"]
            
        print(f"📋 Task: {task}")
        print(f"🤖 Selected Agents: {', '.join(selected_agents)}")
        print(f"🔐 Authentication: {self.auth_method}")
        
        # Generiere Command
        cmd = self.prepare_launch_command(task, selected_agents)
        
        if cmd:
            print("\n📝 Generated Command:")
            print(cmd)
            
            # Optional: Direkt ausführen
            if input("\nExecute command? (y/n): ").lower() == 'y':
                os.system(cmd)
        else:
            print("❌ Cannot proceed without authentication")
            
            
# Beispiel-Verwendung in Ihrer App
def integrate_with_your_app():
    """
    Integration in Ihre bestehende PyQt6 App
    """
    
    # In Ihrer Hive-Launch Methode:
    project_path = "D:\\03_Git\\02_Python\\01_AI_Coding_Station"
    workflow = CustomWorkflowManager(project_path)
    
    # Ihre Task aus der UI
    task = "Im fenster Launch hive, steht hinter Console output..."
    
    # Ihr Agent-Preset
    preset = "python_development"
    
    # Workflow ausführen
    workflow.execute_workflow(task, preset)
    

# Standalone Test
if __name__ == "__main__":
    # Test mit Ihrem Setup
    manager = CustomWorkflowManager("/mnt/d/03_Git/02_Python/01_AI_Coding_Station")
    
    print("Your Authentication Method:", manager.auth_method)
    print("Your Agents:", list(manager.your_agents.keys()))
    
    # Test-Task
    test_task = "Implement a REST API with authentication"
    manager.execute_workflow(test_task, "python_development")