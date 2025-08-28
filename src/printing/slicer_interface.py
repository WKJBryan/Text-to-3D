# src/printing/prusaslicer_interface.py
"""PrusaSlicer CLI Interface for AI Manufacturing Pipeline"""
import os
import subprocess
import json
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
    brim_width: int = 5
    retraction_length: float = 0.5
    retraction_speed: int = 40

class PrusaSlicerInterface:
    """Interface for PrusaSlicer CLI operations"""
    
    def __init__(self):
        self.prusaslicer_path = os.getenv('PRUSASLICER_PATH', 'C:\\Program Files\\Prusa3D\\PrusaSlicer\\prusa-slicer.exe')
        self.config_dir = Path(os.getenv('SLICER_CONFIG_DIR', './slicer_configs'))
        self.temp_gcode_dir = Path(os.getenv('TEMP_GCODE_DIR', './temp_gcode'))
        
        # Create directories
        self.config_dir.mkdir(exist_ok=True)
        self.temp_gcode_dir.mkdir(exist_ok=True)
        
        # Voron 2.4 specifications
        self.bed_size = (
            int(os.getenv('PRINTER_BED_X', 350)),
            int(os.getenv('PRINTER_BED_Y', 350)),
            int(os.getenv('PRINTER_BED_Z', 350))
        )
        self.nozzle_diameter = float(os.getenv('NOZZLE_DIAMETER', 0.4))
        
        # Initialize profiles
        self.profiles = self._create_default_profiles()
        self._ensure_prusaslicer_available()
    
    def _ensure_prusaslicer_available(self) -> bool:
        """Check if PrusaSlicer is available"""
        try:
            # Try common Windows paths
            possible_paths = [
                self.prusaslicer_path,
                'C:\\Program Files\\Prusa3D\\PrusaSlicer\\prusa-slicer.exe',
                'C:\\Program Files (x86)\\Prusa3D\\PrusaSlicer\\prusa-slicer.exe',
                'prusa-slicer.exe',  # If in PATH
                'prusa-slicer'       # Linux/Mac style
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
    
    def _create_default_profiles(self) -> Dict[str, SlicingProfile]:
        """Create default slicing profiles for Voron 2.4"""
        return {
            'draft': SlicingProfile(
                name="Draft (Fast)",
                layer_height=0.3,
                infill_percentage=15,
                print_speed=80,
                travel_speed=150,
                extruder_temp=int(os.getenv('EXTRUDER_TEMP', 210)),
                bed_temp=int(os.getenv('BED_TEMP', 60)),
                support_material="auto",
                brim_width=3
            ),
            'standard': SlicingProfile(
                name="Standard (Balanced)",
                layer_height=float(os.getenv('LAYER_HEIGHT', 0.2)),
                infill_percentage=int(os.getenv('INFILL_PERCENTAGE', 20)),
                print_speed=int(os.getenv('PRINT_SPEED', 60)),
                travel_speed=int(os.getenv('TRAVEL_SPEED', 150)),
                extruder_temp=int(os.getenv('EXTRUDER_TEMP', 210)),
                bed_temp=int(os.getenv('BED_TEMP', 60)),
                support_material=os.getenv('SUPPORT_MATERIAL', 'auto'),
                brim_width=int(os.getenv('BRIM_WIDTH', 5))
            ),
            'fine': SlicingProfile(
                name="Fine (High Quality)",
                layer_height=0.1,
                infill_percentage=25,
                print_speed=40,
                travel_speed=120,
                extruder_temp=int(os.getenv('EXTRUDER_TEMP', 210)),
                bed_temp=int(os.getenv('BED_TEMP', 60)),
                support_material="auto",
                brim_width=8
            ),
            'vase': SlicingProfile(
                name="Vase Mode (Single Wall)",
                layer_height=0.2,
                infill_percentage=0,
                print_speed=50,
                travel_speed=120,
                extruder_temp=int(os.getenv('EXTRUDER_TEMP', 210)),
                bed_temp=int(os.getenv('BED_TEMP', 60)),
                support_material="none",
                brim_width=0
            )
        }
    
    def slice_file(self, stl_path: str, profile_name: str = 'standard', 
                   custom_settings: Optional[Dict] = None) -> Dict:
        """Slice STL file using PrusaSlicer CLI"""
        
        if profile_name not in self.profiles:
            raise ValueError(f"Unknown profile: {profile_name}. Available: {list(self.profiles.keys())}")
        
        profile = self.profiles[profile_name]
        stl_path = Path(stl_path)
        
        if not stl_path.exists():
            raise FileNotFoundError(f"STL file not found: {stl_path}")
        
        # Generate output filename
        gcode_filename = f"{stl_path.stem}_{profile_name}.gcode"
        gcode_path = self.temp_gcode_dir / gcode_filename
        
        try:
            # Build PrusaSlicer command
            cmd = self._build_slice_command(stl_path, gcode_path, profile, custom_settings)
            
            print(f"🔄 Slicing {stl_path.name} with {profile.name} profile...")
            print(f"   Output: {gcode_path.name}")
            
            # Execute slicing
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                raise Exception(f"PrusaSlicer failed: {result.stderr}")
            
            if not gcode_path.exists():
                raise Exception("G-code file was not created")
            
            # Get file info
            file_size_mb = gcode_path.stat().st_size / 1024 / 1024
            print_time = self._estimate_print_time(gcode_path)
            filament_used = self._estimate_filament_usage(gcode_path)
            
            success_info = {
                'success': True,
                'gcode_path': str(gcode_path),
                'gcode_filename': gcode_filename,
                'profile_used': profile.name,
                'file_size_mb': file_size_mb,
                'estimated_print_time': print_time,
                'estimated_filament_mm': filament_used,
                'layer_height': profile.layer_height,
                'infill_percentage': profile.infill_percentage,
                'settings_summary': self._get_settings_summary(profile, custom_settings)
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
                'profile_used': profile.name
            }
    
    def _build_slice_command(self, stl_path: Path, gcode_path: Path, 
                           profile: SlicingProfile, custom_settings: Optional[Dict] = None) -> List[str]:
        """Build PrusaSlicer CLI command"""
        
        cmd = [
            self.prusaslicer_path,
            '--export-gcode',
            str(stl_path),
            '--output', str(gcode_path),
            
            # Voron 2.4 printer settings
            f'--bed-shape=0x0,{self.bed_size[0]}x0,{self.bed_size[0]}x{self.bed_size[1]},0x{self.bed_size[1]}',
            f'--max-print-height={self.bed_size[2]}',
            f'--nozzle-diameter={self.nozzle_diameter}',
            
            # Profile settings
            f'--layer-height={profile.layer_height}',
            f'--fill-density={profile.infill_percentage}%',
            f'--perimeter-speed={profile.print_speed}',
            f'--travel-speed={profile.travel_speed}',
            f'--temperature={profile.extruder_temp}',
            f'--bed-temperature={profile.bed_temp}',
            f'--brim-width={profile.brim_width}',
            f'--retract-length={profile.retraction_length}',
            f'--retract-speed={profile.retraction_speed}',
            
            # Voron-specific optimizations
            f'--max-volumetric-speed=15',
            f'--pressure-advance={os.getenv("PRESSURE_ADVANCE", 0.04)}',
            
            # Support settings
            '--support-material=' + ('1' if profile.support_material == 'auto' else '0'),
            
            # Quality settings
            '--infill-every-layers=1',
            '--solid-infill-every-layers=0',
            '--fill-pattern=gyroid',
            '--perimeters=3',
            '--top-solid-layers=5',
            '--bottom-solid-layers=4',
        ]
        
        # Add custom settings if provided
        if custom_settings:
            for key, value in custom_settings.items():
                cmd.append(f'--{key}={value}')
        
        return cmd
    
    def _estimate_print_time(self, gcode_path: Path) -> str:
        """Estimate print time from G-code comments"""
        try:
            with open(gcode_path, 'r') as f:
                for line in f:
                    if 'estimated printing time' in line.lower():
                        # Extract time from PrusaSlicer comment
                        if '=' in line:
                            time_str = line.split('=')[-1].strip()
                            return time_str
                    if line.startswith(';'): continue
                    if line.strip() and not line.startswith(';'): break
        except Exception:
            pass
        return "Unknown"
    
    def _estimate_filament_usage(self, gcode_path: Path) -> float:
        """Estimate filament usage from G-code"""
        try:
            with open(gcode_path, 'r') as f:
                for line in f:
                    if 'filament used' in line.lower() and 'mm' in line.lower():
                        # Extract filament length
                        import re
                        match = re.search(r'(\d+\.?\d*)\s*mm', line)
                        if match:
                            return float(match.group(1))
                    if line.startswith(';'): continue
                    if line.strip() and not line.startswith(';'): break
        except Exception:
            pass
        return 0.0
    
    def _get_settings_summary(self, profile: SlicingProfile, custom_settings: Optional[Dict]) -> Dict:
        """Get summary of slicing settings"""
        summary = asdict(profile)
        if custom_settings:
            summary.update(custom_settings)
        return summary
    
    def get_available_profiles(self) -> Dict[str, str]:
        """Get available slicing profiles"""
        return {name: profile.name for name, profile in self.profiles.items()}
    
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
    
    def validate_stl_for_printing(self, stl_path: str) -> Dict:
        """Validate STL file for 3D printing"""
        stl_path = Path(stl_path)
        
        if not stl_path.exists():
            return {'valid': False, 'error': 'STL file not found'}
        
        try:
            file_size_mb = stl_path.stat().st_size / 1024 / 1024
            
            if file_size_mb > int(os.getenv('MAX_FILE_SIZE_MB', 50)):
                return {
                    'valid': False, 
                    'error': f'STL file too large: {file_size_mb:.1f}MB (max: {os.getenv("MAX_FILE_SIZE_MB")}MB)'
                }
            
            # Basic STL validation (check if it's binary STL)
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