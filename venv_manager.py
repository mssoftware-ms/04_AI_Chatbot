#!/usr/bin/env python3
"""
Virtual Environment Manager
Ensures all projects run in virtual environments with proper dependency management.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import List, Optional


class VenvManager:
    """Manages virtual environments for Python projects."""
    
    def __init__(self, project_dir: Optional[str] = None):
        """Initialize the virtual environment manager.
        
        Args:
            project_dir: Project directory path. Defaults to current directory.
        """
        self.project_dir = Path(project_dir) if project_dir else Path.cwd()
        self.venv_dir = self.project_dir / "venv"
        self.requirements_file = self.project_dir / "requirements.txt"
        self.test_requirements_file = self.project_dir / "requirements_test.txt"
        
        # Platform-specific executables
        if sys.platform == "win32":
            self.python_exe = self.venv_dir / "Scripts" / "python.exe"
            self.pip_exe = self.venv_dir / "Scripts" / "pip.exe"
        else:
            self.python_exe = self.venv_dir / "bin" / "python"
            self.pip_exe = self.venv_dir / "bin" / "pip"
    
    def venv_exists(self) -> bool:
        """Check if virtual environment exists."""
        return self.venv_dir.exists() and self.python_exe.exists()
    
    def create_venv(self) -> bool:
        """Create virtual environment if it doesn't exist.
        
        Returns:
            True if successful, False otherwise.
        """
        if self.venv_exists():
            print(f"✓ Virtual environment already exists at {self.venv_dir}")
            return True
        
        print(f"Creating virtual environment at {self.venv_dir}...")
        
        try:
            # Remove existing venv directory if it's partially created
            if self.venv_dir.exists():
                shutil.rmtree(self.venv_dir)
            
            # Create virtual environment (Windows-compatible, no symlinks)
            venv_args = [sys.executable, "-m", "venv", str(self.venv_dir)]
            
            # Force Windows mode - no symlinks that cause permission errors
            if sys.platform == "win32":
                venv_args.append("--copies")  # Use copies instead of symlinks
            
            result = subprocess.run(venv_args, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"✗ Failed to create virtual environment: {result.stderr}")
                return False
            
            # Windows compatibility fix: Remove problematic lib64 symlink
            lib64_path = self.venv_dir / "lib64"
            if lib64_path.exists() and lib64_path.is_symlink():
                try:
                    lib64_path.unlink()  # Remove symlink
                    print("✓ Removed lib64 symlink for Windows compatibility")
                except Exception as e:
                    print(f"⚠ Warning: Could not remove lib64 symlink: {e}")
            
            print(f"✓ Virtual environment created successfully at {self.venv_dir}")
            return True
            
        except Exception as e:
            print(f"✗ Error creating virtual environment: {e}")
            return False
    
    def install_requirements(self, requirements_files: Optional[List[str]] = None) -> bool:
        """Install requirements from requirements files.
        
        Args:
            requirements_files: List of requirements files to install.
                              Defaults to ['requirements.txt', 'requirements_test.txt']
        
        Returns:
            True if successful, False otherwise.
        """
        if not self.venv_exists():
            print("✗ Virtual environment doesn't exist. Create it first.")
            return False
        
        if requirements_files is None:
            requirements_files = ["requirements.txt", "requirements_test.txt"]
        
        success = True
        
        for req_file in requirements_files:
            req_path = self.project_dir / req_file
            
            if not req_path.exists():
                print(f"⚠ Requirements file not found: {req_path}")
                continue
            
            print(f"Installing requirements from {req_file}...")
            
            try:
                result = subprocess.run([
                    str(self.pip_exe), "install", "-r", str(req_path)
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    print(f"✗ Failed to install {req_file}: {result.stderr}")
                    success = False
                else:
                    print(f"✓ Successfully installed requirements from {req_file}")
                    
            except Exception as e:
                print(f"✗ Error installing {req_file}: {e}")
                success = False
        
        return success
    
    def reinstall_requirements(self, requirements_files: Optional[List[str]] = None) -> bool:
        """Reinstall requirements (force reinstall).
        
        Args:
            requirements_files: List of requirements files to reinstall.
        
        Returns:
            True if successful, False otherwise.
        """
        if not self.venv_exists():
            print("✗ Virtual environment doesn't exist. Create it first.")
            return False
        
        if requirements_files is None:
            requirements_files = ["requirements.txt", "requirements_test.txt"]
        
        success = True
        
        for req_file in requirements_files:
            req_path = self.project_dir / req_file
            
            if not req_path.exists():
                print(f"⚠ Requirements file not found: {req_path}")
                continue
            
            print(f"Reinstalling requirements from {req_file}...")
            
            try:
                result = subprocess.run([
                    str(self.pip_exe), "install", "--force-reinstall", 
                    "--no-deps", "-r", str(req_path)
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    print(f"✗ Failed to reinstall {req_file}: {result.stderr}")
                    success = False
                else:
                    print(f"✓ Successfully reinstalled requirements from {req_file}")
                    
            except Exception as e:
                print(f"✗ Error reinstalling {req_file}: {e}")
                success = False
        
        return success
    
    def upgrade_pip(self) -> bool:
        """Upgrade pip in the virtual environment.
        
        Returns:
            True if successful, False otherwise.
        """
        if not self.venv_exists():
            print("✗ Virtual environment doesn't exist. Create it first.")
            return False
        
        print("Upgrading pip...")
        
        try:
            result = subprocess.run([
                str(self.python_exe), "-m", "pip", "install", "--upgrade", "pip"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"✗ Failed to upgrade pip: {result.stderr}")
                return False
            
            print("✓ Pip upgraded successfully")
            return True
            
        except Exception as e:
            print(f"✗ Error upgrading pip: {e}")
            return False
    
    def run_python_script(self, script_path: str, *args) -> int:
        """Run a Python script using the virtual environment.
        
        Args:
            script_path: Path to the Python script to run.
            *args: Additional arguments to pass to the script.
        
        Returns:
            Exit code of the script.
        """
        if not self.venv_exists():
            print("✗ Virtual environment doesn't exist. Setting up...")
            if not self.setup_project():
                print("✗ Failed to set up project. Cannot run script.")
                return 1
        
        script_full_path = self.project_dir / script_path
        
        if not script_full_path.exists():
            print(f"✗ Script not found: {script_full_path}")
            return 1
        
        print(f"Running {script_path} in virtual environment...")
        
        try:
            # Run the script with the virtual environment Python
            result = subprocess.run([
                str(self.python_exe), str(script_full_path), *args
            ])
            return result.returncode
            
        except Exception as e:
            print(f"✗ Error running script: {e}")
            return 1
    
    def setup_project(self) -> bool:
        """Complete project setup: create venv, upgrade pip, install requirements.
        
        Returns:
            True if successful, False otherwise.
        """
        print("🚀 Setting up project with virtual environment...")
        
        # Create virtual environment
        if not self.create_venv():
            return False
        
        # Upgrade pip
        if not self.upgrade_pip():
            print("⚠ Failed to upgrade pip, continuing anyway...")
        
        # Install requirements
        if not self.install_requirements():
            print("⚠ Some requirements failed to install")
            return False
        
        print("✓ Project setup completed successfully!")
        return True
    
    def get_activation_command(self) -> str:
        """Get the command to activate the virtual environment.
        
        Returns:
            Activation command string.
        """
        if sys.platform == "win32":
            return f"{self.venv_dir}\\Scripts\\activate.bat"
        else:
            return f"source {self.venv_dir}/bin/activate"
    
    def show_status(self):
        """Show virtual environment status."""
        print(f"📁 Project directory: {self.project_dir}")
        print(f"🐍 Virtual environment: {self.venv_dir}")
        print(f"📦 Virtual environment exists: {'✓' if self.venv_exists() else '✗'}")
        print(f"📋 Requirements file: {'✓' if self.requirements_file.exists() else '✗'}")
        print(f"🧪 Test requirements file: {'✓' if self.test_requirements_file.exists() else '✗'}")
        
        if self.venv_exists():
            print(f"🔧 Python executable: {self.python_exe}")
            print(f"📦 Pip executable: {self.pip_exe}")
            print(f"⚡ Activation command: {self.get_activation_command()}")


def main():
    """Main entry point for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Virtual Environment Manager")
    parser.add_argument("--project-dir", help="Project directory path")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Set up project with venv")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create virtual environment")
    
    # Install command
    install_parser = subparsers.add_parser("install", help="Install requirements")
    install_parser.add_argument("--files", nargs="+", help="Requirements files to install")
    
    # Reinstall command
    reinstall_parser = subparsers.add_parser("reinstall", help="Reinstall requirements")
    reinstall_parser.add_argument("--files", nargs="+", help="Requirements files to reinstall")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run Python script in venv")
    run_parser.add_argument("script", help="Python script to run")
    run_parser.add_argument("args", nargs="*", help="Script arguments")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show venv status")
    
    args = parser.parse_args()
    
    # Create venv manager instance
    venv_manager = VenvManager(args.project_dir)
    
    if args.command == "setup":
        success = venv_manager.setup_project()
        sys.exit(0 if success else 1)
    
    elif args.command == "create":
        success = venv_manager.create_venv()
        sys.exit(0 if success else 1)
    
    elif args.command == "install":
        success = venv_manager.install_requirements(args.files)
        sys.exit(0 if success else 1)
    
    elif args.command == "reinstall":
        success = venv_manager.reinstall_requirements(args.files)
        sys.exit(0 if success else 1)
    
    elif args.command == "run":
        exit_code = venv_manager.run_python_script(args.script, *args.args)
        sys.exit(exit_code)
    
    elif args.command == "status":
        venv_manager.show_status()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()