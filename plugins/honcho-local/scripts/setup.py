#!/usr/bin/env python3
"""
Honcho Local Setup Script

Installs Ollama (if needed), pulls required models, and installs Python dependencies.
Run from: /honcho-install command
"""

import os
import sys
import subprocess
import platform
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


def print_warning(msg):
    print(f"[WARNING] {msg}")


def run_command(cmd, check=True, capture=True):
    """Run a shell command and return output."""
    try:
        if capture:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                check=check
            )
            return result.stdout.strip(), result.returncode
        else:
            subprocess.run(cmd, shell=True, check=check)
            return "", 0
    except subprocess.CalledProcessError as e:
        if capture:
            return e.stdout.strip(), e.returncode
        return "", e.returncode


def check_ollama_installed():
    """Check if Ollama is installed."""
    output, code = run_command("ollama --version", check=False)
    return code == 0


def check_ollama_running():
    """Check if Ollama is running."""
    try:
        import urllib.request
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2) as response:
            return response.status == 200
    except:
        return False


def check_model_available(model):
    """Check if a model is available in Ollama."""
    try:
        import urllib.request
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=5) as response:
            data = json.loads(response.read())
            models = data.get("models", [])
            for m in models:
                if model in m.get("name", ""):
                    return True
        return False
    except:
        return False


def pull_model(model):
    """Pull an Ollama model."""
    print_info(f"Downloading {model}... (this may take a while)")
    print_info("You can also run this manually in another terminal:")
    print_info(f"  ollama pull {model}")

    # Use subprocess to show progress
    import subprocess
    process = subprocess.Popen(
        ["ollama", "pull", model],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    for line in process.stdout:
        print(f"  {line.strip()}" if line.strip() else "")

    process.wait()
    return process.returncode == 0


def install_python_dependencies():
    """Install Python dependencies."""
    print_info("Installing Python dependencies...")

    dependencies = ["ollama", "psycopg2-binary"]

    for dep in dependencies:
        print_info(f"  Installing {dep}...")
        output, code = run_command(f"pip install {dep}", check=False)
        if code == 0:
            print_ok(f"  {dep} installed")
        else:
            print_warning(f"  {dep} installation had issues, trying to continue...")

    return True


def get_ollama_install_instructions():
    """Get platform-specific Ollama installation instructions."""
    system = platform.system()

    if system == "Windows":
        return {
            "url": "https://ollama.ai/download",
            "instructions": """
1. Download Ollama from https://ollama.ai/download
2. Run the installer
3. Ollama will start automatically and run on boot
4. Open a new terminal after installation
            """.strip()
        }
    elif system == "Darwin":  # macOS
        return {
            "url": "https://ollama.ai/download",
            "instructions": """
# Option 1: Download directly
1. Download from https://ollama.ai/download
2. Drag Ollama to your Applications folder
3. Run Ollama from Applications

# Option 2: Use terminal
curl -fsSL https://ollama.ai/install.sh | sh
            """.strip()
        }
    else:  # Linux
        return {
            "url": "https://ollama.ai/download",
            "instructions": """
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama
ollama serve &
            """.strip()
        }


def main():
    print_header("Honcho Local Installation")

    # Step 1: Check Ollama
    print("\n[1/5] Checking Ollama installation...")
    if not check_ollama_installed():
        print_error("Ollama is not installed!")
        info = get_ollama_install_instructions()
        print(f"\nDownload from: {info['url']}")
        print(f"\nInstructions:\n{info['instructions']}")
        print("\nAfter installing Ollama, run /honcho-install again.")
        return 1

    print_ok("Ollama is installed")

    # Step 2: Check Ollama is running
    print("\n[2/5] Checking Ollama service...")
    if not check_ollama_running():
        print_warning("Ollama is not running. Starting it now...")
        print_info("Run 'ollama serve' in another terminal, or press Ctrl+C to stop it later")

        # Try to start Ollama in background
        if platform.system() == "Windows":
            print_info("On Windows, Ollama should start automatically. Check the system tray.")
            print_info("If not running, start Ollama from the Start Menu.")
        else:
            print_info("Starting Ollama in background...")
            subprocess.Popen(["ollama", "serve"],
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)

        import time
        print_info("Waiting for Ollama to start...")
        for i in range(10):
            time.sleep(1)
            if check_ollama_running():
                print_ok("Ollama started successfully")
                break
        else:
            print_error("Could not start Ollama. Please run 'ollama serve' manually.")
            return 1
    else:
        print_ok("Ollama is running")

    # Step 3: Pull models
    print("\n[3/5] Checking required models...")
    models = ["qwen3.5:9b", "qwen3-embedding:0.6b"]

    for model in models:
        if check_model_available(model):
            print_ok(f"{model} is already downloaded")
        else:
            print_info(f"{model} needs to be downloaded")
            if not pull_model(model):
                print_error(f"Failed to download {model}")
                print_info(f"You can download it manually with: ollama pull {model}")
                return 1

    # Step 4: Install Python dependencies
    print("\n[4/5] Installing Python dependencies...")
    if not install_python_dependencies():
        print_warning("Some dependencies had issues, but continuing...")

    # Step 5: Verify
    print("\n[5/5] Verifying installation...")
    try:
        # Import would work from plugin path
        import ollama
        print_ok("ollama Python package is available")
    except ImportError:
        print_error("ollama Python package is not available")
        return 1

    print_header("Installation Complete!")
    print_ok("Honcho Local is ready to use!")
    print("\nNext steps:")
    print("  1. Run /honcho-check to verify everything is working")
    print("  2. Use the honcho-local skill in your agents")
    print("\nRequired models:")
    for model in models:
        print(f"  - {model}")
    print("\nPython dependencies:")
    print("  - ollama")
    print("  - psycopg2-binary (optional, for Postgres)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
