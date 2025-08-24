"""
Version information display window.
Shows system info, package versions, and application status.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import sys
import platform
import subprocess
import pkg_resources
from datetime import datetime
import threading
import time


class VersionWindow:
    """Standalone version information window using tkinter."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("WhatsApp AI Chatbot - Version Info")
        self.root.geometry("800x600")
        self.root.configure(bg='#2b2b2b')
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_system_tab()
        self.create_packages_tab()
        self.create_status_tab()
        
        # Update status periodically
        self.update_status()
        
    def create_system_tab(self):
        """Create system information tab."""
        system_frame = ttk.Frame(self.notebook)
        self.notebook.add(system_frame, text="System Info")
        
        # System info text
        system_text = scrolledtext.ScrolledText(
            system_frame, 
            wrap=tk.WORD, 
            height=20,
            bg='#1e1e1e',
            fg='#ffffff',
            insertbackground='#ffffff',
            font=('Consolas', 10)
        )
        system_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Collect system information
        info = []
        info.append("🖥️  SYSTEM INFORMATION")
        info.append("=" * 50)
        info.append(f"Platform: {platform.platform()}")
        info.append(f"System: {platform.system()} {platform.release()}")
        info.append(f"Architecture: {platform.architecture()[0]}")
        info.append(f"Machine: {platform.machine()}")
        info.append(f"Processor: {platform.processor()}")
        info.append(f"Hostname: {platform.node()}")
        info.append("")
        
        info.append("🐍 PYTHON INFORMATION")
        info.append("=" * 50)
        info.append(f"Version: {sys.version}")
        info.append(f"Executable: {sys.executable}")
        info.append(f"Path: {sys.path[0]}")
        info.append("")
        
        # Add current time
        info.append("⏰ CURRENT TIME")
        info.append("=" * 50)
        info.append(f"Local Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        system_text.insert(tk.END, "\n".join(info))
        system_text.config(state=tk.DISABLED)
    
    def create_packages_tab(self):
        """Create installed packages tab."""
        packages_frame = ttk.Frame(self.notebook)
        self.notebook.add(packages_frame, text="Packages")
        
        # Search frame
        search_frame = ttk.Frame(packages_frame)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(search_frame, text="Filter:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        search_entry.bind('<KeyRelease>', self.filter_packages)
        
        # Packages text
        self.packages_text = scrolledtext.ScrolledText(
            packages_frame,
            wrap=tk.WORD,
            height=20,
            bg='#1e1e1e',
            fg='#ffffff',
            insertbackground='#ffffff',
            font=('Consolas', 9)
        )
        self.packages_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Load packages in background
        threading.Thread(target=self.load_packages, daemon=True).start()
    
    def create_status_tab(self):
        """Create application status tab."""
        status_frame = ttk.Frame(self.notebook)
        self.notebook.add(status_frame, text="App Status")
        
        # Status text
        self.status_text = scrolledtext.ScrolledText(
            status_frame,
            wrap=tk.WORD,
            height=20,
            bg='#1e1e1e',
            fg='#ffffff',
            insertbackground='#ffffff',
            font=('Consolas', 10)
        )
        self.status_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Auto-refresh checkbox
        self.auto_refresh = tk.BooleanVar(value=True)
        refresh_check = ttk.Checkbutton(
            status_frame,
            text="Auto-refresh (5s)",
            variable=self.auto_refresh
        )
        refresh_check.pack(pady=5)
        
        # Manual refresh button
        refresh_btn = ttk.Button(
            status_frame,
            text="🔄 Refresh Now",
            command=self.update_status
        )
        refresh_btn.pack(pady=5)
    
    def load_packages(self):
        """Load installed packages information."""
        try:
            packages = []
            packages.append("📦 INSTALLED PACKAGES")
            packages.append("=" * 50)
            packages.append(f"{'Package':<30} {'Version':<15} {'Location'}")
            packages.append("-" * 80)
            
            # Get installed packages
            installed_packages = [d for d in pkg_resources.working_set]
            installed_packages.sort(key=lambda x: x.project_name.lower())
            
            for package in installed_packages:
                location = package.location if package.location else "Unknown"
                if len(location) > 40:
                    location = "..." + location[-37:]
                
                packages.append(f"{package.project_name:<30} {package.version:<15} {location}")
            
            # Update packages text
            self.root.after(0, lambda: self.update_packages_display("\n".join(packages)))
            
        except Exception as e:
            error_msg = f"Error loading packages: {str(e)}"
            self.root.after(0, lambda: self.update_packages_display(error_msg))
    
    def update_packages_display(self, content):
        """Update packages display with content."""
        self.packages_text.config(state=tk.NORMAL)
        self.packages_text.delete(1.0, tk.END)
        self.packages_text.insert(tk.END, content)
        self.packages_text.config(state=tk.DISABLED)
        self.all_packages_content = content
    
    def filter_packages(self, event=None):
        """Filter packages based on search term."""
        if hasattr(self, 'all_packages_content'):
            search_term = self.search_var.get().lower()
            if not search_term:
                filtered_content = self.all_packages_content
            else:
                lines = self.all_packages_content.split('\n')
                filtered_lines = []
                for line in lines:
                    if search_term in line.lower() or line.startswith('=') or line.startswith('-') or line.startswith('📦'):
                        filtered_lines.append(line)
                filtered_content = '\n'.join(filtered_lines)
            
            self.packages_text.config(state=tk.NORMAL)
            self.packages_text.delete(1.0, tk.END)
            self.packages_text.insert(tk.END, filtered_content)
            self.packages_text.config(state=tk.DISABLED)
    
    def update_status(self):
        """Update application status information."""
        try:
            status = []
            status.append("🚀 APPLICATION STATUS")
            status.append("=" * 50)
            status.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            status.append("")
            
            # Check if ports are in use
            status.append("🌐 PORT STATUS")
            status.append("-" * 30)
            
            # Check port 8000 (Backend)
            try:
                result = subprocess.run(
                    ['netstat', '-an'], 
                    capture_output=True, 
                    text=True, 
                    timeout=5
                )
                if ':8000' in result.stdout:
                    status.append("✅ Port 8000 (Backend): ACTIVE")
                else:
                    status.append("❌ Port 8000 (Backend): INACTIVE")
                    
                if ':8550' in result.stdout:
                    status.append("✅ Port 8550 (UI Server): ACTIVE")
                else:
                    status.append("❌ Port 8550 (UI Server): INACTIVE")
                    
            except Exception as e:
                status.append(f"❓ Port check failed: {str(e)}")
            
            status.append("")
            
            # Memory usage
            try:
                import psutil
                memory = psutil.virtual_memory()
                status.append("💾 MEMORY USAGE")
                status.append("-" * 30)
                status.append(f"Total: {memory.total // (1024**3):.1f} GB")
                status.append(f"Available: {memory.available // (1024**3):.1f} GB")
                status.append(f"Used: {memory.percent:.1f}%")
                status.append("")
            except ImportError:
                pass
            
            # Key package versions
            status.append("📋 KEY PACKAGES")
            status.append("-" * 30)
            
            key_packages = ['flet', 'fastapi', 'uvicorn', 'websockets', 'pydantic']
            for pkg_name in key_packages:
                try:
                    pkg = pkg_resources.get_distribution(pkg_name)
                    status.append(f"{pkg_name}: {pkg.version}")
                except:
                    status.append(f"{pkg_name}: Not installed")
            
            # Update status display
            self.status_text.config(state=tk.NORMAL)
            self.status_text.delete(1.0, tk.END)
            self.status_text.insert(tk.END, "\n".join(status))
            self.status_text.config(state=tk.DISABLED)
            
        except Exception as e:
            error_status = f"Error updating status: {str(e)}"
            self.status_text.config(state=tk.NORMAL)
            self.status_text.delete(1.0, tk.END)
            self.status_text.insert(tk.END, error_status)
            self.status_text.config(state=tk.DISABLED)
        
        # Schedule next update if auto-refresh is enabled
        if self.auto_refresh.get():
            self.root.after(5000, self.update_status)  # Update every 5 seconds
    
    def run(self):
        """Start the version window."""
        # Set window icon if available
        try:
            # Try to set a nice window icon
            self.root.iconname("Version Info")
        except:
            pass
        
        # Center window on screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - self.root.winfo_width()) // 2
        y = (self.root.winfo_screenheight() - self.root.winfo_height()) // 2
        self.root.geometry(f"+{x}+{y}")
        
        # Start main loop
        self.root.mainloop()


def show_version_window():
    """Create and show the version window."""
    app = VersionWindow()
    app.run()


if __name__ == "__main__":
    show_version_window()