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
