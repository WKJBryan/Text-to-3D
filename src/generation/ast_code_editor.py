# src/generation/ast_code_editor.py
"""AST-based code editing with smart parameter detection"""
import ast
import astor
from typing import Dict, Any, List, Set, Optional, Tuple
import re

class ParameterRewriter(ast.NodeTransformer):
    """AST transformer for safe parameter replacement"""
    
    def __init__(self, replacements: Dict[str, Any]):
        self.replacements = replacements
        self.replaced_params = set()
    
    def visit_Assign(self, node: ast.Assign) -> ast.AST:
        """Replace parameter assignments"""
        if (len(node.targets) == 1 and 
            isinstance(node.targets[0], ast.Name)):
            
            param_name = node.targets[0].id
            
            if param_name in self.replacements:
                new_value = self.replacements[param_name]
                self.replaced_params.add(param_name)
                
                if isinstance(new_value, (int, float)):
                    node.value = ast.Constant(value=new_value)
                elif isinstance(new_value, str):
                    node.value = ast.Constant(value=new_value)
                elif isinstance(new_value, bool):
                    node.value = ast.Constant(value=new_value)
                else:
                    node.value = ast.Constant(value=str(new_value))
        
        return node

class SmartParameterExtractor(ast.NodeVisitor):
    """ENHANCED: Distinguishes input vs calculated parameters + detects booleans"""
    
    def __init__(self):
        self.input_params = {}      # Only these need user input
        self.calculated_params = {}  # These are formulas, don't ask user
        self.boolean_params = {}     # Boolean flags
        self.features = set()
    
    def visit_Assign(self, node: ast.Assign):
        """Extract and classify parameters"""
        if (len(node.targets) == 1 and 
            isinstance(node.targets[0], ast.Name)):
            
            param_name = node.targets[0].id
            
            # Check if it's a LITERAL VALUE (input parameter)
            if isinstance(node.value, ast.Constant):
                value = node.value.value
                
                if isinstance(value, bool):
                    # Boolean parameter
                    self.boolean_params[param_name] = value
                    print(f"  📌 Boolean param: {param_name} = {value}")
                    
                elif isinstance(value, (int, float)):
                    # Numeric input parameter
                    self.input_params[param_name] = value
                    print(f"  📏 Input param: {param_name} = {value}")
                    
                elif isinstance(value, str):
                    # String parameter (rare in CAD)
                    self.input_params[param_name] = value
            
            # Check if it's a CALCULATED VALUE (formula)
            elif self._is_expression(node.value):
                # This is calculated, don't ask user for it
                self.calculated_params[param_name] = "formula"
                print(f"  🧮 Calculated param: {param_name} (skip asking user)")
        
        self.generic_visit(node)
    
    def _is_expression(self, node) -> bool:
        """Check if node is an expression (formula) vs literal"""
        return isinstance(node, (
            ast.BinOp,      # radius * 2
            ast.UnaryOp,    # -value
            ast.Call,       # math.sqrt(x)
            ast.Name,       # another_variable
            ast.Subscript,  # array[0]
            ast.Compare,    # x > 5
            ast.BoolOp,     # x and y
            ast.IfExp,      # x if y else z
        ))
    
    def visit_If(self, node: ast.If):
        """Detect optional features"""
        if isinstance(node.test, ast.Name):
            feature_name = node.test.id
            if any(keyword in feature_name.lower() for keyword in ['has_', 'have_', 'with_', 'is_']):
                self.features.add(feature_name)
        
        self.generic_visit(node)

class ASTCodeEditor:
    """Main class for AST-based code editing"""
    
    def __init__(self):
        self.last_edit_log = []
    
    def extract_parameters_from_code(self, code: str) -> Dict[str, Any]:
        """ENHANCED: Extract ONLY input parameters (not calculated ones)"""
        try:
            tree = ast.parse(code)
            extractor = SmartParameterExtractor()
            extractor.visit(tree)
            
            # CRITICAL: Only return input + boolean parameters
            # Do NOT return calculated parameters
            result = {}
            result.update(extractor.input_params)
            result.update(extractor.boolean_params)
            
            print(f"📊 AST Analysis:")
            print(f"   Input params: {len(extractor.input_params)}")
            print(f"   Boolean params: {len(extractor.boolean_params)}")
            print(f"   Calculated params (skipped): {len(extractor.calculated_params)}")
            
            return result
            
        except SyntaxError as e:
            print(f"Code parsing failed: {e}")
            return self._fallback_regex_extraction(code)
        except Exception as e:
            print(f"AST extraction failed: {e}")
            return self._fallback_regex_extraction(code)
    
    def get_parameter_classification(self, code: str) -> Tuple[Dict, Dict, Dict]:
        """Get detailed classification of all parameters
        
        Returns:
            (input_params, boolean_params, calculated_params)
        """
        try:
            tree = ast.parse(code)
            extractor = SmartParameterExtractor()
            extractor.visit(tree)
            
            return (
                extractor.input_params,
                extractor.boolean_params,
                extractor.calculated_params
            )
        except Exception as e:
            print(f"Classification failed: {e}")
            return ({}, {}, {})
    
    def replace_parameters(self, code: str, parameter_replacements: Dict[str, Any]) -> str:
        """Replace parameters in code using AST transformation"""
        try:
            tree = ast.parse(code)
            
            rewriter = ParameterRewriter(parameter_replacements)
            modified_tree = rewriter.visit(tree)
            
            missing_params = set(parameter_replacements.keys()) - rewriter.replaced_params
            
            if missing_params:
                modified_tree = self._inject_missing_parameters(modified_tree, missing_params, parameter_replacements)
            
            ast.fix_missing_locations(modified_tree)
            
            try:
                result_code = astor.to_source(modified_tree)
            except:
                result_code = self._ast_to_code_manual(modified_tree)
            
            self.last_edit_log = [
                f"Replaced parameters: {list(rewriter.replaced_params)}",
                f"Injected parameters: {list(missing_params)}"
            ]
            
            return result_code
            
        except Exception as e:
            print(f"AST parameter replacement failed: {e}")
            return self._fallback_regex_replacement(code, parameter_replacements)
    
    def remove_features(self, code: str, features_to_remove: List[str]) -> str:
        """Remove features from code using AST transformation"""
        try:
            tree = ast.parse(code)
            
            remover = FeatureRemover(features_to_remove)
            modified_tree = remover.visit(tree)
            
            ast.fix_missing_locations(modified_tree)
            
            try:
                result_code = astor.to_source(modified_tree)
            except:
                result_code = self._ast_to_code_manual(modified_tree)
            
            self.last_edit_log.append(f"Removed features: {list(remover.removed_features)}")
            
            return result_code
            
        except Exception as e:
            print(f"AST feature removal failed: {e}")
            return self._fallback_regex_removal(code, features_to_remove)
    
    def _inject_missing_parameters(self, tree: ast.AST, missing_params: Set[str], values: Dict[str, Any]) -> ast.AST:
        """Inject missing parameters at the top of the code"""
        param_assignments = []
        
        for param in missing_params:
            value = values[param]
            if isinstance(value, (int, float, str, bool)):
                assign_node = ast.Assign(
                    targets=[ast.Name(id=param, ctx=ast.Store())],
                    value=ast.Constant(value=value)
                )
                param_assignments.append(assign_node)
        
        if isinstance(tree, ast.Module):
            insert_index = 0
            for i, node in enumerate(tree.body):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    insert_index = i + 1
                else:
                    break
            
            tree.body[insert_index:insert_index] = param_assignments
        
        return tree
    
    def _fallback_regex_extraction(self, code: str) -> Dict[str, Any]:
        """Fallback regex-based parameter extraction (input params only)"""
        parameters = {}
        
        # Only extract literal assignments, skip formulas
        patterns = [
            r'(\w+)\s*=\s*(\d+(?:\.\d+)?)\s*(?:#.*)?$',  # number assignments
            r'(\w+)\s*=\s*["\']([^"\']+)["\']',           # string assignments
            r'(\w+)\s*=\s*(True|False)',                   # boolean assignments
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, code, re.MULTILINE)
            for match in matches:
                param_name = match[0]
                value = match[1]
                
                try:
                    if '.' in value:
                        parameters[param_name] = float(value)
                    elif value.isdigit():
                        parameters[param_name] = int(value)
                    elif value in ['True', 'False']:
                        parameters[param_name] = value == 'True'
                    else:
                        parameters[param_name] = value
                except:
                    parameters[param_name] = value
        
        return parameters
    
    def _fallback_regex_replacement(self, code: str, replacements: Dict[str, Any]) -> str:
        """Fallback regex-based parameter replacement"""
        result = code
        
        for param, value in replacements.items():
            pattern = rf'{param}\s*=\s*[^#\n]+'
            replacement = f'{param} = {value}'
            result = re.sub(pattern, replacement, result)
        
        return result
    
    def _fallback_regex_removal(self, code: str, features_to_remove: List[str]) -> str:
        """Fallback regex-based feature removal"""
        lines = code.split('\n')
        cleaned_lines = []
        
        for line in lines:
            should_skip = any(feature.lower() in line.lower() for feature in features_to_remove)
            
            if not should_skip:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _ast_to_code_manual(self, tree: ast.AST) -> str:
        """Manual AST to code conversion for fallback"""
        try:
            import ast
            if hasattr(ast, 'unparse'):
                return ast.unparse(tree)
            else:
                return "# AST conversion failed - using original code\n"
        except:
            return "# AST conversion failed - using original code\n"
    
    def get_edit_log(self) -> List[str]:
        """Get log of last edit operations"""
        return self.last_edit_log.copy()

class FeatureRemover(ast.NodeTransformer):
    """AST transformer for removing features"""
    
    def __init__(self, features_to_remove: List[str]):
        self.features_to_remove = [f.lower() for f in features_to_remove]
        self.removed_features = set()
    
    def visit_Assign(self, node: ast.Assign) -> Optional[ast.AST]:
        if (len(node.targets) == 1 and 
            isinstance(node.targets[0], ast.Name)):
            
            var_name = node.targets[0].id.lower()
            
            for feature in self.features_to_remove:
                if feature in var_name:
                    self.removed_features.add(var_name)
                    return None
        
        return node
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> Optional[ast.AST]:
        func_name = node.name.lower()
        
        for feature in self.features_to_remove:
            if feature in func_name:
                self.removed_features.add(node.name)
                return None
        
        return node
    
    def visit_If(self, node: ast.If) -> Optional[ast.AST]:
        if isinstance(node.test, ast.Name):
            var_name = node.test.id.lower()
            for feature in self.features_to_remove:
                if feature in var_name:
                    self.removed_features.add(var_name)
                    return None
        
        return node