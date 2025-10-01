# src/assistant_llama.py
"""COMPLETE FIX: Boolean-first flow + Smart defaults + Handle extraction"""
import json
import re
from typing import Dict, Optional, List, Tuple

from src.models.model_spec import ModelSpec

class IntelligentConversationAssistant:
    
    # Default parameter schemas when RAG/AST unavailable
    DEFAULT_PARAMS = {
        "mug": ["radius", "height", "wall_thickness", "have_handle"],
        "cup": ["bottom_radius", "top_radius", "height", "wall_thickness"],
        "bowl": ["top_radius", "height", "wall_thickness"],
        "cylinder": ["radius", "height"],
        "box": ["length", "width", "height"],
        "gear": ["teeth", "module", "pressure_angle", "bore_diameter"],
        "spring": ["coil_diameter", "coils", "wire_diameter", "free_length"],
    }
    
    # Smart defaults for non-critical parameters (FIX 3)
    PARAMETER_DEFAULTS = {
        'handle_arc_radius': 15,
        'handle_path_width': 30,
        'handle_path_height': 45,
        'offset_from_bottom': 10,
        'center_handle': True,
        'rim_fillet': 1.35,  # (wall_thickness * 0.9) / 2 for typical 3mm wall
    }
    
    # Boolean parameters that should be asked FIRST (FIX 1)
    BOOLEAN_PARAMS = ['have_handle', 'center_handle', 'thin', 'is_hollow']
    
    PARAMETER_ALIASES = {
        'height': ['height', 'h'],
        'width': ['width', 'w'],
        'length': ['length', 'l'],
        'radius': ['radius', 'diameter', 'r', 'd'],
        'bottom_radius': ['bottom_radius', 'bottom_diameter', 'base_radius', 'base_diameter'],
        'top_radius': ['top_radius', 'top_diameter'],
        'wall_thickness': ['wall_thickness', 'thickness', 'wall_t', 't'],
        'teeth': ['teeth', 'tooth_count', 'num_teeth'],
        'handle_width': ['handle_width', 'handle_thickness'],
        'handle_height': ['handle_height', 'handle_length'],
    }
    
    FRIENDLY_NAMES = {
        'height': 'height',
        'width': 'width',
        'radius': 'diameter',
        'bottom_radius': 'bottom diameter',
        'top_radius': 'top diameter',
        'wall_thickness': 'wall thickness',
        'handle_width': 'handle width',
        'handle_height': 'handle height',
        'have_handle': 'handle',
    }
    
    def __init__(self, llm_engine, rag_generator=None):
        self.llm_engine = llm_engine
        self.rag_generator = rag_generator
        self.conversation_history = []
        self.exchange_count = 0
        self.detected_object = None
        self.relevant_references = []
        self.extracted_parameters = {}
        self.collected_specs = {}
        self.system_prompt = self._build_strict_system_prompt()
    
    def _build_strict_system_prompt(self) -> str:
        """Natural conversation system prompt"""
        return """You're a friendly CAD assistant helping create 3D models. Chat naturally!

YOUR STYLE:
- Talk like a helpful friend, not a robot
- Use casual language and contractions ("I'll", "let's", "you're")
- Keep it brief (under 25 words usually)

WHAT TO ASK ABOUT (ONLY THESE):
- Size/dimensions: diameter, height, thickness (always in mm)
- Yes/no design choices ONLY if relevant: "Want a handle?"

NEVER ASK ABOUT:
- Colors, materials, finishes, style, decorations
- Spouts, lips, rims, or any features not mentioned
- Manufacturing details
- ONLY ask about what's needed for the basic shape

CRITICAL RULES:
1. If user says "no" to a feature (like handle), move on to dimensions immediately
2. Only ask about parameters that are actually needed
3. Never invent new features or ask about things not in the design

EXAMPLES:
User: "I want a mug"
You: "Want a handle on it?"

User: "no"
You: "Cool! What diameter and height?" ← NOT "what about spout?" or "what style?"

User: "50mm diameter, 100mm tall"
You: "Nice! How thick for the walls?"

User: "3mm"
You: "Awesome - creating that for you!"

Just be natural, brief, and only ask about dimensions!
"""
    
    def _get_missing_parameters_smart(self) -> List[str]:
        """FIX 1 & 3: Get missing params with boolean-first and skip dependent params"""
        missing = []
        
        # STEP 1: Check booleans first
        for param in self.extracted_parameters.keys():
            if param in self.BOOLEAN_PARAMS and not self._is_parameter_collected(param):
                # CRITICAL FIX: Skip center_handle if have_handle is False
                if param == 'center_handle':
                    has_handle = self.collected_specs.get('have_handle', True)
                    if not has_handle:
                        # User doesn't want a handle, so don't ask about centering
                        continue
                
                friendly_name = self.FRIENDLY_NAMES.get(param, param.replace('_', ' '))
                missing.append(friendly_name)
        
        # If any booleans are missing, ONLY return booleans (ask them first)
        if missing:
            return missing
        
        # STEP 2: Check if handle is wanted
        has_handle = self.collected_specs.get('have_handle', True)
        
        # STEP 3: Get critical dimensional parameters
        for param in self.extracted_parameters.keys():
            # Skip if already collected
            if self._is_parameter_collected(param):
                continue
            
            # Skip if it's a boolean (already handled)
            if param in self.BOOLEAN_PARAMS:
                continue
            
            # Skip if it has a default value (non-critical)
            if param in self.PARAMETER_DEFAULTS:
                continue
            
            # Skip handle-related params if no handle wanted (FIX 3)
            if not has_handle and param.startswith('handle_'):
                continue
            
            # Skip center_handle-dependent params
            if param == 'offset_from_bottom':
                center_handle = self.collected_specs.get('center_handle', True)
                if center_handle:  # Don't need offset if centered
                    continue
            
            friendly_name = self.FRIENDLY_NAMES.get(param, param.replace('_', ' '))
            missing.append(friendly_name)
        
        return missing
    
    def _build_natural_response_prompt(self, user_message: str) -> str:
        """Natural conversation prompt - less rigid, more human"""
        needed_params = self._get_missing_parameters_smart()
        
        # Build what we know so far
        known = []
        if self.collected_specs:
            for key, value in self.collected_specs.items():
                if isinstance(value, bool):
                    if value and key != 'center_handle':  # Don't mention center_handle
                        known.append(f"with {key.replace('_', ' ')}")
                elif isinstance(value, (int, float)) and value > 0:
                    name = self.FRIENDLY_NAMES.get(key, key.replace('_', ' '))
                    known.append(f"{name}: {value}mm")
        
        context = f"Context: {self.detected_object}" + (f" ({', '.join(known)})" if known else "")
        
        # All done - time to generate
        if not needed_params:
            return f"""{context}
User just said: "{user_message}"

All dimensions are collected. Say something like:
"Awesome - I'll make that now!" or "Perfect! Creating your {self.detected_object}..."

Keep it natural and brief!"""
        
        # Figure out what to ask next
        next_param = needed_params[0]
        
        # CRITICAL: Distinguish between mug dimensions and handle dimensions
        has_handle = self.collected_specs.get('have_handle', False)
        asking_about_handle = has_handle and next_param in ['handle width', 'handle height']
        
        # Check if we can ask about 2 related things at once
        pairs = [
            ('bottom diameter', 'top diameter'),
            ('diameter', 'height'),
            ('height', 'wall thickness'),
            ('handle width', 'handle height'),
        ]
        
        ask_pair = None
        for p1, p2 in pairs:
            if p1 in needed_params and p2 in needed_params:
                ask_pair = (p1, p2)
                break
        
        # Handle boolean questions naturally
        if next_param in ['handle']:
            return f"""{context}
User: "{user_message}"

Time to ask about the handle. Be casual! Examples:
"Want a handle on it?"
"Should I add a handle?"
"Handle or no handle?"

CRITICAL: Do NOT ask about spouts, lips, decorations, or any other features!

Your response:"""
        
        # Acknowledge if they just gave us info
        just_gave_info = len([v for v in self._extract_specifications_naturally(user_message).values() 
                             if (isinstance(v, (int, float)) and v > 0) or isinstance(v, bool)]) > 0
        
        # Ask about a pair of related params
        if ask_pair:
            p1, p2 = ask_pair
            
            # CRITICAL: Make it clear if asking about mug or handle
            object_context = "for the handle" if asking_about_handle else f"for the {self.detected_object}"
            
            if just_gave_info:
                return f"""{context}
User: "{user_message}"

They just gave you info - acknowledge it quickly, then ask ONLY about {p1} and {p2} {object_context}.
Examples:
"Nice! What {p1} and {p2} {object_context}?"
"Cool! How about the {p1} and {p2}?"

CRITICAL: Only ask about {p1} and {p2}. Do NOT mention spouts, styles, colors, or anything else!
Make it clear you're asking about the {self.detected_object if not asking_about_handle else 'handle'}!

Keep it casual and brief!"""
            else:
                return f"""{context}
User: "{user_message}"

Ask ONLY about {p1} and {p2} {object_context} naturally:
"What {p1} and {p2} are you thinking {object_context}?"
"How about {p1} and {p2}?"

CRITICAL: Only ask about these two dimensions {object_context}. Nothing else!
Be clear you're asking about the {self.detected_object if not asking_about_handle else 'handle'}!

Your response:"""
        
        # Ask about single param
        object_context = "for the handle" if asking_about_handle else f"for the {self.detected_object}"
        
        if just_gave_info:
            return f"""{context}
User: "{user_message}"

Quick acknowledgment + ask ONLY about {next_param} {object_context}:
"Great! And the {next_param} {object_context}?"
"Nice! How about {next_param}?"
"Perfect! What {next_param}?"

CRITICAL: Only ask about {next_param}. Do NOT invent other features!
Make it clear you're asking about the {self.detected_object if not asking_about_handle else 'handle'}!

Natural and brief!"""
        else:
            return f"""{context}
User: "{user_message}"

Ask ONLY about {next_param} {object_context} casually:
"What {next_param} do you want {object_context}?"
"How about the {next_param}?"

CRITICAL: Only ask about {next_param}. Nothing else!
Be clear you're asking about the {self.detected_object if not asking_about_handle else 'handle'}!

Your response:"""
    
    def _extract_specifications_naturally(self, user_message: str) -> Dict:
        """FIXED: Extract dimensions + BOOLEANS with better handle height detection"""
        if not self.detected_object:
            return {}
        
        extracted = {}
        text = user_message.lower()
        
        # BOOLEAN DETECTION FIRST (FIX 1)
        boolean_triggers = {
            'thin': (['thin', 'slim', 'narrow'], ['thick', 'not thin', 'chunky']),
            'have_handle': (['with handle', 'has handle', 'want a handle', 'want handle', 'yes'], 
                           ['without handle', 'no handle', 'handleless', "don't want", 'no']),
            'is_hollow': (['hollow', 'empty'], ['solid', 'filled']),
            'center_handle': (['center', 'centered', 'middle'], 
                            ['offset', 'not centered', 'not center', "don't center", 'off-center']),
        }
        
        for param_name, (true_triggers, false_triggers) in boolean_triggers.items():
            # CRITICAL: Skip center_handle entirely if no handle wanted
            if param_name == 'center_handle':
                has_handle = self.collected_specs.get('have_handle')
                if has_handle is False:
                    continue
            
            # Check if this param is in the template
            if param_name in self.extracted_parameters:
                # Special context check for "yes/no" responses
                if param_name == 'have_handle':
                    prev_message = self.conversation_history[-1]['content'] if self.conversation_history else ""
                    if 'handle' in prev_message.lower():
                        if any(trigger in text for trigger in ['yes', 'yeah', 'yep', 'sure']):
                            extracted[param_name] = True
                            print(f"✅ Boolean: {param_name} = True (found affirmative)")
                            continue
                        elif any(trigger in text for trigger in ['no', 'nah', 'nope']):
                            extracted[param_name] = False
                            print(f"✅ Boolean: {param_name} = False (found negative)")
                            continue
                
                # Check FALSE triggers FIRST (more specific)
                for trigger in false_triggers:
                    if trigger in text:
                        extracted[param_name] = False
                        print(f"✅ Boolean: {param_name} = False (found '{trigger}')")
                        break
                
                # Only check true triggers if we didn't find a false trigger
                if param_name not in extracted:
                    for trigger in true_triggers:
                        if trigger in text:
                            extracted[param_name] = True
                            print(f"✅ Boolean: {param_name} = True (found '{trigger}')")
                            break
        
        # MATH RELATIONSHIPS (before simple number extraction)
        math_results = self._extract_math_relationships(text)
        if math_results:
            extracted.update(math_results)
            print(f"🧮 Math relationship extracted: {math_results}")
        
        # DIAMETER - More flexible patterns
        diameter_patterns = [
            r'diameter\s+will\s+be\s+(\d+(?:\.\d+)?)',
            r'the\s+diameter\s+will\s+be\s+(\d+(?:\.\d+)?)',
            r'diameter\s+(?:is|of)\s+(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*mm\s+diameter',
            r'diameter.{0,10}(\d+(?:\.\d+)?)\s*mm',
        ]
        
        if 'diameter' not in extracted and 'radius' not in extracted:
            if 'bottom' not in text and 'top' not in text:
                for pattern in diameter_patterns:
                    match = re.search(pattern, text)
                    if match:
                        diameter = float(match.group(1))
                        if diameter > 0:
                            extracted['diameter'] = diameter
                            extracted['radius'] = diameter / 2
                            print(f"✅ Diameter: {diameter}mm (radius: {diameter/2}mm)")
                            break
        
        # HANDLE HEIGHT - SPECIFIC PATTERNS FIRST (CRITICAL FIX)
        if 'handle_height' not in extracted and 'handle' in text:
            handle_height_specific = [
                r'handle\s+height\s+will\s+be\s+(\d+(?:\.\d+)?)',
                r'handle\s+height\s+(?:is|of)\s+(\d+(?:\.\d+)?)',
                r'handle.*?height.*?(\d+(?:\.\d+)?)\s*mm',
                r'height.*?handle.*?(\d+(?:\.\d+)?)\s*mm',
                r'(\d+(?:\.\d+)?)\s*mm.*?handle.*?height',
            ]
            for pattern in handle_height_specific:
                match = re.search(pattern, text)
                if match:
                    value = float(match.group(1))
                    if value > 0:
                        extracted['handle_height'] = value
                        print(f"✅ Handle height: {value}mm")
                        break
        
        # HANDLE WIDTH - SPECIFIC PATTERNS
        if 'handle_width' not in extracted and 'handle' in text:
            handle_width_patterns = [
                r'handle\s+width\s+will\s+be\s+(\d+(?:\.\d+)?)',
                r'handle\s+width\s+(?:is|of)\s+(\d+(?:\.\d+)?)',
                r'handle.*?width.*?(\d+(?:\.\d+)?)\s*mm',
                r'width.*?handle.*?(\d+(?:\.\d+)?)\s*mm',
            ]
            for pattern in handle_width_patterns:
                match = re.search(pattern, text)
                if match:
                    value = float(match.group(1))
                    if value > 0:
                        extracted['handle_width'] = value
                        print(f"✅ Handle width: {value}mm")
                        break
        
        # HEIGHT (MUG/CUP HEIGHT - NOT HANDLE)
        # Only extract if NOT talking about handle
        if 'height' not in extracted and 'handle_height' not in extracted:
            # Check if this is clearly about the mug/object, not handle
            is_about_handle = 'handle' in text and any(word in text for word in ['handle height', 'height of the handle', 'handle is', 'handle will be'])
            
            if not is_about_handle:
                height_patterns = [
                    r'(\d+(?:\.\d+)?)\s*mm\s+tall(?!\s+handle)',  # "80mm tall" but not "80mm tall handle"
                    r'(\d+(?:\.\d+)?)\s*mm\s+high(?!\s+handle)',
                    r'(?:mug|cup|object)\s+height.{0,20}(\d+(?:\.\d+)?)',
                    r'(\d+(?:\.\d+)?)\s*mm\s+in\s+height',
                    r'tall.{0,20}(\d+(?:\.\d+)?)',
                    r'it\s+will\s+be\s+(\d+(?:\.\d+)?)\s*mm\s+tall',
                ]
                for pattern in height_patterns:
                    match = re.search(pattern, text)
                    if match:
                        height = float(match.group(1))
                        if height > 0:
                            extracted['height'] = height
                            print(f"✅ Height: {height}mm")
                            break
        
        # BOTTOM DIAMETER/RADIUS
        bottom_patterns = [
            r'bottom.{0,30}?(\d+(?:\.\d+)?)\s*mm',
            r'(\d+(?:\.\d+)?)\s*mm.{0,20}?bottom',
            r'base.{0,20}(\d+(?:\.\d+)?)\s*mm',
        ]
        if 'bottom_diameter' not in extracted and 'bottom_radius' not in extracted:
            for pattern in bottom_patterns:
                match = re.search(pattern, text)
                if match:
                    diameter = float(match.group(1))
                    if diameter > 0:
                        extracted['bottom_diameter'] = diameter
                        extracted['bottom_radius'] = diameter / 2
                        break
        
        # TOP DIAMETER/RADIUS (skip if contains math words)
        if not re.search(r'\d+\s*(?:times|x|multiplied)', text):
            top_patterns = [
                r'top.{0,20}(\d+(?:\.\d+)?)\s*mm',
                r'(?:the\s+)?top\s+will\s+be\s+(\d+(?:\.\d+)?)\s*mm',
                r'(\d+(?:\.\d+)?)\s*mm.{0,20}top',
            ]
            if 'top_diameter' not in extracted and 'top_radius' not in extracted:
                for pattern in top_patterns:
                    match = re.search(pattern, text)
                    if match:
                        diameter = float(match.group(1))
                        if diameter > 0:
                            extracted['top_diameter'] = diameter
                            extracted['top_radius'] = diameter / 2
                            break
        
        # HANDLE "SAME" REFERENCES
        if 'same' in text and 'top_diameter' not in extracted:
            same_match = re.search(r'same\s+(?:as\s+)?(\d+(?:\.\d+)?)', text)
            if same_match:
                diameter = float(same_match.group(1))
                if 'bottom_diameter' in self.collected_specs:
                    extracted['top_diameter'] = diameter
                    extracted['top_radius'] = diameter / 2
            elif 'bottom' in text and 'bottom_diameter' in self.collected_specs:
                extracted['top_diameter'] = self.collected_specs['bottom_diameter']
                extracted['top_radius'] = self.collected_specs['bottom_radius']
        
        # WALL THICKNESS
        thickness_patterns = [
            r'wall\s+thickness\s+will\s+be\s+(\d+(?:\.\d+)?)',
            r'wall.{0,20}thickness.{0,20}(\d+(?:\.\d+)?)',
            r'thickness.{0,20}(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*mm\s+thick',
            r'thick.{0,20}(\d+(?:\.\d+)?)',
        ]
        for pattern in thickness_patterns:
            match = re.search(pattern, text)
            if match:
                thickness = float(match.group(1))
                if thickness > 0:
                    extracted['wall_thickness'] = thickness
                    break
        
        # GENERIC PARAMETER EXTRACTION (catches remaining params)
        # This must come LAST after all specific extractions
        for param_name in self.extracted_parameters.keys():
            # Skip if already extracted
            if param_name in extracted:
                continue
            
            # Skip booleans (handled earlier)
            if param_name in self.BOOLEAN_PARAMS:
                continue
            
            # Skip if has a default (non-critical)
            if param_name in self.PARAMETER_DEFAULTS:
                continue
            
            # Skip handle params (already handled above)
            if param_name in ['handle_height', 'handle_width']:
                continue
            
            # CRITICAL: Skip generic 'height' if we just extracted 'handle_height'
            # This prevents "height will be 50mm" from overwriting mug height
            # when user is talking about handle dimensions
            if param_name == 'height' and 'handle_height' in extracted:
                print(f"⏭️ Skipping generic 'height' - already extracted handle_height")
                continue
            
            # Similarly, skip 'width' if we just extracted 'handle_width'
            if param_name == 'width' and 'handle_width' in extracted:
                print(f"⏭️ Skipping generic 'width' - already extracted handle_width")
                continue
            
            # Create pattern from parameter name
            param_display = param_name.replace('_', ' ')
            
            generic_patterns = [
                rf'{param_display}\s+will\s+be\s+(\d+(?:\.\d+)?)',
                rf'the\s+{param_display}\s+will\s+be\s+(\d+(?:\.\d+)?)',
                rf'{param_display}\s+(?:is|of)\s+(\d+(?:\.\d+)?)',
                rf'(\d+(?:\.\d+)?)\s*mm\s+{param_display}',
                rf'{param_display}.{{0,10}}(\d+(?:\.\d+)?)\s*mm',
                rf'{param_display}.{{0,5}}(\d+(?:\.\d+)?)',
            ]
            
            for pattern in generic_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = float(match.group(1))
                    if value > 0:
                        extracted[param_name] = value
                        print(f"✅ Generic extraction: {param_name} = {value}mm")
                        break
            
            if param_name in extracted:
                break
        
        # CRITICAL FIX: Remove any invalid values (≤ 0) before returning
        invalid_keys = []
        for key, value in extracted.items():
            if isinstance(value, (int, float)) and value <= 0:
                invalid_keys.append(key)
        
        for key in invalid_keys:
            del extracted[key]
            print(f"⚠️ Removed invalid value: {key} = 0")
        
        return extracted
    
    def _extract_math_relationships(self, text: str) -> Dict:
        """Handle mathematical relationships like '2 times bigger'"""
        extracted = {}
        
        # Pattern: "X times bigger/larger than bottom"
        times_patterns = [
            r'(\d+(?:\.\d+)?)\s*times?\s+(?:bigger|larger)',
            r'(\d+(?:\.\d+)?)\s*x\s+(?:bigger|larger)',
        ]
        
        for pattern in times_patterns:
            match = re.search(pattern, text)
            if match:
                multiplier = float(match.group(1))
                print(f"🧮 Found multiplier: {multiplier}")
                
                # Get bottom diameter from collected specs FIRST
                bottom_diameter = self.collected_specs.get('bottom_diameter')
                
                # If not in collected specs, try to extract from same message
                if not bottom_diameter or bottom_diameter <= 0:
                    # Look for bottom diameter in same text (flexible pattern for typos)
                    bottom_patterns = [
                        r'bottom.{0,30}?(\d+(?:\.\d+)?)\s*mm',  # More flexible
                        r'(\d+(?:\.\d+)?)\s*mm.{0,20}?bottom',
                        r'bottom.{0,30}?(\d+(?:\.\d+)?)',       # Without mm
                    ]
                    
                    for bp in bottom_patterns:
                        bottom_match = re.search(bp, text)
                        if bottom_match:
                            bottom_diameter = float(bottom_match.group(1))
                            print(f"🧮 Found bottom diameter in text: {bottom_diameter}")
                            # Only add if valid
                            if bottom_diameter > 0:
                                extracted['bottom_diameter'] = bottom_diameter
                                extracted['bottom_radius'] = bottom_diameter / 2
                            break
                
                # Calculate top diameter only if we have valid bottom diameter
                if bottom_diameter and bottom_diameter > 0:
                    top_diameter = bottom_diameter * multiplier
                    extracted['top_diameter'] = top_diameter
                    extracted['top_radius'] = top_diameter / 2
                    print(f"🧮 Calculated: {bottom_diameter} × {multiplier} = {top_diameter}")
                else:
                    print(f"🧮 Cannot calculate top - no valid bottom diameter (got {bottom_diameter})")
                
                break
        
        return extracted
    
    def _get_missing_geometry_parameters(self) -> List[str]:
        """Legacy method - now uses _get_missing_parameters_smart()"""
        return self._get_missing_parameters_smart()
    
    def _is_parameter_collected(self, param: str) -> bool:
        """Check if parameter is collected WITH A VALID VALUE"""
        aliases = self.PARAMETER_ALIASES.get(param, [param])
        
        # Check each alias
        for alias in aliases:
            if alias in self.collected_specs:
                value = self.collected_specs[alias]
                
                # For booleans, any value (True/False) is valid
                if isinstance(value, bool):
                    return True
                
                # For numbers, must be > 0 to be valid
                if isinstance(value, (int, float)) and value > 0:
                    return True
        
        # Handle radius/diameter conversion (check if valid > 0)
        if param.endswith('_radius'):
            diameter_key = param.replace('_radius', '_diameter')
            if diameter_key in self.collected_specs:
                value = self.collected_specs[diameter_key]
                if isinstance(value, (int, float)) and value > 0:
                    return True
        elif param.endswith('_diameter'):
            radius_key = param.replace('_diameter', '_radius')
            if radius_key in self.collected_specs:
                value = self.collected_specs[radius_key]
                if isinstance(value, (int, float)) and value > 0:
                    return True
        
        # Also check the param itself
        if param in self.collected_specs:
            value = self.collected_specs[param]
            if isinstance(value, bool):
                return True
            if isinstance(value, (int, float)) and value > 0:
                return True
        
        return False
    
    def chat(self, user_message: str) -> Dict:
        """Main chat method - passes system prompt"""
        self.exchange_count += 1
        self.conversation_history.append({"role": "user", "content": user_message})
        
        if self.exchange_count == 1:
            self._handle_initial_object_detection(user_message)
        
        # Extract specifications
        new_specs = self._extract_specifications_naturally(user_message)
        if new_specs:
            self.collected_specs.update(new_specs)
            
            # CRITICAL FIX: Auto-apply defaults based on have_handle value
            if 'have_handle' in new_specs:
                if new_specs['have_handle'] is False:
                    # User doesn't want a handle, set all handle params to defaults
                    if 'center_handle' not in self.collected_specs:
                        self.collected_specs['center_handle'] = True  # Default doesn't matter
                    if 'handle_width' not in self.collected_specs:
                        self.collected_specs['handle_width'] = 8  # Default
                    if 'handle_height' not in self.collected_specs:
                        self.collected_specs['handle_height'] = 45  # Default
                    print(f"   🔒 No handle wanted - auto-filled handle params with defaults")
                
                elif new_specs['have_handle'] is True:
                    # User DOES want a handle, auto-fill center_handle with default
                    if 'center_handle' not in self.collected_specs:
                        self.collected_specs['center_handle'] = True  # Default: centered
                    print(f"   ✅ Handle wanted - center_handle defaulted to True")
        
        missing_params = self._get_missing_parameters_smart()
        has_essential = self._has_essential_parameters()
        
        print(f"\n💬 Exchange {self.exchange_count}: {self.detected_object}")
        print(f"   Collected: {self.collected_specs}")
        print(f"   Still need: {missing_params}")
        
        # Build prompt
        prompt = self._build_natural_response_prompt(user_message)
        
        # Pass system prompt to LLM with low temperature to prevent hallucinations
        ai_response = self.llm_engine.generate(
            prompt,
            temperature=0.1,  # Low temp to prevent hallucinations like "spout"
            system=self.system_prompt
        )
        
        # Clean up the response - remove any "(in mm)" artifacts if LLM added them
        ai_response = re.sub(r'\s*\(in mm\)\s*', '', ai_response)
        ai_response = re.sub(r'\s*\(mm\)\s*', '', ai_response)
        
        self.conversation_history.append({"role": "assistant", "content": ai_response})
        
        # Check if ready to generate
        model_spec = None
        if "GENERATE_MODEL:" in ai_response or (has_essential and len(missing_params) == 0):
            final_specs = self._convert_specs_to_model_format()
            
            # Apply defaults for non-critical params
            for param, default_value in self.PARAMETER_DEFAULTS.items():
                if param in self.extracted_parameters and param not in final_specs:
                    final_specs[param] = default_value
                    print(f"   📝 Using default: {param} = {default_value}")
            
            if 'wall_thickness' not in final_specs:
                return {
                    'message': "Just need one more thing - how thick should the walls be?",
                    'generate_model': False,
                    'model_spec': None,
                    'cadquery_code': None,
                    'rag_references': self.relevant_references
                }
            
            model_spec = ModelSpec(object_type=self.detected_object, **final_specs)
            
            if self.relevant_references:
                model_spec.rag_reference = self.relevant_references[0][0]
                model_spec.rag_similarity = self.relevant_references[0][1]
            
            # Natural completion messages
            completion_messages = [
                f"Perfect! Making your {self.detected_object} now...",
                f"Awesome - creating that for you!",
                f"Got it! I'll generate your {self.detected_object}.",
                f"Sweet! Building your {self.detected_object}...",
            ]
            import random
            ai_response = random.choice(completion_messages)
            print(f"\n✅ {ai_response}")
            print(f"   Final specs: {final_specs}")
        
        return {
            'message': ai_response,
            'generate_model': model_spec is not None,
            'model_spec': model_spec.model_dump() if model_spec else None,
            'cadquery_code': None,
            'rag_references': self.relevant_references
        }
    
    def _has_essential_parameters(self) -> bool:
        """Check if essential parameters are collected - WORKS FOR ANY OBJECT TYPE"""
        converted = self._convert_specs_to_model_format()
        
        # Get list of what's still needed
        missing = self._get_missing_parameters_smart()
        
        # If nothing is missing, we're ready!
        if len(missing) == 0:
            print(f"   ✅ All parameters collected - ready to generate!")
            return True
        
        # Debug output
        print(f"   ⏳ Still missing {len(missing)} params: {missing}")
        return False
    
    def _convert_specs_to_model_format(self) -> Dict:
        """Convert collected specs to model parameters"""
        converted = {}
        
        for key, value in self.collected_specs.items():
            # Handle booleans
            if isinstance(value, bool):
                converted[key] = value
                continue
            
            if not isinstance(value, (int, float)) or value <= 0:
                continue
            
            if key == 'height':
                converted['height'] = value
            elif key == 'diameter':
                converted['radius'] = value / 2
            elif key == 'bottom_diameter':
                converted['bottom_radius'] = value / 2
            elif key == 'top_diameter':
                converted['top_radius'] = value / 2
            elif key == 'radius':
                converted['radius'] = value
            elif key == 'bottom_radius':
                converted['bottom_radius'] = value
            elif key == 'top_radius':
                converted['top_radius'] = value
            elif key in ['thickness', 'wall_thickness']:
                converted['wall_thickness'] = value
            elif key in ['handle_width', 'handle_height']:
                converted[key] = value
        
        return converted
    
    def _handle_initial_object_detection(self, message: str):
        """Always detect object, only gate RAG"""
        # ALWAYS detect object type
        self.detected_object = self._llm_extract_object_type(message)
        
        # Only do RAG if available
        if self.rag_generator and self.detected_object:
            try:
                search_query = f"{self.detected_object} CAD 3D model"
                results = self.rag_generator.rag_library.semantic_search(
                    search_query, top_k=3, threshold=0.13
                )
                
                if results:
                    # Check for exact match
                    exact_match = None
                    for ref_name, similarity in results:
                        if ref_name.lower() == self.detected_object.lower():
                            exact_match = (ref_name, similarity)
                            break
                    
                    if exact_match:
                        self.relevant_references = [exact_match]
                    else:
                        self.relevant_references = results
                    
                    best_ref_name = self.relevant_references[0][0]
                    best_ref = self.rag_generator.rag_library.get_reference(best_ref_name)
                    
                    if best_ref and 'code' in best_ref:
                        self.extracted_parameters = self.rag_generator.ast_editor.extract_parameters_from_code(
                            best_ref['code']
                        )
            except Exception as e:
                print(f"RAG search failed: {e}")
        
        # Use default schema if AST extraction failed or no RAG
        if not self.extracted_parameters and self.detected_object:
            if self.detected_object in self.DEFAULT_PARAMS:
                self.extracted_parameters = {
                    p: None for p in self.DEFAULT_PARAMS[self.detected_object]
                }
                print(f"Using default schema for {self.detected_object}: {list(self.extracted_parameters.keys())}")
    
    def _llm_extract_object_type(self, message: str) -> Optional[str]:
        """Extract object type from user message"""
        prompt = f"""Extract the object type from: "{message}"

Return ONLY the object name (one word). Examples:
"I want a mug" -> mug
"Make me a cup" -> cup
"I need a gear" -> gear

Object type:"""
        
        try:
            response = self.llm_engine.generate(prompt, temperature=0.0)
            object_type = response.strip().lower().split()[0]
            return object_type
        except Exception as e:
            print(f"Object detection failed: {e}")
            return None
    
    def reset(self):
        """Reset conversation state"""
        self.conversation_history = []
        self.exchange_count = 0
        self.detected_object = None
        self.relevant_references = []
        self.extracted_parameters = {}
        self.collected_specs = {}