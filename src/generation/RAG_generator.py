# src/generation/RAG_generator.py
"""Enhanced RAG CAD Generator with Intelligent Reasoning"""
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
        self.last_generation_mode = "rag"  # Track generation mode
        self.last_similarity_score = 0.0   # Track similarity score
        self.last_complexity_used = "unknown"  # Track complexity level
        
        # RAG control
        self.rag_enabled = True  # Default enabled
        
        # Initialize Enhanced RAG components
        embedding_model = embedding_model or os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
        cache_dir = cache_dir or os.getenv('EMBEDDING_CACHE_DIR', './embeddings')
        
        print("🧠 Initializing Enhanced RAG generator with intelligent reasoning...")
        self.rag_library = EnhancedRAGReferenceLibrary(embedding_model, cache_dir)
        
        # RAG settings
        self.top_k = int(os.getenv('VECTOR_SEARCH_TOP_K', '2'))
        self.similarity_threshold = float(os.getenv('SIMILARITY_THRESHOLD', '0.3'))
    
    def set_rag_enabled(self, enabled: bool):
        """Enable or disable RAG mode"""
        self.rag_enabled = enabled
        mode_text = "Enhanced RAG + Intelligent Reasoning" if enabled else "Pure Intelligent Reasoning"
        print(f"🔄 Mode changed: {mode_text}")
    
    def generate_model(self, model_spec: Dict, provided_code: Optional[str] = None) -> cq.Workplane:
        """Generate 3D model using Enhanced RAG with intelligent reasoning"""
        if provided_code:
            code = provided_code
            self.last_generation_mode = "provided"
        else:
            code = self._generate_code_with_enhanced_rag(model_spec)
        
        self.last_code = code
        self.generation_history.append({
            'spec': model_spec, 
            'code': code,
            'mode': self.last_generation_mode,
            'similarity': self.last_similarity_score,
            'complexity': self.last_complexity_used
        })
        
        return self._execute_code(code)
    
    def _generate_code_with_enhanced_rag(self, spec: Dict) -> str:
        """Generate code using Enhanced RAG with intelligent fallback"""
        # Check if RAG is enabled
        if not self.rag_enabled:
            print("🤖 RAG disabled - using pure intelligent reasoning")
            prompt = self._build_intelligent_reasoning_prompt(spec)
            self.last_generation_mode = "intelligent_reasoning_forced"
            return self.llm_engine.generate(prompt, temperature=0.3)
        
        # Build semantic query from specification
        query = self._build_enhanced_semantic_query(spec)
        
        # Perform Enhanced RAG search
        relevant_refs = self._enhanced_rag_search(query)
        
        # Choose generation strategy based on RAG results
        if relevant_refs:  # Good RAG matches found
            prompt = self._build_enhanced_rag_prompt(spec, relevant_refs)
            self.last_generation_mode = "enhanced_rag"
            print(f"✅ Using Enhanced RAG with {len(relevant_refs)} examples")
        else:  # No good matches, use intelligent reasoning
            prompt = self._build_intelligent_reasoning_prompt(spec)
            self.last_generation_mode = "intelligent_reasoning"
            print("🧠 Using intelligent reasoning (no relevant examples)")
        
        return self.llm_engine.generate(prompt, temperature=0.3)  # Very low for consistency
    
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
    
    def _enhanced_rag_search(self, query: str) -> List[Dict]:
        """Perform Enhanced RAG search with complexity and category awareness"""
        try:
            # Get semantic search results
            search_results = self.rag_library.semantic_search(
                query, 
                top_k=self.top_k * 2,  # Get more candidates for filtering
                threshold=0.0  # Get all results first
            )
            
            if not search_results:
                print("❌ No search results returned")
                self.last_similarity_score = 0.0
                return []
            
            # Enhanced filtering with complexity progression
            best_similarity = search_results[0][1]
            self.last_similarity_score = best_similarity
            
            print(f"🔍 Best similarity: {best_similarity:.3f} (threshold: {self.similarity_threshold})")
            
            if best_similarity < self.similarity_threshold:
                print(f"⚠️  Enhanced RAG similarity too low ({best_similarity:.3f}) - switching to intelligent reasoning")
                return []
            
            # Select examples with complexity consideration
            selected_refs = []
            complexity_counts = {"simple": 0, "medium": 0, "complex": 0, "advanced": 0}
            
            for ref_key, similarity in search_results:
                if similarity >= self.similarity_threshold and len(selected_refs) < self.top_k:
                    reference = self.rag_library.get_reference(ref_key)
                    complexity = reference.get('complexity', 'medium')
                    
                    # Prefer diversity in complexity if multiple good matches
                    if complexity_counts[complexity] < 1 or len(selected_refs) == 0:
                        selected_refs.append({
                            'name': ref_key,
                            'similarity': similarity,
                            'description': reference['description'],
                            'code': reference['code'],
                            'complexity': complexity,
                            'category': reference.get('category', 'functional')
                        })
                        complexity_counts[complexity] += 1
                        self.last_complexity_used = complexity
            
            if not selected_refs:
                print(f"⚠️  No examples above threshold - switching to intelligent reasoning")
                return []
            
            print(f"✅ Using {len(selected_refs)} Enhanced RAG examples")
            print(f"📊 Complexity levels: {[ref['complexity'] for ref in selected_refs]}")
            return selected_refs
            
        except Exception as e:
            print(f"❌ Enhanced RAG search failed: {e} - falling back to intelligent reasoning")
            self.last_similarity_score = 0.0
            return []
    
    def _build_enhanced_rag_prompt(self, spec: Dict, relevant_refs: List[Dict]) -> str:
        """Build enhanced prompt using hierarchical RAG examples"""
        
        # Build reference examples section with complexity hierarchy
        examples_section = "ENHANCED RAG-SELECTED EXAMPLES (Hierarchical Complexity):\n\n"
        for i, ref in enumerate(relevant_refs, 1):
            examples_section += f"EXAMPLE {i}: {ref['description']}\n"
            examples_section += f"├─ Similarity: {ref['similarity']:.3f}\n"
            examples_section += f"├─ Complexity: {ref['complexity']}\n"
            examples_section += f"├─ Category: {ref['category']}\n"
            examples_section += f"└─ Reference: {ref['name']}\n"
            examples_section += f"```python\n{ref['code']}\n```\n\n"
        
        prompt = f"""You are a CadQuery expert using Enhanced RAG with hierarchical complexity examples. The examples below were automatically selected based on semantic similarity and complexity appropriateness.

{examples_section}

TARGET SPECIFICATION:
{json.dumps(spec, indent=2)}

ENHANCED RAG GUIDANCE:
- Study the hierarchical examples above for progressive complexity patterns
- These examples represent best practices at different complexity levels
- Use appropriate complexity level for the target specification
- Follow the semantic patterns that led to their selection
- Combine techniques from multiple examples if beneficial

REQUIREMENTS:
- Import cadquery as cq
- Create 'result' variable with final model
- Use exact specifications from the target specification
- Include comprehensive try/except error handling
- Apply manufacturing considerations (3D printing, wall thickness, etc.)
- Use proper CadQuery syntax patterns from the examples
- Scale complexity appropriately to match the specification

CODING STANDARDS FROM ENHANCED EXAMPLES:
- Use clear, descriptive variable names
- Apply .edges("|Z").fillet() for vertical edges
- Use .edges(">>Z").chamfer() for top edges  
- Include .shell(-thickness) for objects that require thickness
- Add robust try/except with meaningful fallbacks
- Use .translate(), .rotate() for positioning
- Apply .union(), .cut() for boolean operations
- Consider manufacturing constraints and material properties

COMPLEXITY SCALING:
- Simple specs → Use basic geometric operations
- Medium specs → Add functional features and constraints
- Complex specs → Include mathematical calculations and advanced geometry
- Advanced specs → Apply manufacturing optimization and assembly considerations

The Enhanced RAG system selected these examples as semantically and complexity-appropriate: {[ref['name'] for ref in relevant_refs]}

Generate ONLY the CadQuery code following these enhanced hierarchical patterns:"""

        return prompt
    
    def _build_intelligent_reasoning_prompt(self, spec: Dict) -> str:
        return f"""Generate CadQuery code for: {json.dumps(spec, indent=2)}

    Requirements:
    - Import cadquery as cq
    - Create 'result' variable  
    - Include try/except fallback
    - Use appropriate CadQuery methods for this object type
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
            pass
            raise Exception(f"Code execution failed: {e}")
            pass
    
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
            'used_rag': self.last_generation_mode == "enhanced_rag",
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