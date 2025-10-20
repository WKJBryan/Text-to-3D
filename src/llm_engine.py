# src/llm_engine.py
"""LLM Engine with proper system message support - DEFENSIVE VERSION"""
import ollama
from typing import Optional

class LLMEngine:
    def __init__(self, model: str = "llama3.1:8b", reasoning_mode: str = None, **kwargs):
        """Initialize with flexible parameters
        
        Args:
            model: Model name
            reasoning_mode: Optional reasoning mode (ignored for compatibility)
            **kwargs: Any other arguments (ignored for compatibility)
        """
        self.model = model
        self.reasoning_mode = reasoning_mode
        # Store any extra kwargs for compatibility
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def generate(self, prompt: str, temperature: float = None, 
                 reasoning_effort: str = None, system: str = None) -> str:
        """Generate response with optional system message"""
        messages = []
        
        # Add system message if provided - THIS IS CRITICAL
        if system:
            messages.append({"role": "system", "content": system})
        
        # Add user prompt
        messages.append({"role": "user", "content": prompt})
        
        # Build options
        options = {}
        if temperature is not None:
            options['temperature'] = temperature
        if reasoning_effort:
            options['reasoning_effort'] = reasoning_effort
        
        # Call Ollama
        response = ollama.chat(
            model=self.model,
            messages=messages,
            options=options
        )
        
        return response['message']['content']
