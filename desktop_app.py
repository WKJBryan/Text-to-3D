# interfaces/desktop_app.py
"""Enhanced RAG + Intelligent Reasoning Desktop Application with RAG Toggle"""
import customtkinter as ctk
import threading
import os
from datetime import datetime
from tkinter import messagebox
from pathlib import Path
from dotenv import load_dotenv

from src.llm_engine import LLMEngine
from src.assistant import IntelligentConversationAssistant
from src.generation.RAG_generator import EnhancedRAGCADGenerator
from src.generation.export import ModelExporter

# Load environment variables
load_dotenv()

class EnhancedDesktopApp:
    def __init__(self):
        self._setup_ui()
        self._initialize_components()
        self.current_model = None
        self.current_spec = None
    
    def _setup_ui(self):
        """Initialize the enhanced user interface"""
        ctk.set_appearance_mode(os.getenv('THEME', 'dark'))
        ctk.set_default_color_theme("blue")
        
        window_size = os.getenv('WINDOW_SIZE', '900x700')
        
        self.root = ctk.CTk()
        self.root.title("🧠 Enhanced RAG + Intelligent AI Manufacturing")
        self.root.geometry(window_size)
        
        # Header
        header = ctk.CTkLabel(self.root, text="🧠 Enhanced RAG + Intelligent AI Manufacturing", 
                             font=ctk.CTkFont(size=20, weight="bold"))
        header.pack(pady=10)
        
        # Main frame
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Chat display
        self.chat_display = ctk.CTkTextbox(main_frame, height=400)
        self.chat_display.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Input frame
        input_frame = ctk.CTkFrame(main_frame)
        input_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.message_entry = ctk.CTkEntry(input_frame, placeholder_text="Describe what you want to design...")
        self.message_entry.pack(side="left", fill="x", expand=True, padx=10, pady=10)
        self.message_entry.bind("<Return>", self.send_message)
        
        self.send_button = ctk.CTkButton(input_frame, text="Send", command=self.send_message, width=80)
        self.send_button.pack(side="right", padx=10, pady=10)
        
        # Action buttons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.view_button = ctk.CTkButton(button_frame, text="👁️ View 3D", 
                                        command=self.view_model, state="disabled")
        self.view_button.pack(side="left", padx=5)
        
        self.export_button = ctk.CTkButton(button_frame, text="💾 Export STL/STEP/Code", 
                                          command=self.export_model, state="disabled")
        self.export_button.pack(side="left", padx=5)
        
        self.copy_button = ctk.CTkButton(button_frame, text="📋 Copy Code", 
                                        command=self.copy_code, state="disabled")
        self.copy_button.pack(side="left", padx=5)
        
        # Enhanced: RAG Info Button
        self.rag_info_button = ctk.CTkButton(button_frame, text="🧠 Enhanced RAG Info", 
                                            command=self.show_enhanced_rag_info)
        self.rag_info_button.pack(side="left", padx=5)
        
        # NEW: RAG Toggle Controls
        rag_control_frame = ctk.CTkFrame(button_frame)
        rag_control_frame.pack(side="left", padx=10)
        
        self.rag_label = ctk.CTkLabel(rag_control_frame, text="🧠 Enhanced RAG:")
        self.rag_label.pack(side="left", padx=(10, 5))
        
        self.rag_toggle = ctk.CTkSwitch(rag_control_frame, text="", 
                                       command=self.toggle_rag_mode, width=50)
        self.rag_toggle.pack(side="left", padx=(0, 10))
        self.rag_toggle.select()  # Start with RAG enabled
        
        self.rag_status_label = ctk.CTkLabel(rag_control_frame, text="ON", 
                                            text_color="green", font=ctk.CTkFont(weight="bold"))
        self.rag_status_label.pack(side="left")
        
        self.new_button = ctk.CTkButton(button_frame, text="🔄 New Design", 
                                       command=self.new_conversation)
        self.new_button.pack(side="right", padx=5)
        
        # Status
        self.status = ctk.CTkLabel(self.root, text="Ready...")
        self.status.pack(pady=5)
    
    def toggle_rag_mode(self):
        """Toggle RAG mode on/off"""
        rag_enabled = self.rag_toggle.get()
        
        if hasattr(self, 'generator'):
            self.generator.set_rag_enabled(rag_enabled)
        
        # Update visual indicators
        if rag_enabled:
            self.rag_status_label.configure(text="ON", text_color="green")
            status_text = "🧠 Enhanced RAG enabled - will use examples when relevant"
            self.rag_info_button.configure(text="🧠 Enhanced RAG Info")
        else:
            self.rag_status_label.configure(text="OFF", text_color="red")
            status_text = "🤖 RAG disabled - using intelligent reasoning only"
            self.rag_info_button.configure(text="🤖 Intelligent Mode Info")
        
        self.status.configure(text=status_text)
        self._add_message("System", f"🔄 Mode changed: {'Enhanced RAG + Intelligent Reasoning' if rag_enabled else 'Intelligent Reasoning Only'}")
    
    def _initialize_components(self):
        """Initialize Enhanced RAG + Intelligent Reasoning components"""
        try:
            model_name = os.getenv('DEFAULT_MODEL', 'llama3.1:8b')
            performance_mode = os.getenv('PERFORMANCE_MODE', 'balanced')
            embedding_model = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
            
            # Initialize LLM engine
            llm_engine = LLMEngine(model_name, performance_mode)
            
            # Initialize Enhanced components
            self.assistant = IntelligentConversationAssistant(llm_engine)
            self.generator = EnhancedRAGCADGenerator(llm_engine)
            self.exporter = ModelExporter(os.getenv('EXPORT_DIRECTORY', './exports'))
            
            #Set initial RAG state from toggle
            self.generator.set_rag_enabled(self.rag_toggle.get())
            
            stats = self.generator.get_enhanced_rag_stats()
            
            print(f"✅ Enhanced RAG + Intelligent Reasoning system initialized:")
            print(f"   LLM: {model_name} ({performance_mode})")
            print(f"   Embedding: {embedding_model}")
            print(f"   References: {stats['total_references']}")
            print(f"   RAG Enabled: {stats['rag_enabled']}")
            print(f"   Complexity levels: {stats['complexity_distribution']}")
            print(f"   Categories: {stats['category_distribution']}")
            
            self._add_welcome_message()
            
        except Exception as e:
            messagebox.showerror("Enhanced RAG Initialization Error", f"Failed to start Enhanced RAG system: {e}")
    
    def _add_welcome_message(self):
        """Add Enhanced RAG welcome message to chat"""
        stats = self.generator.get_enhanced_rag_stats()
        
        complexity_summary = ", ".join([f"{k}: {v}" for k, v in stats['complexity_distribution'].items()])
        
        welcome = f"""🚀 Welcome to Enhanced RAG + Intelligent AI Manufacturing!

🧠 **Enhanced RAG System Active** (Toggle: 🔲 ON/OFF):
• **{stats['total_references']} hierarchical examples** across complexity levels
• **Embedding model:** {stats['embedding_model']}
• **Intelligent reasoning** for novel designs without relevant examples
• **Similarity threshold:** {stats['similarity_threshold']} (smart fallback enabled)

📊 **Reference Library:**
• **Complexity levels:** {complexity_summary}
• **Categories:** {", ".join(stats['category_distribution'].keys())}

💡 **Mode Control:**
• **🧠 RAG ON** → Use examples when relevant + intelligent fallback
• **🤖 RAG OFF** → Pure intelligent reasoning from engineering principles
• **Toggle anytime** to compare generation approaches!

🎯 **Examples:**
• "20 tooth gear" → RAG: finds gear patterns | Pure: engineering calculation  
• "phone stand" → RAG: functional patterns | Pure: ergonomic reasoning
• "novel device" → Both modes use intelligent reasoning

📤 **Exports:** STL for 3D printing, STEP for CAD, and enhanced CadQuery code

Describe anything you want to create - toggle RAG to compare approaches!"""
        
        self._add_message("Enhanced RAG Assistant", welcome)
    
    def show_enhanced_rag_info(self):
        """Show Enhanced RAG system information dialog with toggle state"""
        if hasattr(self, 'generator'):
            stats = self.generator.get_enhanced_rag_stats()
            rag_enabled = self.rag_toggle.get()
            
            complexity_details = '\n'.join([f"• {k.title()}: {v} examples" for k, v in stats['complexity_distribution'].items()])
            category_details = '\n'.join([f"• {k.title()}: {v} examples" for k, v in stats['category_distribution'].items()])
            
            # Different content based on RAG toggle state
            if rag_enabled:
                mode_title = "🧠 Enhanced RAG + Intelligent Reasoning System"
                mode_description = f"""🎯 **Current Mode: Enhanced RAG ENABLED**

**Enhanced RAG Mode** (similarity ≥ {stats['similarity_threshold']:.1f}):
• Uses hierarchical examples with complexity scaling
• Combines patterns from multiple relevant examples
• Applies proven engineering solutions and best practices
• Scales from simple geometric to advanced mathematical objects

**Intelligent Reasoning Mode** (similarity < {stats['similarity_threshold']:.1f}):
• Uses LLM's engineering knowledge from training
• Applies first-principles design thinking
• Calculates parameters based on functional requirements
• Creates novel solutions for unprecedented designs

🔄 **Automatic Mode Selection:**
1. Semantic search finds most relevant examples
2. **IF** similarity ≥ threshold → Enhanced RAG with hierarchical patterns
3. **IF** similarity < threshold → Intelligent reasoning from engineering principles
4. System always chooses the optimal approach for each design"""
            else:
                mode_title = "🤖 Intelligent Reasoning Only System"
                mode_description = """🎯 **Current Mode: RAG DISABLED - Intelligent Reasoning Only**

**Pure Intelligent Reasoning Mode**:
• Uses LLM's engineering knowledge exclusively
• Applies first-principles design thinking for all objects
• Calculates parameters based on functional requirements  
• Creates solutions using engineering principles only
• No reference examples used (even if available)

🧠 **Engineering Knowledge Sources:**
• Mechanical engineering principles from training data
• Materials science and manufacturing knowledge
• Mathematical calculations for gears, springs, structures
• Ergonomic and functional design principles
• 3D printing and manufacturing constraints

⚙️ **This mode tests pure reasoning capability:**
• No dependency on reference library
• Tests LLM's inherent engineering knowledge
• Useful for novel/unprecedented designs
• Good for comparing against RAG approaches"""
            
            info_text = f"""{mode_title}

📊 **Statistics:**
• Total References: {stats['total_references']} (Available but {'DISABLED' if not rag_enabled else 'ENABLED'})
• Embedding Model: {stats['embedding_model']}
• Search Top-K: {stats['top_k']}
• Similarity Threshold: {stats['similarity_threshold']:.2f}

📁 **Cache Directory:**
{stats['cache_dir']}

🎯 **Last Generation:**
• Mode: {stats['last_generation_mode'].replace('_', ' ').title()}
• Similarity Score: {stats['last_similarity_score']:.3f}
• Complexity Used: {stats['last_complexity_used'].title()}

📚 **Complexity Distribution:**
{complexity_details}

🏷️ **Category Distribution:**
{category_details}

{mode_description}

💡 **Tips:**
• **Compare modes** by toggling RAG ON/OFF for same design
• **RAG ON**: Good for learning from proven patterns
• **RAG OFF**: Good for testing pure reasoning and novel designs
• **Engineering constraints** handled by both modes
• **Toggle anytime** to see different approaches to same problem"""
            
            # Create enhanced info dialog
            dialog = ctk.CTkToplevel(self.root)
            dialog.title(mode_title)
            dialog.geometry("650x500")
            dialog.transient(self.root)
            
            text_widget = ctk.CTkTextbox(dialog)
            text_widget.pack(fill="both", expand=True, padx=20, pady=20)
            text_widget.insert("1.0", info_text)
            text_widget.configure(state="disabled")
    
    def _add_message(self, sender: str, message: str):
        """Add message to chat display"""
        timestamp = datetime.now().strftime("%H:%M")
        self.chat_display.insert("end", f"\n[{timestamp}] {sender}:\n{message}\n")
        self.chat_display.see("end")
    
    def send_message(self, event=None):
        """Send user message"""
        message = self.message_entry.get().strip()
        if not message:
            return
        
        self._add_message("You", message)
        self.message_entry.delete(0, "end")
        self.status.configure(text="🤔 Thinking...")
        self.send_button.configure(state="disabled")
        
        # Process in background
        threading.Thread(target=self._process_message, args=(message,), daemon=True).start()
    
    def _process_message(self, message: str):
        """Process message with Enhanced RAG debugging"""
        try:
            print(f"🎯 Processing: '{message}'")
            result = self.assistant.chat(message)
            print(f"📊 Result keys: {list(result.keys())}")
            print(f"🎯 Generate model: {result.get('generate_model', False)}")
            
            self.root.after(0, self._handle_response, result)
        except Exception as e:
            print(f"❌ Enhanced RAG Processing error: {e}")
            import traceback
            traceback.print_exc()
            self.root.after(0, self._handle_error, str(e))
    
    def _handle_response(self, result: dict):
        """Handle assistant response"""
        # Show response
        display_message = result['message']
        if 'GENERATE_MODEL:' in display_message:
            display_message = display_message.split('GENERATE_MODEL:')[0].strip()
        
        if display_message:
            self._add_message("Enhanced RAG Assistant", display_message)
        
        # Check if generation requested
        if result['generate_model']:
            self.status.configure(text="🧠 Enhanced RAG analysis + Intelligent generation...")
            self.current_spec = result['model_spec']
            threading.Thread(
                target=self._generate_model,
                args=(result['model_spec'], result['cadquery_code']),
                daemon=True
            ).start()
        else:
            self.status.configure(text="💬 Continue chatting...")
        
        self.send_button.configure(state="normal")
    
    def _handle_error(self, error: str):
        """Handle error"""
        self._add_message("Enhanced RAG Error", f"❌ {error}")
        self.status.configure(text="❌ Enhanced RAG Error occurred")
        self.send_button.configure(state="normal")
    
    def _generate_model(self, spec: dict, code: str = None):
        """Generate 3D model using Enhanced RAG + Intelligent Reasoning"""
        try:
            model = self.generator.generate_model(spec, code)
            self.current_model = model
            
            self.root.after(0, self._handle_generation_success, spec)
        except Exception as e:
            self.root.after(0, self._handle_generation_error, str(e))
    
    def _handle_generation_success(self, spec: dict):
        """Handle successful Enhanced RAG generation with detailed mode info"""
        object_type = spec.get('object_type', 'model')
        dims = f"{spec.get('width', '?')} × {spec.get('depth', '?')} × {spec.get('height', '?')} mm"
        
        # Get enhanced generation info
        gen_info = self.generator.get_last_generation_info()
        rag_enabled = self.rag_toggle.get()
        
        if rag_enabled and gen_info['used_rag']:
            mode_text = f"Enhanced RAG ({gen_info['complexity_used']})"
            detail_text = f"Similarity: {gen_info['similarity_score']:.3f} | Used hierarchical {gen_info['complexity_used']} complexity patterns"
            status_prefix = "🧠 RAG"
        elif rag_enabled and not gen_info['used_rag']:
            mode_text = "Intelligent Reasoning (Auto-Fallback)"
            detail_text = f"No relevant examples (similarity < {gen_info['similarity_threshold']}) | Generated from engineering principles"
            status_prefix = "🤖 REASONING"
        else:  # RAG disabled
            mode_text = "Intelligent Reasoning (RAG Disabled)"
            detail_text = "RAG disabled by user | Generated purely from engineering principles"
            status_prefix = "🤖 PURE-REASONING"
        
        message = f"✅ {mode_text} Generated {object_type}!\n{detail_text}\nDimensions: {dims}\n\nReady to view and export!"
        self._add_message("Enhanced RAG Assistant", message)
        
        # Update status with enhanced mode info
        status_text = f"✅ Model ready! ({status_prefix})"
        self.status.configure(text=status_text)
        
        self.view_button.configure(state="normal")
        self.export_button.configure(state="normal")
        self.copy_button.configure(state="normal")
    
    def _handle_generation_error(self, error: str):
        """Handle Enhanced RAG generation error"""
        code = self.generator.get_last_code()
        gen_info = self.generator.get_last_generation_info()
        rag_enabled = self.rag_toggle.get()
        
        if rag_enabled:
            mode_text = "Enhanced RAG" if gen_info['used_rag'] else "Intelligent Reasoning"
        else:
            mode_text = "Intelligent Reasoning (RAG Disabled)"
        
        message = f"""❌ {mode_text} Generation failed: {error}

💻 Generated CadQuery code:
```python
{code[:500]}...
```

Click "📋 Copy Code" to get the full code for manual use."""
        
        self._add_message("Enhanced RAG Assistant", message)
        self.status.configure(text="❌ Generation failed - code available")
        self.copy_button.configure(state="normal")
    
    def view_model(self):
        """View 3D model"""
        if self.current_model:
            self.status.configure(text="👁️ Opening 3D viewer...")
            threading.Thread(target=self._view_in_background, daemon=True).start()
    
    def _view_in_background(self):
        """View model in background"""
        try:
            self.generator.visualize(self.current_model)
            self.root.after(0, lambda: self.status.configure(text="👁️ 3D viewer opened"))
        except Exception as e:
            self.root.after(0, lambda: self.status.configure(text=f"❌ View failed: {e}"))
    
    def export_model(self):
        """Export model to files"""
        if self.current_model and self.current_spec:
            self.status.configure(text="💾 Exporting STL, STEP, and Enhanced code...")
            threading.Thread(target=self._export_in_background, daemon=True).start()
    
    def _export_in_background(self):
        """Export in background"""
        try:
            cadquery_code = self.generator.get_last_code()
            result = self.exporter.export_model(self.current_model, self.current_spec, cadquery_code)
            self.root.after(0, self._handle_export_success, result)
        except Exception as e:
            self.root.after(0, self._handle_export_error, str(e))
    
    def _handle_export_success(self, result: dict):
        """Handle successful export"""
        files = result['files']
        size = result['file_size_mb']
        
        file_list = '\n'.join([f"• {fmt}: {Path(path).name}" for fmt, path in files.items()])
        
        message = f"💾 Enhanced RAG Export successful!\n\n{file_list}\n\nFile size: {size:.2f} MB"
        self._add_message("Enhanced RAG Assistant", message)
        self.status.configure(text="✅ Enhanced Export complete!")
    
    def _handle_export_error(self, error: str):
        """Handle export error"""
        self._add_message("Enhanced RAG Assistant", f"❌ Export failed: {error}")
        self.status.configure(text="❌ Export failed")
    
    def copy_code(self):
        """Copy Enhanced RAG generated code to clipboard"""
        code = self.generator.get_last_code()
        if code:
            self.root.clipboard_clear()
            self.root.clipboard_append(code)
            self.status.configure(text="📋 Enhanced RAG Code copied!")
    
    def new_conversation(self):
        """Start new conversation"""
        if messagebox.askyesno("New Design", "Start new design? Current conversation will be lost."):
            self.assistant.reset()
            self.chat_display.delete("1.0", "end")
            self._add_welcome_message()
            self.current_model = None
            self.current_spec = None
            self.view_button.configure(state="disabled")
            self.export_button.configure(state="disabled")
            self.copy_button.configure(state="disabled")
            self.status.configure(text="Ready for new Enhanced RAG design...")
    
    def run(self):
        """Start the Enhanced application"""
        self.root.mainloop()