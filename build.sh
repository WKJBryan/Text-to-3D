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
