#!/usr/bin/env python3
"""
Build script for creating executable files (.exe/.app) for Text-to-3D
Uses PyInstaller to package the application
"""
import subprocess
import sys
import os
import platform
import shutil
from pathlib import Path

def run_command(command, shell=True):
    """Run a command and print output"""
    try:
        result = subprocess.run(command, shell=shell, check=True, 
                              capture_output=True, text=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return False

def install_build_deps():
    """Install build dependencies"""
    print("Installing build dependencies...")
    deps = ["pyinstaller", "auto-py-to-exe"]
    
    for dep in deps:
        if not run_command(f"pip install {dep}"):
            print(f"Failed to install {dep}")
            return False
    return True

def create_spec_file():
    """Create PyInstaller spec file"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

# Get the project root directory
project_root = Path.cwd()

a = Analysis(
    ['main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        ('src', 'src'),
        ('embeddings', 'embeddings'),
        ('.env.example', '.'),
        ('README.md', '.'),
    ],
    hiddenimports=[
        'cadquery',
        'sentence_transformers',
        'faiss',
        'customtkinter',
        'ollama',
        'transformers',
        'torch',
        'numpy',
        'PIL',
        'tkinter',
        'json',
        're',
        'os',
        'sys',
        'pathlib',
        'typing',
        'threading',
        'queue',
        'time',
        'datetime',
        'logging',
        'subprocess',
        'shutil',
        'tempfile',
        'requests',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Text-to-3D',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Set to True for debugging
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if Path('icon.ico').exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Text-to-3D',
)

# For macOS app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='Text-to-3D.app',
        icon='icon.icns' if Path('icon.icns').exists() else None,
        bundle_identifier='com.text-to-3d.app',
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSAppleScriptEnabled': False,
            'CFBundleDocumentTypes': [
                {
                    'CFBundleTypeName': 'Python Script',
                    'CFBundleTypeExtensions': ['py'],
                    'CFBundleTypeRole': 'Editor'
                }
            ]
        },
    )
'''
    
    with open('text-to-3d.spec', 'w') as f:
        f.write(spec_content)
    
    print("Created PyInstaller spec file: text-to-3d.spec")

def build_executable():
    """Build the executable using PyInstaller"""
    system = platform.system().lower()
    
    print(f"Building executable for {system}...")
    
    # Build using the spec file
    build_cmd = "pyinstaller text-to-3d.spec --clean --noconfirm"
    
    if not run_command(build_cmd):
        print("Build failed!")
        return False
    
    # Copy additional files
    dist_dir = Path('dist/Text-to-3D')
    if dist_dir.exists():
        # Copy environment file
        if Path('.env.example').exists():
            shutil.copy2('.env.example', dist_dir)
        
        # Copy reference examples if they exist
        if Path('reference_examples').exists():
            shutil.copytree('reference_examples', dist_dir / 'reference_examples', dirs_exist_ok=True)
        
        print(f"Build completed! Executable available in: {dist_dir}")
        
        if system == "windows":
            print("Windows executable: dist/Text-to-3D/Text-to-3D.exe")
        elif system == "darwin":
            print("macOS app bundle: dist/Text-to-3D.app")
        else:
            print("Linux executable: dist/Text-to-3D/Text-to-3D")
        
        return True
    
    print("Build directory not found!")
    return False

def create_installer_script():
    """Create installer/setup script for the executable"""
    system = platform.system().lower()
    
    if system == "windows":
        installer_content = '''@echo off
echo Installing Text-to-3D CAD Generator...
echo.

REM Check if Ollama is installed
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Ollama not found. Please install Ollama from https://ollama.ai
    pause
    exit /b 1
)

REM Create application directory
set APP_DIR=%LOCALAPPDATA%\\Text-to-3D
if not exist "%APP_DIR%" mkdir "%APP_DIR%"

REM Copy files
echo Copying application files...
xcopy /E /I /Y "Text-to-3D" "%APP_DIR%"

REM Create desktop shortcut
echo Creating desktop shortcut...
set SHORTCUT_PATH=%USERPROFILE%\\Desktop\\Text-to-3D.lnk
powershell "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SHORTCUT_PATH%'); $Shortcut.TargetPath = '%APP_DIR%\\Text-to-3D.exe'; $Shortcut.Save()"

REM Start Ollama and download model
echo Starting Ollama and downloading model...
start /B ollama serve
timeout /t 3 >nul
ollama pull llama3.1:8b

echo.
echo Installation completed!
echo Text-to-3D has been installed to: %APP_DIR%
echo Desktop shortcut created.
pause
'''
        
        with open('dist/install.bat', 'w') as f:
            f.write(installer_content)
        
        print("Created Windows installer: dist/install.bat")
    
    elif system == "darwin":
        installer_content = '''#!/bin/bash
echo "Installing Text-to-3D CAD Generator..."

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "Ollama not found. Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
fi

# Create Applications directory entry
APP_DIR="/Applications/Text-to-3D.app"
if [ -d "Text-to-3D.app" ]; then
    echo "Copying application to Applications folder..."
    sudo cp -R "Text-to-3D.app" "/Applications/"
    echo "Text-to-3D.app installed to /Applications/"
else
    echo "Text-to-3D.app not found in current directory"
    exit 1
fi

# Start Ollama and download model
echo "Starting Ollama and downloading model..."
ollama serve &
sleep 3
ollama pull llama3.1:8b

echo ""
echo "Installation completed!"
echo "Text-to-3D is now available in your Applications folder."
'''
        
        with open('dist/install.sh', 'w') as f:
            f.write(installer_content)
        
        # Make the installer executable
        os.chmod('dist/install.sh', 0o755)
        
        print("Created macOS installer: dist/install.sh")

def create_readme():
    """Create README for the executable distribution"""
    readme_content = '''# Text-to-3D CAD Generator - Executable Distribution

## Quick Start

### Windows
1. Extract all files to a folder
2. Run `install.bat` as Administrator
3. Wait for Ollama to download (this may take several minutes)
4. Launch "Text-to-3D" from your desktop

### macOS
1. Extract all files to a folder
2. Run `sudo ./install.sh` in Terminal
3. Wait for Ollama to download (this may take several minutes)
4. Launch "Text-to-3D" from Applications folder

### Linux
1. Extract all files to a folder
2. Install Ollama: `curl -fsSL https://ollama.ai/install.sh | sh`
3. Start Ollama: `ollama serve &`
4. Download model: `ollama pull llama3.1:8b`
5. Run: `./Text-to-3D`

## System Requirements

- **RAM**: Minimum 8GB (16GB recommended)
- **Storage**: 10GB free space for models
- **OS**: Windows 10+, macOS 10.15+, or modern Linux

## Troubleshooting

### "Model not found" error
1. Ensure Ollama is running: `ollama serve`
2. Download the model: `ollama pull llama3.1:8b`
3. Check available models: `ollama list`

### "CadQuery import error"
This usually means the executable was built without proper CadQuery support.
Try running from source instead.

### Performance issues
1. Close other applications to free RAM
2. Use a smaller model: `ollama pull llama3.2:3b`
3. Update .env file to use the smaller model

## Using the Application

1. **Start a conversation**: Type what you want to create (e.g., "I need a cup")
2. **Follow prompts**: The AI will ask for specific dimensions
3. **Generate**: Click generate to create your 3D model
4. **Export**: Save as STL, STEP, or other formats

## Support

- Issues: https://github.com/WKJBryan/Text-to-3D/issues
- Documentation: https://github.com/WKJBryan/Text-to-3D
- Email: bryan_wang@mymail.sutd.edu.sg

Built with ❤️ for the maker community
'''
    
    with open('dist/README.txt', 'w') as f:
        f.write(readme_content)
    
    print("Created distribution README: dist/README.txt")

def main():
    """Main build function"""
    print("=" * 50)
    print("Text-to-3D Executable Builder")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path('main.py').exists():
        print("Error: Please run this script from the project root directory")
        sys.exit(1)
    
    # Install build dependencies
    if not install_build_deps():
        print("Failed to install build dependencies")
        sys.exit(1)
    
    # Create spec file
    create_spec_file()
    
    # Build executable
    if not build_executable():
        print("Failed to build executable")
        sys.exit(1)
    
    # Create installer scripts
    create_installer_script()
    
    # Create distribution README
    create_readme()
    
    print("\n" + "=" * 50)
    print("Build completed successfully!")
    print("=" * 50)
    print("Files created in 'dist/' directory:")
    
    system = platform.system().lower()
    if system == "windows":
        print("- Text-to-3D.exe (main executable)")
        print("- install.bat (installer script)")
    elif system == "darwin":
        print("- Text-to-3D.app (macOS application bundle)")
        print("- install.sh (installer script)")
    else:
        print("- Text-to-3D (Linux executable)")
    
    print("- README.txt (distribution documentation)")

if __name__ == "__main__":
    main()
