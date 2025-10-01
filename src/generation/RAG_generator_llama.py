# src/generation/RAG_generator_stable.py
"""Enhanced RAG CAD Generator with FIXED Parameter Mapping"""
import cadquery as cq
import json
import re
import os
from typing import Dict, Optional, List, Tuple
from .reference_library import EnhancedRAGReferenceLibrary
from src.generation.ast_code_editor import ASTCodeEditor
from src.models.model_spec import ModelSpec

class EnhancedRAGCADGenerator:
    def __init__(self, llm_engine, embedding_model: str = None, cache_dir: str = None):
        self.llm_engine = llm_engine
        self.ast_editor = ASTCodeEditor()  # New AST-based editor
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
        
        print("Initializing Enhanced RAG generator with AST editing...")
        self.rag_library = EnhancedRAGReferenceLibrary(embedding_model, cache_dir)
        
        # RAG settings
        self.top_k = int(os.getenv('VECTOR_SEARCH_TOP_K', '3'))
        self.similarity_threshold = float(os.getenv('SIMILARITY_THRESHOLD', '0.3'))

    def set_rag_enabled(self, enabled: bool):
        """Enable or disable RAG mode"""
        self.rag_enabled = enabled
        mode_text = "Enhanced RAG + Intelligent Adaptation" if enabled else "Pure Intelligent Reasoning"
        print(f"🔄 Mode changed: {mode_text}")

    def get_enhanced_rag_stats(self) -> Dict:
        """Get Enhanced RAG system statistics"""
        complexity_counts = {}
        category_counts = {}
        
        try:
            for ref in self.rag_library.get_all_references().values():
                complexity = ref.get('complexity', 'unknown')
                category = ref.get('category', 'unknown')
                complexity_counts[complexity] = complexity_counts.get(complexity, 0) + 1
                category_counts[category] = category_counts.get(category, 0) + 1
        except:
            pass
        
        return {
            'total_references': len(self.rag_library.get_all_references()) if self.rag_library else 0,
            'embedding_model': getattr(self.rag_library, 'embedding_model_name', 'unknown'),
            'top_k': self.top_k,
            'similarity_threshold': self.similarity_threshold,
            'last_generation_mode': self.last_generation_mode,
            'last_similarity_score': self.last_similarity_score,
            'last_complexity_used': self.last_complexity_used,
            'complexity_distribution': complexity_counts,
            'category_distribution': category_counts,
            'rag_enabled': self.rag_enabled
        }
    
    def generate_model(self, model_spec: Dict, provided_code: Optional[str] = None) -> cq.Workplane:
        """Generate 3D model using Enhanced RAG with AST-based adaptation"""
        
        # Convert dict to ModelSpec for validation and normalization
        if isinstance(model_spec, dict):
            try:
                spec = ModelSpec(**model_spec)
            except Exception as e:
                print(f"ModelSpec validation failed: {e}")
                # Fallback to dict processing
                spec = model_spec
        else:
            spec = model_spec
        
        if provided_code:
            code = provided_code
            self.last_generation_mode = "provided"
        else:
            code = self._generate_code_with_ast_adaptation(spec)
        
        self.last_code = code
        self.generation_history.append({
            'spec': spec.model_dump() if hasattr(spec, 'model_dump') else spec,
            'code': code,
            'mode': self.last_generation_mode,
            'similarity': self.last_similarity_score,
            'complexity': self.last_complexity_used
        })
        
        return self._execute_code_safely(code)
    
    def _generate_code_with_ast_adaptation(self, spec) -> str:
        """Generate code with AST-based template adaptation"""
        
        # Extract spec data for processing
        if hasattr(spec, 'model_dump'):
            spec_dict = spec.model_dump()
            object_type = spec.object_type
            parameters = spec.to_code_parameters()
        else:
            spec_dict = spec
            object_type = spec.get('object_type', 'unknown')
            parameters = {k: v for k, v in spec.items() if not k.startswith('_')}
        
        print(f"🔧 Input parameters: {parameters}")
        
        # Check if RAG is disabled
        if not self.rag_enabled:
            print("RAG disabled - using pure intelligent reasoning")
            return self._generate_with_intelligent_reasoning(spec_dict)
        
        # Check for pre-selected RAG reference
        rag_reference = spec_dict.get('_rag_reference') or spec_dict.get('rag_reference')
        if rag_reference:
            print(f"Using pre-selected reference: {rag_reference}")
            reference = self.rag_library.get_reference(rag_reference)
            if reference:
                return self._adapt_reference_with_ast(reference, spec, parameters)
        
        # Perform RAG search
        query = self._build_enhanced_semantic_query(spec_dict)
        relevant_refs = self._intelligent_rag_search(query, spec_dict)
        
        # Choose generation strategy
        if relevant_refs:
            best_match = relevant_refs[0]
            similarity = best_match['similarity']
            
            if similarity >= 0.5:
                print(f"Excellent match ({similarity:.3f}) - AST adaptation")
                return self._adapt_reference_with_ast(best_match, spec, parameters)
            elif similarity >= 0.3:
                print(f"Good match ({similarity:.3f}) - Pattern combination")
                return self._combine_reference_patterns_ast(relevant_refs, spec_dict)
            else:
                print(f"Weak match ({similarity:.3f}) - Hybrid approach")
                return self._hybrid_generation_ast(relevant_refs, spec_dict)
        else:
            print("No relevant matches - Pure intelligent reasoning")
            return self._generate_with_intelligent_reasoning(spec_dict)
    
    def _adapt_reference_with_ast(self, reference: Dict, spec, parameters: Dict) -> str:
        """Adapt reference code using AST editing for robust parameter replacement - FIXED MAPPING"""
        
        # Get reference code
        code = reference['code'] if isinstance(reference, dict) else reference
        if not code:
            return self._generate_with_intelligent_reasoning(spec)
        
        self.last_generation_mode = "ast_adaptation"
        
        try:
            # Step 1: Extract current parameters from template
            template_params = self.ast_editor.extract_parameters_from_code(code)
            print(f"Template parameters: {list(template_params.keys())}")
            print(f"User parameters: {parameters}")
            
            # Step 2: FIXED parameter mapping
            param_mapping = self._map_user_specs_to_template_params(parameters, template_params)
            print(f"🔄 Parameter mapping: {param_mapping}")
            
            # Step 3: Determine features to remove based on spec
            features_to_remove = []
            if hasattr(spec, 'has_handle') and spec.has_handle == False:
                features_to_remove.append('handle')
            elif isinstance(spec, dict) and spec.get('has_handle') == False:
                features_to_remove.append('handle')
            
            if hasattr(spec, 'has_lid') and spec.has_lid == False:
                features_to_remove.append('lid')
            elif isinstance(spec, dict) and spec.get('has_lid') == False:
                features_to_remove.append('lid')
            
            # Step 4: Remove unwanted features using AST
            if features_to_remove:
                code = self.ast_editor.remove_features(code, features_to_remove)
                print(f"Removed features: {features_to_remove}")
            
            # Step 5: Apply parameter mapping using AST
            if param_mapping:
                code = self.ast_editor.replace_parameters(code, param_mapping)
                print(f"Applied parameters: {list(param_mapping.keys())}")
            else:
                print("❌ No parameter mapping applied!")
            
            # Step 6: Validate and clean the code
            code = self._clean_and_validate_code(code)
            
            edit_log = self.ast_editor.get_edit_log()
            print(f"AST edit operations: {edit_log}")
            
            return code
            
        except Exception as e:
            print(f"AST adaptation failed: {e}")
            # Fallback to LLM-based adaptation
            return self._fallback_llm_adaptation(code, parameters)
    
    def _map_user_specs_to_template_params(self, user_params: Dict, template_params: Dict) -> Dict:
        """FIXED: Intelligently map user specifications to template parameter names"""
        mapping = {}
        
        print(f"🔍 Mapping user params {user_params} to template params {list(template_params.keys())}")
        
        # Direct matches first
        for user_param, value in user_params.items():
            if user_param in template_params:
                mapping[user_param] = value
                print(f"✅ Direct match: {user_param} = {value}")
        
        # FIXED: Handle specific conversions and aliases
        for user_param, value in user_params.items():
            if user_param in mapping:
                continue  # Already mapped
                
            # Convert diameter to radius if template expects radius
            if user_param == 'diameter' and 'radius' in template_params:
                mapping['radius'] = value / 2
                print(f"✅ Converted diameter {value} to radius {value/2}")
                
            # Convert radius to diameter if template expects diameter  
            elif user_param == 'radius' and 'diameter' in template_params:
                mapping['diameter'] = value * 2
                print(f"✅ Converted radius {value} to diameter {value*2}")
                
            # Handle bottom_radius specifically
            elif user_param == 'bottom_radius' and 'bottom_radius' in template_params:
                mapping['bottom_radius'] = value
                print(f"✅ Bottom radius: {value}")
                
            # Handle top_radius specifically  
            elif user_param == 'top_radius' and 'top_radius' in template_params:
                mapping['top_radius'] = value
                print(f"✅ Top radius: {value}")
                
            # Handle height
            elif user_param == 'height' and 'height' in template_params:
                mapping['height'] = value
                print(f"✅ Height: {value}")
                
            # Handle wall thickness variations
            elif user_param in ['wall_thickness', 'thickness'] and 'wall_thickness' in template_params:
                mapping['wall_thickness'] = value
                print(f"✅ Wall thickness: {value}")
                
            # Handle width/length
            elif user_param in ['width', 'length'] and any(p in template_params for p in ['width', 'length']):
                if 'width' in template_params:
                    mapping['width'] = value
                elif 'length' in template_params:
                    mapping['length'] = value
                print(f"✅ Dimension {user_param}: {value}")
                
            # Fuzzy matching for similar parameter names
            else:
                user_param_lower = user_param.lower()
                for template_param in template_params.keys():
                    template_param_lower = template_param.lower()
                    
                    # Check if user parameter is contained in template parameter name
                    if user_param_lower in template_param_lower or template_param_lower in user_param_lower:
                        mapping[template_param] = value
                        print(f"✅ Fuzzy match: {user_param} → {template_param} = {value}")
                        break
        
        print(f"🎯 Final mapping: {mapping}")
        return mapping
    
    def _clean_and_validate_code(self, code: str) -> str:
        """Clean and validate generated code"""
        # Remove any remaining markdown
        code = re.sub(r'```python\s*\n?', '', code, flags=re.IGNORECASE)
        code = re.sub(r'```\s*\n?', '', code)
        code = code.replace('`', '')
        
        # Ensure required imports
        if 'import cadquery' not in code:
            code = 'import cadquery as cq\n\n' + code
        
        # Ensure result variable exists
        if 'result =' not in code:
            code += '\n\nresult = cq.Workplane("XY").box(20, 20, 20)  # Fallback result'
        
        return code.strip()
    
    def _fallback_llm_adaptation(self, code: str, parameters: Dict) -> str:
        """Fallback LLM-based adaptation when AST fails"""
        prompt = f"""Adapt this CadQuery code with the specified parameters.

ORIGINAL CODE:
```python
{code}
```

PARAMETERS TO APPLY:
{json.dumps(parameters, indent=2)}

INSTRUCTIONS:
1. Update parameter values to match specifications
2. Keep the overall code structure
3. Ensure the code is valid Python/CadQuery
4. Return ONLY the adapted code

ADAPTED CODE:"""
        
        self.last_generation_mode = "llm_fallback"
        return self.llm_engine.generate(prompt, temperature=0.2)
    
    def _combine_reference_patterns_ast(self, references: List[Dict], spec: Dict) -> str:
        """Combine patterns using AST analysis"""
        # For now, use the best reference and adapt it
        best_ref = references[0]
        parameters = {k: v for k, v in spec.items() if not k.startswith('_')}
        return self._adapt_reference_with_ast(best_ref, spec, parameters)
    
    def _hybrid_generation_ast(self, references: List[Dict], spec: Dict) -> str:
        """Hybrid generation with AST insights"""
        # Extract design patterns from references
        patterns = []
        for ref in references[:2]:
            if 'code' in ref:
                params = self.ast_editor.extract_parameters_from_code(ref['code'])
                patterns.append(f"Reference {ref['name']}: {list(params.keys())}")
        
        prompt = f"""Generate CadQuery code using these design patterns.

DESIGN PATTERNS:
{chr(10).join(patterns)}

TARGET SPECIFICATION:
{json.dumps(spec, indent=2)}

Create a new design that incorporates the best practices from the patterns.
Return ONLY valid CadQuery code."""
        
        self.last_generation_mode = "hybrid_ast"
        return self.llm_engine.generate(prompt, temperature=0.3)
    
    def _generate_with_intelligent_reasoning(self, spec: Dict) -> str:
        """Generate code using pure LLM reasoning"""
        prompt = f"""Generate CadQuery code for: {json.dumps(spec, indent=2)}

Requirements:
- Import cadquery as cq
- Create 'result' variable with the final model
- Use appropriate CadQuery methods
- Follow 3D printing best practices
- Include error handling

Return ONLY executable Python code:"""
        
        self.last_generation_mode = "intelligent_reasoning"
        return self.llm_engine.generate(prompt, temperature=0.3)
    
    def _execute_code_safely(self, code: str) -> cq.Workplane:
        """Execute CadQuery code with enhanced safety and debugging - FIXED for CadQuery imports"""
        
        # Final code cleaning
        code = self._clean_and_validate_code(code)
        
        # Print code for debugging
        print("Generated code with line numbers:")
        for i, line in enumerate(code.split('\n'), 1):
            print(f"{i:2d}: {line}")
        
        # Safe execution environment - FIXED: Allow imports for CadQuery
        safe_globals = {
            '__builtins__': {
                '__import__': __import__,  # CRITICAL FIX: Allow imports
                'len': len,
                'range': range,
                'enumerate': enumerate,
                'int': int,
                'float': float,
                'str': str,
                'bool': bool,
                'Exception': Exception,
                'print': print,  # Allow print for debugging
            },
            'cq': cq,
            'cadquery': cq,
            'math': __import__('math'),
        }
        safe_locals = {}
        
        try:
            # Execute with proper import support
            exec(code, safe_globals, safe_locals)
            
            if 'result' in safe_locals:
                result = safe_locals['result']
                if isinstance(result, cq.Workplane):
                    print(f"✅ Successfully created model using {self.last_generation_mode}")
                    return result
                else:
                    raise Exception(f"Result is not a CadQuery Workplane: {type(result)}")
            else:
                raise Exception("Code didn't create 'result' variable")
                
        except Exception as e:
            print(f"❌ Code execution failed: {e}")
            # Return safe fallback
            return self._create_fallback_model(safe_globals)
    
    def _create_fallback_model(self, safe_globals: Dict) -> cq.Workplane:
        """Create a safe fallback model when code execution fails"""
        try:
            cq = safe_globals['cq']
            fallback = cq.Workplane("XY").box(20, 20, 20)
            print("Created fallback cube model")
            return fallback
        except:
            raise Exception("Failed to create fallback model")
    
    def _intelligent_rag_search(self, query: str, spec: Dict) -> List[Dict]:
        """Enhanced RAG search with intelligent ranking"""
        try:
            search_results = self.rag_library.semantic_search(query, top_k=5, threshold=0.0)
            
            if not search_results:
                return []
            
            # Enhance results with metadata
            enhanced_results = []
            object_type = spec.get('object_type', '')
            
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
                print(f"Found {len(filtered)} intelligent matches")
                return filtered[:self.top_k]
            
            return []
            
        except Exception as e:
            print(f"Intelligent search failed: {e}")
            return []
    
    def _build_enhanced_semantic_query(self, spec: Dict) -> str:
        """Build enhanced semantic search query"""
        query_parts = [spec.get('object_type', '')]
        
        # Add domain-specific terms
        obj_type = spec.get('object_type', '').lower()
        if 'gear' in obj_type:
            query_parts.extend(['mechanical', 'teeth', 'involute'])
        elif 'spring' in obj_type:
            query_parts.extend(['helical', 'coil', 'compression'])
        elif any(word in obj_type for word in ['cup', 'mug', 'container']):
            query_parts.extend(['cylindrical', 'vessel', 'hollow'])
        
        return ' '.join(query_parts)
    
    def _matches_category(self, object_type: str, category: str) -> bool:
        """Check category matching"""
        category_mappings = {
            'primitive': ['box', 'cylinder', 'sphere', 'cone', 'cup'],
            'functional': ['stand', 'holder', 'bracket', 'container', 'hook', 'mug'],
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
        
        if spec_features <= 5:
            return 1.0 if complexity == 'simple' else 0.8
        elif spec_features <= 10:
            return 1.0 if complexity == 'medium' else 0.9
        else:
            return 1.0 if complexity in ['complex', 'advanced'] else 0.8
    
    # Keep existing methods for compatibility
    def get_last_code(self) -> str:
        return self.last_code
    
    def get_last_generation_info(self) -> Dict:
        return {
            'mode': self.last_generation_mode,
            'similarity_score': self.last_similarity_score,
            'complexity_used': self.last_complexity_used,
            'used_rag': 'rag' in self.last_generation_mode or 'ast' in self.last_generation_mode,
            'similarity_threshold': self.similarity_threshold
        }
    
    def visualize(self, model: cq.Workplane):
        """Visualize model using CadQuery viewer"""
        try:
            from cadquery.vis import show
            show(model)
            print("3D viewer opened")
        except ImportError:
            print("Install cadquery[vis] for 3D visualization")
        except Exception as e:
            print(f"Visualization failed: {e}")