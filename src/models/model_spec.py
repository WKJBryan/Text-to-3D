# src/models/model_spec.py
"""Pydantic ModelSpec with Unit Normalization and Validation"""
from __future__ import annotations
from typing import Optional, List, Dict, Any, Tuple
import math
import json
import re
from pydantic import BaseModel, Field, ValidationError, ConfigDict, field_validator

# Unit conversion constants
MM_PER_IN = 25.4
MM_PER_CM = 10.0

# Dimension regex pattern
_DIM_RE = re.compile(r"\s*([+-]?(?:\d+(?:\.\d+)?|\.\d+))(?:\s*(mm|cm|in))?\s*$", re.I)

class ModelSpec(BaseModel):
    """Structured specification for 3D CAD models with automatic unit normalization"""
    
    # Core identification
    object_type: str = Field(..., description="Type of 3D object to create")
    requirements: List[str] = Field(default_factory=list, description="Functional requirements")
    notes: Optional[str] = Field(None, description="Additional notes or context")

    # Primary dimensions (all normalized to mm)
    height: Optional[float] = Field(None, description="Height in mm")
    width: Optional[float] = Field(None, description="Width in mm") 
    depth: Optional[float] = Field(None, description="Depth in mm")
    length: Optional[float] = Field(None, description="Length in mm")
    
    # Circular geometry
    radius: Optional[float] = Field(None, description="Radius in mm")
    diameter: Optional[float] = Field(None, description="Diameter in mm")
    
    # Wall and thickness
    wall_thickness: Optional[float] = Field(None, description="Wall thickness in mm")
    rim_thickness: Optional[float] = Field(None, description="Rim thickness in mm")
    
    # Angular measurements
    angle: Optional[float] = Field(None, description="Angle in degrees")
    pressure_angle: Optional[float] = Field(None, description="Pressure angle in degrees")
    
    # Mechanical/gear parameters
    teeth: Optional[int] = Field(None, description="Number of teeth")
    module: Optional[float] = Field(None, description="Module size")
    coils: Optional[int] = Field(None, description="Number of coils")
    wire_diameter: Optional[float] = Field(None, description="Wire diameter in mm")
    
    # Feature flags
    has_handle: Optional[bool] = Field(None, description="Whether object has a handle")
    has_lid: Optional[bool] = Field(None, description="Whether object has a lid")
    has_holes: Optional[bool] = Field(None, description="Whether object has holes")
    
    # Tapered/conical parameters
    bottom_radius: Optional[float] = Field(None, description="Bottom radius in mm")
    top_radius: Optional[float] = Field(None, description="Top radius in mm")
    
    # Template resolution metadata
    user_preference: Optional[str] = Field(None, description="User's design preference (e.g., cylindrical, tapered)")
    template_conflicts_resolved: Optional[bool] = Field(None, description="Whether template conflicts were resolved")
    
    # RAG metadata
    rag_reference: Optional[str] = Field(None, description="RAG reference used")
    rag_similarity: Optional[float] = Field(None, description="RAG similarity score")
    
    # Catch-all for unknown parameters
    extra: Dict[str, Any] = Field(default_factory=dict, description="Additional parameters")

    model_config = ConfigDict(extra="allow")

    @field_validator('height', 'width', 'depth', 'length', 'radius', 'diameter', 
                    'wall_thickness', 'rim_thickness', 'wire_diameter', 
                    'bottom_radius', 'top_radius', mode='before')
    def normalize_dimensions(cls, v):
        """Convert dimensions to mm from various formats"""
        if v is None:
            return None
        return to_mm(v)
    
    @field_validator('teeth', 'coils', mode='before')
    def validate_positive_integers(cls, v):
        """Ensure counts are positive integers"""
        if v is None:
            return None
        if isinstance(v, (int, float)):
            v = int(v)
            if v <= 0:
                raise ValueError("Count must be positive")
            return v
        raise ValueError("Count must be a number")
    
    def model_post_init(self, __context):
        """Post-initialization processing for diameter/radius semantics and validation"""
        # Handle diameter <-> radius conversion
        self._resolve_diameter_radius()
        
        # Apply geometry invariants
        warnings = self._check_invariants()
        if warnings:
            print(f"⚠️ Geometry warnings: {warnings}")
    
    def _resolve_diameter_radius(self):
        """Handle diameter <-> radius alias semantics"""
        if self.radius is None and self.diameter is not None:
            self.radius = self.diameter / 2.0
        elif self.diameter is None and self.radius is not None:
            self.diameter = self.radius * 2.0
        elif self.radius is not None and self.diameter is not None:
            # If both provided and inconsistent, prefer radius
            if not math.isclose(self.diameter, 2.0 * self.radius, rel_tol=1e-6):
                print(f"⚠️ Diameter/radius inconsistency: using radius={self.radius}")
                self.diameter = 2.0 * self.radius
    
    def _check_invariants(self) -> List[str]:
        """Check and auto-correct geometry invariants"""
        warnings = []
        
        # Wall thickness vs radius
        if self.wall_thickness and self.radius:
            max_wall = self.radius / 3.0
            if self.wall_thickness > max_wall:
                warnings.append(f"wall_thickness {self.wall_thickness:.1f} > radius/3, clamped to {max_wall:.1f}")
                self.wall_thickness = max_wall
        
        # Positive dimensions
        for field_name in ['height', 'width', 'depth', 'radius', 'diameter', 'wall_thickness']:
            value = getattr(self, field_name)
            if value is not None and value <= 0:
                warnings.append(f"{field_name} must be positive, set to {abs(value)}")
                setattr(self, field_name, abs(value))
        
        # Gear constraints
        if self.teeth is not None and self.teeth < 3:
            warnings.append("gear teeth must be >= 3, set to 12")
            self.teeth = 12
        
        # Tapered geometry constraints
        if self.bottom_radius and self.top_radius:
            if self.bottom_radius <= 0 or self.top_radius <= 0:
                warnings.append("tapered radii must be positive")
                if self.bottom_radius <= 0:
                    self.bottom_radius = 5.0
                if self.top_radius <= 0:
                    self.top_radius = 5.0
        
        return warnings
    
    @classmethod
    def from_ollama_response(cls, response_text: str) -> "ModelSpec":
        """Create ModelSpec from Ollama structured output"""
        try:
            # Response should be pure JSON due to structured outputs
            data = json.loads(response_text)
            
            # Handle extra fields
            known_fields = set(cls.model_fields.keys())
            extra_fields = {k: v for k, v in data.items() if k not in known_fields}
            base_fields = {k: v for k, v in data.items() if k in known_fields}
            
            if extra_fields:
                base_fields["extra"] = extra_fields
                print(f"📦 Captured extra fields: {list(extra_fields.keys())}")
            
            return cls(**base_fields)
            
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON from LLM: {e}")
        except Exception as e:
            raise ValidationError(f"ModelSpec creation failed: {e}")
    
    def to_code_parameters(self) -> Dict[str, Any]:
        """Convert to dictionary suitable for code generation"""
        params = {}
        
        # Add all non-None dimensional parameters
        for field_name in self.model_fields:
            value = getattr(self, field_name)
            if value is not None and field_name not in ['extra', 'requirements', 'notes']:
                params[field_name] = value
        
        # Add extra parameters
        if self.extra:
            params.update(self.extra)
        
        return params
    
    def get_conflict_resolution_info(self) -> Dict[str, Any]:
        """Get information about template conflict resolution"""
        return {
            "user_preference": self.user_preference,
            "conflicts_resolved": self.template_conflicts_resolved,
            "rag_reference": self.rag_reference,
            "rag_similarity": self.rag_similarity
        }

def to_mm(value: Any) -> Optional[float]:
    """Convert dimensional value to millimeters"""
    if value is None:
        return None
    
    if isinstance(value, (int, float)):
        return float(value)
    
    if isinstance(value, str):
        match = _DIM_RE.fullmatch(value)
        if not match:
            raise ValueError(f"Invalid dimension format: {value}")
        
        number = float(match.group(1))
        unit = (match.group(2) or "mm").lower()
        
        if unit == "mm":
            return number
        elif unit == "cm":
            return number * MM_PER_CM
        elif unit == "in":
            return number * MM_PER_IN
        else:
            raise ValueError(f"Unknown unit: {unit}")
    
    raise TypeError(f"Cannot convert {type(value)} to mm")

# Example usage and testing
if __name__ == "__main__":
    # Test the ModelSpec
    test_data = {
        "object_type": "cup",
        "diameter": "20mm",
        "height": "5cm",
        "wall_thickness": 1.5,
        "has_handle": False,
        "user_preference": "cylindrical"
    }
    
    spec = ModelSpec(**test_data)
    print("Normalized spec:")
    print(spec.model_dump_json(indent=2))
    
    print("\nCode parameters:")
    print(spec.to_code_parameters())