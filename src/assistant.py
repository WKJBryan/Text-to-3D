# src/assistant.py
"""Intelligent Conversation Assistant with Reasoning-Based Generation"""
import json
import re
from typing import Dict, Optional

class IntelligentConversationAssistant:
    def __init__(self, llm_engine):
        self.llm_engine = llm_engine
        self.conversation_history = []
        self.exchange_count = 0
        self.system_prompt = self._build_intelligent_system_prompt()
    
    def _build_intelligent_system_prompt(self) -> str:
        return """You are a helpful 3D design assistant. Have SHORT conversations to understand what the user wants to create.

RULES:
1. Keep responses to 2-3 sentences MAX
2. Ask only 2 question per response
3. DO NOT ask about materials, colors, or surface finishes (CadQuery only creates geometry)
4. Focus on parameters needed for 3D modeling
5. When you have enough info, suggest generating the model
6. READ conversation history - don't repeat questions

SIMPLE APPROACH:
- For basic shapes (cube, cylinder, sphere): Just ask for size
- For complex objects: Ask about key requirements that matter
- Use your natural knowledge - don't overthink simple requests

GENERATION TRIGGER:
When ready, respond with: GENERATE_MODEL: {flat JSON structure}

Choose the RIGHT parameters for each object type based on your knowledge.

REQUIRED JSON FORMAT (flat structure only):
{"object_type": "object_name", ...appropriate_parameters...}

Must include "GENERATE_MODEL:" prefix and valid JSON on same line.

Keep it simple - let the code generator handle the engineering and focus only on geometry."""
   
    def chat(self, user_message: str) -> Dict:
        """Process user message with intelligent reasoning"""
        # Increment exchange counter
        self.exchange_count += 1
        
        # Add to history with clear separation
        self.conversation_history.append(f"User: {user_message}")
        
        # Build focused context (last 10 exchanges to prevent loops)
        context = "\n".join(self.conversation_history[-10:])
        
        # Create prompt with exchange counter for better control
        prompt = f"""{self.system_prompt}

CONVERSATION HISTORY:
{context}

EXCHANGE COUNT: {self.exchange_count}
INSTRUCTION: If this is exchange 4+ and you have basic info, use intelligent reasoning to GENERATE the model.

Current user message: {user_message}

Response:"""
        
        # Generate response with low temperature for consistency
        ai_response = self.llm_engine.generate(prompt, temperature=0.1)  # Very low for consistent reasoning
        
        # Add response to history
        self.conversation_history.append(f"Assistant: {ai_response}")
        
        # Debug logging
        print(f"🔍 Exchange {self.exchange_count}: {user_message[:50]}...")
        print(f"🤖 Response: {ai_response[:100]}...")
        
        # Parse response with enhanced extraction
        model_spec = self._extract_intelligent_spec(ai_response)
        cadquery_code = self._extract_code(ai_response)
        
        # Force generation if we have enough exchanges and basic info
        if self.exchange_count >= 5 and model_spec is None:
            print("🔧 Forcing intelligent generation due to exchange limit")
            model_spec = self._create_intelligent_fallback_spec()
        
        return {
            'message': ai_response,
            'generate_model': model_spec is not None,
            'model_spec': model_spec,
            'cadquery_code': cadquery_code
        }
    
    def _extract_intelligent_spec(self, response: str) -> Optional[Dict]:
        """Extract GENERATE_MODEL specification with enhanced parsing"""
        # Check for generation keywords
        generation_keywords = ['generate_model', 'generate', 'create', 'ready', 'make']
        has_keyword = any(keyword in response.lower() for keyword in generation_keywords)
        
        # Enhanced patterns for intelligent JSON extraction
        patterns = [
            r'GENERATE_MODEL:\s*(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})',  # Nested JSON
            r'GENERATE_MODEL:\s*(\{[\s\S]*?\})',
            r'(\{"object_type"[^}]*\})',
            r'(\{[^}]*"object_type"[^}]*\})',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
            for match in matches:
                try:
                    spec_text = match.strip()
                    # Enhanced JSON cleaning
                    spec_text = re.sub(r'(\w+):', r'"\1":', spec_text)
                    spec_text = spec_text.replace("'", '"')
                    spec_text = re.sub(r',\s*}', '}', spec_text)  # Remove trailing commas
                    spec_text = re.sub(r',\s*]', ']', spec_text)  # Remove trailing commas in arrays
                    
                    spec = json.loads(spec_text)

                    if 'name' in spec:
                        spec['object_type'] = spec.pop('name')
                
                    if 'size' in spec and isinstance(spec['size'], dict):
                        # Flatten nested size parameters
                        spec.update(spec.pop('size'))

                    print(f"✅ Extracted intelligent spec: {spec}")
                    return spec
                except json.JSONDecodeError as e:
                    print(f"❌ JSON error for '{match[:50]}...': {e}")
                    continue
        
        # Only fall back if exchange count is high
        if self.exchange_count >= 5:
            print("🔧 Forcing intelligent generation due to exchange limit")
            return self._create_intelligent_fallback_spec()
        
        return None
    
    def _create_intelligent_fallback_spec(self) -> Dict:
        """Create intelligent fallback spec using conversation analysis"""
        # Analyze conversation for key details
        full_conversation = " ".join(self.conversation_history).lower()
        
        # Enhanced object type detection with intelligent parameters
        if "gear" in full_conversation:
            # Extract gear-specific parameters intelligently
            teeth = self._extract_number(full_conversation, ["teeth", "tooth"], 20)
            diameter = self._extract_number(full_conversation, ["diameter", "mm"], 50)
            thickness = self._extract_number(full_conversation, ["thickness", "thick"], 6)
            
            return {
                "object_type": "spur_gear",
                "teeth": teeth,
                "module": round(diameter / teeth, 2),
                "diameter": diameter,
                "thickness": thickness,
                "bore_diameter": max(6, diameter // 8),
                "pressure_angle": 20,
                "requirements": ["mechanical", "involute_profile", "3d_printable"],
                "notes": f"Intelligent spur gear - {teeth} teeth, {diameter}mm diameter"
            }
        
        elif any(word in full_conversation for word in ["spring", "coil"]):
            coils = self._extract_number(full_conversation, ["coil", "turn"], 8)
            diameter = self._extract_number(full_conversation, ["diameter"], 20)
            wire = self._extract_number(full_conversation, ["wire", "thick"], 2)
            
            return {
                "object_type": "helical_spring",
                "coils": coils,
                "coil_diameter": diameter,
                "wire_diameter": wire,
                "pitch": wire * 2,
                "free_length": coils * wire * 2,
                "requirements": ["compression", "mechanical", "helical"],
                "notes": f"Intelligent spring - {coils} coils, {diameter}mm diameter"
            }
        
        elif any(word in full_conversation for word in ["bracket", "mount", "support"]):
            width = self._extract_number(full_conversation, ["width", "wide"], 50)
            height = self._extract_number(full_conversation, ["height", "tall"], 40)
            thickness = self._extract_number(full_conversation, ["thick"], 5)
            
            return {
                "object_type": "mounting_bracket",
                "width": width,
                "height": height,  
                "thickness": thickness,
                "mounting_holes": 4,
                "load_capacity": "moderate",
                "requirements": ["structural", "mounting", "3d_printable"],
                "notes": f"Intelligent bracket - {width}x{height}x{thickness}mm"
            }
        
        elif any(word in full_conversation for word in ["container", "box", "storage"]):
            width = self._extract_number(full_conversation, ["width", "wide"], 100)
            height = self._extract_number(full_conversation, ["height", "tall"], 60)
            depth = self._extract_number(full_conversation, ["depth", "deep"], 80)
            
            # Determine if circular
            is_circular = any(word in full_conversation for word in ["round", "circular", "cylinder"])
            
            if is_circular:
                return {
                    "object_type": "cylindrical_container",
                    "diameter": max(width, depth),
                    "height": height,
                    "wall_thickness": 2,
                    "requirements": ["storage", "circular", "3d_printable"],
                    "notes": f"Intelligent circular container - {max(width, depth)}mm diameter"
                }
            else:
                return {
                    "object_type": "rectangular_container",
                    "width": width,
                    "height": height,
                    "depth": depth,
                    "wall_thickness": 2,
                    "requirements": ["storage", "functional", "3d_printable"],
                    "notes": f"Intelligent container - {width}x{depth}x{height}mm"
                }
        
        else:
            # Generic fallback with intelligent defaults
            return {
                "object_type": "custom_object",
                "width": 60,
                "height": 40,
                "depth": 60,
                "requirements": ["functional", "3d_printable"],
                "notes": "Intelligent fallback - custom object from conversation"
            }
    
    def _extract_number(self, text: str, keywords: list, default: int) -> int:
        """Extract numbers associated with keywords from text"""
        import re
        
        for keyword in keywords:
            # Look for patterns like "20 teeth", "teeth 20", "20mm diameter"
            patterns = [
                rf'(\d+)\s*{keyword}',
                rf'{keyword}\s*(\d+)',
                rf'(\d+)\s*mm\s*{keyword}',
                rf'{keyword}\s*(\d+)\s*mm'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    return int(match.group(1))
        
        return default
    
    def _extract_code(self, response: str) -> Optional[str]:
        """Extract CadQuery code from response"""
        patterns = [
            r'```python\n(.*?)\n```',
            r'```\n(.*?)\n```'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response, re.DOTALL)
            if match:
                code = match.group(1).strip()
                if 'cadquery' in code or 'cq.' in code:
                    return code
        return None
    
    def reset(self):
        """Reset conversation state"""
        self.conversation_history = []
        self.exchange_count = 0
        print("🔄 Intelligent conversation reset")