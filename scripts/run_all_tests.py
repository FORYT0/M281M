"""
Run all Phase 0 tests and generate a summary report.
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

def run_test(script_name, description):
    """Run a test script and return success status."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"{'='*60}\n")
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=False,
            text=True,
            timeout=30
        )
        success = result.returncode == 0
        return success, "PASSED" if success else "FAILED"
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"
    except Exception as e:
        return False, f"ERROR: {str(e)}"


def main():
    print("=" * 60)
    print("M281M Phase 0 - Complete Test Suite")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("scripts/quick_test.py", "Project Structure Verification"),
        ("scripts/test_simulator_short.py", "Tick Replay Simulator"),
    ]
    
    results = []
    
    for script, description in tests:
        success, status = run_test(script, description)
        results.append((description, status, success))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for description, status, success in results:
        symbol = "✓" if success else "✗"
        print(f"{symbol} {description}: {status}")
    
    passed = sum(1 for _, _, success in results if success)
    total = len(results)
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    # WebSocket note
    print()
    print("Note: WebSocket test requires internet connection.")
    print("Run manually: .\\venv\\Scripts\\python.exe scripts\\test_websocket_short.py")
    
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 Phase 0 Complete! Ready for Phase 1.")
        return 0
    else:
        print("\n⚠ Some tests failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
