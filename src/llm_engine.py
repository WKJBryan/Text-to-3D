# src/llm_engine.py
"""LLM Engine with Enhanced RAG Support"""
import requests
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LLMEngine:
    def __init__(self, model: str = None, performance_mode: str = None):
        # RAG-related settings - SET FIRST
        self.rag_enabled = True
        
        self.model = model or os.getenv('DEFAULT_MODEL', 'llama3.1:8b')
        self.base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.performance_mode = performance_mode or os.getenv('PERFORMANCE_MODE', 'balanced')
        self._set_performance_config()
        self._verify_connection()
        
        print(f"🧠 LLM Engine initialized for Enhanced RAG + Intelligent Reasoning")
    
    def _set_performance_config(self):
        """Set configuration based on performance mode with Enhanced RAG considerations"""
        configs = {
            "fast": {"num_predict": 512, "num_ctx": 4096, "timeout": 120},
            "balanced": {"num_predict": 1024, "num_ctx": 8192, "timeout": 300},
            "quality": {"num_predict": 2048, "num_ctx": 16384, "timeout": 600}
        }
        self.config = configs.get(self.performance_mode, configs["balanced"])
        
        # Enhanced RAG may need larger context for complex examples
        if self.rag_enabled:
            self.config["num_ctx"] = max(self.config["num_ctx"], 16384)  # Larger for complex examples
    
    def _verify_connection(self):
        """Verify Ollama connection and model availability"""
        try:
            # Test connection
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            
            # Check model availability
            models = [m["name"] for m in response.json().get("models", [])]
            if self.model not in models:
                raise Exception(f"Model {self.model} not found. Install: ollama pull {self.model}")
            
            print(f"✅ {self.model} ready ({self.performance_mode} mode) - Enhanced RAG + Intelligent Reasoning")
            
        except requests.exceptions.RequestException:
            raise Exception("Ollama not running. Start with: ollama serve")
    
    def generate(self, prompt: str, temperature: float = 0.7) -> str:
        """Generate response from LLM with Enhanced RAG context support"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": self.config["num_predict"],
                "num_ctx": self.config["num_ctx"],
                "top_p": 0.9,
                "repeat_penalty": 1.1,
                "num_gpu": 1,
                "f16_kv": False,
                "use_mlock": True
            }
        }
        
        # Debug logging for Enhanced RAG
        prompt_length = len(prompt)
        print(f"🔧 Enhanced RAG-LLM Config: temp={temperature}, predict={self.config['num_predict']}, ctx={self.config['num_ctx']}")
        print(f"📝 Prompt length: {prompt_length} chars (Enhanced RAG)")
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.config["timeout"]
            )
            response.raise_for_status()
            result = response.json().get("response", "").strip()
            
            print(f"📝 Enhanced RAG-LLM Response length: {len(result)} chars")
            return result
        except Exception as e:
            print(f"❌ Enhanced RAG-LLM Error: {e}")
            return f"Error: {str(e)}"
    
    def validate_enhanced_rag_context_size(self, prompt: str) -> bool:
        """Validate that Enhanced RAG prompt fits within context window"""
        # Rough estimate: 4 chars per token
        estimated_tokens = len(prompt) // 4
        max_tokens = self.config["num_ctx"]
        
        if estimated_tokens > max_tokens * 0.8:  # Leave 20% buffer
            print(f"⚠️ Enhanced RAG prompt may be too long: {estimated_tokens} est. tokens (max: {max_tokens})")
            return False
        
        return True