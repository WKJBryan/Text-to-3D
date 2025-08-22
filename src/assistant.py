# src/assistant.py
"""Enhanced Intelligent Conversation Assistant with Object-First RAG Flow"""
import json
import re
from typing import Dict, Optional, List, Tuple

class IntelligentConversationAssistant:
    def __init__(self, llm_engine, rag_generator=None):
        self.llm_engine = llm_engine
        self.rag_generator = rag_generator  # Access to RAG for immediate search
        self.conversation_history = []
        self.exchange_count = 0
        self.detected_object = None
        self.relevant_references = []
        self.extracted_parameters = {}
        self.system_prompt = self._build_intelligent_system_prompt()
        
    def _build_intelligent_system_prompt(self) -> str:
        return """You are a helpful 3D design assistant using OBJECT-FIRST conversation flow.

WORKFLOW:
1. IMMEDIATELY identify the object type from user's first message
2. Use RAG-discovered parameters for intelligent questions
3. Ask ONLY about parameters that matter for the specific object
4. Generate as soon as you have key information

RULES:
- Keep responses to 2-3 sentences MAX
- Ask only 1-2 questions per response
- Use the ACTUAL parameters from reference examples when available
- Suggest defaults from reference code
- DO NOT ask about materials or colors (geometry only)

GENERATION TRIGGER:
When ready, respond with: GENERATE_MODEL: {flat JSON structure}

The JSON must include object_type and relevant parameters discovered from RAG.

Keep it simple and focused on the specific object's needs."""

    def chat(self, user_message: str) -> Dict:
        """Process user message with object-first RAG flow"""
        self.exchange_count += 1
        self.conversation_history.append(f"User: {user_message}")
        
        # STEP 1: Object-first detection on first message
        if self.exchange_count == 1:
            self._handle_initial_object_detection(user_message)
        
        # Build context with RAG insights
        context = self._build_enhanced_context()
        
        # Create prompt with object-specific guidance
        prompt = self._build_object_aware_prompt(user_message, context)
        
        # Generate response
        ai_response = self.llm_engine.generate(prompt, temperature=0.1)
        self.conversation_history.append(f"Assistant: {ai_response}")
        
        # Debug logging
        print(f"🎯 Exchange {self.exchange_count}: Object={self.detected_object}")
        print(f"🤖 Response: {ai_response[:100]}...")
        
        # Parse response
        model_spec = self._extract_intelligent_spec(ai_response)
        
        # Force generation if enough info
        if self.exchange_count >= 4 and model_spec is None and self.detected_object:
            print("🔧 Forcing generation with smart defaults")
            model_spec = self._create_smart_fallback_spec()
        
        return {
            'message': ai_response,
            'generate_model': model_spec is not None,
            'model_spec': model_spec,
            'cadquery_code': None,
            'rag_references': self.relevant_references
        }
    
    def _handle_initial_object_detection(self, message: str):
        """Detect object and search RAG immediately"""
        if not self.rag_generator:
            return
            
        # Extract potential object type
        self.detected_object = self._extract_object_type(message)
        
        if self.detected_object:
            print(f"🎯 Detected object: {self.detected_object}")
            
            # Build smart search query
            search_query = self._build_smart_search_query(self.detected_object, message)
            
            # Search RAG immediately
            try:
                results = self.rag_generator.rag_library.semantic_search(
                    search_query, 
                    top_k=3, 
                    threshold=0.13  # Lower threshold for exploration
                )
                
                if results:
                    self.relevant_references = results
                    print(f"✅ Found {len(results)} relevant references:")
                    for ref_name, similarity in results:
                        print(f"   - {ref_name}: {similarity:.3f}")
                    
                    # Extract parameters from best match - ADD ERROR HANDLING HERE
                    try:
                        best_ref_name = results[0][0]
                        best_ref = self.rag_generator.rag_library.get_reference(best_ref_name)
                        
                        if best_ref and 'code' in best_ref:
                            self.extracted_parameters = self._extract_parameters_from_code(best_ref['code'])
                            print(f"📊 Extracted parameters: {list(self.extracted_parameters.keys())}")
                        else:
                            print(f"⚠️ Reference '{best_ref_name}' is invalid or missing code")
                            self.extracted_parameters = {}
                            
                    except Exception as e:
                        print(f"⚠️ Failed to extract parameters: {e}")
                        self.extracted_parameters = {}
                        
            except Exception as e:
                print(f"⚠️ RAG search failed: {e}")
                self.relevant_references = []
                self.extracted_parameters = {}
    
    def _extract_object_type(self, message: str) -> Optional[str]:
        """Extract object type from user message"""
        message_lower = message.lower()
        
        # Object type mappings
        object_mappings = {
            'gear': ['gear', 'cog', 'sprocket', 'pinion'],
            'spring': ['spring', 'coil', 'helix'],
            'container': ['container', 'box', 'storage', 'holder', 'organizer'],
            'cup': ['cup', 'mug', 'glass', 'tumbler'],
            'bracket': ['bracket', 'mount', 'support', 'holder'],
            'stand': ['stand', 'holder', 'support', 'dock'],
            'hook': ['hook', 'hanger', 'peg'],
            'fastener': ['bolt', 'screw', 'nut', 'fastener', 'thread'],
            'hinge': ['hinge', 'joint', 'pivot'],
            'ring': ['ring', 'band', 'loop', 'annulus'],
            'coaster': ['coaster', 'mat', 'pad'],
            'sphere': ['sphere', 'ball', 'orb'],
            'cylinder': ['cylinder', 'tube', 'pipe', 'rod']
        }
        
        for obj_type, keywords in object_mappings.items():
            if any(keyword in message_lower for keyword in keywords):
                return obj_type
        
        # Check for custom/unknown objects
        pattern = r'(?:make|create|design|want|need)\s+(?:a|an|some)?\s*(\w+)'
        match = re.search(pattern, message_lower)
        if match:
            return match.group(1)
        
        return None
    
    def _build_smart_search_query(self, object_type: str, full_message: str) -> str:
        """Build intelligent semantic search query"""
        query_parts = [object_type]
        
        # Add domain-specific expansions
        expansions = {
            'cup': ['mug', 'beverage', 'container', 'drinking', 'vessel', 'hollow'],
            'gear': ['mechanical', 'teeth', 'transmission', 'involute', 'spur'],
            'spring': ['helical', 'compression', 'coil', 'mechanical', 'elastic'],
            'container': ['storage', 'box', 'hollow', 'walls', 'compartment'],
            'bracket': ['mounting', 'structural', 'support', 'attachment'],
            'stand': ['holder', 'support', 'adjustable', 'angle', 'phone', 'tablet']
        }
        
        if object_type in expansions:
            query_parts.extend(expansions[object_type])
        
        # Add any specific features mentioned
        feature_keywords = ['handle', 'lid', 'holes', 'threads', 'adjustable', 'snap', 'round', 'square']
        for keyword in feature_keywords:
            if keyword in full_message.lower():
                query_parts.append(keyword)
        
        return ' '.join(query_parts)
    
    def _extract_parameters_from_code(self, code: str) -> Dict:
        """Extract parameter names and defaults from reference code - ENHANCED"""
        parameters = {}
        
        # Pattern to find variable assignments
        patterns = [
            r'(\w+)\s*=\s*(\d+(?:\.\d+)?)\s*(?:#.*)?',  # number assignments
            r'(\w+)\s*=\s*["\']([^"\']+)["\']',  # string assignments
        ]
        
        # Comprehensive parameter keywords
        param_keywords = [
            # Dimensions
            'width', 'height', 'depth', 'length', 'diameter', 'radius',
            'thickness', 'wall_thickness', 'size',
            # Ring-specific
            'outer_radius', 'inner_radius', 'band_width', 
            # Features
            'teeth', 'module', 'pitch', 'coils', 'wire_diameter', 
            'angle', 'offset', 'clearance', 'bore', 'thread',
            # Decorative
            'band', 'groove', 'pattern', 'decoration',
            # Counts and spacing
            'count', 'spacing', 'number', 'quantity'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, code)
            for match in matches:
                param_name = match[0].lower()
                # Be more inclusive in parameter detection
                if any(keyword in param_name for keyword in param_keywords):
                    try:
                        parameters[param_name] = float(match[1])
                    except:
                        parameters[param_name] = match[1]
        
        # Detect optional features more comprehensively
        code_lower = code.lower()
        
        # Check for decorative bands
        if 'band' in code_lower and ('decorative' in code_lower or 'band_offset' in code_lower):
            parameters['has_decorative_bands'] = 'optional'
        
        # Check for other optional features
        if 'handle' in code_lower and 'handle =' in code_lower:
            parameters['has_handle'] = 'optional'
        if 'lid' in code_lower:
            parameters['has_lid'] = 'optional'
        if 'groove' in code_lower:
            parameters['has_grooves'] = 'optional'
        if 'pattern' in code_lower:
            parameters['has_pattern'] = 'optional'
        
        return parameters
    
    def _build_enhanced_context(self) -> str:
        """Build context with RAG insights"""
        context = "\n".join(self.conversation_history[-10:])
        
        if self.extracted_parameters:
            context += f"\n\nDISCOVERED PARAMETERS FOR {self.detected_object}:\n"
            for param, value in self.extracted_parameters.items():
                if value == 'optional':
                    context += f"- {param}: OPTIONAL FEATURE\n"
                else:
                    context += f"- {param}: {value} (default)\n"
        
        if self.relevant_references:
            context += f"\n\nRELEVANT EXAMPLES FOUND:\n"
            for ref_name, similarity in self.relevant_references[:2]:
                context += f"- {ref_name} (similarity: {similarity:.3f})\n"
        
        return context
    
    def _build_object_aware_prompt(self, user_message: str, context: str) -> str:
        """Build prompt with object-specific guidance"""
        prompt = f"""{self.system_prompt}

DETECTED OBJECT: {self.detected_object or 'unknown'}
EXCHANGE COUNT: {self.exchange_count}

CONVERSATION CONTEXT:
{context}

INTELLIGENT GUIDANCE:
"""
    
        if self.extracted_parameters and self.exchange_count <= 3:
            # Categorize parameters for intelligent questioning
            critical_params = []
            optional_features = []
            decorative_params = []
            
            for param, value in self.extracted_parameters.items():
                param_lower = param.lower()
                
                # Identify critical dimensions
                if any(dim in param_lower for dim in ['radius', 'diameter', 'height', 'width', 'depth', 'length', 'thickness']):
                    if 'inner' in param_lower or 'outer' in param_lower:
                        critical_params.append(param)  # Inner/outer are critical
                    elif 'wall' not in param_lower:  # Wall thickness is less critical
                        critical_params.append(param)
                
                # Identify optional features
                elif value == 'optional' or param.startswith('has_'):
                    optional_features.append(param)
                
                # Identify decorative elements
                elif any(dec in param_lower for dec in ['band', 'decoration', 'pattern', 'ornament', 'groove']):
                    decorative_params.append(param)
            
            # Build smart questioning strategy
            full_conversation = " ".join(self.conversation_history).lower()
            params_mentioned = []
            
            # Check what's already been discussed
            for param in critical_params + optional_features + decorative_params:
                if param.replace('_', ' ') in full_conversation or param in full_conversation:
                    params_mentioned.append(param)
            
            # Determine what to ask next
            unasked_critical = [p for p in critical_params if p not in params_mentioned]
            unasked_optional = [p for p in optional_features if p not in params_mentioned]
            unasked_decorative = [p for p in decorative_params if p not in params_mentioned]
            
            prompt += f"""
PARAMETER ANALYSIS for {self.detected_object}:
- Critical dimensions found: {critical_params}
- Optional features found: {optional_features}
- Decorative elements found: {decorative_params}
- Already discussed: {params_mentioned}

SMART QUESTIONING PRIORITY:
1. Ask about unasked CRITICAL dimensions first: {unasked_critical[:2]}
2. Then ask about OPTIONAL features: {unasked_optional[:1]}
3. Finally ask about DECORATIVE elements: {unasked_decorative[:1]}

For a {self.detected_object}, you should:
"""
        
            if unasked_critical:
                prompt += f"""
- Ask about {unasked_critical[0]} (critical dimension)
- Suggest default: {self.extracted_parameters.get(unasked_critical[0], 'standard size')}
"""
        
            if unasked_decorative and self.exchange_count >= 2:
                prompt += f"""
- Ask if they want decorative features (like bands/patterns)
- These are optional and can be omitted
"""
        
            prompt += """
Keep questions natural and conversational. Group related parameters.
Example: "What height would you like for your ring? (typical: 5-8mm for comfort)"
"""
        
        elif self.exchange_count >= 4:
            prompt += """
You have enough information. Generate the model now using:
- User-specified values for discussed parameters
- Smart defaults for unmentioned parameters
- Omit optional features unless specifically requested
Include all known parameters in GENERATE_MODEL JSON.
"""
    
        prompt += f"\n\nCurrent user message: {user_message}\n\nResponse:"
        
        return prompt
    
    def _extract_intelligent_spec(self, response: str) -> Optional[Dict]:
        """Extract GENERATE_MODEL specification with smart parsing"""
        patterns = [
            r'GENERATE_MODEL:\s*(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})',
            r'GENERATE_MODEL:\s*(\{[\s\S]*?\})',
            r'(\{"object_type"[^}]*\})',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
            for match in matches:
                try:
                    spec_text = match.strip()
                    # Clean JSON
                    spec_text = re.sub(r'(\w+):', r'"\1":', spec_text)
                    spec_text = spec_text.replace("'", '"')
                    spec_text = re.sub(r',\s*}', '}', spec_text)
                    
                    spec = json.loads(spec_text)
                    
                    # Ensure object_type is set
                    if 'object_type' not in spec and self.detected_object:
                        spec['object_type'] = self.detected_object
                    
                    # Check conversation for feature removals/adaptations needed
                    full_conversation = " ".join(self.conversation_history).lower()
                    adaptation_needed = False
                    
                    # Check for handle removal
                    if 'no handle' in full_conversation or 'without handle' in full_conversation:
                        spec['has_handle'] = False
                        adaptation_needed = True
                        # Remove handle-related parameters
                        handle_params = ['handle_width', 'handle_height', 'handle_thickness', 
                                    'handle_arc_radius', 'handle_offset_from_top', 
                                    'handle_path_width', 'handle_path_height']
                        for param in handle_params:
                            spec.pop(param, None)
                    
                    # Check for other feature removals
                    if 'no lid' in full_conversation or 'without lid' in full_conversation:
                        spec['has_lid'] = False
                        adaptation_needed = True
                    
                    if 'no holes' in full_conversation or 'solid' in full_conversation:
                        spec['has_holes'] = False
                        adaptation_needed = True
                    
                    # Add extracted parameters as defaults (only if not removed)
                    for param, value in self.extracted_parameters.items():
                        if param not in spec and value != 'optional':
                            # Don't add handle params if no handle
                            if 'handle' in param and spec.get('has_handle') == False:
                                continue
                            spec[param] = value
                    
                    # Add reference info and adaptation flag
                    if self.relevant_references:
                        spec['_rag_reference'] = self.relevant_references[0][0]
                        spec['_rag_similarity'] = self.relevant_references[0][1]
                        spec['_adaptation_needed'] = adaptation_needed  # Set this flag!
                    
                    print(f"✅ Extracted intelligent spec: {spec}")
                    print(f"🔧 Adaptation needed: {adaptation_needed}")
                    return spec
                    
                except json.JSONDecodeError as e:
                    print(f"⚠️ JSON error: {e}")
                    continue
        
        return None
    
    def _create_smart_fallback_spec(self) -> Dict:
        """Create intelligent fallback using RAG insights - ENHANCED"""
        spec = {
            "object_type": self.detected_object or "custom_object"
        }
        
        full_conversation = " ".join(self.conversation_history).lower()
        
        # Use extracted parameters as base but be selective
        if self.extracted_parameters:
            for param, value in self.extracted_parameters.items():
                # Skip optional features unless explicitly requested
                if value == 'optional':
                    # Check if feature was requested
                    feature_name = param.replace('has_', '').replace('_', ' ')
                    if feature_name in full_conversation:
                        if any(neg in full_conversation for neg in ['no', 'without', "don't"]):
                            spec[param] = False
                        else:
                            spec[param] = True
                    # Don't include if not mentioned
                    continue
                
                # Skip decorative parameters unless mentioned
                if any(dec in param for dec in ['band', 'decoration', 'pattern', 'groove']):
                    if param.replace('_', ' ') not in full_conversation:
                        continue  # Skip unmentioned decorative elements
                
                # Include other parameters
                spec[param] = value
        
        # Extract dimensions from conversation
        dimension_patterns = [
            r'(\d+)\s*mm',
            r'(\d+)\s*cm',
            r'(\d+)mm',
        ]
        
        found_dimensions = []
        for pattern in dimension_patterns:
            matches = re.findall(pattern, full_conversation)
            found_dimensions.extend([int(m) for m in matches])
        
        # Object-specific intelligent assignment
        if self.detected_object == 'ring' and found_dimensions:
            # For rings, dimensions likely refer to radius or height
            if 'outer' in full_conversation and found_dimensions:
                spec['outer_radius'] = found_dimensions[0]
            if 'inner' in full_conversation and len(found_dimensions) > 1:
                spec['inner_radius'] = found_dimensions[1]
            if 'height' in full_conversation and found_dimensions:
                for dim in found_dimensions:
                    if 3 <= dim <= 20:  # Reasonable ring height
                        spec['height'] = dim
                        break
        
        # Handle feature requests
        adaptation_needed = False
        
        # Decorative bands
        if 'band' in full_conversation or 'decorative' in full_conversation:
            if any(neg in full_conversation for neg in ['no band', 'without band', 'plain']):
                spec['has_decorative_bands'] = False
                adaptation_needed = True
            elif 'band' in full_conversation:
                spec['has_decorative_bands'] = True
        
        # Add requirements
        spec['requirements'] = ['functional', '3d_printable']
        
        # Add RAG reference if available
        if self.relevant_references:
            spec['_rag_reference'] = self.relevant_references[0][0]
            spec['_adaptation_needed'] = adaptation_needed
        
        spec['notes'] = f"Smart spec for {self.detected_object}"
        
        print(f"🎯 Smart fallback spec: {spec}")
        return spec
    
    def _handle_gear_variations(self, gear_type: str, base_spec: Dict) -> Dict:
        """Handle different gear type variations"""
        gear_variants = {
            'bevel': {'angle': 45, 'cone_angle': True},
            'helical': {'helix_angle': 30},
            'worm': {'worm_threads': 1, 'lead_angle': 15},
            'rack': {'linear': True, 'length': 100},
            'internal': {'internal': True},
            'planetary': {'sun_teeth': 20, 'planet_teeth': 10, 'ring_teeth': 50}
        }
        
        for variant, params in gear_variants.items():
            if variant in gear_type.lower():
                base_spec.update(params)
                base_spec['gear_variant'] = variant
                break
        
        return base_spec
    
    def _detect_multiple_objects(self, message: str) -> List[str]:
        """Detect if user wants multiple objects or assembly"""
        objects = []
        
        # Patterns for multiple objects
        multi_patterns = [
            r'(\w+)\s+(?:and|with|plus)\s+(\w+)',
            r'(\w+)\s+inside\s+(?:a|the)?\s*(\w+)',
            r'(\w+)\s+attached\s+to\s+(?:a|the)?\s*(\w+)',
        ]
        
        for pattern in multi_patterns:
            matches = re.findall(pattern, message.lower())
            for match in matches:
                objects.extend(match)
        
        # Clean and validate objects
        valid_objects = []
        for obj in objects:
            detected = self._extract_object_type(obj)
            if detected:
                valid_objects.append(detected)
        
        return valid_objects if len(valid_objects) > 1 else []
    
    def reset(self):
        """Reset conversation state"""
        self.conversation_history = []
        self.exchange_count = 0
        self.detected_object = None
        self.relevant_references = []
        self.extracted_parameters = {}
        print("🔄 Intelligent conversation reset")
