# src/generation/RAG_generator.py
"""Enhanced RAG CAD Generator with Intelligent Code Adaptation"""
import cadquery as cq
import json
import re
import os
from typing import Dict, Optional, List, Tuple
from .reference_library import EnhancedRAGReferenceLibrary

class EnhancedRAGCADGenerator:
    def __init__(self, llm_engine, embedding_model: str = None, cache_dir: str = None):
        self.llm_engine = llm_engine
        self.last_code = ""
        self.generation_history = []
        self.last_generation_mode = "rag"
        self.last_similarity_score = 0.0
        self.last_complexity_used = "unknown"
        
        # RAG control
        self.rag_enabled = True
        
        # Initialize Enhanced RAG components
        embedding_model = embedding_model or os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
        cache_dir = cache_dir or os.getenv('EMBEDDING_CACHE_DIR', './embeddings')
        
        print("🧠 Initializing Enhanced RAG generator with intelligent adaptation...")
        self.rag_library = EnhancedRAGReferenceLibrary(embedding_model, cache_dir)
        
        # RAG settings
        self.top_k = int(os.getenv('VECTOR_SEARCH_TOP_K', '3'))
        self.similarity_threshold = float(os.getenv('SIMILARITY_THRESHOLD', '0.3'))
    
    def set_rag_enabled(self, enabled: bool):
        """Enable or disable RAG mode"""
        self.rag_enabled = enabled
        mode_text = "Enhanced RAG + Intelligent Adaptation" if enabled else "Pure Intelligent Reasoning"
        print(f"🔄 Mode changed: {mode_text}")
    
    def generate_model(self, model_spec: Dict, provided_code: Optional[str] = None) -> cq.Workplane:
        """Generate 3D model using Enhanced RAG with intelligent adaptation"""
        if provided_code:
            code = provided_code
            self.last_generation_mode = "provided"
        else:
            code = self._generate_code_with_intelligent_adaptation(model_spec)
        
        self.last_code = code
        self.generation_history.append({
            'spec': model_spec,
            'code': code,
            'mode': self.last_generation_mode,
            'similarity': self.last_similarity_score,
            'complexity': self.last_complexity_used
        })
        
        return self._execute_code(code)
    
    def _generate_code_with_intelligent_adaptation(self, spec: Dict) -> str:
        """Generate code with intelligent reference adaptation"""
        # Check if RAG is disabled
        if not self.rag_enabled:
            print("🤖 RAG disabled - using pure intelligent reasoning")
            prompt = self._build_intelligent_reasoning_prompt(spec)
            self.last_generation_mode = "intelligent_reasoning_forced"
            return self.llm_engine.generate(prompt, temperature=0.3)
        
        # Check for pre-selected RAG reference
        if '_rag_reference' in spec:
            print(f"📎 Using pre-selected reference: {spec['_rag_reference']}")
            reference = self.rag_library.get_reference(spec['_rag_reference'])
            if spec.get('_adaptation_needed'):
                return self._adapt_reference_code(reference, spec)
            else:
                return self._use_reference_with_parameters(reference, spec)
        
        # Perform intelligent RAG search
        query = self._build_enhanced_semantic_query(spec)
        relevant_refs = self._intelligent_rag_search(query, spec)
        
        # Choose generation strategy based on similarity and complexity
        if relevant_refs:
            best_match = relevant_refs[0]
            similarity = best_match['similarity']
            
            if similarity >= 0.5:  # Very good match
                print(f"✅ Excellent match ({similarity:.3f}) - Direct adaptation")
                return self._adapt_reference_code(best_match, spec)
            elif similarity >= 0.3:  # Good match
                print(f"✅ Good match ({similarity:.3f}) - Pattern combination")
                return self._combine_reference_patterns(relevant_refs, spec)
            elif similarity >= 0.2:  # Related match
                print(f"🔄 Related match ({similarity:.3f}) - Category adaptation")
                return self._adapt_category_patterns(relevant_refs, spec)
            else:  # Weak match
                print(f"⚠️ Weak match ({similarity:.3f}) - Hybrid approach")
                return self._hybrid_generation(relevant_refs, spec)
        else:
            # Pure intelligent reasoning
            print("🧠 No relevant matches - Pure intelligent reasoning")
            prompt = self._build_intelligent_reasoning_prompt(spec)
            self.last_generation_mode = "intelligent_reasoning"
            return self.llm_engine.generate(prompt, temperature=0.3)
    
    def _intelligent_rag_search(self, query: str, spec: Dict) -> List[Dict]:
        """Perform intelligent multi-level RAG search"""
        try:
            # Level 1: Direct search
            search_results = self.rag_library.semantic_search(query, top_k=5, threshold=0.0)
            
            if not search_results:
                return []
            
            # Level 2: Category-based filtering
            object_type = spec.get('object_type', '')
            
            # Enhance results with metadata
            enhanced_results = []
            for ref_key, similarity in search_results:
                reference = self.rag_library.get_reference(ref_key)
                
                # Boost similarity for matching categories
                category_boost = 0.1 if self._matches_category(object_type, reference['category']) else 0
                
                # Adjust for complexity appropriateness
                complexity_factor = self._calculate_complexity_factor(spec, reference['complexity'])
                
                adjusted_similarity = similarity + category_boost * complexity_factor
                
                enhanced_results.append({
                    'name': ref_key,
                    'similarity': adjusted_similarity,
                    'original_similarity': similarity,
                    'description': reference['description'],
                    'code': reference['code'],
                    'complexity': reference['complexity'],
                    'category': reference['category']
                })
            
            # Sort by adjusted similarity
            enhanced_results.sort(key=lambda x: x['similarity'], reverse=True)
            
            # Filter by threshold
            filtered = [r for r in enhanced_results if r['original_similarity'] >= 0.3]
            
            if filtered:
                self.last_similarity_score = filtered[0]['similarity']
                self.last_complexity_used = filtered[0]['complexity']
                print(f"🔍 Found {len(filtered)} intelligent matches")
                return filtered[:self.top_k]
            
            return []
            
        except Exception as e:
            print(f"❌ Intelligent search failed: {e}")
            return []
    
    def _adapt_reference_code(self, reference: Dict, spec: Dict) -> str:
        """Intelligently adapt reference code to match specifications"""
        code = reference['code'] if isinstance(reference, dict) else reference
        
        # Extract current parameters from reference
        current_params = self._extract_parameters_from_code(code)
        
        # Determine what features to remove
        features_to_remove = []
        if spec.get('has_handle') == False:
            features_to_remove.append('handle')
        if spec.get('has_lid') == False:
            features_to_remove.append('lid')
        if spec.get('has_holes') == False:
            features_to_remove.append('holes')
        
        # Build adaptation prompt with clear instructions
        adaptation_instructions = ""
        if features_to_remove:
            adaptation_instructions = f"\nIMPORTANT: Remove these features completely from the code:\n"
            for feature in features_to_remove:
                adaptation_instructions += f"- Remove all {feature}-related code sections\n"
        
        prompt = f"""Adapt this CadQuery code to match the new specifications.

REFERENCE CODE:
```python
{code}
```

NEW SPECIFICATIONS:
{json.dumps(spec, indent=2)}
{adaptation_instructions}
ADAPTATION RULES:
1. Keep the overall structure and approach
2. Update all dimension variables to match specifications
3. COMPLETELY REMOVE code sections for features marked as False (has_handle=False means NO handle code)
4. For has_handle=False: Remove handle creation, handle path, and handle union
5. Add features if spec has new requirements
6. Maintain manufacturing constraints
7. Keep error handling but adapt it too

Generate ONLY the adapted CadQuery code (no handle if has_handle=False):"""
    
        self.last_generation_mode = "intelligent_adaptation"
        adapted_code = self.llm_engine.generate(prompt, temperature=0.2)
        
        # Double-check: if still has handle code when it shouldn't, try simpler approach
        if spec.get('has_handle') == False and 'handle' in adapted_code.lower():
            print("⚠️ LLM didn't remove handle, using direct removal")
            adapted_code = self._remove_handle_code_directly(code, spec)
        
        return adapted_code
    
    def _remove_handle_code_directly(self, code: str, spec: Dict) -> str:
        """Directly remove handle code from reference"""
        lines = code.split('\n')
        cleaned_lines = []
        skip_section = False
        skip_depth = 0
        
        for line in lines:
            # Skip handle-related variable definitions
            if any(h in line.lower() for h in ['handle_width', 'handle_height', 'handle_thickness', 
                                            'handle_arc', 'handle_offset', 'handle_path']):
                continue
            
            # Skip handle creation sections
            if 'handle' in line.lower() and ('=' in line or 'Handle' in line):
                skip_section = True
                skip_depth = len(line) - len(line.lstrip())
                continue
            
            # Continue skipping if we're in a handle section
            if skip_section:
                current_depth = len(line) - len(line.lstrip())
                if current_depth > skip_depth or line.strip() == '':
                    continue
                else:
                    skip_section = False
            
            # Replace union with handle to just return the body
            if 'union(handle)' in line:
                line = line.replace('.union(handle)', '')
            
            # Update result assignment
            if 'result = ' in line and 'union(handle)' in line:
                line = '    result = mug_body'
            
            # Update parameter values from spec
            for param, value in spec.items():
                if param.startswith('_') or param == 'has_handle':
                    continue
                # Simple parameter replacement
                pattern = rf'{param}\s*=\s*\d+(?:\.\d+)?'
                if re.search(pattern, line):
                    line = re.sub(pattern, f'{param} = {value}', line)
            
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _use_reference_with_parameters(self, reference: Dict, spec: Dict) -> str:
        """Use reference code with simple parameter substitution"""
        code = reference['code']
        
        # Simple parameter replacement
        for param, value in spec.items():
            if param.startswith('_'):  # Skip metadata
                continue
            
            # Find and replace parameter assignments
            patterns = [
                rf'{param}\s*=\s*\d+(?:\.\d+)?',
                rf'{param}\s*=\s*["\'][^"\']+["\']',
            ]
            
            for pattern in patterns:
                if re.search(pattern, code):
                    code = re.sub(pattern, f'{param} = {value}', code)
        
        self.last_generation_mode = "parameter_substitution"
        return code
    
    def _combine_reference_patterns(self, references: List[Dict], spec: Dict) -> str:
        """Combine patterns from multiple references"""
        # Build combination prompt
        examples = "\n\n".join([
            f"REFERENCE {i+1} ({ref['name']}, {ref['similarity']:.3f}):\n```python\n{ref['code'][:500]}...\n```"
            for i, ref in enumerate(references[:2])
        ])
        
        prompt = f"""Combine the best patterns from these references to create the target object.

{examples}

TARGET SPECIFICATION:
{json.dumps(spec, indent=2)}

COMBINATION STRATEGY:
- Take the base structure from the most similar reference
- Add features from other references as needed
- Ensure all parts work together
- Match exact specifications

Generate ONLY the combined CadQuery code:"""
        
        self.last_generation_mode = "pattern_combination"
        return self.llm_engine.generate(prompt, temperature=0.3)
    
    def _adapt_category_patterns(self, references: List[Dict], spec: Dict) -> str:
        """Adapt patterns from same category"""
        category_refs = [r for r in references if r['category'] == references[0]['category']]
        
        prompt = f"""Use these {references[0]['category']} category patterns to create a new object.

CATEGORY EXAMPLES:
{category_refs[0]['name']}: {category_refs[0]['description']}

TARGET: Create a {spec.get('object_type', 'object')} with these specifications:
{json.dumps(spec, indent=2)}

Apply the category's design patterns and best practices.

Generate ONLY the CadQuery code:"""
        
        self.last_generation_mode = "category_adaptation"
        return self.llm_engine.generate(prompt, temperature=0.3)
    
    def _hybrid_generation(self, references: List[Dict], spec: Dict) -> str:
        """Hybrid approach combining RAG insights with reasoning"""
        insights = self._extract_design_insights(references)
        
        prompt = f"""Generate CadQuery code using these design insights and engineering principles.

DESIGN INSIGHTS FROM SIMILAR OBJECTS:
{insights}

TARGET SPECIFICATION:
{json.dumps(spec, indent=2)}

Apply both the insights and your engineering knowledge to create the best solution.

Generate ONLY the CadQuery code:"""
        
        self.last_generation_mode = "hybrid_generation"
        return self.llm_engine.generate(prompt, temperature=0.3)
    
    def _extract_design_insights(self, references: List[Dict]) -> str:
        """Extract design patterns and insights from references"""
        insights = []
        
        for ref in references[:3]:
            # Extract key patterns from code
            code = ref['code']
            
            # Look for common patterns
            if 'fillet' in code:
                insights.append(f"- Use filleting for smooth edges (from {ref['name']})")
            if 'shell' in code:
                insights.append(f"- Use shell() for hollow objects (from {ref['name']})")
            if 'union' in code or 'cut' in code:
                insights.append(f"- Use boolean operations for complex shapes (from {ref['name']})")
            
        return '\n'.join(insights) if insights else "- Use standard CadQuery best practices"
    
    def _matches_category(self, object_type: str, category: str) -> bool:
        """Check if object type matches category"""
        category_mappings = {
            'primitive': ['box', 'cylinder', 'sphere', 'cone'],
            'functional': ['stand', 'holder', 'bracket', 'container', 'hook'],
            'mathematical': ['gear', 'spring', 'thread', 'helix'],
            'manufacturing': ['joint', 'hinge', 'snap', 'assembly']
        }
        
        for cat, types in category_mappings.items():
            if cat == category:
                return any(t in object_type.lower() for t in types)
        return False
    
    def _calculate_complexity_factor(self, spec: Dict, complexity: str) -> float:
        """Calculate complexity appropriateness factor"""
        spec_features = len(spec.keys())
        
        if spec_features <= 5:  # Simple spec
            return 1.0 if complexity == 'simple' else 0.8
        elif spec_features <= 10:  # Medium spec
            return 1.0 if complexity == 'medium' else 0.9
        elif spec_features <= 15:  # Complex spec
            return 1.0 if complexity == 'complex' else 0.9
        else:  # Advanced spec
            return 1.0 if complexity == 'advanced' else 0.8
    
    def _extract_parameters_from_code(self, code: str) -> Dict:
        """Extract parameter names and defaults from reference code"""
        parameters = {}
        
        # Pattern to find variable assignments
        patterns = [
            r'(\w+)\s*=\s*(\d+(?:\.\d+)?)\s*(?:#.*)?',  # number assignments
            r'(\w+)\s*=\s*["\']([^"\']+)["\']',  # string assignments
        ]
        
        # Common parameter keywords to look for
        param_keywords = [
            'width', 'height', 'depth', 'length', 'diameter', 'radius',
            'thickness', 'wall_thickness', 'teeth', 'module', 'pitch',
            'coils', 'wire_diameter', 'angle', 'offset', 'clearance',
            'bore', 'thread', 'size', 'count', 'spacing',
            'handle_width', 'handle_height', 'handle_thickness',
            'mug_radius', 'mug_height'  # Add specific mug parameters
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, code)
            for match in matches:
                param_name = match[0].lower()
                if any(keyword in param_name for keyword in param_keywords):
                    try:
                        parameters[param_name] = float(match[1])
                    except:
                        parameters[param_name] = match[1]
        
        # Detect optional features
        if 'handle' in code.lower() and 'handle =' in code.lower():
            parameters['has_handle'] = 'optional'
        
        return parameters
    
    def _build_enhanced_semantic_query(self, spec: Dict) -> str:
        """Build enhanced semantic search query with intelligent context"""
        query_parts = []
        
        # Add object type with intelligent expansion
        if 'object_type' in spec:
            obj_type = spec['object_type']
            query_parts.append(obj_type.replace('_', ' '))
            
            # Add intelligent context based on object type
            if 'gear' in obj_type:
                query_parts.extend(['mechanical', 'transmission', 'involute', 'teeth'])
            elif 'spring' in obj_type:
                query_parts.extend(['helical', 'compression', 'coil', 'mechanical'])
            elif 'bracket' in obj_type or 'mount' in obj_type:
                query_parts.extend(['structural', 'mounting', 'load bearing'])
            elif 'container' in obj_type or 'box' in obj_type:
                query_parts.extend(['storage', 'hollow', 'wall thickness'])
        
        # Add intelligent requirements analysis
        if 'requirements' in spec and spec['requirements']:
            requirements_text = ' '.join(spec['requirements']).replace('_', ' ')
            query_parts.append(requirements_text)
        
        # Add technical specifications
        technical_params = []
        for key, value in spec.items():
            if key in ['teeth', 'diameter', 'coils', 'module', 'pressure_angle']:
                technical_params.append(f"{key} {value}")
        
        if technical_params:
            query_parts.extend(technical_params)
        
        # Add contextual information
        if 'notes' in spec:
            query_parts.append(spec['notes'])
        
        query = ' '.join(query_parts)
        print(f"🔍 Enhanced semantic query: '{query}'")
        return query
    
    def _build_intelligent_reasoning_prompt(self, spec: Dict) -> str:
        """Build prompt for pure intelligent reasoning"""
        return f"""Generate CadQuery code for: {json.dumps(spec, indent=2)}

Requirements:
- Import cadquery as cq
- Create 'result' variable  
- Include try/except fallback
- Use appropriate CadQuery methods for this object type
- Apply engineering principles and best practices
- Consider 3D printing constraints
- ONLY output executable Python code

Code only:"""
    
    def _execute_code(self, code: str) -> cq.Workplane:
        """Execute CadQuery code safely with enhanced debugging"""
        # Clean up code
        code = self._clean_code(code)
        
        # Debug: Print code with line numbers for troubleshooting
        print("🔍 Generated code with line numbers:")
        for i, line in enumerate(code.split('\n'), 1):
            print(f"{i:2d}: {line}")
        
        # Safe execution environment
        safe_globals = {'cq': cq, 'cadquery': cq, 'math': __import__('math')}
        safe_locals = {}
        
        try:
            exec(code, safe_globals, safe_locals)
            
            if 'result' in safe_locals:
                result = safe_locals['result']
                if isinstance(result, cq.Workplane):
                    mode_text = f"Enhanced RAG ({self.last_complexity_used})" if self.last_generation_mode == "enhanced_rag" else "Intelligent Reasoning"
                    print(f"✅ {mode_text} CadQuery model created!")
                    return result
            
            raise Exception("Code didn't produce valid CadQuery Workplane")
            
        except Exception as e:
            print(f"❌ Code execution failed: {e}")
            raise Exception(f"Code execution failed: {e}")
    
    def _clean_code(self, code: str) -> str:
        """Clean and extract ONLY Python code"""
        
        # Remove markdown code blocks - more aggressive patterns
        code = re.sub(r'```python\s*\n?', '', code, flags=re.IGNORECASE)
        code = re.sub(r'```\s*\n?', '', code)
        code = re.sub(r'```python', '', code, flags=re.IGNORECASE)  
        code = re.sub(r'```', '', code)
        
        # Remove any remaining backticks
        code = code.replace('`', '')
        
        # Find code starting with import
        if 'import cadquery' in code:
            start_idx = code.find('import cadquery')
            code = code[start_idx:]
        
        # Remove any trailing markdown or explanatory text
        lines = code.split('\n')
        clean_lines = []
        
        for line in lines:
            # Stop at explanatory text
            if any(phrase in line.lower() for phrase in [
                'this code', 'note that', 'the above', 'explanation:', 'output:'
            ]):
                break
            clean_lines.append(line)
        
        return '\n'.join(clean_lines).strip()
    
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
    
    def get_last_generation_info(self) -> Dict:
        """Get enhanced information about the last generation"""
        return {
            'mode': self.last_generation_mode,
            'similarity_score': self.last_similarity_score,
            'complexity_used': self.last_complexity_used,
            'used_rag': self.last_generation_mode in ["enhanced_rag", "intelligent_adaptation", "pattern_combination"],
            'similarity_threshold': self.similarity_threshold
        }
    
    def search_similar_examples(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """Search for similar examples with enhanced results"""
        return self.rag_library.semantic_search(query, top_k=top_k, threshold=0.0)
    
    def add_reference_example(self, name: str, description: str, code: str, complexity: str = "medium", category: str = "functional"):
        """Add new reference example with enhanced metadata"""
        self.rag_library.add_reference(name, description, code, complexity, category)
        print(f"✅ Added enhanced reference example: {name} ({complexity}, {category})")
    
    def get_enhanced_rag_stats(self) -> Dict:
        """Get Enhanced RAG system statistics"""
        complexity_counts = {}
        category_counts = {}
        
        for ref in self.rag_library.get_all_references().values():
            complexity = ref.get('complexity', 'unknown')
            category = ref.get('category', 'unknown')
            complexity_counts[complexity] = complexity_counts.get(complexity, 0) + 1
            category_counts[category] = category_counts.get(category, 0) + 1
        
        return {
            'total_references': len(self.rag_library.get_all_references()),
            'embedding_model': self.rag_library.embedding_model_name,
            'top_k': self.top_k,
            'similarity_threshold': self.similarity_threshold,
            'cache_dir': str(self.rag_library.cache_dir),
            'last_generation_mode': self.last_generation_mode,
            'last_similarity_score': self.last_similarity_score,
            'last_complexity_used': self.last_complexity_used,
            'complexity_distribution': complexity_counts,
            'category_distribution': category_counts,
            'rag_enabled': self.rag_enabled
        }
    
    def rebuild_embeddings(self):
        """Force rebuild enhanced embeddings"""
        self.rag_library.rebuild_embeddings()