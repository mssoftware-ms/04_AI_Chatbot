#!/usr/bin/env python3
"""
Auto-Run with Virtual Environment
Automatically sets up and runs project in venv
"""

import os
import sys
import subprocess
from pathlib import Path

def is_in_venv():
    """Check if currently running in virtual environment."""
    return (hasattr(sys, 'real_prefix') or 
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))

def main():
    """Main function that ensures venv usage."""
    project_dir = Path(__file__).parent
    
    print(f"🔍 Checking virtual environment for {project_dir.name}...")
    
    # If not in venv, use the launcher
    if not is_in_venv():
        print("⚠️  Not running in virtual environment. Using launcher...")
        launcher_script = project_dir / "run_project.py"
        
        if launcher_script.exists():
            # Use the launcher
            result = subprocess.run([sys.executable, str(launcher_script)] + sys.argv[1:])
            sys.exit(result.returncode)
        else:
            print("✗ run_project.py launcher not found. Please run universal_venv_setup.py")
            sys.exit(1)
    
    # Already in venv, run the project directly
    python_file = "start_windows.py"
    if not python_file or not Path(python_file).exists():
        # Try to find main file
        for candidate in ["main.py", "app.py", "run.py"]:
            if (project_dir / candidate).exists():
                python_file = candidate
                break
        else:
            print("✗ No main Python file found.")
            sys.exit(1)
    
    print(f"✓ Running {python_file} in virtual environment")
    
    # Import and run the main module
    spec = importlib.util.spec_from_file_location("main", python_file)
    main_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(main_module)

if __name__ == "__main__":
    import importlib.util
    main()
