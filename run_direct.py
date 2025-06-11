import subprocess
import sys
import importlib
import os

# List of required packages
required_packages = [
    'pyotp',
    'flask',
    'flask_login',
    'flask_sqlalchemy',
    'flask_wtf',
    'werkzeug',
    'email_validator',
    'jinja2',
    'itsdangerous',
    'click',
    'sqlalchemy',
    'flask_migrate'
]

def check_and_install_package(package):
    try:
        importlib.import_module(package)
        print(f"✓ {package} is already installed")
    except ImportError:
        print(f"✗ {package} is not installed. Installing...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"✓ {package} has been installed")
        except subprocess.CalledProcessError:
            print(f"✗ Failed to install {package}")
            return False
    return True

print("Checking required packages...")
all_installed = True
for package in required_packages:
    if not check_and_install_package(package):
        all_installed = False

if not all_installed:
    print("Failed to install all required packages. Please check the error messages above.")
    sys.exit(1)

print("All required packages are installed. Starting the application...")

# Run the app
if os.path.exists('app.py'):
    import app
    app.app.run(debug=True)
else:
    print("app.py not found in the current directory.")
    sys.exit(1) 