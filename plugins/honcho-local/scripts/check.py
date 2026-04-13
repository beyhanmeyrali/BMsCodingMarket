#!/usr/bin/env python3
"""
Honcho Local Check Script

Verifies that the honcho-local plugin is properly configured and Ollama is working.
Run from: /honcho-check command
"""

import os
import sys
import subprocess
import urllib.request
import json
from pathlib import Path


def print_header(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}")


def print_ok(msg):
    print(f"[OK] {msg}")


def print_info(msg):
    print(f"[INFO] {msg}")


def print_error(msg):
    print(f"[ERROR] {msg}")


def print_fail(msg):
    print(f"[FAIL] {msg}")


def run_command(cmd, check=True):
    """Run a shell command and return output."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=check
        )
        return result.stdout.strip(), result.returncode
    except subprocess.CalledProcessError as e:
        return e.stdout.strip(), e.returncode
    except FileNotFoundError:
        return "", -1


def check_ollama_installed():
    """Check if Ollama is installed."""
    output, code = run_command("ollama --version", check=False)
    if code == 0:
        return True, output
    return False, "Not installed"


def check_ollama_running():
    """Check if Ollama is running."""
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2) as response:
            if response.status == 200:
                return True, "Running on http://localhost:11434"
    except urllib.error.URLError:
        pass
    except Exception:
        pass
    return False, "Not running or not accessible on http://localhost:11434"


def check_models():
    """Check if required models are available."""
    models_status = {}
    required_models = ["qwen3.5:9b", "qwen3-embedding:0.6b"]

    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=5) as response:
            data = json.loads(response.read())
            available_models = data.get("models", [])

            available_names = []
            for m in available_models:
                available_names.append(m.get("name", ""))

            for model in required_models:
                found = any(model in name for name in available_names)
                models_status[model] = found

            return models_status, available_names
    except Exception as e:
        # Ollama not running
        return {m: False for m in required_models}, []


def check_python_packages():
    """Check if Python packages are installed."""
    packages = {
        "ollama": "ollama",
        "psycopg2": "psycopg2-binary",
        "psycopg2-binary": "psycopg2-binary",
    }

    installed = {}
    for module_name, package_name in packages.items():
        try:
            __import__(module_name)
            installed[package_name] = True
        except ImportError:
            installed[package_name] = False

    return installed


def check_plugin_import():
    """Check if the local_honcho module can be imported."""
    try:
        # Try to find the plugin path
        # The plugin should be installed in Claude Code's plugins directory
        import sys

        # Check if we can import from the expected location
        plugin_paths = [
            # When installed via marketplace
            Path.home() / ".claude" / "plugins" / "cache" / "*",
            # When developing locally
            Path.cwd().parent / "plugins" / "honcho-local" / "lib",
            # Add more paths as needed
        ]

        found = False
        for path_pattern in plugin_paths:
            # Handle wildcards
            if "*" in str(path_pattern):
                parent = path_pattern.parent
                if parent.exists():
                    for path in parent.glob(path_pattern.name):
                        lib_path = path / "plugins" / "honcho-local" / "lib"
                        if lib_path.exists():
                            sys.path.insert(0, str(lib_path))
                            found = True
                            break
            else:
                lib_path = path_pattern
                if lib_path.exists():
                    sys.path.insert(0, str(lib_path))
                    found = True
                    break

            if found:
                break

        import local_honcho
        return True, "local_honcho module can be imported"
    except ImportError as e:
        return False, f"Cannot import local_honcho: {e}"
    except Exception as e:
        return False, f"Error checking plugin: {e}"


def test_basic_functionality():
    """Test basic memory functionality."""
    try:
        import sys
        from pathlib import Path

        # Find and import local_honcho
        # local_honcho.py should be in the same directory as this script
        scripts_path = Path(__file__).parent
        sys.path.insert(0, str(scripts_path))

        from local_honcho import get_local_honcho

        # Create a test memory
        memory = get_local_honcho(
            workspace_id="honcho-check-test",
            think=False,
        )

        # Create a peer
        user = memory.peer("test-user")
        agent = memory.peer("test-agent", peer_type="agent")

        # Create session and add message
        session = memory.session("test-session")
        count = session.add_messages([
            {"role": "user", "content": "Test message", "metadata": {"peer_id": user.id}},
        ])

        if count == 1:
            return True, "Can create memory, peers, sessions, and add messages"
        else:
            return False, f"Message addition returned {count}, expected 1"

    except Exception as e:
        return False, f"Functionality test failed: {e}"


def main():
    print_header("Honcho Local Installation Check")

    all_passed = True

    # Check 1: Ollama installation
    print("\n[1/6] Checking Ollama installation...")
    installed, info = check_ollama_installed()
    if installed:
        print_ok(f"Ollama is installed ({info})")
    else:
        print_fail("Ollama is not installed")
        print_info("Run /honcho-install to install Ollama")
        all_passed = False

    # Check 2: Ollama service
    print("\n[2/6] Checking Ollama service...")
    running, info = check_ollama_running()
    if running:
        print_ok(info)
    else:
        print_fail(info)
        print_info("Run 'ollama serve' to start Ollama")
        all_passed = False

    # Check 3: Models
    print("\n[3/6] Checking required models...")
    if running:
        models_status, available = check_models()
        for model, found in models_status.items():
            if found:
                print_ok(f"{model} is available")
            else:
                print_fail(f"{model} is not available")
                print_info("Run /honcho-install to download models")
                all_passed = False
    else:
        print_fail("Cannot check models - Ollama is not running")
        all_passed = False

    # Check 4: Python dependencies
    print("\n[4/6] Checking Python dependencies...")
    packages = check_python_packages()
    for package, installed in packages.items():
        if installed:
            print_ok(f"{package} is installed")
        else:
            print_warning(f"{package} is not installed")
            print_info("Run: pip install ollama psycopg2-binary")

    # Check 5: Plugin paths
    print("\n[5/6] Checking plugin import...")
    can_import, info = check_plugin_import()
    if can_import:
        print_ok(info)
    else:
        print_fail(info)
        print_info("Make sure the honcho-local plugin is installed in Claude Code")
        all_passed = False

    # Check 6: Basic functionality
    print("\n[6/6] Testing basic functionality...")
    works, info = test_basic_functionality()
    if works:
        print_ok(info)
    else:
        print_fail(info)
        all_passed = False

    # Summary
    print_header("Check Complete")
    if all_passed:
        print_ok("All checks passed! Honcho Local is ready to use.")
        print("\nYou can now use the honcho-local skill in your agents:")
        print("  - Agents will automatically use it for memory and reasoning")
        print("  - Use 'think=True' when initializing to enable thinking mode")
        return 0
    else:
        print_fail("Some checks failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("  1. Install Ollama: /honcho-install")
        print("  2. Start Ollama: ollama serve")
        print("  3. Install Python deps: pip install ollama psycopg2-binary")
        return 1


if __name__ == "__main__":
    sys.exit(main())
