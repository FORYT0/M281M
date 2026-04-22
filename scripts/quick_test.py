"""
Quick test to verify Python environment and project structure.
"""

import sys
from pathlib import Path

print("=" * 60)
print("M281M Phase 0 - Quick Test")
print("=" * 60)
print()

# Check Python version
print(f"✓ Python version: {sys.version}")
print()

# Check project structure
project_root = Path(__file__).parent.parent
required_dirs = [
    "data/live",
    "data/historical",
    "src/pipeline",
    "src/agents",
    "src/risk",
    "src/backtest",
    "src/deployment",
    "tests",
    "docs",
    "scripts",
    "config"
]

print("Checking project structure:")
all_exist = True
for dir_path in required_dirs:
    full_path = project_root / dir_path
    exists = full_path.exists()
    status = "✓" if exists else "✗"
    print(f"  {status} {dir_path}")
    if not exists:
        all_exist = False

print()

# Check key files
key_files = [
    "requirements.txt",
    "README.md",
    ".gitignore",
    "config/config.yaml",
    "src/pipeline/websocket_client.py",
    "src/pipeline/tick_simulator.py"
]

print("Checking key files:")
for file_path in key_files:
    full_path = project_root / file_path
    exists = full_path.exists()
    status = "✓" if exists else "✗"
    print(f"  {status} {file_path}")
    if not exists:
        all_exist = False

print()
print("=" * 60)

if all_exist:
    print("SUCCESS: Phase 0 structure is complete!")
    print()
    print("Next steps:")
    print("1. Install dependencies:")
    print("   .\\venv\\Scripts\\python.exe -m pip install pandas numpy websockets aiohttp loguru")
    print()
    print("2. Test WebSocket client:")
    print("   .\\venv\\Scripts\\python.exe scripts\\test_websocket.py")
    print()
    print("3. Test tick simulator:")
    print("   .\\venv\\Scripts\\python.exe scripts\\test_simulator.py")
else:
    print("ERROR: Some files or directories are missing!")
    sys.exit(1)

print("=" * 60)
