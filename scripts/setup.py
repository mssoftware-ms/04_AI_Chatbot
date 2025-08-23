#!/usr/bin/env python
"""Setup script for WhatsApp AI Chatbot."""

import os
import sys
import subprocess
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"🔧 {description}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"❌ Failed: {description}")
        sys.exit(1)
    print(f"✅ Success: {description}")


def main():
    """Main setup function."""
    
    print("\n" + "="*60)
    print("🚀 WhatsApp AI Chatbot - Setup Script")
    print("="*60)
    
    # Check Python version
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ is required")
        sys.exit(1)
    
    # Create virtual environment if it doesn't exist
    venv_path = Path("venv")
    if not venv_path.exists():
        run_command(
            "python -m venv venv",
            "Creating virtual environment"
        )
    
    # Determine pip command based on OS
    if os.name == 'nt':  # Windows
        pip_cmd = "venv\\Scripts\\pip"
        python_cmd = "venv\\Scripts\\python"
    else:  # Unix/Linux/Mac
        pip_cmd = "venv/bin/pip"
        python_cmd = "venv/bin/python"
    
    # Upgrade pip
    run_command(
        f"{pip_cmd} install --upgrade pip",
        "Upgrading pip"
    )
    
    # Install requirements
    run_command(
        f"{pip_cmd} install -r requirements.txt",
        "Installing dependencies"
    )
    
    # Create necessary directories
    directories = [
        "data",
        "data/projects",
        "data/uploads",
        "brain/chroma",
        "logs",
        "assets"
    ]
    
    print(f"\n{'='*60}")
    print("📁 Creating directories")
    print(f"{'='*60}")
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {directory}")
    
    # Copy .env.example to .env if it doesn't exist
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        import shutil
        shutil.copy(env_example, env_file)
        print("\n⚠️  Created .env file from .env.example")
        print("⚠️  Please edit .env and add your API keys!")
    
    # Initialize database
    print(f"\n{'='*60}")
    print("🗄️ Initializing database")
    print(f"{'='*60}")
    
    init_db_script = f"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from src.database.session import DatabaseManager

async def init():
    db = DatabaseManager()
    await db.initialize()
    await db.close()
    print("✅ Database initialized")

asyncio.run(init())
"""
    
    with open("_temp_init_db.py", "w") as f:
        f.write(init_db_script)
    
    run_command(
        f"{python_cmd} _temp_init_db.py",
        "Database initialization"
    )
    
    # Clean up temp file
    os.remove("_temp_init_db.py")
    
    print("\n" + "="*60)
    print("✅ Setup completed successfully!")
    print("="*60)
    print("\n📝 Next steps:")
    print("1. Edit .env file and add your OpenAI API key")
    print("2. Optionally add GitHub token for repository integration")
    print("3. Run the application:")
    print(f"   {python_cmd} app.py")
    print("\nOr run individual components:")
    print(f"   {python_cmd} app.py backend  # Backend only")
    print(f"   {python_cmd} app.py ui       # UI only")
    print(f"   {python_cmd} app.py test     # Run tests")
    print("="*60)


if __name__ == "__main__":
    main()