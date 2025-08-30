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
