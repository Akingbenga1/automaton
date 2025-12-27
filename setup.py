#!/usr/bin/env python3
"""
Setup script for MCP-Based Job Application System
Helps with initial configuration and verification
"""

import os
import sys
import subprocess
from pathlib import Path


def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80 + "\n")


def check_python_version():
    """Check if Python version is adequate"""
    print_header("Checking Python Version")

    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("❌ Python 3.10 or higher is required")
        return False

    print("✓ Python version is adequate")
    return True


def check_node_installed():
    """Check if Node.js is installed"""
    print_header("Checking Node.js Installation")

    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        version = result.stdout.strip()
        print(f"Node.js version: {version}")
        print("✓ Node.js is installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Node.js is not installed")
        print("   Install from: https://nodejs.org/")
        return False


def create_directories():
    """Create necessary directories"""
    print_header("Creating Directories")

    directories = [
        "data",
        "data/logs",
        "cv"
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created {directory}/")

    return True


def check_env_file():
    """Check if .env file exists"""
    print_header("Checking Environment File")

    if os.path.exists(".env"):
        print("✓ .env file exists")
        return True
    else:
        print("⚠ .env file not found")
        print("  Creating from .env.example...")

        if os.path.exists(".env.example"):
            with open(".env.example", "r") as src:
                content = src.read()
            with open(".env", "w") as dst:
                dst.write(content)
            print("✓ Created .env file")
            print("  Please edit .env and add your credentials!")
            return True
        else:
            print("❌ .env.example not found")
            return False


def check_mcp_servers():
    """Check if MCP servers are cloned"""
    print_header("Checking MCP Servers")

    parent = Path("..").resolve()

    servers = {
        "LinkedIn MCP": parent / "linkedin-mcp",
        "JobSpy MCP": parent / "jobspy-mcp-server"
    }

    all_found = True

    for name, path in servers.items():
        if path.exists():
            print(f"✓ {name} found at {path}")
        else:
            print(f"❌ {name} not found at {path}")
            print(f"   Clone from the repository (see QUICKSTART.md)")
            all_found = False

    return all_found


def install_dependencies():
    """Install Python dependencies"""
    print_header("Installing Dependencies")

    print("Installing Python packages...")

    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True
        )
        print("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False


def check_cv_exists():
    """Check if CV file exists"""
    print_header("Checking CV File")

    cv_dir = Path("cv")
    pdf_files = list(cv_dir.glob("*.pdf"))

    if pdf_files:
        print(f"✓ Found {len(pdf_files)} CV file(s):")
        for cv in pdf_files:
            print(f"  - {cv.name}")
        return True
    else:
        print("⚠ No CV files found in cv/ directory")
        print("  Please add your CV as a PDF file")
        return False


def verify_profile_config():
    """Verify profile configuration exists"""
    print_header("Checking Profile Configuration")

    config_file = Path("config/profile.yaml")

    if config_file.exists():
        print("✓ Profile configuration exists")
        print("  Please review and update config/profile.yaml with your information")
        return True
    else:
        print("❌ Profile configuration not found")
        return False


def run_test():
    """Run a quick test"""
    print_header("Running Test")

    print("Testing imports...")

    try:
        from src.database import ApplicationDatabase
        from src.mcp_client import MCPClient
        from src.job_filter import JobFilter
        from src.job_searcher import JobSearcher
        from src.applicator import JobApplicator

        print("✓ All modules imported successfully")

        print("\nTesting database...")
        db = ApplicationDatabase("data/test.db")
        print("✓ Database initialized")

        # Clean up test db
        if os.path.exists("data/test.db"):
            os.remove("data/test.db")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def print_next_steps():
    """Print next steps for user"""
    print_header("Setup Complete! Next Steps:")

    steps = [
        "1. Edit .env file with your LinkedIn credentials",
        "2. Review and update config/profile.yaml with your information",
        "3. Ensure your CV is in the cv/ directory",
        "4. Clone and setup MCP servers (see QUICKSTART.md)",
        "5. Run a test: python main.py --dry-run --limit 5",
        "6. View help: python main.py --help"
    ]

    for step in steps:
        print(f"  {step}")

    print("\n📖 For detailed instructions, see QUICKSTART.md")
    print("🚀 Ready to start your automated job search!\n")


def main():
    """Main setup function"""
    print("\n" + "="*80)
    print("  MCP-Based Automated Job Application System - Setup")
    print("="*80)

    checks = [
        ("Python Version", check_python_version),
        ("Node.js", check_node_installed),
        ("Directories", create_directories),
        ("Environment File", check_env_file),
        ("Profile Config", verify_profile_config),
        ("CV File", check_cv_exists),
        ("Dependencies", install_dependencies),
        ("MCP Servers", check_mcp_servers),
        ("Module Test", run_test)
    ]

    results = {}

    for name, check_func in checks:
        results[name] = check_func()

    # Summary
    print_header("Setup Summary")

    for name, result in results.items():
        status = "✓" if result else "❌"
        print(f"{status} {name}")

    all_passed = all(results.values())

    if all_passed:
        print("\n🎉 All checks passed!")
        print_next_steps()
    else:
        print("\n⚠ Some checks failed. Please address the issues above.")
        print("   See QUICKSTART.md for detailed instructions.")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
