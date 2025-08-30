#!/usr/bin/env python3
"""
Deployment script for Text-to-3D
Creates distributable packages with all necessary components
"""
import shutil
import zipfile
import platform
import subprocess
from pathlib import Path
import os

def create_distribution_package():
    """Create a complete distribution package"""
    system = platform.system().lower()
    
    # Create package directory
    package_name = f"Text-to-3D-{system}"
    package_dir = Path("release") / package_name
    
    # Clean and create directories
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir(parents=True)
    
    print(f"Creating distribution package: {package_name}")
    
    # Copy executable files
    dist_dir = Path("dist")
    if not dist_dir.exists():
        print("Error: No dist directory found. Run build_executable.py first.")
        return False
    
    if system == "windows":
        if (dist_dir / "Text-to-3D" / "Text-to-3D.exe").exists():
            shutil.copytree(dist_dir / "Text-to-3D", package_dir / "Text-to-3D")
        else:
            print("Error: Windows executable not found")
            return False
    elif system == "darwin":
        if (dist_dir / "Text-to-3D.app").exists():
            shutil.copytree(dist_dir / "Text-to-3D.app", package_dir / "Text-to-3D.app")
        else:
            print("Error: macOS app bundle not found")
            return False
    else:  # Linux
        if (dist_dir / "Text-to-3D" / "Text-to-3D").exists():
            shutil.copytree(dist_dir / "Text-to-3D", package_dir / "Text-to-3D")
        else:
            print("Error: Linux executable not found")
            return False
    
    # Copy additional files
    additional_files = [
        "README.txt",
        "install.bat" if system == "windows" else "install.sh",
    ]
    
    for file_name in additional_files:
        src_file = dist_dir / file_name
        if src_file.exists():
            shutil.copy2(src_file, package_dir)
    
    # Copy documentation and examples
    docs_to_copy = [
        "README.md",
        ".env.example",
        "requirements.txt"
    ]
    
    for doc in docs_to_copy:
        if Path(doc).exists():
            shutil.copy2(doc, package_dir)
    
    # Copy reference examples if they exist
    if Path("reference_examples").exists():
        shutil.copytree("reference_examples", package_dir / "reference_examples")
    
    # Create a simple launcher script
    create_launcher_scripts(package_dir, system)
    
    # Create package info
    create_package_info(package_dir, system)
    
    print(f"Distribution package created: {package_dir}")
    return package_dir

def create_launcher_scripts(package_dir, system):
    """Create simple launcher scripts"""
    if system == "windows":
        launcher_content = '''@echo off
echo Starting Text-to-3D CAD Generator...

REM Check if Ollama is running
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
if "%ERRORLEVEL%"=="1" (
    echo Starting Ollama service...
    start /B ollama serve
    timeout /t 5 >nul
)

REM Check if model exists
ollama list | findstr "llama3.1:8b" >nul
if %errorlevel% neq 0 (
    echo Downloading AI model (this may take a few minutes)...
    ollama pull llama3.1:8b
)

REM Launch application
start "" "Text-to-3D\\Text-to-3D.exe"
'''
        
        with open(package_dir / "Launch Text-to-3D.bat", 'w') as f:
            f.write(launcher_content)
    
    else:  # macOS/Linux
        launcher_content = '''#!/bin/bash
echo "Starting Text-to-3D CAD Generator..."

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "Ollama not found. Please install Ollama first:"
    echo "curl -fsSL https://ollama.ai/install.sh | sh"
    exit 1
fi

# Start Ollama if not running
if ! pgrep -x "ollama" > /dev/null; then
    echo "Starting Ollama service..."
    ollama serve &
    sleep 5
fi

# Check if model exists
if ! ollama list | grep -q "llama3.1:8b"; then
    echo "Downloading AI model (this may take a few minutes)..."
    ollama pull llama3.1:8b
fi

# Launch application
if [[ "$OSTYPE" == "darwin"* ]]; then
    open "Text-to-3D.app"
else
    ./Text-to-3D/Text-to-3D
fi
'''
        
        launcher_file = package_dir / "Launch Text-to-3D.sh"
        with open(launcher_file, 'w') as f:
            f.write(launcher_content)
        
        # Make executable
        os.chmod(launcher_file, 0o755)

def create_package_info(package_dir, system):
    """Create package information file"""
    info_content = f'''Text-to-3D CAD Generator - Distribution Package
Platform: {system}
Build Date: {subprocess.check_output(['date'], shell=True, text=True).strip()}

QUICK START:
1. Extract all files to a folder
2. {"Run 'Launch Text-to-3D.bat'" if system == "windows" else "Run './Launch Text-to-3D.sh'"}
3. Wait for AI model download (first time only)
4. Start creating 3D models!

REQUIREMENTS:
- Minimum 8GB RAM
- 10GB free storage for AI models
- Internet connection (first run only)

TROUBLESHOOTING:
- If Ollama fails to install, download manually from https://ollama.ai
- For memory issues, use smaller model: ollama pull llama3.2:3b
- Check logs in application for detailed error messages

SUPPORT:
- GitHub: https://github.com/WKJBryan/Text-to-3D
- Email: bryan_wang@mymail.sutd.edu.sg

Built with ❤️ for the maker community
'''
    
    with open(package_dir / "PACKAGE_INFO.txt", 'w') as f:
        f.write(info_content)

def create_zip_package(package_dir):
    """Create a ZIP file of the distribution package"""
    zip_name = f"{package_dir.name}.zip"
    zip_path = package_dir.parent / zip_name
    
    print(f"Creating ZIP package: {zip_name}")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(package_dir.parent)
                zipf.write(file_path, arcname)
    
    print(f"ZIP package created: {zip_path}")
    print(f"Package size: {zip_path.stat().st_size / (1024*1024):.1f} MB")
    
    return zip_path

def main():
    """Main deployment function"""
    print("=" * 50)
    print("Text-to-3D Deployment Package Creator")
    print("=" * 50)
    
    # Check if executable exists
    if not Path("dist").exists():
        print("Error: No dist directory found.")
        print("Please run 'python build_executable.py' first.")
        return
    
    # Create distribution package
    package_dir = create_distribution_package()
    if not package_dir:
        print("Failed to create distribution package")
        return
    
    # Create ZIP package
    zip_path = create_zip_package(package_dir)
    
    print("\n" + "=" * 50)
    print("Deployment completed successfully!")
    print("=" * 50)
    print(f"Distribution folder: {package_dir}")
    print(f"ZIP package: {zip_path}")
    print("\nThe ZIP file contains everything needed to run Text-to-3D")
    print("on systems without Python/conda installed.")

if __name__ == "__main__":
    main()
