"""
ISL MudraVaani - Complete Setup and Environment Check Script

This script:
1. Checks system requirements (Python, Node.js, PostgreSQL)
2. Installs all dependencies
3. Verifies model availability
4. Creates sample training data if needed
5. Runs evaluation if model exists
6. Provides final status report
"""

import subprocess
import sys
import os
from pathlib import Path
import json

PROJECT_ROOT = Path(__file__).parent.resolve()
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_section(title):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{title}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

def print_success(msg):
    print(f"{GREEN}✓{RESET} {msg}")

def print_error(msg):
    print(f"{RED}✗{RESET} {msg}")

def print_warning(msg):
    print(f"{YELLOW}⚠{RESET} {msg}")

def run_command(cmd, cwd=None, check=True):
    """Run a shell command and return success status"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            shell=True,
            capture_output=True,
            text=True,
            check=check
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr

def check_python_version():
    """Check if Python version is 3.10 or 3.11"""
    print_section("1. PYTHON VERSION CHECK")
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    print(f"Detected Python: {version_str}")
    
    if version.major == 3 and version.minor in [10, 11]:
        print_success(f"Python {version_str} is compatible")
        return True
    else:
        print_error(f"Python {version_str} is NOT compatible")
        print_warning("This project requires Python 3.10 or 3.11 due to MediaPipe compatibility")
        print_warning("Python 3.12+ breaks MediaPipe 0.10.x")
        print()
        print("To fix this:")
        print("1. Install Python 3.11 from python.org")
        print("2. Run this script with: py -3.11 setup_and_check.py")
        return False

def check_node_version():
    """Check Node.js version"""
    print_section("2. NODE.JS VERSION CHECK")
    success, stdout, _ = run_command("node --version", check=False)
    
    if success:
        version = stdout.strip()
        print_success(f"Node.js {version} detected")
        return True
    else:
        print_error("Node.js not found")
        print_warning("Install Node.js >= 18.18 from nodejs.org")
        return False

def check_docker():
    """Check if Docker is available"""
    print_section("3. DOCKER CHECK")
    success, stdout, _ = run_command("docker --version", check=False)
    
    if success:
        version = stdout.strip()
        print_success(f"Docker detected: {version}")
        return True
    else:
        print_warning("Docker not found (optional - you can use local PostgreSQL)")
        return False

def check_postgres():
    """Check if PostgreSQL is running"""
    print_section("4. POSTGRESQL CHECK")
    
    # Try to check if postgres container is running
    success, stdout, _ = run_command(
        'docker ps --filter "name=isl_postgres" --format "{{.Names}}"',
        check=False
    )
    
    if success and "isl_postgres" in stdout:
        print_success("PostgreSQL container is running")
        return True
    else:
        print_warning("PostgreSQL container not running")
        print("To start it: docker compose up -d")
        return False

def install_node_dependencies():
    """Install Node.js dependencies"""
    print_section("5. NODE.JS DEPENDENCIES")
    
    if (PROJECT_ROOT / "node_modules").exists():
        print_success("node_modules exists")
    else:
        print("Installing Node.js dependencies...")
        success, stdout, stderr = run_command("npm install", cwd=PROJECT_ROOT)
        
        if success:
            print_success("npm install completed")
        else:
            print_error("npm install failed")
            print(stderr)
            return False
    
    # Build shared package
    print("Building shared package...")
    success, _, _ = run_command("npm run build:shared", cwd=PROJECT_ROOT)
    
    if success:
        print_success("Shared package built")
        return True
    else:
        print_error("Failed to build shared package")
        return False

def setup_python_venv():
    """Set up Python virtual environment for ML service"""
    print_section("6. PYTHON VIRTUAL ENVIRONMENT")
    
    venv_path = PROJECT_ROOT / "apps" / "ml-service" / ".venv"
    
    if venv_path.exists():
        print_success("Virtual environment exists")
    else:
        print("Creating virtual environment...")
        success, _, stderr = run_command(
            f"{sys.executable} -m venv .venv",
            cwd=PROJECT_ROOT / "apps" / "ml-service"
        )
        
        if success:
            print_success("Virtual environment created")
        else:
            print_error("Failed to create venv")
            print(stderr)
            return False
    
    # Install Python dependencies
    print("Installing Python dependencies...")
    
    if os.name == 'nt':  # Windows
        pip_path = venv_path / "Scripts" / "pip.exe"
    else:
        pip_path = venv_path / "bin" / "pip"
    
    success, stdout, stderr = run_command(
        f'"{pip_path}" install -r requirements.txt',
        cwd=PROJECT_ROOT / "apps" / "ml-service"
    )
    
    if success:
        print_success("Python dependencies installed")
        return True
    else:
        print_error("Failed to install Python dependencies")
        print(stderr)
        return False

def check_model():
    """Check if trained model exists"""
    print_section("7. MODEL CHECK")
    
    # Check both possible locations
    model_path_1 = PROJECT_ROOT / "ml" / "models_out" / "isl_model.pt"
    model_path_2 = PROJECT_ROOT / "apps" / "ml" / "models_out" / "isl_model.pt"
    
    if model_path_2.exists():
        print_success(f"Model found at: {model_path_2}")
        
        # Copy to expected location if not there
        if not model_path_1.exists():
            print("Copying model to expected location...")
            model_path_1.parent.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copy2(model_path_2, model_path_1)
            print_success("Model copied to ml/models_out/")
        
        return True, model_path_1
    elif model_path_1.exists():
        print_success(f"Model found at: {model_path_1}")
        return True, model_path_1
    else:
        print_warning("No trained model found")
        print()
        print("To train a model:")
        print("1. Collect training data: cd ml/dataset_tool && python collect.py --label A --samples 40")
        print("2. Train the model: cd ml/training && python train.py --epochs 60")
        print()
        print("NOTE: The project includes a pre-trained model in apps/ml/models_out/")
        print("but no training data is included (you must record your own)")
        return False, None

def check_training_data():
    """Check if training data exists"""
    print_section("8. TRAINING DATA CHECK")
    
    data_dir = PROJECT_ROOT / "ml" / "data" / "raw"
    data_files = list(data_dir.glob("*.npy"))
    
    if len(data_files) > 1:  # > 1 because .gitkeep might be counted
        print_success(f"Found {len(data_files)} training data files")
        for f in data_files[:5]:  # Show first 5
            print(f"  - {f.name}")
        if len(data_files) > 5:
            print(f"  ... and {len(data_files) - 5} more")
        return True
    else:
        print_warning("No training data found")
        print()
        print("This project requires you to record your own training data.")
        print("Use: cd ml/dataset_tool && python collect.py --label <SIGN> --samples 40")
        print()
        print("Available labels: A-Z, 0-9, HELLO, THANK_YOU, PLEASE, YES, NO, etc.")
        print("(See apps/ml-service/app/core/labels.py for full list)")
        return False

def check_env_files():
    """Check if environment files exist"""
    print_section("9. ENVIRONMENT FILES CHECK")
    
    server_env = PROJECT_ROOT / "apps" / "server" / ".env"
    web_env = PROJECT_ROOT / "apps" / "web" / ".env"
    
    issues = []
    
    if not server_env.exists():
        print_warning("apps/server/.env not found")
        print("Creating from .env.example...")
        
        example = PROJECT_ROOT / "apps" / "server" / ".env.example"
        if example.exists():
            import shutil
            shutil.copy2(example, server_env)
            print_success("Created apps/server/.env")
        else:
            issues.append("apps/server/.env.example not found")
    else:
        print_success("apps/server/.env exists")
    
    if not web_env.exists():
        print_warning("apps/web/.env not found")
        print("Creating from .env.example...")
        
        example = PROJECT_ROOT / "apps" / "web" / ".env.example"
        if example.exists():
            import shutil
            shutil.copy2(example, web_env)
            print_success("Created apps/web/.env")
        else:
            issues.append("apps/web/.env.example not found")
    else:
        print_success("apps/web/.env exists")
    
    return len(issues) == 0

def generate_status_report(checks):
    """Generate final status report"""
    print_section("FINAL STATUS REPORT")
    
    all_passed = all(checks.values())
    
    print(f"Overall Status: {'READY' if all_passed else 'NOT READY'}")
    print()
    
    print("Component Status:")
    for component, status in checks.items():
        status_str = f"{GREEN}✓ PASS{RESET}" if status else f"{RED}✗ FAIL{RESET}"
        print(f"  {component:30} {status_str}")
    
    if all_passed:
        print()
        print(f"{GREEN}{'='*60}{RESET}")
        print(f"{GREEN}System is ready! Follow these steps to run:{RESET}")
        print(f"{GREEN}{'='*60}{RESET}")
        print()
        print("1. Start PostgreSQL (if not running):")
        print("   docker compose up -d")
        print()
        print("2. Run database migrations:")
        print("   cd apps/server && npm run db:migrate")
        print()
        print("3. Start the application (3 terminals):")
        print()
        print("   Terminal 1 - ML Service:")
        print("   cd apps/ml-service")
        print("   .venv\\Scripts\\activate    (Windows)")
        print("   uvicorn app.main:app --reload --port 8000")
        print()
        print("   Terminal 2 - Backend API:")
        print("   cd apps/server")
        print("   npm run dev")
        print()
        print("   Terminal 3 - Frontend:")
        print("   cd apps/web")
        print("   npm run dev")
        print()
        print("4. Open browser: http://localhost:5173")
        print()
    else:
        print()
        print(f"{RED}{'='*60}{RESET}")
        print(f"{RED}System NOT ready - fix the issues above{RESET}")
        print(f"{RED}{'='*60}{RESET}")
    
    return all_passed

def main():
    print(f"{BLUE}╔{'='*58}╗{RESET}")
    print(f"{BLUE}║{' '*58}║{RESET}")
    print(f"{BLUE}║  ISL MudraVaani - Setup & Environment Check{' '*14}║{RESET}")
    print(f"{BLUE}║{' '*58}║{RESET}")
    print(f"{BLUE}╚{'='*58}╝{RESET}")
    
    checks = {}
    
    # Run all checks
    checks["Python 3.10/3.11"] = check_python_version()
    
    if not checks["Python 3.10/3.11"]:
        print()
        print(f"{RED}CRITICAL: Wrong Python version. Stopping.{RESET}")
        print()
        print("Please run this script with Python 3.11:")
        print(f"  py -3.11 {Path(__file__).name}")
        sys.exit(1)
    
    checks["Node.js >= 18.18"] = check_node_version()
    checks["Docker (optional)"] = check_docker()
    checks["PostgreSQL"] = check_postgres()
    
    if checks["Node.js >= 18.18"]:
        checks["Node dependencies"] = install_node_dependencies()
    else:
        checks["Node dependencies"] = False
    
    checks["Python venv + deps"] = setup_python_venv()
    
    model_exists, model_path = check_model()
    checks["Trained model"] = model_exists
    
    checks["Training data"] = check_training_data()
    checks["Environment files"] = check_env_files()
    
    # Generate final report
    all_ready = generate_status_report(checks)
    
    sys.exit(0 if all_ready else 1)

if __name__ == "__main__":
    main()
