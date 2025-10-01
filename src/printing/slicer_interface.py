# src/printing/prusaslicer_interface.py
"""FIXED: PrusaSlicer Interface - Properly Loads config.ini"""
import os
import subprocess
import json
import re
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

load_dotenv()

@dataclass
class SlicingProfile:
    """Slicing profile configuration"""
    name: str
    layer_height: float
    infill_percentage: int
    print_speed: int
    travel_speed: int
    extruder_temp: int
    bed_temp: int
    support_material: str = "auto"
    brim_width: int = 3
    retraction_length: float = 0.5
    retraction_speed: int = 40

class PrusaSlicerInterface:
    """FIXED: Interface for PrusaSlicer with proper config.ini loading"""
    
    def __init__(self):
        self.prusaslicer_path = os.getenv('PRUSASLICER_PATH', 'C:\\Program Files\\Prusa3D\\PrusaSlicer\\prusa-slicer.exe')
        self.config_path = Path(os.getenv('SLICER_CONFIG_PATH', './config.ini'))
        self.temp_gcode_dir = Path(os.getenv('TEMP_GCODE_DIR', './exports'))
        
        # Create directories
        self.temp_gcode_dir.mkdir(exist_ok=True)
        
        # Verify config.ini exists
        if not self.config_path.exists():
            print(f"⚠️ WARNING: config.ini not found at {self.config_path}")
            print(f"   Create a config.ini or update SLICER_CONFIG_PATH in .env")
        else:
            print(f"✅ Found config.ini: {self.config_path}")
        
        self._ensure_prusaslicer_available()
    
    def _ensure_prusaslicer_available(self) -> bool:
        """Check if PrusaSlicer is available"""
        try:
            possible_paths = [
                self.prusaslicer_path,
                'C:\\Program Files\\Prusa3D\\PrusaSlicer\\prusa-slicer.exe',
                'C:\\Program Files (x86)\\Prusa3D\\PrusaSlicer\\prusa-slicer.exe',
                'prusa-slicer.exe',
                'prusa-slicer'
            ]
            
            for path in possible_paths:
                try:
                    result = subprocess.run([path, '--version'], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        self.prusaslicer_path = path
                        print(f"✅ Found PrusaSlicer: {path}")
                        print(f"   Version: {result.stdout.strip()}")
                        return True
                except (subprocess.SubprocessError, FileNotFoundError):
                    continue
            
            print(f"❌ PrusaSlicer not found. Please install or update path in .env")
            print(f"   Tried paths: {possible_paths}")
            return False
            
        except Exception as e:
            print(f"❌ Error checking PrusaSlicer: {e}")
            return False
    
    def slice_file(self, stl_path: str, profile_name: str = None, 
                   custom_settings: Optional[Dict] = None) -> Dict:
        """FIXED: Slice STL file using config.ini"""
        
        stl_path = Path(stl_path)
        
        if not stl_path.exists():
            raise FileNotFoundError(f"STL file not found: {stl_path}")
        
        # Generate output filename with profile name
        if profile_name:
            gcode_filename = f"{stl_path.stem}_{profile_name.replace(' ', '_').lower()}.gcode"
        else:
            gcode_filename = f"{stl_path.stem}.gcode"
        
        gcode_path = self.temp_gcode_dir / gcode_filename
        
        try:
            # CRITICAL FIX: Use absolute paths for everything
            abs_stl_path = stl_path.resolve()
            abs_gcode_path = gcode_path.resolve()
            abs_config_path = self.config_path.resolve()
            
            print(f"🔄 Slicing {stl_path.name} with config.ini...")
            print(f"   Config: {abs_config_path}")
            print(f"   Output: {gcode_filename}")
            
            # CRITICAL FIX: Build command to load config.ini
            cmd = [
                self.prusaslicer_path,
                '--load', str(abs_config_path),  # Load the entire config.ini
                '--export-gcode',
                '--output', str(abs_gcode_path),
                str(abs_stl_path)
            ]
            
            # Add custom settings if provided (override config.ini)
            if custom_settings:
                for key, value in custom_settings.items():
                    cmd.append(f'--{key}={value}')
            
            print(f"   Command: {' '.join(cmd[:5])}...")  # Don't print full command
            
            # Execute slicing
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                print(f"❌ PrusaSlicer stderr: {result.stderr}")
                raise Exception(f"PrusaSlicer failed with code {result.returncode}")
            
            if not gcode_path.exists():
                raise Exception("G-code file was not created")
            
            # Parse G-code metadata
            file_size_mb = gcode_path.stat().st_size / 1024 / 1024
            print_time = self._extract_print_time(gcode_path)
            filament_used = self._extract_filament_usage(gcode_path)
            layer_height = self._extract_layer_height(gcode_path)
            
            success_info = {
                'success': True,
                'gcode_path': str(gcode_path),
                'gcode_filename': gcode_filename,
                'profile_used': profile_name or 'config.ini',
                'file_size_mb': file_size_mb,
                'estimated_print_time': print_time,
                'estimated_filament_mm': filament_used,
                'layer_height': layer_height,
            }
            
            print(f"✅ Slicing complete!")
            print(f"   File size: {file_size_mb:.2f} MB")
            print(f"   Estimated time: {print_time}")
            print(f"   Filament: {filament_used:.1f}mm")
            
            return success_info
            
        except subprocess.TimeoutExpired:
            raise Exception("Slicing timed out after 5 minutes")
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'profile_used': profile_name or 'config.ini'
            }
    
    def _extract_print_time(self, gcode_path: Path) -> str:
        """FIXED: Extract print time from G-code comments"""
        try:
            with open(gcode_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    # Stop at first non-comment G-code line
                    if line.strip() and not line.startswith(';'):
                        break
                    
                    # PrusaSlicer formats:
                    # ; estimated printing time (normal mode) = 1h 23m 45s
                    if 'estimated printing time' in line.lower():
                        # Extract everything after the = sign
                        if '=' in line:
                            time_str = line.split('=')[-1].strip()
                            # Clean up
                            time_str = time_str.replace('(normal mode)', '').strip()
                            return time_str
        except Exception as e:
            print(f"⚠️ Could not extract print time: {e}")
        
        return "Unknown"
    
    def _extract_filament_usage(self, gcode_path: Path) -> float:
        """FIXED: Extract filament usage from G-code"""
        try:
            with open(gcode_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if line.strip() and not line.startswith(';'):
                        break
                    
                    # ; filament used [mm] = 1234.56
                    # ; filament used = 1234.56mm
                    if 'filament used' in line.lower() and 'mm' in line.lower():
                        # Extract number
                        match = re.search(r'(\d+\.?\d*)\s*mm', line)
                        if match:
                            return float(match.group(1))
                        
                        # Alternative format: after =
                        if '=' in line:
                            value_str = line.split('=')[-1].strip()
                            match = re.search(r'(\d+\.?\d*)', value_str)
                            if match:
                                return float(match.group(1))
        except Exception as e:
            print(f"⚠️ Could not extract filament usage: {e}")
        
        return 0.0
    
    def _extract_layer_height(self, gcode_path: Path) -> float:
        """Extract layer height from G-code"""
        try:
            with open(gcode_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if line.strip() and not line.startswith(';'):
                        break
                    
                    # ; layer_height = 0.3
                    if 'layer_height' in line.lower() and '=' in line:
                        value_str = line.split('=')[-1].strip()
                        match = re.search(r'(\d+\.?\d*)', value_str)
                        if match:
                            return float(match.group(1))
        except Exception:
            pass
        
        return 0.3  # Default
    
    def validate_stl_for_printing(self, stl_path: str) -> Dict:
        """Validate STL file for 3D printing"""
        stl_path = Path(stl_path)
        
        if not stl_path.exists():
            return {'valid': False, 'error': 'STL file not found'}
        
        try:
            file_size_mb = stl_path.stat().st_size / 1024 / 1024
            
            max_size = int(os.getenv('MAX_FILE_SIZE_MB', 50))
            if file_size_mb > max_size:
                return {
                    'valid': False, 
                    'error': f'STL file too large: {file_size_mb:.1f}MB (max: {max_size}MB)'
                }
            
            # Basic STL validation
            with open(stl_path, 'rb') as f:
                header = f.read(80)
                if len(header) < 80:
                    return {'valid': False, 'error': 'Invalid STL file (too short)'}
            
            return {
                'valid': True,
                'file_size_mb': file_size_mb,
                'ready_for_slicing': True
            }
            
        except Exception as e:
            return {'valid': False, 'error': f'STL validation failed: {e}'}
    
    def cleanup_old_gcode(self, keep_recent: int = 10):
        """Clean up old G-code files"""
        gcode_files = sorted(self.temp_gcode_dir.glob('*.gcode'), 
                           key=lambda x: x.stat().st_mtime, reverse=True)
        
        deleted_count = 0
        for gcode_file in gcode_files[keep_recent:]:
            try:
                gcode_file.unlink()
                deleted_count += 1
            except Exception as e:
                print(f"❌ Failed to delete {gcode_file}: {e}")
        
        if deleted_count > 0:
            print(f"🧹 Cleaned up {deleted_count} old G-code files")