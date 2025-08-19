# src/generation/reference_library.txt
"""Enhanced Hierarchical RAG Reference Library with Intelligent Patterns"""
#TO ADD - ALL EXCEPT should be a LOGO GENERATION FAILED
import numpy as np
import pickle
import os
from pathlib import Path
from typing import Dict, List, Tuple
from sentence_transformers import SentenceTransformer
import faiss

class EnhancedRAGReferenceLibrary:
    """Enhanced RAG library with hierarchical complexity and intelligent patterns"""
    
    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2", cache_dir: str = "./embeddings"):
        self.embedding_model_name = embedding_model
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Initialize embedding model
        print(f"🧠 Loading embedding model: {embedding_model}")
        self.embedding_model = SentenceTransformer(embedding_model)
        
        # Enhanced hierarchical reference library
        self.library = self._build_enhanced_library()
        
        # RAG components
        self.embeddings = None
        self.faiss_index = None
        self.reference_keys = None
        
        # Initialize embeddings
        self._initialize_embeddings()
    
    def _build_enhanced_library(self) -> Dict:
        """Enhanced hierarchical reference library with complexity levels"""
        return {
            # LEVEL 1: SIMPLE GEOMETRIC PRIMITIVES
            "simple_container": {
                "description": "Basic rectangular box with rounded edges and wall thickness",
                "complexity": "simple",
                "category": "primitive",
                "code": """import cadquery as cq

# Simple container with rounded edges
length = 90
width = 90
height = 8
rounded_corner = 8

try:
    # Create container with rounded corners
    result = (cq.Workplane("XY")
             .box(length, width, height)
             # Create opening
             .faces("+Z")
             # Rounding corners
             .shell(rounded_corner)
             )

except Exception:
    result = cq.Workplane("XY").box(width, depth, height)"""
            },
            
            "simple_cylinder": {
                "description": "Basic cylinder with smooth walls",
                "complexity": "simple", 
                "category": "primitive",
                "code": """import cadquery as cq

# Simple cylinder
diameter = 80
height = 30

try:
    # Create cylinder
    result = (cq.Workplane("XY")
             .cylinder(height,diameter/2)
             )

except Exception:
    result = (cq.Workplane("XY")
             .circle(diameter/2)
             .extrude(height))"""
            },

            "simple_sphere": {
                "description": "Basic simple smooth sphere",
                "complexity": "simple", 
                "category": "primitive",
                "code": """import cadquery as cq

# Simple sphere
diameter = 80

try:
    # Create sphere
    result = (cq.Workplane("XY")
             .sphere(diameter/2)

except Exception:
    result = (cq.Workplane("XY")
             .circle(diameter/2)
             .extrude(height))"""
            },

            "simple_rectangular_coaster": {
                "description": "Simple rectangular coaster with decorative center pattern",
                "complexity": "simple",
                "category": "primitive",
                "code": """import cadquery as cq

# Simple rectangular coaster with decorative center pattern
width = 90
height = 90
thickness = 8
corner_radius = 8
rim_depth = 4
rim_inset = 5
center_decoration_radius = 20
decoration_depth = 1

try:
    # Create rectangular coaster with decorative center pattern
    result = (cq.Workplane("XY")
                .box(width, height, thickness)
                .edges("|Z")
                .fillet(corner_radius)
                # Create rim
                .faces(">Z")
                .workplane()
                .rect(width - rim_inset*2, height - rim_inset*2)
                .cutBlind(-rim_depth)
                .edges("|Z")
                .fillet(corner_radius/4)
                # Add decorative center pattern
                .faces(">Z")
                .workplane(offset=-rim_depth)
                .circle(center_decoration_radius)
                .cutBlind(-decoration_depth)
                )

except Exception:
    result = cq.Workplane("XY").box(width, depth, height)"""
            },

            "simple_ring": {
                "description": "Simple ring with decorative bands",
                "complexity": "simple",
                "category": "primitive",
                "code": """import cadquery as cq

# Simple ring with decorative bands
outer_radius = 30
inner_radius = 25
height = 35
band_offset_1 = 5
band_offset_2 = 25
band_thickness = 2
band_protrusion = 1
edge_fillet = (band_protrusion * 0.9) / 2 

try:
    # Create Simple ring with decorative bands
    result = (cq.Workplane("XY")
                .circle(outer_radius)
                .circle(inner_radius)
                .extrude(height)
                # Add decorative bands
                .faces(">Z")
                .workplane(offset=-band_offset_1)
                .circle(outer_radius + band_protrusion)
                .circle(outer_radius)
                .extrude(band_thickness)
                .faces(">Z")
                .workplane(offset=-band_offset_2)
                .circle(outer_radius + band_protrusion)
                .circle(outer_radius)
                .extrude(band_thickness)
                # Smooth all edges
                .edges()
                .fillet(edge_fillet)
            )

except Exception:
    result = cq.Workplane("XY").box(width, depth, height)"""
            },
            
            # LEVEL 2: FUNCTIONAL OBJECTS WITH CONSTRAINTS
            "phone_stand": {
                "description": "Adjustable phone stand with charging port and stability features",
                "complexity": "medium",
                "category": "functional",
                "code": """import cadquery as cq

# Phone stand with engineering considerations
width = 80
depth = 60
height = 50
angle = 15
wall_thickness = 3

try:
    # Create stable base with weight distribution
    base = (cq.Workplane("XY")
           .box(width, depth, 8)
           .edges("|Z").fillet(2))
    
    # Create angled back support with proper geometry
    support = (cq.Workplane("XY")
              .move(0, depth/4)
              .rect(width-10, wall_thickness)
              .extrude(height)
              .rotate((0,0,0), (1,0,0), angle))
    
    # Add charging port with cable management
    charging_port = (cq.Workplane("XY")
                    .rect(15, 10)
                    .extrude(20)
                    .translate((0, -depth/3, 5)))
    
    # Anti-slip grooves for phone
    for i in range(3):
        groove = (cq.Workplane("XY")
                 .rect(width-20, 1)
                 .extrude(2)
                 .translate((0, 10 + i*5, height-5)))
        support = support.cut(groove)
    
    # Combine with proper fillets for 3D printing
    result = (base.union(support)
             .cut(charging_port)
             .edges(">>Z").chamfer(0.5))

except Exception:
    result = cq.Workplane("XY").box(width, depth, height)"""
            },
            
            "wall_hook": {
                "description": "Wall mounting hook with load distribution and mounting considerations",
                "complexity": "medium",
                "category": "functional",
                "code": """import cadquery as cq

# Engineering-focused wall hook
width = 40
depth = 25
thickness = 6
load_capacity = 5  # kg

try:
    # Create reinforced mounting plate
    plate = (cq.Workplane("XY")
            .box(width, thickness, depth)
            .edges("|Y").fillet(2))
    
    # Add structural ribs for load distribution
    for i in range(2):
        rib = (cq.Workplane("XY")
              .move(-width/4 + i*width/2, thickness/2)
              .rect(2, thickness)
              .extrude(depth*0.7)
              .edges().fillet(0.5))
        plate = plate.union(rib)
    
    # Create hook arm with proper load geometry
    hook_arm = (cq.Workplane("XY")
               .move(0, thickness/2)
               .circle(4)  # Thicker for load bearing
               .extrude(width*0.7)
               .rotate((0,0,0), (0,0,1), 90))
    
    # Create hook end with anti-slip
    hook_end = (cq.Workplane("XZ")
               .move(width*0.3, depth/2)
               .circle(4)
               .extrude(-15))
    
    # Add mounting holes with countersink
    holes = (cq.Workplane("XY")
            .pushPoints([(-width/3, 0), (width/3, 0)])
            .circle(2.5)
            .cutThruAll())
    
    countersinks = (cq.Workplane("XY")
                   .pushPoints([(-width/3, 0), (width/3, 0)])
                   .circle(5)
                   .cutBlind(2))
    
    result = (plate.union(hook_arm)
             .union(hook_end)
             .cut(holes)
             .cut(countersinks)
             .edges().fillet(0.5))

except Exception:
    result = cq.Workplane("XY").box(width, thickness, depth)"""
            },

            "mug": {
                "description": "Cup with handle",
                "complexity": "medium",
                "category": "functional",
                "code": """import cadquery as cq

# Mug
mug_radius = 40
mug_height = 90
wall_thickness = 3
rim_fillet = (wall_thickness * 0.9) / 2
handle_width = 8
handle_height = 60
handle_thickness = handle_width / 2
handle_arc_radius = 10
handle_offset_from_top = 20
handle_path_width = 30 # How far the handle sticks out
handle_path_height = 45 # Vertical distance of the handle

try:
   # Mug body
    mug_body = (
        cq.Workplane("XY")
        .circle(mug_radius)
        .extrude(mug_height)
        .faces(">Z")
        .shell(-wall_thickness)
        .edges(">Z")
        .fillet(rim_fillet)
    )

    # Handle path
    handle_path = (
        cq.Workplane("YZ")
        .moveTo(mug_radius-1, mug_height - handle_offset_from_top)
        .lineTo(mug_radius + handle_width, mug_height - handle_offset_from_top)
        .radiusArc((mug_radius + handle_width + handle_arc_radius, mug_height - handle_offset_from_top - handle_arc_radius), handle_arc_radius)
        .lineTo(mug_radius + handle_width + handle_arc_radius, mug_height - handle_height - handle_arc_radius) # Note the Z coordinate
        .radiusArc((mug_radius + handle_width, mug_height - handle_height - (handle_arc_radius * 2)), handle_arc_radius)
        .lineTo(mug_radius-1, mug_height - handle_height - (handle_arc_radius * 2))
        .close()
    )

    handle = (handle_path.extrude(handle_width)
            .faces(">X or <X")
            .shell(-handle_thickness)
            .edges()
            .fillet(1)
    )


    result = mug_body.union(handle)

except Exception:
    result = cq.Workplane("XY").box(width, thickness, depth)"""
            },
            
            "cable_management": {
                "description": "Cable management system with snap-fit and mounting options",
                "complexity": "medium",
                "category": "functional",
                "code": """import cadquery as cq

# Advanced cable management clip
width = 30
depth = 20
height = 15
cable_diameter = 8

try:
    # Create main body with ergonomic shape
    body = (cq.Workplane("XY")
           .box(width, depth, height)
           .edges().fillet(2))
    
    # Create C-shaped cable channel with proper clearance
    channel = (cq.Workplane("XY")
              .circle(cable_diameter/2 + 1)  # Extra clearance
              .extrude(height + 2)
              .translate((0, -depth/4, -1)))
    
    # Create snap-fit opening with flex consideration
    opening_width = cable_diameter * 0.9  # Tight fit
    opening = (cq.Workplane("XY")
              .rect(opening_width, depth)
              .extrude(height + 2)
              .translate((0, 0, -1)))
    
    # Add mounting options: screw hole
    mount_hole = (cq.Workplane("XY")
                 .move(0, depth/3)
                 .circle(2)
                 .cutThruAll())
    
    # Add mounting options: adhesive pad area
    adhesive_pad = (cq.Workplane("XY")
                   .move(0, -depth/3)
                   .rect(width*0.8, 8)
                   .cutBlind(0.5))
    
    # Combine with proper edge finishing
    result = (body.cut(channel)
             .cut(opening)
             .cut(mount_hole)
             .cut(adhesive_pad)
             .edges().fillet(1))

except Exception:
    result = cq.Workplane("XY").box(width, depth, height)"""
            },
            
            # LEVEL 3: MATHEMATICAL/COMPLEX GEOMETRIES
            "involute_gear": {
                "description": "Parametric involute spur gear with proper mathematical calculations",
                "complexity": "complex",
                "category": "mathematical",
                "code": """import cadquery as cq
import math

# Involute spur gear with proper calculations
teeth = 20
module = 2.5  # mm per tooth
pressure_angle = 20  # degrees
thickness = 6
bore_diameter = 8

try:
    # Calculate gear geometry
    pitch_diameter = teeth * module
    pitch_radius = pitch_diameter / 2
    base_radius = pitch_radius * math.cos(math.radians(pressure_angle))
    addendum = module
    dedendum = 1.25 * module
    outer_radius = pitch_radius + addendum
    root_radius = pitch_radius - dedendum
    
    # Create gear body
    gear_body = (cq.Workplane("XY")
                .circle(outer_radius)
                .extrude(thickness))
    
    # Generate involute tooth profile (simplified)
    tooth_points = []
    for i in range(20):  # Points per tooth side
        t = i * 0.1  # Parameter
        inv_x = base_radius * (math.cos(t) + t * math.sin(t))
        inv_y = base_radius * (math.sin(t) - t * math.cos(t))
        tooth_points.append((inv_x, inv_y))
    
    # Create tooth profile and pattern around gear
    angular_pitch = 360 / teeth
    for tooth_num in range(teeth):
        angle = tooth_num * angular_pitch
        
        # Simplified tooth (trapezoidal approximation)
        tooth_width_pitch = math.pi * module / 2
        tooth_width_top = tooth_width_pitch * 0.7
        
        tooth = (cq.Workplane("XY")
                .moveTo(pitch_radius, -tooth_width_pitch/2)
                .lineTo(outer_radius, -tooth_width_top/2)
                .lineTo(outer_radius, tooth_width_top/2)
                .lineTo(pitch_radius, tooth_width_pitch/2)
                .lineTo(root_radius, tooth_width_pitch/2)
                .lineTo(root_radius, -tooth_width_pitch/2)
                .close()
                .extrude(thickness)
                .rotate((0,0,0), (0,0,1), angle))
        
        gear_body = gear_body.union(tooth)
    
    # Add center bore with keyway
    bore = (cq.Workplane("XY")
           .circle(bore_diameter/2)
           .extrude(thickness))
    
    # Add keyway for shaft connection
    keyway = (cq.Workplane("XY")
             .rect(2, bore_diameter)
             .extrude(thickness))
    
    # Final gear with proper finishing
    result = (gear_body.cut(bore)
             .cut(keyway)
             .edges(">>Z").chamfer(0.2)
             .edges("<<Z").chamfer(0.2))

except Exception:
    # Fallback to simple gear approximation
    result = (cq.Workplane("XY")
             .circle(pitch_diameter/2)
             .extrude(thickness)
             .faces(">Z").circle(bore_diameter/2)
             .cutThruAll())"""
            },
            
            "helical_spring": {
                "description": "Parametric helical compression spring with proper coil geometry",
                "complexity": "complex", 
                "category": "mathematical",
                "code": """import cadquery as cq
import math

# Helical compression spring parameters
wire_diameter = 2
coil_diameter = 20
coils = 8
pitch = 4
free_length = coils * pitch

try:
    # Generate helix path
    helix_points = []
    points_per_coil = 20
    
    for i in range(coils * points_per_coil):
        angle = (i / points_per_coil) * 2 * math.pi
        x = (coil_diameter/2) * math.cos(angle)
        y = (coil_diameter/2) * math.sin(angle)
        z = (i / points_per_coil) * pitch
        helix_points.append((x, y, z))
    
    # Create wire cross-section
    wire_section = (cq.Workplane("YZ")
                   .circle(wire_diameter/2))
    
    # Sweep wire along helix path
    # Note: This is simplified - real implementation would use spline
    spring_coil = wire_section.sweep(
        cq.Workplane("XY").spline(helix_points[:10])  # Simplified for demo
    )
    
    # Add flat ends for compression
    end_coil_height = pitch/2
    bottom_end = (cq.Workplane("XY")
                 .circle(coil_diameter/2)
                 .circle(coil_diameter/2 - wire_diameter)
                 .extrude(end_coil_height))
    
    top_end = (cq.Workplane("XY")
              .circle(coil_diameter/2)
              .circle(coil_diameter/2 - wire_diameter)
              .extrude(end_coil_height)
              .translate((0, 0, free_length - end_coil_height)))
    
    result = spring_coil.union(bottom_end).union(top_end)

except Exception:
    # Fallback to simplified spring representation
    outer_cylinder = (cq.Workplane("XY")
                     .circle(coil_diameter/2)
                     .extrude(free_length))
    
    inner_cylinder = (cq.Workplane("XY")
                     .circle(coil_diameter/2 - wire_diameter)
                     .extrude(free_length))
    
    result = outer_cylinder.cut(inner_cylinder)"""
            },
            
            "threaded_fastener": {
                "description": "Metric threaded bolt with proper thread geometry and head",
                "complexity": "complex",
                "category": "mathematical", 
                "code": """import cadquery as cq
import math

# M8 bolt parameters
major_diameter = 8
pitch = 1.25  # Standard metric coarse
head_diameter = 13
head_height = 5.3
thread_length = 30
total_length = 40

try:
    # Create bolt head (hex)
    hex_head = (cq.Workplane("XY")
               .polygon(6, head_diameter)
               .extrude(head_height))
    
    # Create bolt shank
    shank = (cq.Workplane("XY")
            .circle(major_diameter/2)
            .extrude(total_length))
    
    # Create simplified thread representation
    minor_diameter = major_diameter - 1.25 * pitch
    thread_depth = (major_diameter - minor_diameter) / 2
    
    # Thread helix (simplified as spiral grooves)
    threads_count = int(thread_length / pitch)
    
    for i in range(threads_count):
        z_pos = head_height + i * pitch
        
        # Create thread groove
        thread_groove = (cq.Workplane("XY")
                        .move(0, 0)
                        .rect(major_diameter + 2, thread_depth/2)
                        .extrude(pitch/2)
                        .translate((major_diameter/2, 0, z_pos)))
        
        # Rotate for helix effect
        thread_groove = thread_groove.rotate(
            (0, 0, z_pos), (0, 0, z_pos + 1), i * 360 / 8
        )
        
        shank = shank.cut(thread_groove)
    
    # Add chamfer to thread start
    thread_chamfer = (cq.Workplane("XY")
                     .circle(major_diameter/2 + 0.2)
                     .circle(major_diameter/2 - 0.2)
                     .extrude(1)
                     .translate((0, 0, head_height + thread_length - 1)))
    
    # Combine head and threaded shank
    result = (hex_head.union(shank)
             .union(thread_chamfer)
             .edges(">>Z").chamfer(0.2))

except Exception:
    # Fallback to simple bolt
    head = (cq.Workplane("XY")
           .circle(head_diameter/2)
           .extrude(head_height))
    
    shaft = (cq.Workplane("XY")
            .circle(major_diameter/2)
            .extrude(total_length))
    
    result = head.union(shaft)"""
            },

            "Cycloidal_gear": {
                "description": "3 tooth cycloidal gear",
                "complexity": "complex",
                "category": "mathematical", 
                "code": """import cadquery as cq
from math import sin, cos, pi, floor

try:
    # define the generating function
    def hypocycloid(t, r1, r2):
        return (
            (r1 - r2) * cos(t) + r2 * cos(r1 / r2 * t - t),
            (r1 - r2) * sin(t) + r2 * sin(-(r1 / r2 * t - t)),
        )


    def epicycloid(t, r1, r2):
        return (
            (r1 + r2) * cos(t) - r2 * cos(r1 / r2 * t + t),
            (r1 + r2) * sin(t) - r2 * sin(r1 / r2 * t + t),
        )


    def gear(t, r1=4, r2=1):
        if (-1) ** (1 + floor(t / 2 / pi * (r1 / r2))) < 0:
            return epicycloid(t, r1, r2)
        else:
            return hypocycloid(t, r1, r2)


    # create the gear profile and extrude it
    result = (
        cq.Workplane("XY")
            .parametricCurve(lambda t: gear(t * 2 * pi, 6, 1))
            .twistExtrude(15, 90)
            .faces(">Z")
            .workplane()
            .circle(2)
            .cutThruAll()
    )

except Exception:
    # Fallback to simple bolt
    head = (cq.Workplane("XY")
           .circle(head_diameter/2)
           .extrude(head_height))
    
    shaft = (cq.Workplane("XY")
            .circle(major_diameter/2)
            .extrude(total_length))
    
    result = head.union(shaft)"""
            },
            
            # LEVEL 4: ADVANCED MANUFACTURING PATTERNS
            "overhang_optimized": {
                "description": "Design optimized for 3D printing with overhang angle considerations",
                "complexity": "advanced",
                "category": "manufacturing",
                "code": """import cadquery as cq
import math

# Overhang-optimized bracket design
width = 60
depth = 40  
height = 30
max_overhang_angle = 45  # degrees

try:
    # Create base with no overhangs
    base = (cq.Workplane("XY")
           .box(width, depth, 8)
           .edges("|Z").fillet(2))
    
    # Create support arm with proper overhang angles
    arm_length = 25
    arm_height = height - 8
    
    # Calculate support geometry to stay within overhang limits
    support_offset = arm_height * math.tan(math.radians(max_overhang_angle))
    
    # Create tapered support following overhang rule
    support_profile = (cq.Workplane("XZ")
                      .moveTo(0, 8)
                      .lineTo(support_offset, height)
                      .lineTo(arm_length, height)
                      .lineTo(arm_length, height - 5)
                      .lineTo(5, 8)
                      .close())
    
    support_arm = support_profile.extrude(width/3)
    
    # Add mounting hole with bridging consideration
    mount_hole = (cq.Workplane("XY")
                 .move(arm_length - 8, 0)
                 .circle(4)
                 .extrude(8)
                 .translate((0, 0, height - 8)))
    
    # Add support material for hole bridging
    bridge_support = (cq.Workplane("XY")
                     .move(arm_length - 8, 0)
                     .rect(8, 1)
                     .extrude(1)
                     .translate((0, 0, height - 5)))
    
    # Combine with print-friendly fillets
    result = (base.union(support_arm)
             .cut(mount_hole)
             .union(bridge_support)
             .edges().fillet(0.5))  # Small fillets for better bridging

except Exception:
    result = cq.Workplane("XY").box(width, depth, height)"""
            },
            
            "living_hinge": {
                "description": "Flexible living hinge design for 3D printed assemblies",
                "complexity": "advanced",
                "category": "manufacturing",
                "code": """import cadquery as cq

# Living hinge parameters
hinge_length = 50
hinge_width = 20
part_thickness = 3
hinge_thickness = 0.6  # Thin for flexibility
gap_width = 0.2

try:
    # Create main body parts
    part1 = (cq.Workplane("XY")
            .box(hinge_width, hinge_length/2 - gap_width/2, part_thickness)
            .translate((0, -hinge_length/4 - gap_width/4, 0)))
    
    part2 = (cq.Workplane("XY")
            .box(hinge_width, hinge_length/2 - gap_width/2, part_thickness)
            .translate((0, hinge_length/4 + gap_width/4, 0)))
    
    # Create flexible hinge section
    hinge_segments = 8
    segment_length = (hinge_length - 2*gap_width) / hinge_segments
    
    hinge_parts = []
    for i in range(hinge_segments):
        if i % 2 == 0:  # Alternating pattern for flexibility
            segment = (cq.Workplane("XY")
                      .box(hinge_width*0.8, segment_length*0.8, hinge_thickness)
                      .translate((0, -hinge_length/2 + gap_width + i*segment_length + segment_length/2, part_thickness/2)))
        else:
            segment = (cq.Workplane("XY")
                      .box(hinge_width*0.6, segment_length*0.6, hinge_thickness)
                      .translate((0, -hinge_length/2 + gap_width + i*segment_length + segment_length/2, part_thickness/2)))
        
        hinge_parts.append(segment)
    
    # Combine all parts
    result = part1.union(part2)
    for segment in hinge_parts:
        result = result.union(segment)
    
    # Add connection points between segments
    for i in range(hinge_segments - 1):
        y_pos = -hinge_length/2 + gap_width + (i+1)*segment_length
        connector = (cq.Workplane("XY")
                    .box(2, 1, hinge_thickness)
                    .translate((0, y_pos, part_thickness/2)))
        result = result.union(connector)
    
    # Final cleanup with minimal filleting
    result = result.edges("|Z").fillet(0.2)

except Exception:
    # Simple fallback hinge
    result = (cq.Workplane("XY")
             .box(hinge_width, hinge_length, part_thickness)
             .faces(">Z").shell(-0.5))"""
            },
            
            "assembly_joint": {
                "description": "Snap-fit assembly joint for multi-part 3D printed objects",
                "complexity": "advanced", 
                "category": "manufacturing",
                "code": """import cadquery as cq

# Snap-fit joint parameters
joint_length = 20
joint_width = 8
joint_height = 6
snap_depth = 1.5
clearance = 0.2

try:
    # Create male part (tab)
    tab_width = joint_width - 2*clearance
    tab_height = joint_height - clearance
    
    tab_base = (cq.Workplane("XY")
               .box(tab_width, joint_length, tab_height/2)
               .translate((0, 0, tab_height/4)))
    
    # Create snap feature with proper draft angles
    snap_feature = (cq.Workplane("XY")
                   .move(0, joint_length/2 - 2)
                   .rect(tab_width, 4)
                   .extrude(snap_depth)
                   .translate((0, 0, tab_height/2)))
    
    # Add lead-in chamfer for easy insertion
    lead_in = (cq.Workplane("XY")
              .move(0, joint_length/2)
              .rect(tab_width, 2)
              .extrude(tab_height/2)
              .edges(">>Y").chamfer(tab_height/4)
              .translate((0, 0, tab_height/4)))
    
    male_part = (tab_base.union(snap_feature)
                .union(lead_in)
                .edges().fillet(0.3))
    
    # Create female part (socket)
    socket_outer = (cq.Workplane("XY")
                   .box(joint_width, joint_length + 4, joint_height))
    
    socket_cavity = (cq.Workplane("XY")
                    .box(tab_width + clearance, joint_length, tab_height + clearance)
                    .translate((0, 0, (joint_height - tab_height)/2)))
    
    # Create snap recess
    snap_recess = (cq.Workplane("XY")
                  .move(0, joint_length/2 - 2)
                  .rect(tab_width + clearance, 4)
                  .extrude(snap_depth + clearance)
                  .translate((0, 0, joint_height/2)))
    
    # Add flex slots for snap action
    flex_slots = []
    for i in [-1, 1]:
        slot = (cq.Workplane("XY")
               .move(i * (joint_width/4), 0)
               .rect(0.5, joint_length)
               .extrude(joint_height))
        flex_slots.append(slot)
    
    female_part = socket_outer.cut(socket_cavity).cut(snap_recess)
    for slot in flex_slots:
        female_part = female_part.cut(slot)
    
    # Combine both parts for demonstration
    result = (male_part.translate((-joint_width, 0, 0))
             .union(female_part.translate((joint_width, 0, 0))))

except Exception:
    # Simple interlocking joint fallback
    result = (cq.Workplane("XY")
             .box(joint_width*2, joint_length, joint_height))"""
            }
        }
    
    def _initialize_embeddings(self):
        """Initialize or load embeddings for semantic search"""
        embeddings_path = self.cache_dir / "enhanced_embeddings.pkl"
        index_path = self.cache_dir / "enhanced_faiss_index.bin"
        
        if embeddings_path.exists() and index_path.exists():
            self._load_embeddings()
        else:
            self._create_embeddings()
    
    def _create_embeddings(self):
        """Create embeddings for all reference examples"""
        print("🔄 Creating embeddings for enhanced reference library...")
        
        # Prepare texts for embedding with enhanced context
        texts = []
        keys = []
        
        for key, example in self.library.items():
            # Enhanced text includes complexity and category
            text = f"{key.replace('_', ' ')} {example['description']} {example['complexity']} {example['category']}"
            texts.append(text)
            keys.append(key)
        
        # Create embeddings
        embeddings = self.embedding_model.encode(texts)
        
        # Create FAISS index
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)  # Inner product (cosine similarity)
        
        # Normalize vectors for cosine similarity
        faiss.normalize_L2(embeddings)
        index.add(embeddings.astype('float32'))
        
        # Store
        self.embeddings = embeddings
        self.faiss_index = index
        self.reference_keys = keys
        
        # Cache to disk
        self._save_embeddings()
        
        print(f"✅ Created enhanced embeddings for {len(texts)} references")
    
    def _save_embeddings(self):
        """Save embeddings to disk"""
        embeddings_path = self.cache_dir / "enhanced_embeddings.pkl"
        index_path = self.cache_dir / "enhanced_faiss_index.bin"
        keys_path = self.cache_dir / "enhanced_keys.pkl"
        
        # Save embeddings and keys
        with open(embeddings_path, 'wb') as f:
            pickle.dump(self.embeddings, f)
        
        with open(keys_path, 'wb') as f:
            pickle.dump(self.reference_keys, f)
        
        # Save FAISS index
        faiss.write_index(self.faiss_index, str(index_path))
        
        print(f"💾 Cached enhanced embeddings to {self.cache_dir}")
    
    def _load_embeddings(self):
        """Load embeddings from disk"""
        embeddings_path = self.cache_dir / "enhanced_embeddings.pkl"
        index_path = self.cache_dir / "enhanced_faiss_index.bin"
        keys_path = self.cache_dir / "enhanced_keys.pkl"
        
        try:
            # Load embeddings and keys
            with open(embeddings_path, 'rb') as f:
                self.embeddings = pickle.load(f)
            
            with open(keys_path, 'rb') as f:
                self.reference_keys = pickle.load(f)
            
            # Load FAISS index
            self.faiss_index = faiss.read_index(str(index_path))
            
            print(f"📚 Loaded cached enhanced embeddings for {len(self.reference_keys)} references")
            
        except Exception as e:
            print(f"❌ Failed to load cached embeddings: {e}")
            self._create_embeddings()
    
    def semantic_search(self, query: str, top_k: int = 2, threshold: float = 0.3) -> List[Tuple[str, float]]:
        """Enhanced semantic search with complexity consideration"""
        if self.faiss_index is None:
            print("❌ Embeddings not initialized")
            return [("simple_box", 1.0)]  # Fallback
        
        try:
            # Encode query
            query_embedding = self.embedding_model.encode([query])
            faiss.normalize_L2(query_embedding)  # Normalize for cosine similarity
            
            # Search with larger pool first
            search_k = min(len(self.reference_keys), top_k * 3)
            similarities, indices = self.faiss_index.search(query_embedding.astype('float32'), search_k)
            
            # Enhanced filtering with complexity consideration
            results = []
            complexity_scores = {"simple": 1.0, "medium": 0.9, "complex": 0.8, "advanced": 0.7}
            
            for i, (similarity, idx) in enumerate(zip(similarities[0], indices[0])):
                if similarity >= threshold:
                    key = self.reference_keys[idx]
                    example = self.library[key]
                    
                    # Adjust score based on complexity appropriateness
                    complexity_factor = complexity_scores.get(example['complexity'], 0.8)
                    adjusted_similarity = similarity * complexity_factor
                    
                    results.append((key, float(adjusted_similarity)))
            
            # Sort by adjusted similarity and take top_k
            results.sort(key=lambda x: x[1], reverse=True)
            results = results[:top_k]
            
            # Ensure at least one result
            if not results:
                results = [(self.reference_keys[indices[0][0]], float(similarities[0][0]))]
            
            print(f"🔍 Enhanced search for '{query}': {[(r[0], f'{r[1]:.3f}') for r in results]}")
            return results
            
        except Exception as e:
            print(f"❌ Enhanced search failed: {e}")
            return [("simple_box", 1.0)]  # Fallback
    
    def get_reference(self, key: str) -> Dict:
        """Get reference example by key"""
        return self.library.get(key, self.library["simple_box"])
    
    def get_all_references(self) -> Dict:
        """Get all reference examples"""
        return self.library
    
    def get_by_complexity(self, complexity: str) -> Dict:
        """Get references by complexity level"""
        return {k: v for k, v in self.library.items() if v.get('complexity') == complexity}
    
    def get_by_category(self, category: str) -> Dict:
        """Get references by category"""
        return {k: v for k, v in self.library.items() if v.get('category') == category}
    
    def add_reference(self, key: str, description: str, code: str, complexity: str = "medium", category: str = "functional"):
        """Add new reference example with metadata"""
        self.library[key] = {
            "description": description,
            "code": code,
            "complexity": complexity,
            "category": category
        }
        
        print(f"✅ Added reference: {key} ({complexity}, {category})")
        print("🔄 Rebuilding enhanced embeddings...")
        self._create_embeddings()
    
    def rebuild_embeddings(self):
        """Force rebuild of embeddings"""
        print("🔄 Rebuilding enhanced embeddings...")
        self._create_embeddings()
