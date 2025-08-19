# src/generation/export.py
"""Enhanced Model Exporter for STL, STEP, and Code Export"""
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import cadquery as cq

class ModelExporter:
    def __init__(self, export_directory: str = "./exports"):
        self.export_directory = Path(export_directory)
        self.export_directory.mkdir(exist_ok=True)
        print(f"📁 Export directory: {self.export_directory}")
    
    def export_model(self, model: cq.Workplane, model_spec: Dict, cadquery_code: str) -> Dict:
        """Export model to multiple formats with enhanced metadata"""
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
            
            return {
                'files': files,
                'file_size_mb': total_size / 1024 / 1024,
                'base_filename': base_filename,
                'export_directory': str(self.export_directory)
            }
            
        except Exception as e:
            print(f"❌ Enhanced export failed: {e}")
            raise Exception(f"Export failed: {e}")
    
    def _create_enhanced_code_export(self, code: str, spec: Dict) -> str:
        """Create enhanced code export with metadata and documentation"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        object_type = spec.get('object_type', 'unknown')
        
        enhanced_code = f'''"""
Enhanced RAG + Intelligent Reasoning Generated CadQuery Model
=============================================================

Generated: {timestamp}
Object Type: {object_type}
System: Enhanced RAG + Intelligent AI Manufacturing

Specification:
{self._format_spec_as_comment(spec)}

Instructions:
1. Ensure CadQuery is installed: pip install cadquery
2. For visualization: pip install cadquery[vis]
3. Run this script to recreate the model
4. Modify parameters as needed for your use case

Enhanced RAG Documentation:
- This code was generated using either hierarchical reference patterns
  or intelligent engineering reasoning from first principles
- The system automatically selected the optimal generation approach
- Code includes manufacturing considerations and 3D printing optimizations
"""

import cadquery as cq

# Enhanced RAG + Intelligent Reasoning Generated Code
{code}

# Visualization (uncomment to view)
# if __name__ == "__main__":
#     from cadquery.vis import show
#     show(result)

# Export functions (uncomment to use)
# def export_stl(filename="model.stl"):
#     cq.exporters.export(result, filename)
#     print(f"Exported STL: {{filename}}")

# def export_step(filename="model.step"):
#     cq.exporters.export(result, filename)
#     print(f"Exported STEP: {{filename}}")

# Enhanced RAG Generation Complete
'''
        return enhanced_code
    
    def _format_spec_as_comment(self, spec: Dict) -> str:
        """Format specification as readable comment"""
        lines = []
        for key, value in spec.items():
            if isinstance(value, list):
                value = ', '.join(str(v) for v in value)
            lines.append(f"  {key}: {value}")
        return '\n'.join(lines)
    
    def _create_metadata(self, spec: Dict, files: Dict) -> Dict:
        """Create comprehensive metadata for the export"""
        return {
            "export_info": {
                "timestamp": datetime.now().isoformat(),
                "system": "Enhanced RAG + Intelligent AI Manufacturing",
                "version": "1.0",
                "generator": "EnhancedRAGCADGenerator"
            },
            "model_specification": spec,
            "exported_files": files,
            "file_formats": {
                "STL": "Stereolithography - 3D printing ready",
                "STEP": "Standard for Exchange of Product Data - CAD interop",
                "Python": "CadQuery source code with enhanced documentation",
                "Metadata": "Export information and specifications"
            },
            "usage_instructions": {
                "3d_printing": "Use STL file with your slicer software",
                "cad_software": "Import STEP file for further editing",
                "code_modification": "Edit Python file to customize parameters",
                "regeneration": "Run Python script to recreate model"
            },
            "enhanced_rag_info": {
                "description": "Generated using Enhanced RAG + Intelligent Reasoning",
                "approach": "Hierarchical pattern matching or engineering first-principles",
                "optimization": "Manufacturing constraints and 3D printing considerations"
            }
        }
    
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
                    'files': metadata.get('exported_files', {})
                })
            except Exception as e:
                print(f"❌ Failed to read metadata {file_path}: {e}")
        
        return sorted(exports, key=lambda x: x['timestamp'], reverse=True)
    
    def cleanup_old_exports(self, keep_recent: int = 10):
        """Clean up old exports, keeping only recent ones"""
        exports = self.list_exports()
        
        if len(exports) <= keep_recent:
            return
        
        to_delete = exports[keep_recent:]
        deleted_count = 0
        
        for export in to_delete:
            try:
                base_name = export['filename']
                # Delete all associated files
                for pattern in [f"{base_name}.*", f"{base_name}_metadata.json"]:
                    for file_path in self.export_directory.glob(pattern):
                        file_path.unlink()
                        deleted_count += 1
            except Exception as e:
                print(f"❌ Failed to delete export {export['filename']}: {e}")
        
        print(f"🧹 Cleaned up {deleted_count} old export files")