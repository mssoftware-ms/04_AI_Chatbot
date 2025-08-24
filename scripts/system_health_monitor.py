#!/usr/bin/env python3
"""
System Health Monitor for WhatsApp AI Chatbot
Comprehensive monitoring and diagnostic tool for system health and performance.
"""

import sys
import os
import subprocess
import json
import time
import psutil
import sqlite3
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SystemHealthMonitor:
    """Comprehensive system health monitoring for the chatbot application."""
    
    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.data_dir = self.project_root / "data"
        self.logs_dir = self.project_root / "logs"
        self.venv_dir = self.project_root / "venv"
        
        # Health status tracking
        self.health_status = {
            "overall": "unknown",
            "timestamp": datetime.now().isoformat(),
            "components": {}
        }
        
    def check_python_environment(self) -> Dict:
        """Check Python environment health."""
        try:
            version_info = sys.version_info
            python_version = f"{version_info.major}.{version_info.minor}.{version_info.micro}"
            
            # Check if version meets requirements (3.11+)
            version_ok = version_info.major == 3 and version_info.minor >= 11
            
            # Check virtual environment
            venv_active = bool(os.environ.get('VIRTUAL_ENV'))
            venv_path = os.environ.get('VIRTUAL_ENV', 'Not activated')
            
            # Check virtual environment structure
            venv_exists = self.venv_dir.exists()
            venv_type = "unknown"
            
            if venv_exists:
                if (self.venv_dir / "bin" / "python").exists():
                    venv_type = "linux/wsl"
                elif (self.venv_dir / "Scripts" / "python.exe").exists():
                    venv_type = "windows"
                else:
                    venv_type = "invalid"
            
            status = "healthy" if version_ok and venv_active else "warning"
            
            return {
                "status": status,
                "python_version": python_version,
                "version_compatible": version_ok,
                "virtual_env_active": venv_active,
                "virtual_env_path": venv_path,
                "virtual_env_exists": venv_exists,
                "virtual_env_type": venv_type,
                "executable": sys.executable
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def check_dependencies(self) -> Dict:
        """Check Python package dependencies."""
        try:
            # Run pip check
            result = subprocess.run(
                [sys.executable, "-m", "pip", "check"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Check for specific packages
            key_packages = [
                "fastapi", "uvicorn", "flet", "sqlalchemy", 
                "openai", "anthropic", "chromadb", "langchain"
            ]
            
            installed_packages = {}
            missing_packages = []
            
            for package in key_packages:
                try:
                    pkg_result = subprocess.run(
                        [sys.executable, "-c", f"import {package}; print({package}.__version__)"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if pkg_result.returncode == 0:
                        installed_packages[package] = pkg_result.stdout.strip()
                    else:
                        missing_packages.append(package)
                except subprocess.TimeoutExpired:
                    missing_packages.append(package)
            
            conflicts = result.stderr.strip() if result.stderr else None
            has_conflicts = bool(conflicts)
            
            status = "error" if missing_packages else ("warning" if has_conflicts else "healthy")
            
            return {
                "status": status,
                "pip_check_success": result.returncode == 0,
                "conflicts": conflicts,
                "has_conflicts": has_conflicts,
                "installed_packages": installed_packages,
                "missing_packages": missing_packages,
                "total_installed": len(installed_packages),
                "total_missing": len(missing_packages)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def check_database(self) -> Dict:
        """Check database connectivity and health."""
        try:
            db_file = self.data_dir / "chatbot.db"
            chroma_dir = self.data_dir / "chroma"
            
            # Check SQLite database
            sqlite_status = "not_found"
            sqlite_size = 0
            table_count = 0
            
            if db_file.exists():
                sqlite_size = db_file.stat().st_size
                try:
                    with sqlite3.connect(str(db_file)) as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                        tables = cursor.fetchall()
                        table_count = len(tables)
                        sqlite_status = "healthy"
                except sqlite3.Error:
                    sqlite_status = "error"
            
            # Check ChromaDB
            chroma_status = "healthy" if chroma_dir.exists() else "not_found"
            chroma_collections = 0
            
            if chroma_dir.exists():
                try:
                    # Try to count collections (simplified check)
                    collection_dirs = [d for d in chroma_dir.iterdir() if d.is_dir()]
                    chroma_collections = len(collection_dirs)
                except:
                    chroma_status = "error"
            
            status = "healthy" if sqlite_status == "healthy" and chroma_status in ["healthy", "not_found"] else "warning"
            
            return {
                "status": status,
                "sqlite": {
                    "status": sqlite_status,
                    "file_exists": db_file.exists(),
                    "size_bytes": sqlite_size,
                    "size_mb": round(sqlite_size / (1024 * 1024), 2),
                    "table_count": table_count
                },
                "chromadb": {
                    "status": chroma_status,
                    "directory_exists": chroma_dir.exists(),
                    "collections": chroma_collections
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def check_services(self) -> Dict:
        """Check if application services are running."""
        try:
            api_port = int(os.environ.get('PORT', 8550))
            ui_port = int(os.environ.get('UI_PORT', 8551))
            
            # Check if ports are in use (indicates services running)
            api_running = self._is_port_in_use(api_port)
            ui_running = self._is_port_in_use(ui_port)
            
            # Try to make HTTP requests to services
            api_responding = False
            ui_responding = False
            
            if api_running:
                try:
                    response = requests.get(f"http://localhost:{api_port}/health", timeout=5)
                    api_responding = response.status_code == 200
                except:
                    pass
            
            if ui_running:
                try:
                    response = requests.get(f"http://localhost:{ui_port}", timeout=5)
                    ui_responding = response.status_code in [200, 404]  # 404 is OK for Flet
                except:
                    pass
            
            # Check for Python processes
            python_processes = self._get_python_processes()
            
            status = "healthy" if (api_running and ui_running) else ("partial" if (api_running or ui_running) else "stopped")
            
            return {
                "status": status,
                "api_server": {
                    "port": api_port,
                    "port_in_use": api_running,
                    "responding": api_responding
                },
                "ui_server": {
                    "port": ui_port,
                    "port_in_use": ui_running,
                    "responding": ui_responding
                },
                "python_processes": len(python_processes),
                "process_details": python_processes[:3]  # Limit to first 3
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def check_system_resources(self) -> Dict:
        """Check system resource utilization."""
        try:
            # Memory
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_gb = memory.available / (1024**3)
            
            # Disk
            disk = psutil.disk_usage(str(self.project_root))
            disk_percent = disk.percent
            disk_free_gb = disk.free / (1024**3)
            
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Load average (Unix only)
            try:
                load_avg = os.getloadavg()
            except (OSError, AttributeError):
                load_avg = None
            
            # Check resource thresholds
            memory_warning = memory_percent > 85
            disk_warning = disk_percent > 90
            cpu_warning = cpu_percent > 80
            
            status = "warning" if (memory_warning or disk_warning or cpu_warning) else "healthy"
            
            return {
                "status": status,
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory_available_gb, 2),
                    "used_percent": round(memory_percent, 1),
                    "warning": memory_warning
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk_free_gb, 2),
                    "used_percent": round(disk_percent, 1),
                    "warning": disk_warning
                },
                "cpu": {
                    "cores": cpu_count,
                    "usage_percent": round(cpu_percent, 1),
                    "load_average": load_avg,
                    "warning": cpu_warning
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def check_configuration(self) -> Dict:
        """Check application configuration."""
        try:
            env_file = self.project_root / ".env"
            config_file = self.project_root / "config" / "settings.py"
            
            # Check .env file
            env_exists = env_file.exists()
            env_variables = {}
            required_vars = ["OPENAI_API_KEY", "SECRET_KEY", "DATABASE_URL"]
            missing_vars = []
            
            if env_exists:
                try:
                    with open(env_file, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if '=' in line and not line.startswith('#'):
                                key, _ = line.split('=', 1)
                                env_variables[key] = "set"
                except:
                    pass
            
            for var in required_vars:
                if var not in env_variables and var not in os.environ:
                    missing_vars.append(var)
            
            # Check config file
            config_exists = config_file.exists()
            
            status = "warning" if missing_vars else ("healthy" if env_exists else "warning")
            
            return {
                "status": status,
                "env_file": {
                    "exists": env_exists,
                    "path": str(env_file),
                    "variables_count": len(env_variables)
                },
                "config_file": {
                    "exists": config_exists,
                    "path": str(config_file)
                },
                "required_variables": {
                    "total": len(required_vars),
                    "missing": missing_vars,
                    "missing_count": len(missing_vars)
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def check_logs(self) -> Dict:
        """Check application logs for errors and warnings."""
        try:
            log_file = self.logs_dir / "app.log"
            
            if not log_file.exists():
                return {
                    "status": "warning",
                    "log_file_exists": False,
                    "message": "No log file found"
                }
            
            # Read recent log entries
            recent_errors = []
            recent_warnings = []
            total_lines = 0
            
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    total_lines = len(lines)
                    
                    # Check last 100 lines for recent issues
                    recent_lines = lines[-100:] if len(lines) > 100 else lines
                    
                    for line in recent_lines:
                        if " ERROR " in line:
                            recent_errors.append(line.strip())
                        elif " WARNING " in line:
                            recent_warnings.append(line.strip())
            
            except Exception as e:
                return {
                    "status": "error",
                    "error": f"Could not read log file: {e}"
                }
            
            file_size = log_file.stat().st_size
            file_age = datetime.now() - datetime.fromtimestamp(log_file.stat().st_mtime)
            
            status = "error" if recent_errors else ("warning" if recent_warnings else "healthy")
            
            return {
                "status": status,
                "log_file_exists": True,
                "file_size_bytes": file_size,
                "file_size_mb": round(file_size / (1024 * 1024), 2),
                "file_age_hours": round(file_age.total_seconds() / 3600, 1),
                "total_lines": total_lines,
                "recent_errors": len(recent_errors),
                "recent_warnings": len(recent_warnings),
                "latest_errors": recent_errors[-3:] if recent_errors else [],
                "latest_warnings": recent_warnings[-3:] if recent_warnings else []
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _is_port_in_use(self, port: int) -> bool:
        """Check if a port is in use."""
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == port:
                    return True
            return False
        except:
            # Fallback method
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                return result == 0
            except:
                return False
    
    def _get_python_processes(self) -> List[Dict]:
        """Get information about running Python processes."""
        processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'cpu_percent']):
                try:
                    if 'python' in proc.info['name'].lower():
                        cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                        if 'app.py' in cmdline or 'chatbot' in cmdline:
                            processes.append({
                                'pid': proc.info['pid'],
                                'name': proc.info['name'],
                                'cmdline': cmdline[:100],  # Truncate long command lines
                                'memory_mb': round(proc.info['memory_info'].rss / (1024 * 1024), 1),
                                'cpu_percent': round(proc.info['cpu_percent'] or 0, 1)
                            })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            pass
        
        return processes
    
    def run_comprehensive_check(self) -> Dict:
        """Run all health checks and return comprehensive status."""
        print("🏥 Running comprehensive system health check...")
        print("=" * 60)
        
        checks = {
            "python_environment": self.check_python_environment(),
            "dependencies": self.check_dependencies(),
            "database": self.check_database(),
            "services": self.check_services(),
            "system_resources": self.check_system_resources(),
            "configuration": self.check_configuration(),
            "logs": self.check_logs()
        }
        
        # Determine overall health
        statuses = [check.get("status", "unknown") for check in checks.values()]
        error_count = statuses.count("error")
        warning_count = statuses.count("warning")
        
        if error_count > 0:
            overall_status = "critical"
        elif warning_count > 2:
            overall_status = "degraded"
        elif warning_count > 0:
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        self.health_status = {
            "overall_status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_checks": len(checks),
                "healthy": statuses.count("healthy"),
                "warnings": warning_count,
                "errors": error_count,
                "unknown": statuses.count("unknown")
            },
            "components": checks
        }
        
        return self.health_status
    
    def print_health_report(self, detailed: bool = False):
        """Print a formatted health report."""
        if not self.health_status or "components" not in self.health_status:
            print("❌ No health data available. Run comprehensive check first.")
            return
        
        status = self.health_status["overall_status"]
        status_icons = {
            "healthy": "✅",
            "warning": "⚠️", 
            "degraded": "🟡",
            "critical": "❌",
            "error": "💥",
            "unknown": "❓"
        }
        
        print(f"\n{status_icons.get(status, '❓')} Overall System Health: {status.upper()}")
        print(f"🕒 Check Time: {self.health_status['timestamp']}")
        
        summary = self.health_status["summary"]
        print(f"📊 Summary: {summary['healthy']}/{summary['total_checks']} healthy, "
              f"{summary['warnings']} warnings, {summary['errors']} errors")
        
        print("\n📋 Component Status:")
        for component, data in self.health_status["components"].items():
            comp_status = data.get("status", "unknown")
            icon = status_icons.get(comp_status, "❓")
            print(f"  {icon} {component.replace('_', ' ').title()}: {comp_status}")
            
            if detailed and comp_status in ["warning", "error"]:
                if "error" in data:
                    print(f"      Error: {data['error']}")
                if "missing_packages" in data and data["missing_packages"]:
                    print(f"      Missing: {', '.join(data['missing_packages'])}")
                if "conflicts" in data and data["conflicts"]:
                    print(f"      Conflicts: {data['conflicts'][:100]}...")
        
        print("\n💡 Recommendations:")
        self._print_recommendations()
    
    def _print_recommendations(self):
        """Print recommendations based on health status."""
        components = self.health_status.get("components", {})
        
        # Python environment recommendations
        python_env = components.get("python_environment", {})
        if python_env.get("status") != "healthy":
            if not python_env.get("virtual_env_active"):
                print("  • Activate virtual environment: source venv/bin/activate")
            if not python_env.get("version_compatible"):
                print("  • Upgrade Python to 3.11 or higher")
        
        # Dependency recommendations
        deps = components.get("dependencies", {})
        if deps.get("status") != "healthy":
            if deps.get("missing_packages"):
                print("  • Install missing packages: pip install -r requirements.txt")
            if deps.get("has_conflicts"):
                print("  • Fix dependency conflicts: pip install pytest-cov==5.0.0 pydantic-core==2.23.4")
        
        # Configuration recommendations
        config = components.get("configuration", {})
        if config.get("status") != "healthy":
            missing_vars = config.get("required_variables", {}).get("missing", [])
            if missing_vars:
                print(f"  • Set environment variables: {', '.join(missing_vars)}")
            if not config.get("env_file", {}).get("exists"):
                print("  • Create .env file with API keys")
        
        # Service recommendations
        services = components.get("services", {})
        if services.get("status") != "healthy":
            print("  • Start application services: python app.py")
        
        # Database recommendations
        database = components.get("database", {})
        if database.get("status") != "healthy":
            if not database.get("sqlite", {}).get("file_exists"):
                print("  • Initialize database: python -c 'from src.database.session import init_db; init_db()'")
        
        # Resource recommendations
        resources = components.get("system_resources", {})
        if resources.get("status") == "warning":
            if resources.get("memory", {}).get("warning"):
                print("  • Free up memory: close unnecessary applications")
            if resources.get("disk", {}).get("warning"):
                print("  • Free up disk space: clean temporary files")
    
    def save_health_report(self, filepath: Optional[str] = None):
        """Save health report to JSON file."""
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = self.logs_dir / f"health_report_{timestamp}.json"
        
        try:
            self.logs_dir.mkdir(exist_ok=True)
            with open(filepath, 'w') as f:
                json.dump(self.health_status, f, indent=2, default=str)
            print(f"💾 Health report saved to: {filepath}")
        except Exception as e:
            print(f"❌ Could not save health report: {e}")

def main():
    """Main function to run health monitoring."""
    import argparse
    
    parser = argparse.ArgumentParser(description="WhatsApp AI Chatbot System Health Monitor")
    parser.add_argument("--detailed", "-d", action="store_true", help="Show detailed output")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    parser.add_argument("--save", "-s", action="store_true", help="Save report to file")
    parser.add_argument("--monitor", "-m", type=int, metavar="SECONDS", 
                       help="Continuous monitoring mode (check every N seconds)")
    
    args = parser.parse_args()
    
    monitor = SystemHealthMonitor()
    
    if args.monitor:
        print(f"🔄 Starting continuous monitoring (every {args.monitor} seconds)")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                monitor.run_comprehensive_check()
                
                if args.json:
                    print(json.dumps(monitor.health_status, indent=2, default=str))
                else:
                    monitor.print_health_report(detailed=args.detailed)
                
                if args.save:
                    monitor.save_health_report()
                
                print(f"\n⏰ Next check in {args.monitor} seconds...\n")
                time.sleep(args.monitor)
                
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped")
            
    else:
        # Single check
        monitor.run_comprehensive_check()
        
        if args.json:
            print(json.dumps(monitor.health_status, indent=2, default=str))
        else:
            monitor.print_health_report(detailed=args.detailed)
        
        if args.save:
            monitor.save_health_report()

if __name__ == "__main__":
    main()