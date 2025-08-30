#!/usr/bin/env python3
"""
Setup script for Text-to-3D CAD Generation System
Handles conda environment creation and dependency installation
"""
import subprocess
import sys
import os
import platform
from pathlib import Path

def run_command(command, shell=True, check=True):
    """Run a command and handle errors"""
    try:
        result = subprocess.run(command, shell=shell, check=check, 
                              capture_output=True, text=True)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error: {e.stderr}")
        return None

def check_conda():
    """Check if conda is available"""
    result = run_command("conda --version", check=False)
    if result and result.returncode == 0:
        return True
    
    # Try mamba as alternative
    result = run_command("mamba --version", check=False)
    return result and result.returncode == 0

def install_ollama():
    """Install Ollama based on the platform"""
    system = platform.system().lower()
    
    if system == "linux" or system == "darwin":  # macOS
        print("Installing Ollama...")
        result = run_command("curl -fsSL https://ollama.ai/install.sh | sh")
        if result and result.returncode == 0:
            print("Ollama installed successfully")
        else:
            print("Please install Ollama manually from https://ollama.ai")
    else:
        print("Please install Ollama manually from https://ollama.ai")

def setup_environment():
    """Set up the conda environment"""
    if not check_conda():
        print("Conda not found. Please install Miniconda or Anaconda first.")
        print("Download from: https://docs.conda.io/en/latest/miniconda.html")
        return False
    
    env_name = "text-to-3d"
    python_version = "3.11"
    
    print(f"Creating conda environment: {env_name}")
    
    # Create conda environment
    create_cmd = f"conda create -n {env_name} python={python_version} -y"
    if run_command(create_cmd):
        print(f"Environment {env_name} created successfully")
    else:
        print("Failed to create conda environment")
        return False
    
    # Install CadQuery via conda
    print("Installing CadQuery...")
    cadquery_cmd = f"conda activate {env_name} && mamba install -c conda-forge cadquery -y"
    if not run_command(cadquery_cmd):
        # Fallback to conda if mamba fails
        cadquery_cmd = f"conda activate {env_name} && conda install -c conda-forge cadquery -y"
        if not run_command(cadquery_cmd):
            print("Failed to install CadQuery. Please install manually.")
            return False
    
    print("CadQuery installed successfully")
    return True

def install_python_deps():
    """Install Python dependencies via pip"""
    env_name = "text-to-3d"
    
    print("Installing Python dependencies...")
    pip_cmd = f"conda activate {env_name} && pip install -r requirements.txt"
    
    if run_command(pip_cmd):
        print("Python dependencies installed successfully")
        return True
    else:
        print("Failed to install Python dependencies")
        return False

def setup_ollama_model():
    """Download and setup Ollama model"""
    print("Setting up Ollama model...")
    
    # Start Ollama service
    start_cmd = "ollama serve &"
    run_command(start_cmd, check=False)
    
    # Wait a moment for service to start
    import time
    time.sleep(3)
    
    # Pull the model
    model_cmd = "ollama pull llama3.1:8b"
    if run_command(model_cmd):
        print("Ollama model downloaded successfully")
        return True
    else:
        print("Failed to download Ollama model. Please run 'ollama pull llama3.1:8b' manually")
        return False

def create_directories():
    """Create necessary directories"""
    directories = ['exports', 'embeddings', 'logs']
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"Created directory: {directory}")

def copy_env_file():
    """Copy .env.example to .env if it doesn't exist"""
    env_file = Path('.env')
    env_example = Path('.env.example')
    
    if not env_file.exists() and env_example.exists():
        env_file.write_text(env_example.read_text())
        print("Created .env file from .env.example")

def main():
    """Main setup function"""
    print("=" * 50)
    print("Text-to-3D CAD Generation Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path('main.py').exists():
        print("Error: Please run this script from the project root directory")
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Copy environment file
    copy_env_file()
    
    # Install Ollama
    install_ollama()
    
    # Setup conda environment
    if not setup_environment():
        print("Failed to setup conda environment")
        sys.exit(1)
    
    # Install Python dependencies
    if not install_python_deps():
        print("Failed to install Python dependencies")
        sys.exit(1)
    
    # Setup Ollama model
    setup_ollama_model()
    
    print("\n" + "=" * 50)
    print("Setup completed!")
    print("=" * 50)
    print("To run the application:")
    print("1. conda activate text-to-3d")
    print("2. python main.py")
    print("\nTo test the installation:")
    print("1. python test_rag_search.py")
    print("2. python test_handle_removal.py")

if __name__ == "__main__":
    main()
