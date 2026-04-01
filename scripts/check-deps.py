#!/usr/bin/env python3
"""
Dependency checker for L'Aura project
Checks if all required dependencies are installed
"""

import sys
import subprocess
import os
from pathlib import Path

def check_command(cmd, name, install_hint):
    """Check if a command exists"""
    try:
        subprocess.run([cmd, "--version"], capture_output=True, check=True)
        print(f"✅ {name} is installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"❌ {name} is NOT installed")
        print(f"   Install: {install_hint}")
        return False

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python version {version.major}.{version.minor} is too old")
        print("   Required: Python 3.11+")
        return False

def check_node_version():
    """Check Node version"""
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True, check=True)
        version = result.stdout.strip()
        major = int(version.split('.')[0].replace('v', ''))
        if major >= 18:
            print(f"✅ Node {version}")
            return True
        else:
            print(f"❌ Node {version} is too old")
            print("   Required: Node 18+")
            return False
    except:
        return False

def check_env_file(path, name):
    """Check if .env file exists"""
    if Path(path).exists():
        print(f"✅ {name} .env exists")
        return True
    else:
        print(f"⚠️  {name} .env missing (copy from .env.example)")
        return True  # Not critical

def main():
    print("="*60)
    print("🔍 L'Aura Project - Dependency Check")
    print("="*60)
    print()
    
    all_ok = True
    
    # Check Python
    all_ok &= check_python_version()
    
    # Check Node
    all_ok &= check_node_version()
    
    # Check MongoDB
    all_ok &= check_command("mongod", "MongoDB", "https://www.mongodb.com/try/download/community")
    
    # Check Yarn
    all_ok &= check_command("yarn", "Yarn", "npm install -g yarn")
    
    print()
    print("📁 Configuration Files:")
    check_env_file("/app/backend/.env", "Backend")
    check_env_file("/app/frontend/.env", "Frontend")
    
    print()
    if all_ok:
        print("✅ All dependencies are installed!")
        print("\n📝 Next steps:")
        print("   1. Copy .env.example to .env if needed")
        print("   2. Run: make dev (or npm run dev)")
        return 0
    else:
        print("❌ Some dependencies are missing. Install them first.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
