# Windows Build Script (build.bat)
# Save this as "build.bat" in the project root

@echo off
echo Building Text-to-3D Executable for Windows...
echo.

REM Activate conda environment
call conda activate text-to-3d

REM Install build dependencies
pip install pyinstaller

REM Run the build script
python build_executable.py

echo.
echo Build completed! Check the 'dist' folder for your executable.
pause

# =============================================================================

# macOS/Linux Build Script (build.sh)
# Save this as "build.sh" in the project root and make it executable: chmod +x build.sh

#!/bin/bash
echo "Building Text-to-3D Executable..."

# Activate conda environment
source $(conda info --base)/etc/profile.d/conda.sh
conda activate text-to-3d

# Install build dependencies
pip install pyinstaller

# Run the build script
python build_executable.py

echo ""
echo "Build completed! Check the 'dist' folder for your executable."

# =============================================================================

# Universal Build Script (build_all.py)
# This can be run on any platform

#!/usr/bin/env python3
import subprocess
import sys
import platform

def main():
    system = platform.system().lower()
    
    print(f"Building for {system}...")
    
    # Ensure we're in the right environment
    try:
        subprocess.run([sys.executable, "-c", "import cadquery"], check=True)
        print("✓ CadQuery available")
    except subprocess.CalledProcessError:
        print("✗ CadQuery not found. Please run setup.py first.")
        sys.exit(1)
    
    # Run the main build script
    subprocess.run([sys.executable, "build_executable.py"])

if __name__ == "__main__":
    main()
