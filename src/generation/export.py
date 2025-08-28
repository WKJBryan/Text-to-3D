# src/generation/export.py
"""Enhanced Model Exporter with 3D Printing Pipeline Integration"""
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import cadquery as cq

class ModelExporter:
    def __init__(self, export_directory: str = "./exports"):
        self.export_directory = Path(export_directory)
        self.export_directory.mkdir(exist_ok=True)
        print(f"📁 Export directory: {self.export_directory}")
        
        # Initialize printing components if available
        self.slicer = None
        self.mainsail = None
        self._init_printing_components()
    
    def _init_printing_components(self):
        """Initialize 3D printing components (optional)"""
        try:
            from src.printing.prusaslicer_interface import PrusaSlicerInterface
            from src.printing.mainsail_client import MainsailClient
            
            self.slicer = PrusaSlicerInterface()
            self.mainsail = MainsailClient()
            print("✅ 3D printing pipeline initialized")
            
        except ImportError as e:
            print("ℹ️ 3D printing features not available (missing dependencies)")
            print(f"   Install with: pip install requests")
        except Exception as e:
            print(f"⚠️ 3D printing initialization failed: {e}")
            print("   Export will work, but slicing/printing features disabled")
    
    def export_model(self, model: cq.Workplane, model_spec: Dict, 
                    cadquery_code: str, auto_slice: bool = None) -> Dict:
        """Export model to multiple formats with optional slicing"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        object_type = model_spec.get('object_type', 'model')
        base_filename = f"{object_type}_{timestamp}"
        
        files = {}
        total_size = 0
        
        try:
            # Export STL for 3D printing
            stl_path = self.export_directory / f"{base_filename}.stl"
            cq.exporters.export(model, str(stl_path))
            files['STL'] = str(stl_path)
            total_size += stl_path.stat().st_size
            
            # Export STEP for CAD interoperability
            step_path = self.export_directory / f"{base_filename}.step"
            cq.exporters.export(model, str(step_path))
            files['STEP'] = str(step_path)
            total_size += step_path.stat().st_size
            
            # Export CadQuery code with enhanced metadata
            code_path = self.export_directory / f"{base_filename}.py"
            enhanced_code = self._create_enhanced_code_export(cadquery_code, model_spec)
            with open(code_path, 'w') as f:
                f.write(enhanced_code)
            files['Python'] = str(code_path)
            total_size += code_path.stat().st_size
            
            # Export metadata JSON
            metadata_path = self.export_directory / f"{base_filename}_metadata.json"
            metadata = self._create_metadata(model_spec, files)
            import json
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            files['Metadata'] = str(metadata_path)
            total_size += metadata_path.stat().st_size
            
            print(f"✅ Enhanced export complete: {len(files)} files, {total_size/1024/1024:.2f} MB")
            
            result = {
                'files': files,
                'file_size_mb': total_size / 1024 / 1024,
                'base_filename': base_filename,
                'export_directory': str(self.export_directory),
                'stl_path': str(stl_path),  # For slicing
                'printing_ready': self.slicer is not None
            }
            
            # Auto-slice if requested and slicer available
            if auto_slice is None:
                auto_slice = os.getenv('AUTO_SLICE_AFTER_EXPORT', 'false').lower() == 'true'
            
            if auto_slice and self.slicer is not None:
                print("🔄 Auto-slicing enabled, starting slice...")
                slice_result = self.slice_model(str(stl_path))
                result['slice_info'] = slice_result
            
            return result
            
        except Exception as e:
            print(f"❌ Enhanced export failed: {e}")
            raise Exception(f"Export failed: {e}")
    
    def slice_model(self, stl_path: str, profile: str = 'standard', 
                   custom_settings: Optional[Dict] = None) -> Dict:
        """Slice STL model for 3D printing"""
        if self.slicer is None:
            return {
                'success': False,
                'error': 'Slicer not available. Check PrusaSlicer installation.'
            }
        
        try:
            print(f"🔄 Slicing {Path(stl_path).name} with {profile} profile...")
            
            # Validate STL first
            validation = self.slicer.validate_stl_for_printing(stl_path)
            if not validation['valid']:
                return {
                    'success': False,
                    'error': f'STL validation failed: {validation["error"]}'
                }
            
            # Perform slicing
            slice_result = self.slicer.slice_file(stl_path, profile, custom_settings)
            
            if slice_result['success']:
                print(f"✅ Slicing complete: {slice_result['gcode_filename']}")
                print(f"   Time: {slice_result['estimated_print_time']}")
                print(f"   Filament: {slice_result['estimated_filament_mm']:.1f}mm")
                
                # Add printing readiness info
                slice_result['ready_for_upload'] = self.mainsail is not None
                if self.mainsail:
                    slice_result['printer_ready'] = self.mainsail.is_printer_ready()
            
            return slice_result
            
        except Exception as e:
            return {'success': False, 'error': f'Slicing failed: {e}'}
    
    def upload_and_print(self, gcode_path: str, start_immediately: bool = None) -> Dict:
        """Upload G-code to printer and optionally start printing"""
        if self.mainsail is None:
            return {
                'success': False,
                'error': 'Mainsail client not available. Check printer connection.'
            }
        
        try:
            # Upload G-code file
            print(f"📤 Uploading {Path(gcode_path).name} to printer...")
            upload_result = self.mainsail.upload_gcode_file(gcode_path)
            
            if not upload_result['success']:
                return upload_result
            
            result = {
                'upload_success': True,
                'filename': upload_result['filename'],
                'size_mb': upload_result['size_mb']
            }
            
            # Auto-start if configured
            if start_immediately is None:
                start_immediately = os.getenv('AUTO_START_PRINT_AFTER_SLICE', 'false').lower() == 'true'
            
            if start_immediately:
                # Safety confirmation check
                confirm_required = os.getenv('CONFIRM_BEFORE_PRINT', 'true').lower() == 'true'
                
                if not confirm_required:  # Skip confirmation in auto mode
                    print(f"🖨️ Auto-starting print: {upload_result['filename']}")
                    print_result = self.mainsail.start_print(upload_result['filename'])
                    result.update(print_result)
                else:
                    result['print_ready'] = True
                    result['message'] = 'File uploaded. Confirmation required to start print.'
            else:
                result['print_ready'] = True
                result['message'] = 'File uploaded and ready to print.'
            
            return result
            
        except Exception as e:
            return {'success': False, 'error': f'Upload/print failed: {e}'}
    
    def get_printer_status(self) -> Dict:
        """Get current printer status"""
        if self.mainsail is None:
            return {'error': 'Mainsail client not available'}
        
        try:
            status = self.mainsail.get_printer_status()
            return {
                'state': status.state,
                'extruder_temp': status.extruder_temp,
                'extruder_target': status.extruder_target,
                'bed_temp': status.bed_temp,
                'bed_target': status.bed_target,
                'chamber_temp': status.chamber_temp,
                'progress': status.progress,
                'print_time': self.mainsail.format_print_time(status.print_time),
                'current_file': status.current_file,
                'ready': status.state == 'ready',
                'error_message': status.error_message
            }
        except Exception as e:
            return {'error': f'Status request failed: {e}'}
    
    def get_available_slice_profiles(self) -> Dict:
        """Get available slicing profiles"""
        if self.slicer is None:
            return {'error': 'Slicer not available'}
        
        return self.slicer.get_available_profiles()
    
    def _create_enhanced_code_export(self, code: str, spec: Dict) -> str:
        """Create enhanced code export with 3D printing metadata"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        object_type = spec.get('object_type', 'unknown')
        
        # Add printing recommendations based on object type
        printing_notes = self._get_printing_recommendations(object_type, spec)
        
        enhanced_code = f'''"""
Enhanced RAG + Intelligent Reasoning Generated CadQuery Model
=============================================================

Generated: {timestamp}
Object Type: {object_type}
System: Enhanced RAG + Intelligent AI Manufacturing

Specification:
{self._format_spec_as_comment(spec)}

3D Printing Recommendations:
{printing_notes}

Instructions:
1. Ensure CadQuery is installed: pip install cadquery
2. For visualization: pip install cadquery[vis]
3. Run this script to recreate the model
4. Export STL for 3D printing: cq.exporters.export(result, "model.stl")
5. Slice with recommended settings for best results

Enhanced RAG Documentation:
- This code was generated using either hierarchical reference patterns
  or intelligent engineering reasoning from first principles
- The system automatically selected the optimal generation approach
- Code includes manufacturing considerations and 3D printing optimizations
- Recommended slicing profiles and settings included below
"""

import cadquery as cq

# Enhanced RAG + Intelligent Reasoning Generated Code
{code}

# 3D Printing Export Functions
def export_for_printing(filename_base="model"):
    \"\"\"Export model ready for 3D printing\"\"\"
    stl_file = f"{{filename_base}}.stl"
    step_file = f"{{filename_base}}.step"
    
    # Export STL for slicing
    cq.exporters.export(result, stl_file)
    print(f"✅ STL exported: {{stl_file}}")
    
    # Export STEP for CAD editing
    cq.exporters.export(result, step_file)
    print(f"✅ STEP exported: {{step_file}}")
    
    return stl_file, step_file

# Visualization (uncomment to view)
# if __name__ == "__main__":
#     from cadquery.vis import show
#     show(result)

# Quick printing export (uncomment to use)
# export_for_printing("{object_type}")

# Enhanced RAG Generation Complete - Ready for Manufacturing!
'''
        return enhanced_code
    
    def _get_printing_recommendations(self, object_type: str, spec: Dict) -> str:
        """Get 3D printing recommendations based on object type"""
        
        recommendations = {
            'gear': """
- Layer Height: 0.15-0.2mm for smooth gear teeth
- Infill: 25-40% for strength, gyroid pattern recommended
- Supports: Usually not needed if designed properly
- Orientation: Print with gear axis vertical for best tooth quality
- Post-processing: Light sanding may improve meshing""",
            
            'bracket': """
- Layer Height: 0.2-0.3mm for structural parts
- Infill: 30-50% with rectilinear or honeycomb pattern
- Supports: May be needed for overhangs
- Orientation: Consider stress direction and support requirements
- Material: PETG or ABS recommended for mechanical parts""",
            
            'phone_stand': """
- Layer Height: 0.2mm for good surface finish
- Infill: 15-25% sufficient for this application
- Supports: Likely needed for angled sections
- Orientation: Consider stability and surface finish
- Post-processing: Support removal and light sanding""",
            
            'cup': """
- Layer Height: 0.2mm for smooth surfaces
- Infill: 10-20% for lightweight, 2-3 perimeters for strength
- Supports: May need for handle if present
- Orientation: Print upright for best surface finish
- Post-processing: Food-safe coating if for beverage use""",
            
            'spring': """
- Layer Height: 0.1-0.15mm for fine details
- Infill: 100% for solid spring action
- Supports: None needed
- Orientation: Print axis along build plate
- Material: Flexible filament (TPU) recommended
- Post-processing: Test compression and adjust if needed"""
        }
        
        # Default recommendations
        default = """
- Layer Height: 0.2mm (standard quality)
- Infill: 20% with gyroid or honeycomb pattern
- Supports: Auto-generate as needed
- Orientation: Consider overhangs and surface finish
- Material: PLA for prototypes, PETG/ABS for functional parts"""
        
        return recommendations.get(object_type.lower(), default)
    
    def _format_spec_as_comment(self, spec: Dict) -> str:
        """Format specification as readable comment"""
        lines = []
        for key, value in spec.items():
            if isinstance(value, list):
                value = ', '.join(str(v) for v in value)
            lines.append(f"  {key}: {value}")
        return '\n'.join(lines)
    
    def _create_metadata(self, spec: Dict, files: Dict) -> Dict:
        """Create comprehensive metadata with 3D printing info"""
        metadata = {
            "export_info": {
                "timestamp": datetime.now().isoformat(),
                "system": "Enhanced RAG + Intelligent AI Manufacturing",
                "version": "2.0",
                "generator": "EnhancedRAGCADGenerator",
                "printing_pipeline": "PrusaSlicer + Mainsail/Klipper"
            },
            "model_specification": spec,
            "exported_files": files,
            "file_formats": {
                "STL": "Stereolithography - 3D printing ready",
                "STEP": "Standard for Exchange of Product Data - CAD interop",
                "Python": "CadQuery source code with enhanced documentation",
                "Metadata": "Export information and specifications"
            },
            "printing_info": {
                "slicer_available": self.slicer is not None,
                "printer_available": self.mainsail is not None,
                "recommended_profile": "standard",
                "estimated_print_time": "Run slice operation for estimate",
                "material_recommendation": "PLA for prototypes, PETG for functional parts"
            },
            "usage_instructions": {
                "3d_printing": "Use STL file with slicer software",
                "slicing": "Use integrated slicer or PrusaSlicer manually",
                "printing": "Upload G-code via Mainsail web interface or integrated client",
                "cad_software": "Import STEP file for further editing",
                "code_modification": "Edit Python file to customize parameters",
                "regeneration": "Run Python script to recreate model"
            },
            "enhanced_rag_info": {
                "description": "Generated using Enhanced RAG + Intelligent Reasoning",
                "approach": "Hierarchical pattern matching or engineering first-principles",
                "optimization": "Manufacturing constraints and 3D printing considerations",
                "pipeline_integration": "Full CAD-to-part manufacturing pipeline"
            }
        }
        
        # Add printer status if available
        if self.mainsail:
            try:
                printer_status = self.get_printer_status()
                metadata["printer_status"] = printer_status
            except:
                pass
        
        return metadata
    
    def list_exports(self) -> List[Dict]:
        """List all previous exports with metadata"""
        exports = []
        
        for file_path in self.export_directory.glob("*_metadata.json"):
            try:
                import json
                with open(file_path, 'r') as f:
                    metadata = json.load(f)
                exports.append({
                    'filename': file_path.stem.replace('_metadata', ''),
                    'timestamp': metadata.get('export_info', {}).get('timestamp', 'unknown'),
                    'object_type': metadata.get('model_specification', {}).get('object_type', 'unknown'),
                    'files': metadata.get('exported_files', {}),
                    'has_printing_info': 'printing_info' in metadata
                })
            except Exception as e:
                print(f"❌ Failed to read metadata {file_path}: {e}")
        
        return sorted(exports, key=lambda x: x['timestamp'], reverse=True)
    
    def cleanup_old_exports(self, keep_recent: int = 10):
        """Clean up old exports and related G-code files"""
        exports = self.list_exports()
        
        if len(exports) <= keep_recent:
            return
        
        to_delete = exports[keep_recent:]
        deleted_count = 0
        
        for export in to_delete:
            try:
                base_name = export['filename']
                # Delete all associated files
                patterns = [f"{base_name}.*", f"{base_name}_metadata.json"]
                
                for pattern in patterns:
                    for file_path in self.export_directory.glob(pattern):
                        file_path.unlink()
                        deleted_count += 1
                        
            except Exception as e:
                print(f"❌ Failed to delete export {export['filename']}: {e}")
        
        # Also cleanup old G-code files if slicer available
        if self.slicer:
            self.slicer.cleanup_old_gcode(keep_recent)
        
        if deleted_count > 0:
            print(f"🧹 Cleaned up {deleted_count} old export files")
