# interfaces/desktop_app.py
"""Enhanced RAG + Intelligent Reasoning Desktop Application with 3D Printing Pipeline"""
import customtkinter as ctk
import threading
import os
from datetime import datetime
from tkinter import messagebox, simpledialog
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
        self.current_stl_path = None
        self.current_gcode_path = None
        self.printer_status_timer = None
    
    def _setup_ui(self):
        """Initialize the enhanced user interface with 3D printing controls"""
        ctk.set_appearance_mode(os.getenv('THEME', 'dark'))
        ctk.set_default_color_theme("blue")
        
        window_size = os.getenv('WINDOW_SIZE', '1100x800')  # Bigger for printing controls
        
        self.root = ctk.CTk()
        self.root.title("🚀 Enhanced RAG + AI Manufacturing + 3D Printing Pipeline")
        self.root.geometry(window_size)
        
        # Header
        header = ctk.CTkLabel(self.root, text="🚀 AI Manufacturing → 3D Printing Pipeline", 
                             font=ctk.CTkFont(size=20, weight="bold"))
        header.pack(pady=10)
        
        # Create main horizontal layout
        main_container = ctk.CTkFrame(self.root)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left side - Chat and controls
        left_frame = ctk.CTkFrame(main_container)
        left_frame.pack(side="left", fill="both", expand=True, padx=5)
        
        # Right side - 3D printing panel
        self.printing_frame = ctk.CTkFrame(main_container, width=350)
        self.printing_frame.pack(side="right", fill="y", padx=5)
        self.printing_frame.pack_propagate(False)
        
        self._setup_chat_interface(left_frame)
        self._setup_printing_interface()
        
        # Status bar
        self.status = ctk.CTkLabel(self.root, text="Ready for AI Manufacturing + 3D Printing...")
        self.status.pack(pady=5)
    
    def _setup_chat_interface(self, parent):
        """Setup the chat interface"""
        # Chat display
        self.chat_display = ctk.CTkTextbox(parent, height=400)
        self.chat_display.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Input frame
        input_frame = ctk.CTkFrame(parent)
        input_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.message_entry = ctk.CTkEntry(input_frame, placeholder_text="Describe what you want to design...")
        self.message_entry.pack(side="left", fill="x", expand=True, padx=10, pady=10)
        self.message_entry.bind("<Return>", self.send_message)
        
        self.send_button = ctk.CTkButton(input_frame, text="Send", command=self.send_message, width=80)
        self.send_button.pack(side="right", padx=10, pady=10)
        
        # Action buttons
        button_frame = ctk.CTkFrame(parent)
        button_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # First row of buttons
        button_row1 = ctk.CTkFrame(button_frame)
        button_row1.pack(fill="x", pady=5)
        
        self.view_button = ctk.CTkButton(button_row1, text="👁️ View 3D", 
                                        command=self.view_model, state="disabled")
        self.view_button.pack(side="left", padx=5)
        
        self.export_button = ctk.CTkButton(button_row1, text="💾 Export Files", 
                                          command=self.export_model, state="disabled")
        self.export_button.pack(side="left", padx=5)
        
        self.copy_button = ctk.CTkButton(button_row1, text="📋 Copy Code", 
                                        command=self.copy_code, state="disabled")
        self.copy_button.pack(side="left", padx=5)
        
        # Second row - 3D Printing buttons
        button_row2 = ctk.CTkFrame(button_frame)
        button_row2.pack(fill="x", pady=5)
        
        self.slice_button = ctk.CTkButton(button_row2, text="🔄 Slice for 3D Printing", 
                                         command=self.slice_model, state="disabled",
                                         fg_color="orange", hover_color="darkorange")
        self.slice_button.pack(side="left", padx=5)
        
        self.print_button = ctk.CTkButton(button_row2, text="🖨️ Send to Printer", 
                                         command=self.send_to_printer, state="disabled",
                                         fg_color="green", hover_color="darkgreen")
        self.print_button.pack(side="left", padx=5)
        
        # Third row - Controls
        button_row3 = ctk.CTkFrame(button_frame)
        button_row3.pack(fill="x", pady=5)
        
        # RAG Toggle Controls
        rag_control_frame = ctk.CTkFrame(button_row3)
        rag_control_frame.pack(side="left", padx=5)
        
        self.rag_label = ctk.CTkLabel(rag_control_frame, text="🧠 RAG:")
        self.rag_label.pack(side="left", padx=(10, 5))
        
        self.rag_toggle = ctk.CTkSwitch(rag_control_frame, text="", 
                                       command=self.toggle_rag_mode, width=50)
        self.rag_toggle.pack(side="left", padx=(0, 5))
        self.rag_toggle.select()
        
        self.rag_status_label = ctk.CTkLabel(rag_control_frame, text="ON", 
                                            text_color="green", font=ctk.CTkFont(weight="bold"))
        self.rag_status_label.pack(side="left", padx=(0, 10))
        
        # Info and New buttons
        self.rag_info_button = ctk.CTkButton(button_row3, text="🧠 RAG Info", 
                                            command=self.show_enhanced_rag_info, width=100)
        self.rag_info_button.pack(side="left", padx=5)
        
        self.new_button = ctk.CTkButton(button_row3, text="🔄 New Design", 
                                       command=self.new_conversation)
        self.new_button.pack(side="right", padx=5)
    
    def _setup_printing_interface(self):
        """Setup the 3D printing control interface"""
        # 3D Printing Panel Header
        print_header = ctk.CTkLabel(self.printing_frame, text="🖨️ 3D Printing Pipeline", 
                                   font=ctk.CTkFont(size=16, weight="bold"))
        print_header.pack(pady=10)
        
        # Printer Status Section
        status_frame = ctk.CTkFrame(self.printing_frame)
        status_frame.pack(fill="x", padx=10, pady=5)
        
        status_label = ctk.CTkLabel(status_frame, text="Printer Status", 
                                   font=ctk.CTkFont(weight="bold"))
        status_label.pack(pady=5)
        
        self.printer_status_display = ctk.CTkTextbox(status_frame, height=120)
        self.printer_status_display.pack(fill="x", padx=5, pady=5)
        
        # Status refresh button
        refresh_button = ctk.CTkButton(status_frame, text="🔄 Refresh Status", 
                                      command=self.refresh_printer_status, height=30)
        refresh_button.pack(pady=5)
        
        # Slicing Options Section
        slice_frame = ctk.CTkFrame(self.printing_frame)
        slice_frame.pack(fill="x", padx=10, pady=5)
        
        slice_label = ctk.CTkLabel(slice_frame, text="Slicing Options", 
                                  font=ctk.CTkFont(weight="bold"))
        slice_label.pack(pady=5)
        
        # Profile selection
        profile_row = ctk.CTkFrame(slice_frame)
        profile_row.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkLabel(profile_row, text="Profile:").pack(side="left", padx=5)
        
        self.profile_var = ctk.StringVar(value="standard")
        self.profile_menu = ctk.CTkOptionMenu(profile_row, 
                                             values=["draft", "standard", "fine", "vase"],
                                             variable=self.profile_var)
        self.profile_menu.pack(side="right", padx=5)
        
        # Layer height
        layer_row = ctk.CTkFrame(slice_frame)
        layer_row.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkLabel(layer_row, text="Layer Height:").pack(side="left", padx=5)
        
        self.layer_height_var = ctk.StringVar(value="0.2")
        layer_entry = ctk.CTkEntry(layer_row, textvariable=self.layer_height_var, width=60)
        layer_entry.pack(side="right", padx=5)
        
        # Infill
        infill_row = ctk.CTkFrame(slice_frame)
        infill_row.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkLabel(infill_row, text="Infill %:").pack(side="left", padx=5)
        
        self.infill_var = ctk.StringVar(value="20")
        infill_entry = ctk.CTkEntry(infill_row, textvariable=self.infill_var, width=60)
        infill_entry.pack(side="right", padx=5)
        
        # Supports checkbox
        self.supports_var = ctk.BooleanVar(value=True)
        supports_check = ctk.CTkCheckBox(slice_frame, text="Auto Supports", 
                                        variable=self.supports_var)
        supports_check.pack(pady=2)
        
        # Print Management Section
        print_mgmt_frame = ctk.CTkFrame(self.printing_frame)
        print_mgmt_frame.pack(fill="x", padx=10, pady=5)
        
        mgmt_label = ctk.CTkLabel(print_mgmt_frame, text="Print Management", 
                                 font=ctk.CTkFont(weight="bold"))
        mgmt_label.pack(pady=5)
        
        # Print control buttons
        control_row1 = ctk.CTkFrame(print_mgmt_frame)
        control_row1.pack(fill="x", padx=5, pady=2)
        
        self.preheat_button = ctk.CTkButton(control_row1, text="🔥 Preheat", 
                                           command=self.preheat_printer, height=30)
        self.preheat_button.pack(side="left", padx=2, fill="x", expand=True)
        
        self.pause_button = ctk.CTkButton(control_row1, text="⏸️ Pause", 
                                         command=self.pause_print, height=30)
        self.pause_button.pack(side="right", padx=2, fill="x", expand=True)
        
        control_row2 = ctk.CTkFrame(print_mgmt_frame)
        control_row2.pack(fill="x", padx=5, pady=2)
        
        self.resume_button = ctk.CTkButton(control_row2, text="▶️ Resume", 
                                          command=self.resume_print, height=30)
        self.resume_button.pack(side="left", padx=2, fill="x", expand=True)
        
        self.cancel_button = ctk.CTkButton(control_row2, text="❌ Cancel", 
                                          command=self.cancel_print, height=30,
                                          fg_color="red", hover_color="darkred")
        self.cancel_button.pack(side="right", padx=2, fill="x", expand=True)
        
        # File List Section
        files_frame = ctk.CTkFrame(self.printing_frame)
        files_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        files_label = ctk.CTkLabel(files_frame, text="Printer Files", 
                                  font=ctk.CTkFont(weight="bold"))
        files_label.pack(pady=5)
        
        self.files_display = ctk.CTkTextbox(files_frame, height=100)
        self.files_display.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Refresh files button
        refresh_files_button = ctk.CTkButton(files_frame, text="📁 Refresh Files", 
                                           command=self.refresh_printer_files, height=30)
        refresh_files_button.pack(pady=5)
        
        # Initialize printer status
        self.refresh_printer_status()
        
        # Start periodic status updates
        self._start_status_updates()
    
    def toggle_rag_mode(self):
        """Toggle RAG mode on/off"""
        rag_enabled = self.rag_toggle.get()
        
        if hasattr(self, 'generator'):
            self.generator.set_rag_enabled(rag_enabled)

        if hasattr(self, 'assistant'):
            self.assistant.rag_generator = self.generator if rag_enabled else None
        
        # Update visual indicators
        if rag_enabled:
            self.rag_status_label.configure(text="ON", text_color="green")
            status_text = "🧠 Enhanced RAG enabled - will use examples when relevant"
            self.rag_info_button.configure(text="🧠 RAG Info")
        else:
            self.rag_status_label.configure(text="OFF", text_color="red")
            status_text = "🤖 RAG disabled - using intelligent reasoning only"
            self.rag_info_button.configure(text="🤖 Pure AI Info")
        
        self.status.configure(text=status_text)
        self._add_message("System", f"🔄 Mode changed: {'Enhanced RAG + Intelligent Reasoning' if rag_enabled else 'Intelligent Reasoning Only'}")
    
    def _initialize_components(self):
        """Initialize Enhanced RAG + 3D Printing components"""
        try:
            model_name = os.getenv('DEFAULT_MODEL', 'llama3.1:8b')
            performance_mode = os.getenv('PERFORMANCE_MODE', 'balanced')
            
            # Initialize LLM engine
            llm_engine = LLMEngine(model_name, performance_mode)
            
            # Initialize Enhanced components with 3D printing
            self.generator = EnhancedRAGCADGenerator(llm_engine)
            self.assistant = IntelligentConversationAssistant(llm_engine, self.generator)
            self.exporter = ModelExporter(os.getenv('EXPORT_DIRECTORY', './exports'))
            
            # Set initial RAG state
            self.generator.set_rag_enabled(self.rag_toggle.get())
            
            stats = self.generator.get_enhanced_rag_stats()
            
            # Check 3D printing availability
            printing_available = (hasattr(self.exporter, 'slicer') and self.exporter.slicer is not None and
                                hasattr(self.exporter, 'mainsail') and self.exporter.mainsail is not None)
            
            print(f"✅ Enhanced RAG + 3D Printing system initialized:")
            print(f"   LLM: {model_name} ({performance_mode})")
            print(f"   References: {stats['total_references']}")
            print(f"   3D Printing: {'✅ Available' if printing_available else '❌ Limited (check config)'}")
            
            if not printing_available:
                # Disable 3D printing buttons if not available
                self.slice_button.configure(state="disabled", text="🔄 Slice (Not Available)")
                self.print_button.configure(state="disabled", text="🖨️ Print (Not Available)")
                self._add_message("System", "⚠️ 3D printing features limited. Check PrusaSlicer and Mainsail configuration.")
            
            self._add_welcome_message()
            
        except Exception as e:
            messagebox.showerror("Initialization Error", f"Failed to start system: {e}")
    
    def _add_welcome_message(self):
        """Add Enhanced RAG + 3D Printing welcome message"""
        stats = self.generator.get_enhanced_rag_stats()
        printing_status = "✅ Ready" if (hasattr(self.exporter, 'slicer') and self.exporter.slicer) else "⚠️ Check Config"
        
        welcome = f"""🚀 Welcome to Enhanced RAG + AI Manufacturing + 3D Printing Pipeline!

🧠 **AI Generation System**:
• {stats['total_references']} hierarchical examples + intelligent reasoning
• Toggle RAG ON/OFF to compare approaches
• Automatic mode selection based on similarity

🖨️ **3D Printing Pipeline**: {printing_status}
• Integrated PrusaSlicer for G-code generation
• Mainsail/Klipper printer control
• Real-time status monitoring
• Complete CAD-to-part workflow

💡 **Full Workflow**:
1. "I need a 20-tooth gear" → AI generates CadQuery model
2. "Slice for printing" → Creates G-code with your settings  
3. "Send to printer" → Uploads and starts print
4. Monitor progress in real-time

🎯 **Example Commands**:
• "Make a phone stand for my device"
• "Create a 30mm diameter gear with 24 teeth"
• "Design a bracket to hold a 40mm fan"

Ready to go from conversation to physical part!"""
        
        self._add_message("AI Manufacturing Assistant", welcome)
    
    def show_enhanced_rag_info(self):
        """Show system information with 3D printing details"""
        if hasattr(self, 'generator'):
            stats = self.generator.get_enhanced_rag_stats()
            rag_enabled = self.rag_toggle.get()
            
            printing_info = ""
            if hasattr(self, 'exporter'):
                if self.exporter.slicer and self.exporter.mainsail:
                    printer_status = self.exporter.get_printer_status()
                    printing_info = f"""

🖨️ **3D Printing Status**:
• Slicer: ✅ PrusaSlicer Available
• Printer: ✅ Connected ({printer_status.get('state', 'unknown')})
• Bed Temp: {printer_status.get('bed_temp', 0):.1f}°C / {printer_status.get('bed_target', 0):.1f}°C
• Extruder: {printer_status.get('extruder_temp', 0):.1f}°C / {printer_status.get('extruder_target', 0):.1f}°C
• Ready: {'✅ Yes' if printer_status.get('ready', False) else '❌ No'}"""
                else:
                    printing_info = f"""

🖨️ **3D Printing Status**:
• Slicer: {'✅' if self.exporter.slicer else '❌'} PrusaSlicer
• Printer: {'✅' if self.exporter.mainsail else '❌'} Mainsail Connection
• Status: Configuration needed"""
            
            mode_desc = "Enhanced RAG + Intelligent Reasoning" if rag_enabled else "Intelligent Reasoning Only"
            
            info_text = f"""🚀 **AI Manufacturing + 3D Printing Pipeline**

🧠 **Current Mode**: {mode_desc}
• References: {stats['total_references']} available
• RAG Status: {'✅ Enabled' if rag_enabled else '❌ Disabled'}
• Last Generation: {stats['last_generation_mode'].replace('_', ' ').title()}

📊 **Complexity Distribution**:
{chr(10).join([f'• {k.title()}: {v} examples' for k, v in stats['complexity_distribution'].items()])}
{printing_info}

🔄 **Complete Workflow**:
1. **Chat** → Describe your part
2. **Generate** → AI creates CadQuery model  
3. **Export** → STL + STEP + Python code
4. **Slice** → Generate G-code for your printer
5. **Print** → Send to Mainsail/Klipper printer
6. **Monitor** → Real-time status updates

Toggle RAG ON/OFF to compare generation approaches!"""
            
            # Create info dialog
            dialog = ctk.CTkToplevel(self.root)
            dialog.title("🚀 AI Manufacturing + 3D Printing Pipeline Info")
            dialog.geometry("700x600")
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
        
        threading.Thread(target=self._process_message, args=(message,), daemon=True).start()
    
    def _process_message(self, message: str):
        """Process message with Enhanced RAG"""
        try:
            result = self.assistant.chat(message)
            self.root.after(0, self._handle_response, result)
        except Exception as e:
            self.root.after(0, self._handle_error, str(e))
    
    def _handle_response(self, result: dict):
        """Handle assistant response"""
        display_message = result['message']
        if 'GENERATE_MODEL:' in display_message:
            display_message = display_message.split('GENERATE_MODEL:')[0].strip()
        
        if display_message:
            self._add_message("AI Assistant", display_message)
        
        # Check if generation requested
        if result['generate_model']:
            self.status.configure(text="🧠 Generating model...")
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
        self._add_message("Error", f"❌ {error}")
        self.status.configure(text="❌ Error occurred")
        self.send_button.configure(state="normal")
    
    def _generate_model(self, spec: dict, code: str = None):
        """Generate 3D model"""
        try:
            model = self.generator.generate_model(spec, code)
            self.current_model = model
            self.root.after(0, self._handle_generation_success, spec)
        except Exception as e:
            self.root.after(0, self._handle_generation_error, str(e))
    
    def _handle_generation_success(self, spec: dict):
        """Handle successful generation with 3D printing readiness"""
        gen_info = self.generator.get_last_generation_info()
        rag_enabled = self.rag_toggle.get()
        
        if rag_enabled and gen_info['used_rag']:
            mode_text = f"Enhanced RAG ({gen_info['complexity_used']})"
        else:
            mode_text = "Intelligent Reasoning"
        
        message = f"✅ {mode_text} Generated {spec.get('object_type', 'model')}!\n\nReady for 3D printing pipeline:\n• View 3D model\n• Export files (STL/STEP/Code)\n• Slice for 3D printing\n• Send to printer"
        self._add_message("AI Assistant", message)
        
        self.status.configure(text="✅ Model ready for 3D printing!")
        
        # Enable all buttons
        self.view_button.configure(state="normal")
        self.export_button.configure(state="normal") 
        self.copy_button.configure(state="normal")
        
        # Enable 3D printing buttons if available
        if hasattr(self.exporter, 'slicer') and self.exporter.slicer:
            self.slice_button.configure(state="disabled")  # Need STL first
    
    def _handle_generation_error(self, error: str):
        """Handle generation error"""
        code = self.generator.get_last_code()
        message = f"❌ Generation failed: {error}\n\n💻 Code available for manual use."
        self._add_message("AI Assistant", message)
        self.status.configure(text="❌ Generation failed")
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
            self.status.configure(text="💾 Exporting files...")
            threading.Thread(target=self._export_in_background, daemon=True).start()
    
    def _export_in_background(self):
        """Export in background"""
        try:
            cadquery_code = self.generator.get_last_code()
            result = self.exporter.export_model(self.current_model, self.current_spec, cadquery_code)
            self.current_stl_path = result['stl_path']
            self.root.after(0, self._handle_export_success, result)
        except Exception as e:
            self.root.after(0, self._handle_export_error, str(e))
    
    def _handle_export_success(self, result: dict):
        """Handle successful export"""
        files = result['files']
        message = f"💾 Export successful!\n\n{chr(10).join([f'• {fmt}: {Path(path).name}' for fmt, path in files.items()])}\n\n✅ Ready for 3D printing pipeline!"
        self._add_message("AI Assistant", message)
        self.status.configure(text="✅ Files exported - ready for slicing!")
        
        # Enable slicing if available
        if hasattr(self.exporter, 'slicer') and self.exporter.slicer and self.current_stl_path:
            self.slice_button.configure(state="normal", text="🔄 Slice for 3D Printing")
    
    def _handle_export_error(self, error: str):
        """Handle export error"""
        self._add_message("AI Assistant", f"❌ Export failed: {error}")
        self.status.configure(text="❌ Export failed")
    
    def copy_code(self):
        """Copy generated code to clipboard"""
        code = self.generator.get_last_code()
        if code:
            self.root.clipboard_clear()
            self.root.clipboard_append(code)
            self.status.configure(text="📋 Code copied!")
    
    def slice_model(self):
        """Slice model for 3D printing"""
        if not self.current_stl_path or not hasattr(self.exporter, 'slicer'):
            messagebox.showerror("Slicing Error", "No STL file available or slicer not configured")
            return
        
        self.status.configure(text="🔄 Slicing model...")
        self.slice_button.configure(state="disabled", text="🔄 Slicing...")
        
        # Get custom settings from UI
        custom_settings = {}
        try:
            if self.layer_height_var.get() != "0.2":
                custom_settings['layer-height'] = float(self.layer_height_var.get())
            if self.infill_var.get() != "20":
                custom_settings['fill-density'] = f"{self.infill_var.get()}%"
            if not self.supports_var.get():
                custom_settings['support-material'] = '0'
        except ValueError:
            pass  # Use defaults if invalid input
        
        threading.Thread(target=self._slice_in_background, 
                        args=(self.profile_var.get(), custom_settings), daemon=True).start()
    
    def _slice_in_background(self, profile: str, custom_settings: dict):
        """Slice in background"""
        try:
            result = self.exporter.slice_model(self.current_stl_path, profile, custom_settings)
            self.root.after(0, self._handle_slice_result, result)
        except Exception as e:
            self.root.after(0, self._handle_slice_error, str(e))
    
    def _handle_slice_result(self, result: dict):
        """Handle slicing result"""
        self.slice_button.configure(state="normal", text="🔄 Slice for 3D Printing")
        
        if result['success']:
            self.current_gcode_path = result['gcode_path']
            message = f"✅ Slicing complete!\n\n• Profile: {result['profile_used']}\n• Print time: {result['estimated_print_time']}\n• Filament: {result['estimated_filament_mm']:.1f}mm\n• File: {result['gcode_filename']}\n\n🖨️ Ready to send to printer!"
            self._add_message("3D Printing", message)
            self.status.configure(text="✅ G-code ready for printing!")
            
            # Enable print button if printer available
            if hasattr(self.exporter, 'mainsail') and self.exporter.mainsail:
                self.print_button.configure(state="normal", text="🖨️ Send to Printer")
        else:
            self._handle_slice_error(result['error'])
    
    def _handle_slice_error(self, error: str):
        """Handle slicing error"""
        self.slice_button.configure(state="normal", text="🔄 Slice for 3D Printing")
        self._add_message("3D Printing", f"❌ Slicing failed: {error}")
        self.status.configure(text="❌ Slicing failed")
    
    def send_to_printer(self):
        """Send G-code to printer"""
        if not self.current_gcode_path or not hasattr(self.exporter, 'mainsail'):
            messagebox.showerror("Print Error", "No G-code file or printer not configured")
            return
        
        # Confirmation dialog
        if os.getenv('CONFIRM_BEFORE_PRINT', 'true').lower() == 'true':
            if not messagebox.askyesno("Confirm Print", 
                                     f"Send to printer and start printing?\n\nFile: {Path(self.current_gcode_path).name}"):
                return
        
        self.status.configure(text="📤 Sending to printer...")
        self.print_button.configure(state="disabled", text="📤 Uploading...")
        
        threading.Thread(target=self._print_in_background, daemon=True).start()
    
    def _print_in_background(self):
        """Upload and print in background"""
        try:
            result = self.exporter.upload_and_print(self.current_gcode_path, start_immediately=True)
            self.root.after(0, self._handle_print_result, result)
        except Exception as e:
            self.root.after(0, self._handle_print_error, str(e))
    
    def _handle_print_result(self, result: dict):
        """Handle print result"""
        self.print_button.configure(state="normal", text="🖨️ Send to Printer")
        
        if result.get('upload_success', False):
            if result.get('success', False):  # Print started
                message = f"✅ Print started!\n\n• File uploaded: {result['filename']}\n• Size: {result['size_mb']:.1f} MB\n• Status: Printing\n\n📊 Monitor progress in printer status panel."
                self._add_message("3D Printing", message)
                self.status.configure(text="🖨️ Print started - monitoring...")
            else:
                message = f"📤 File uploaded successfully!\n\n• File: {result['filename']}\n• Ready to print manually"
                self._add_message("3D Printing", message) 
                self.status.configure(text="📤 Uploaded - ready to print")
        else:
            self._handle_print_error(result.get('error', 'Upload failed'))
    
    def _handle_print_error(self, error: str):
        """Handle print error"""
        self.print_button.configure(state="normal", text="🖨️ Send to Printer")
        self._add_message("3D Printing", f"❌ Print failed: {error}")
        self.status.configure(text="❌ Print failed")
    
    def refresh_printer_status(self):
        """Refresh printer status display"""
        if not hasattr(self.exporter, 'mainsail') or not self.exporter.mainsail:
            self.printer_status_display.delete("1.0", "end")
            self.printer_status_display.insert("1.0", "❌ Printer not connected\nCheck Mainsail configuration")
            return
        
        threading.Thread(target=self._get_status_in_background, daemon=True).start()
    
    def _get_status_in_background(self):
        """Get printer status in background"""
        try:
            status = self.exporter.get_printer_status()
            self.root.after(0, self._update_status_display, status)
        except Exception as e:
            self.root.after(0, lambda: self._update_status_display({'error': str(e)}))
    
    def _update_status_display(self, status: dict):
        """Update status display"""
        self.printer_status_display.delete("1.0", "end")
        
        if 'error' in status:
            self.printer_status_display.insert("1.0", f"❌ Status Error:\n{status['error']}")
            return
        
        status_text = f"""🖨️ Printer Status: {status.get('state', 'unknown').upper()}

🌡️ Temperatures:
• Extruder: {status.get('extruder_temp', 0):.1f}°C / {status.get('extruder_target', 0):.1f}°C
• Bed: {status.get('bed_temp', 0):.1f}°C / {status.get('bed_target', 0):.1f}°C
• Chamber: {status.get('chamber_temp', 0):.1f}°C

📊 Progress: {status.get('progress', 0)*100:.1f}%
⏱️ Print Time: {status.get('print_time', 'N/A')}
📄 Current: {status.get('current_file', 'None')}

✅ Ready: {'Yes' if status.get('ready', False) else 'No'}"""
        
        self.printer_status_display.insert("1.0", status_text)
    
    def refresh_printer_files(self):
        """Refresh printer files list"""
        if not hasattr(self.exporter, 'mainsail') or not self.exporter.mainsail:
            self.files_display.delete("1.0", "end")
            self.files_display.insert("1.0", "❌ Printer not connected")
            return
        
        threading.Thread(target=self._get_files_in_background, daemon=True).start()
    
    def _get_files_in_background(self):
        """Get printer files in background"""
        try:
            files = self.exporter.mainsail.get_file_list()
            self.root.after(0, self._update_files_display, files)
        except Exception as e:
            self.root.after(0, lambda: self._update_files_display([]))
    
    def _update_files_display(self, files: list):
        """Update files display"""
        self.files_display.delete("1.0", "end")
        
        if not files:
            self.files_display.insert("1.0", "📁 No G-code files found")
            return
        
        files_text = "📁 Recent G-code Files:\n\n"
        for i, file in enumerate(files[:10]):  # Show top 10
            files_text += f"{i+1}. {file['filename']}\n   {file['size_mb']:.1f} MB\n\n"
        
        self.files_display.insert("1.0", files_text)
    
    # Printer control methods
    def preheat_printer(self):
        """Preheat printer"""
        if hasattr(self.exporter, 'mainsail') and self.exporter.mainsail:
            threading.Thread(target=self._preheat_in_background, daemon=True).start()
    
    def _preheat_in_background(self):
        try:
            result = self.exporter.mainsail.preheat_printer()
            message = "🔥 Preheat started" if result['success'] else f"❌ Preheat failed: {result['error']}"
            self.root.after(0, lambda: self._add_message("Printer", message))
        except Exception as e:
            self.root.after(0, lambda: self._add_message("Printer", f"❌ Preheat error: {e}"))
    
    def pause_print(self):
        """Pause current print"""
        if hasattr(self.exporter, 'mainsail') and self.exporter.mainsail:
            threading.Thread(target=self._pause_in_background, daemon=True).start()
    
    def _pause_in_background(self):
        try:
            result = self.exporter.mainsail.pause_print()
            message = "⏸️ Print paused" if result['success'] else f"❌ Pause failed: {result['error']}"
            self.root.after(0, lambda: self._add_message("Printer", message))
        except Exception as e:
            self.root.after(0, lambda: self._add_message("Printer", f"❌ Pause error: {e}"))
    
    def resume_print(self):
        """Resume paused print"""
        if hasattr(self.exporter, 'mainsail') and self.exporter.mainsail:
            threading.Thread(target=self._resume_in_background, daemon=True).start()
    
    def _resume_in_background(self):
        try:
            result = self.exporter.mainsail.resume_print()
            message = "▶️ Print resumed" if result['success'] else f"❌ Resume failed: {result['error']}"
            self.root.after(0, lambda: self._add_message("Printer", message))
        except Exception as e:
            self.root.after(0, lambda: self._add_message("Printer", f"❌ Resume error: {e}"))
    
    def cancel_print(self):
        """Cancel current print with confirmation"""
        if messagebox.askyesno("Confirm Cancel", "Are you sure you want to cancel the current print?"):
            if hasattr(self.exporter, 'mainsail') and self.exporter.mainsail:
                threading.Thread(target=self._cancel_in_background, daemon=True).start()
    
    def _cancel_in_background(self):
        try:
            result = self.exporter.mainsail.cancel_print()
            message = "❌ Print cancelled" if result['success'] else f"❌ Cancel failed: {result['error']}"
            self.root.after(0, lambda: self._add_message("Printer", message))
        except Exception as e:
            self.root.after(0, lambda: self._add_message("Printer", f"❌ Cancel error: {e}"))
    
    def _start_status_updates(self):
        """Start periodic printer status updates"""
        def update_status():
            if hasattr(self.exporter, 'mainsail') and self.exporter.mainsail:
                self.refresh_printer_status()
            # Schedule next update in 10 seconds
            self.printer_status_timer = self.root.after(10000, update_status)
        
        # Start updates
        self.root.after(2000, update_status)  # First update after 2 seconds
    
    def new_conversation(self):
        """Start new conversation"""
        if messagebox.askyesno("New Design", "Start new design? Current conversation will be lost."):
            self.assistant.reset()
            self.chat_display.delete("1.0", "end")
            self._add_welcome_message()
            self.current_model = None
            self.current_spec = None
            self.current_stl_path = None
            self.current_gcode_path = None
            
            # Reset buttons
            self.view_button.configure(state="disabled")
            self.export_button.configure(state="disabled")
            self.copy_button.configure(state="disabled")
            self.slice_button.configure(state="disabled", text="🔄 Slice for 3D Printing")
            self.print_button.configure(state="disabled", text="🖨️ Send to Printer")
            
            self.status.configure(text="Ready for new AI Manufacturing + 3D Printing project...")
    
    def run(self):
        """Start the Enhanced application with 3D printing"""
        try:
            self.root.mainloop()
        finally:
            # Cleanup
            if self.printer_status_timer:
                self.root.after_cancel(self.printer_status_timer)
