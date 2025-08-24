#!/usr/bin/env python3
"""
Universal Project Launcher
FORCES virtual environment usage for 04_AI_Chatbot
"""

import os
import sys
from pathlib import Path

# Add current directory to path for venv_manager import
sys.path.insert(0, str(Path(__file__).parent))

try:
    from venv_manager import VenvManager
except ImportError:
    print("✗ venv_manager.py not found. Please run universal_venv_setup.py first.")
    sys.exit(1)

def main():
    """Main launcher that enforces venv usage."""
    project_dir = Path(__file__).parent
    venv_manager = VenvManager(str(project_dir))
    
    # Show current status
    print(f"🚀 Starting {project_dir.name} with virtual environment enforcement...")
    venv_manager.show_status()
    
    # Ensure venv exists and is set up
    if not venv_manager.venv_exists():
        print("\n📦 Setting up virtual environment...")
        if not venv_manager.setup_project():
            print("✗ Failed to set up virtual environment. Exiting.")
            sys.exit(1)
    
    # Run the main Python file
    python_file = "start_windows.py"
    if not python_file or not Path(python_file).exists():
        # Try to find main file
        for candidate in ["main.py", "app.py", "run.py"]:
            if (project_dir / candidate).exists():
                python_file = candidate
                break
        else:
            print("✗ No main Python file found. Please specify the file to run.")
            sys.exit(1)
    
    print(f"\n▶️ Running {python_file} in virtual environment...")
    exit_code = venv_manager.run_python_script(python_file, *sys.argv[1:])
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
