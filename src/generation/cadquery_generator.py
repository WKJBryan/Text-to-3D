# src/generation/simple_generator.py (Obsolete)
import cadquery as cq
import json
import re
from typing import Dict, Optional

class CADGenerator:
    def __init__(self, llm_engine):
        self.llm_engine = llm_engine
        self.last_code = ""
        self.generation_history = []
    
    def generate_model(self, model_spec: Dict, provided_code: Optional[str] = None) -> cq.Workplane:
        """Generate 3D model from specification"""
        if provided_code:
            code = provided_code
        else:
            code = self._generate_code(model_spec)
        
        self.last_code = code
        self.generation_history.append({'spec': model_spec, 'code': code})
        
        return self._execute_code(code)
    
    def _generate_code(self, spec: Dict) -> str:
        """Generate CadQuery code using LLM"""
        prompt = f"""Generate CadQuery 2.5.2 code for this specification:

{json.dumps(spec, indent=2)}

CADQUERY 2.5.2 REQUIREMENTS:
1. Import cadquery as cq
2. Create 'result' variable with final CadQuery Workplane
3. Use exact dimensions from specification
4. Implement ALL requirements listed
5. Include try/except error handling
6. Make it 3D printable (avoid steep overhangs)
7. Use minimum 1.5mm wall thickness

CADQUERY 2.5.2 ADVANCED FEATURES TO USE:
- Advanced selectors: .edges("|Z and >X"), .faces(">>Z[1]"), .edges("<Y")
- Sketch mode: .sketch().circle(radius).rectangle(w,h).finalize()
- Better fillets: .fillet(radius) with precise edge selection
- Chamfers: .chamfer(distance) for clean edges
- Complex boolean operations: .cut(), .union(), .intersect()
- Parametric construction with variables
- Assembly features for multi-part designs
- Improved performance methods

EXAMPLE TEMPLATE:
```python
import cadquery as cq

# Extract and validate dimensions
width = max({spec.get('width', 50)}, 10)
height = max({spec.get('height', 50)}, 5)
depth = max({spec.get('depth', 50)}, 10)

try:
    # Create base geometry using modern CadQuery methods
    base = (cq.Workplane("XY")
           .box(width, depth, height))
    
    # Use advanced selectors for precise modifications
    result = base.edges("|Z").fillet(1.0)
    
    # Add features based on requirements using CadQuery 2.5.2 capabilities
    # Example: .sketch().circle(5).rectangle(10,20).finalize().extrude(5)
    
    # Apply finishing touches
    result = result.edges(">>Z").chamfer(0.5)
    
except Exception as e:
    # Robust fallback
    result = cq.Workplane("XY").box(width, depth, height)
```

IMPLEMENTATION GUIDELINES:
- Use .sketch() mode for complex 2D profiles
- Leverage advanced edge/face selectors for precision
- Apply fillets and chamfers for printability
- Use parametric variables for flexibility
- Include validation (min/max dimensions)
- Handle edge cases gracefully

Generate ONLY the Python code with CadQuery 2.5.2 features, no explanations:"""

            
        return self.llm_engine.generate(prompt, temperature=0.2)
    
    def _execute_code(self, code: str) -> cq.Workplane:
        """Execute CadQuery code safely"""
        # Clean up code
        code = self._clean_code(code)
        
        # Safe execution environment
        safe_globals = {'cq': cq, 'cadquery': cq}
        safe_locals = {}
        
        try:
            exec(code, safe_globals, safe_locals)
            
            if 'result' in safe_locals:
                result = safe_locals['result']
                if isinstance(result, cq.Workplane):
                    return result
            
            raise Exception("Code didn't produce valid CadQuery Workplane")
            
        except Exception as e:
            raise Exception(f"Code execution failed: {e}")
    
    def _clean_code(self, code: str) -> str:
        """Clean and extract Python code"""
        # Remove markdown code blocks
        code = re.sub(r'```python\n?', '', code)
        code = re.sub(r'```\n?', '', code)
        
        # Find code starting with import
        if 'import cadquery' in code:
            start_idx = code.find('import cadquery')
            code = code[start_idx:]
        
        return code.strip()
    
    def visualize(self, model: cq.Workplane):
        """Visualize model using CadQuery viewer"""
        try:
            from cadquery.vis import show
            show(model)
            print("✅ 3D viewer opened")
        except ImportError:
            print("❌ Install cadquery[vis] for 3D visualization")
        except Exception as e:
            print(f"❌ Visualization failed: {e}")
    
    def get_last_code(self) -> str:
        """Get the last generated code"""
        return self.last_code