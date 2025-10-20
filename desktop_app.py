# interfaces/desktop_app_simplified.py
"""Simplified RAG + AI Manufacturing Desktop Application - Separate Upload and Start"""
import customtkinter as ctk
import threading
import os
from datetime import datetime
from tkinter import messagebox, simpledialog
from pathlib import Path
from dotenv import load_dotenv

from src.llm_engine import LLMEngine
from src.assistant_llama import IntelligentConversationAssistant
from src.generation.RAG_generator_llama import EnhancedRAGCADGenerator
from src.generation.export import ModelExporter

load_dotenv()

class EnhancedDesktopApp:
    def __init__(self):
        self._setup_ui()
        self._initialize_components()
        self.current_model = None
        self.current_spec = None
        self.current_stl_path = None
        self.current_gcode_path = None
        self.uploaded_filename = None  # Track uploaded file for starting
        self.printer_status_timer = None
    
    def _setup_ui(self):
        """Initialize the enhanced user interface"""
        ctk.set_appearance_mode(os.getenv('THEME', 'dark'))
        ctk.set_default_color_theme("blue")
        
        window_size = os.getenv('WINDOW_SIZE', '1100x800')
        
        self.root = ctk.CTk()
        self.root.title("Enhanced RAG + AI Manufacturing + 3D Printing Pipeline")
        self.root.geometry(window_size)
        
        header = ctk.CTkLabel(self.root, text="AI Manufacturing → 3D Printing Pipeline", 
                             font=ctk.CTkFont(size=20, weight="bold"))
        header.pack(pady=10)
        
        main_container = ctk.CTkFrame(self.root)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        left_frame = ctk.CTkFrame(main_container)
        left_frame.pack(side="left", fill="both", expand=True, padx=5)
        
        self.printing_frame = ctk.CTkFrame(main_container, width=350)
        self.printing_frame.pack(side="right", fill="y", padx=5)
        self.printing_frame.pack_propagate(False)
        
        self._setup_chat_interface(left_frame)
        self._setup_simplified_printing_interface()
        
        self.status = ctk.CTkLabel(self.root, text="Ready for AI Manufacturing + 3D Printing...")
        self.status.pack(pady=5)
    
    def _setup_chat_interface(self, parent):
        """Setup the chat interface"""
        self.chat_display = ctk.CTkTextbox(parent, height=400)
        self.chat_display.pack(fill="both", expand=True, padx=10, pady=10)
        
        input_frame = ctk.CTkFrame(parent)
        input_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.message_entry = ctk.CTkEntry(input_frame, placeholder_text="Describe what you want to design...")
        self.message_entry.pack(side="left", fill="x", expand=True, padx=10, pady=10)
        self.message_entry.bind("<Return>", self.send_message)
        
        self.send_button = ctk.CTkButton(input_frame, text="Send", command=self.send_message, width=80)
        self.send_button.pack(side="right", padx=10, pady=10)
        
        button_frame = ctk.CTkFrame(parent)
        button_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # First row
        button_row1 = ctk.CTkFrame(button_frame)
        button_row1.pack(fill="x", pady=5)
        
        self.view_button = ctk.CTkButton(button_row1, text="View 3D", 
                                        command=self.view_model, state="disabled")
        self.view_button.pack(side="left", padx=5)
        
        self.export_button = ctk.CTkButton(button_row1, text="Export Files", 
                                          command=self.export_model, state="disabled")
        self.export_button.pack(side="left", padx=5)
        
        self.copy_button = ctk.CTkButton(button_row1, text="Copy Code", 
                                        command=self.copy_code, state="disabled")
        self.copy_button.pack(side="left", padx=5)
        
        # Second row - 3D Printing
        button_row2 = ctk.CTkFrame(button_frame)
        button_row2.pack(fill="x", pady=5)
        
        self.slice_button = ctk.CTkButton(button_row2, text="Slice for 3D Printing", 
                                         command=self.slice_model, state="disabled",
                                         fg_color="orange", hover_color="darkorange")
        self.slice_button.pack(side="left", padx=5)
        
        # NEW: Separate upload and start buttons
        self.upload_button = ctk.CTkButton(button_row2, text="Upload to Printer", 
                                          command=self.upload_to_printer, state="disabled",
                                          fg_color="blue", hover_color="darkblue")
        self.upload_button.pack(side="left", padx=5)
        
        self.start_print_button = ctk.CTkButton(button_row2, text="Start Print", 
                                               command=self.start_print, state="disabled",
                                               fg_color="green", hover_color="darkgreen")
        self.start_print_button.pack(side="left", padx=5)
        
        # Third row - Controls
        button_row3 = ctk.CTkFrame(button_frame)
        button_row3.pack(fill="x", pady=5)
        
        rag_control_frame = ctk.CTkFrame(button_row3)
        rag_control_frame.pack(side="left", padx=5)
        
        self.rag_label = ctk.CTkLabel(rag_control_frame, text="RAG:")
        self.rag_label.pack(side="left", padx=(10, 5))
        
        self.rag_toggle = ctk.CTkSwitch(rag_control_frame, text="", 
                                       command=self.toggle_rag_mode, width=50)
        self.rag_toggle.pack(side="left", padx=(0, 5))
        self.rag_toggle.select()
        
        self.rag_status_label = ctk.CTkLabel(rag_control_frame, text="ON", 
                                            text_color="green", font=ctk.CTkFont(weight="bold"))
        self.rag_status_label.pack(side="left", padx=(0, 10))
        
        self.rag_info_button = ctk.CTkButton(button_row3, text="RAG Info", 
                                            command=self.show_enhanced_rag_info, width=100)
        self.rag_info_button.pack(side="left", padx=5)
        
        self.new_button = ctk.CTkButton(button_row3, text="New Design", 
                                       command=self.new_conversation)
        self.new_button.pack(side="right", padx=5)
    
    def _setup_simplified_printing_interface(self):
        """Setup simplified 3D printing interface"""
        print_header = ctk.CTkLabel(self.printing_frame, text="3D Printing Pipeline", 
                                   font=ctk.CTkFont(size=16, weight="bold"))
        print_header.pack(pady=10)
        
        # Printer Status
        status_frame = ctk.CTkFrame(self.printing_frame)
        status_frame.pack(fill="x", padx=10, pady=5)
        
        status_label = ctk.CTkLabel(status_frame, text="Printer Status", 
                                   font=ctk.CTkFont(weight="bold"))
        status_label.pack(pady=5)
        
        self.printer_status_display = ctk.CTkTextbox(status_frame, height=100)
        self.printer_status_display.pack(fill="x", padx=5, pady=5)
        
        refresh_button = ctk.CTkButton(status_frame, text="Refresh Status", 
                                      command=self.refresh_printer_status, height=30)
        refresh_button.pack(pady=5)
        
        # Slicing Options
        slice_frame = ctk.CTkFrame(self.printing_frame)
        slice_frame.pack(fill="x", padx=10, pady=5)
        
        slice_label = ctk.CTkLabel(slice_frame, text="Slicing Options", 
                                  font=ctk.CTkFont(weight="bold"))
        slice_label.pack(pady=5)
        
        profile_row = ctk.CTkFrame(slice_frame)
        profile_row.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkLabel(profile_row, text="Profile:").pack(side="left", padx=5)
        
        self.profile_var = ctk.StringVar(value="0.3mm_0.4nozzle_v2_optimised")
        self.profile_menu = ctk.CTkOptionMenu(profile_row, 
                                             values=["0.3mm_0.4nozzle_v2_optimised"],
                                             variable=self.profile_var)
        self.profile_menu.pack(side="right", padx=5)
        
        layer_row = ctk.CTkFrame(slice_frame)
        layer_row.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkLabel(layer_row, text="Layer Height:").pack(side="left", padx=5)
        self.layer_height_var = ctk.StringVar(value="0.3")
        layer_entry = ctk.CTkEntry(layer_row, textvariable=self.layer_height_var, width=60)
        layer_entry.pack(side="right", padx=5)
        
        infill_row = ctk.CTkFrame(slice_frame)
        infill_row.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkLabel(infill_row, text="Infill %:").pack(side="left", padx=5)
        self.infill_var = ctk.StringVar(value="5")
        infill_entry = ctk.CTkEntry(infill_row, textvariable=self.infill_var, width=60)
        infill_entry.pack(side="right", padx=5)
        
        self.supports_var = ctk.BooleanVar(value=True)
        supports_check = ctk.CTkCheckBox(slice_frame, text="Auto Supports", 
                                        variable=self.supports_var)
        supports_check.pack(pady=2)
        
        # Print Management
        print_mgmt_frame = ctk.CTkFrame(self.printing_frame)
        print_mgmt_frame.pack(fill="x", padx=10, pady=5)
        
        mgmt_label = ctk.CTkLabel(print_mgmt_frame, text="Print Management", 
                                 font=ctk.CTkFont(weight="bold"))
        mgmt_label.pack(pady=5)
        
        info_text = ctk.CTkLabel(print_mgmt_frame, 
                                text="1. Upload G-code to printer\n2. Click Start Print when ready",
                                font=ctk.CTkFont(size=12))
        info_text.pack(pady=5)
        
        # File List
        files_frame = ctk.CTkFrame(self.printing_frame)
        files_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        files_label = ctk.CTkLabel(files_frame, text="Printer Files", 
                                  font=ctk.CTkFont(weight="bold"))
        files_label.pack(pady=5)
        
        self.files_display = ctk.CTkTextbox(files_frame, height=120)
        self.files_display.pack(fill="both", expand=True, padx=5, pady=5)
        
        refresh_files_button = ctk.CTkButton(files_frame, text="Refresh Files", 
                                           command=self.refresh_printer_files, height=30)
        refresh_files_button.pack(pady=5)
    
    def toggle_rag_mode(self):
        """Toggle RAG mode"""
        rag_enabled = self.rag_toggle.get()
        
        if hasattr(self, 'generator'):
            self.generator.set_rag_enabled(rag_enabled)
        if hasattr(self, 'assistant'):
            self.assistant.rag_generator = self.generator if rag_enabled else None
        
        if rag_enabled:
            self.rag_status_label.configure(text="ON", text_color="green")
            status_text = "Enhanced RAG enabled"
        else:
            self.rag_status_label.configure(text="OFF", text_color="red")
            status_text = "RAG disabled"
        
        self.status.configure(text=status_text)
        self._add_message("System", f"Mode: {'Enhanced RAG' if rag_enabled else 'Intelligent Reasoning Only'}")
    
    def _initialize_components(self):
        """Initialize components"""
        try:
            model_name = os.getenv('DEFAULT_MODEL', 'llama3.1:8b')
            performance_mode = os.getenv('PERFORMANCE_MODE', 'balanced')
            
            llm_engine = LLMEngine(model_name, performance_mode)
            self.generator = EnhancedRAGCADGenerator(llm_engine)
            self.assistant = IntelligentConversationAssistant(llm_engine, self.generator)
            self.exporter = ModelExporter(os.getenv('EXPORT_DIRECTORY', './exports'))
            
            self.generator.set_rag_enabled(self.rag_toggle.get())
            
            stats = self.generator.get_enhanced_rag_stats()
            slicer_available = (hasattr(self.exporter, 'slicer') and self.exporter.slicer is not None)
            mainsail_available = (hasattr(self.exporter, 'mainsail') and self.exporter.mainsail is not None)
            
            print(f"Enhanced RAG + 3D Printing system initialized:")
            print(f"   LLM: {model_name} ({performance_mode})")
            print(f"   References: {stats['total_references']}")
            print(f"   PrusaSlicer: {'Available' if slicer_available else 'Not available'}")
            print(f"   Mainsail: {'Available' if mainsail_available else 'Not available'}")
            
            if not slicer_available:
                self.slice_button.configure(state="disabled", text="Slice (No Slicer)")
                self.upload_button.configure(state="disabled", text="Upload (No Slicer)")
                self._add_message("System", "PrusaSlicer not available")
            elif not mainsail_available:
                self.upload_button.configure(state="disabled", text="Upload (No Printer)")
                self.start_print_button.configure(state="disabled", text="Start (No Printer)")
                self._add_message("System", "Slicing available. Printer not connected")
            else:
                self._add_message("System", "Full 3D printing pipeline ready!")
            
            self._initialize_printer_interface()
                
        except Exception as e:
            messagebox.showerror("Initialization Error", f"Failed: {e}")
    
    def _initialize_printer_interface(self):
        """Initialize printer interface"""
        self.refresh_printer_status()
        self._start_status_updates()
    
    def _add_message(self, sender: str, message: str):
        """Add message to chat"""
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
        self.status.configure(text="Thinking...")
        self.send_button.configure(state="disabled")
        
        threading.Thread(target=self._process_message, args=(message,), daemon=True).start()
    
    def _process_message(self, message: str):
        """Process message"""
        try:
            result = self.assistant.chat(message)
            self.root.after(0, self._handle_response, result)
        except Exception as e:
            self.root.after(0, self._handle_error, str(e))
    
    def _handle_response(self, result: dict):
        """Handle response"""
        display_message = result['message']
        if 'GENERATE_MODEL:' in display_message:
            display_message = display_message.split('GENERATE_MODEL:')[0].strip()
        
        if display_message:
            self._add_message("AI Assistant", display_message)
        
        if result['generate_model']:
            self.status.configure(text="Generating model...")
            self.current_spec = result['model_spec']
            threading.Thread(
                target=self._generate_model,
                args=(result['model_spec'], result['cadquery_code']),
                daemon=True
            ).start()
        else:
            self.status.configure(text="Continue chatting...")
        
        self.send_button.configure(state="normal")
    
    def _handle_error(self, error: str):
        """Handle error"""
        self._add_message("Error", f"Error: {error}")
        self.status.configure(text="Error occurred")
        self.send_button.configure(state="normal")
    
    def _generate_model(self, spec: dict, code: str = None):
        """Generate model"""
        try:
            model = self.generator.generate_model(spec, code)
            self.current_model = model
            self.root.after(0, self._handle_generation_success, spec)
        except Exception as e:
            self.root.after(0, self._handle_generation_error, str(e))
    
    def _handle_generation_success(self, spec: dict):
        """Handle generation success"""
        gen_info = self.generator.get_last_generation_info()
        rag_enabled = self.rag_toggle.get()
        
        mode_text = f"Enhanced RAG ({gen_info['complexity_used']})" if (rag_enabled and gen_info['used_rag']) else "Intelligent Reasoning"
        
        message = f"Generated {spec.get('object_type', 'model')} using {mode_text}!\n\nReady for 3D printing pipeline"
        self._add_message("AI Assistant", message)
        
        self.status.configure(text="Model ready!")
        
        self.view_button.configure(state="normal")
        self.export_button.configure(state="normal") 
        self.copy_button.configure(state="normal")
        
        if hasattr(self.exporter, 'slicer') and self.exporter.slicer:
            self.slice_button.configure(state="disabled")
    
    def _handle_generation_error(self, error: str):
        """Handle generation error"""
        self._add_message("AI Assistant", f"Generation failed: {error}")
        self.status.configure(text="Generation failed")
        self.copy_button.configure(state="normal")
    
    def view_model(self):
        """View model"""
        if self.current_model:
            self.status.configure(text="Opening 3D viewer...")
            threading.Thread(target=self._view_in_background, daemon=True).start()
    
    def _view_in_background(self):
        """View in background"""
        try:
            self.generator.visualize(self.current_model)
            self.root.after(0, lambda: self.status.configure(text="3D viewer opened"))
        except Exception as e:
            self.root.after(0, lambda: self.status.configure(text=f"View failed: {e}"))
    
    def export_model(self):
        """Export model"""
        if self.current_model and self.current_spec:
            self.status.configure(text="Exporting files...")
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
        """Handle export success"""
        files = result['files']
        message = f"Export successful!\n\n{chr(10).join([f'• {fmt}: {Path(path).name}' for fmt, path in files.items()])}\n\nReady for slicing!"
        self._add_message("AI Assistant", message)
        self.status.configure(text="Files exported - ready for slicing!")
        
        if hasattr(self.exporter, 'slicer') and self.exporter.slicer and self.current_stl_path:
            self.slice_button.configure(state="normal", text="Slice for 3D Printing")
    
    def _handle_export_error(self, error: str):
        """Handle export error"""
        self._add_message("AI Assistant", f"Export failed: {error}")
        self.status.configure(text="Export failed")
    
    def copy_code(self):
        """Copy code"""
        code = self.generator.get_last_code()
        if code:
            self.root.clipboard_clear()
            self.root.clipboard_append(code)
            self.status.configure(text="Code copied!")
    
    def slice_model(self):
        """Slice model"""
        if not self.current_stl_path or not hasattr(self.exporter, 'slicer'):
            messagebox.showerror("Slicing Error", "No STL file or slicer not configured")
            return
        
        self.status.configure(text="Slicing...")
        self.slice_button.configure(state="disabled", text="Slicing...")
        
        custom_settings = {}
        try:
            if self.layer_height_var.get() != "0.3":
                custom_settings['layer-height'] = float(self.layer_height_var.get())
            if self.infill_var.get() != "20":
                custom_settings['fill-density'] = f"{self.infill_var.get()}%"
            if not self.supports_var.get():
                custom_settings['support-material'] = '0'
        except ValueError:
            pass
        
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
        """Handle slice result"""
        self.slice_button.configure(state="normal", text="Slice for 3D Printing")
        
        if result['success']:
            self.current_gcode_path = result['gcode_path']
            message = f"Slicing complete!\n\n• Profile: {result['profile_used']}\n• Print time: {result['estimated_print_time']}\n• Filament: {result['estimated_filament_mm']:.1f}mm\n• File: {result['gcode_filename']}\n\nReady to upload!"
            self._add_message("3D Printing", message)
            self.status.configure(text="G-code ready!")
            
            if hasattr(self.exporter, 'mainsail') and self.exporter.mainsail:
                self.upload_button.configure(state="normal", text="Upload to Printer")
        else:
            self._handle_slice_error(result['error'])
    
    def _handle_slice_error(self, error: str):
        """Handle slice error"""
        self.slice_button.configure(state="normal", text="Slice for 3D Printing")
        self._add_message("3D Printing", f"Slicing failed: {error}")
        self.status.configure(text="Slicing failed")
    
    def upload_to_printer(self):
        """Upload G-code to printer (does NOT start print)"""
        if not self.current_gcode_path or not hasattr(self.exporter, 'mainsail'):
            messagebox.showerror("Upload Error", "No G-code or printer not configured")
            return
        
        self.status.configure(text="Uploading to printer...")
        self.upload_button.configure(state="disabled", text="Uploading...")
        
        threading.Thread(target=self._upload_in_background, daemon=True).start()
    
    def _upload_in_background(self):
        """Upload in background"""
        try:
            # Upload ONLY - do not start print
            result = self.exporter.upload_and_print(self.current_gcode_path, start_immediately=False)
            self.root.after(0, self._handle_upload_result, result)
        except Exception as e:
            self.root.after(0, self._handle_upload_error, str(e))
    
    def _handle_upload_result(self, result: dict):
        """Handle upload result"""
        self.upload_button.configure(state="normal", text="Upload to Printer")
        
        if result.get('upload_success', False):
            self.uploaded_filename = result['filename']
            message = f"Upload successful!\n\n• File: {result['filename']}\n• Size: {result['size_mb']:.1f} MB\n\nReady to start print!"
            self._add_message("3D Printing", message)
            self.status.configure(text="Uploaded! Click 'Start Print' when ready")
            
            # Enable Start Print button
            self.start_print_button.configure(state="normal", text="Start Print")
        else:
            self._handle_upload_error(result.get('error', 'Upload failed'))
    
    def _handle_upload_error(self, error: str):
        """Handle upload error"""
        self.upload_button.configure(state="normal", text="Upload to Printer")
        self._add_message("3D Printing", f"Upload failed: {error}")
        self.status.configure(text="Upload failed")
    
    def start_print(self):
        """Start printing the uploaded file"""
        if not self.uploaded_filename or not hasattr(self.exporter, 'mainsail'):
            messagebox.showerror("Print Error", "No uploaded file or printer not configured")
            return
        
        # Confirmation
        if not messagebox.askyesno("Confirm Print", 
                                 f"Start printing?\n\nFile: {self.uploaded_filename}"):
            return
        
        self.status.configure(text="Starting print...")
        self.start_print_button.configure(state="disabled", text="Starting...")
        
        threading.Thread(target=self._start_print_in_background, daemon=True).start()
    
    def _start_print_in_background(self):
        """Start print in background"""
        try:
            success, message = self.exporter.mainsail.start_print(self.uploaded_filename)
            self.root.after(0, self._handle_start_print_result, success, message)
        except Exception as e:
            self.root.after(0, self._handle_start_print_error, str(e))
    
    def _handle_start_print_result(self, success: bool, message: str):
        """Handle start print result"""
        self.start_print_button.configure(state="normal", text="Start Print")
        
        if success:
            msg = f"Print started!\n\n• File: {self.uploaded_filename}\n\nMonitor via Mainsail interface"
            self._add_message("3D Printing", msg)
            self.status.configure(text="Print started!")
            self.uploaded_filename = None  # Clear after starting
            self.start_print_button.configure(state="disabled")
        else:
            self._add_message("3D Printing", f"Failed to start: {message}")
            self.status.configure(text="Start failed - try from Mainsail")
    
    def _handle_start_print_error(self, error: str):
        """Handle start print error"""
        self.start_print_button.configure(state="normal", text="Start Print")
        self._add_message("3D Printing", f"Start failed: {error}")
        self.status.configure(text="Start failed - try from Mainsail")
    
    def refresh_printer_status(self):
        """Refresh status"""
        if not hasattr(self, 'exporter') or not self.exporter:
            self.printer_status_display.delete("1.0", "end")
            self.printer_status_display.insert("1.0", "System initializing...")
            return
            
        if not hasattr(self.exporter, 'mainsail') or not self.exporter.mainsail:
            self.printer_status_display.delete("1.0", "end")
            self.printer_status_display.insert("1.0", "Printer not connected")
            return
        
        threading.Thread(target=self._get_status_in_background, daemon=True).start()
    
    def _get_status_in_background(self):
        """Get status in background"""
        try:
            status = self.exporter.get_printer_status()
            self.root.after(0, self._update_status_display, status)
        except Exception as e:
            self.root.after(0, lambda: self._update_status_display({'error': str(e)}))
    
    def _update_status_display(self, status: dict):
        """Update status display"""
        self.printer_status_display.delete("1.0", "end")
        
        if 'error' in status:
            self.printer_status_display.insert("1.0", f"Error:\n{status['error']}")
            return
        
        status_text = f"""Status: {status.get('state', 'unknown').upper()}

Temperatures:
• Extruder: {status.get('extruder_temp', 0):.1f}°C / {status.get('extruder_target', 0):.1f}°C
• Bed: {status.get('bed_temp', 0):.1f}°C / {status.get('bed_target', 0):.1f}°C

Ready: {'Yes' if status.get('ready', False) else 'No'}"""
        
        self.printer_status_display.insert("1.0", status_text)
    
    def refresh_printer_files(self):
        """Refresh files"""
        if not hasattr(self.exporter, 'mainsail') or not self.exporter.mainsail:
            self.files_display.delete("1.0", "end")
            self.files_display.insert("1.0", "Printer not connected")
            return
        
        threading.Thread(target=self._get_files_in_background, daemon=True).start()
    
    def _get_files_in_background(self):
        """Get files in background"""
        try:
            files = self.exporter.mainsail.get_file_list()
            self.root.after(0, self._update_files_display, files)
        except Exception as e:
            self.root.after(0, lambda: self._update_files_display([]))
    
    def _update_files_display(self, files: list):
        """Update files display"""
        self.files_display.delete("1.0", "end")
        
        if not files:
            self.files_display.insert("1.0", "No G-code files")
            return
        
        files_text = "Recent G-code Files:\n\n"
        for i, file in enumerate(files[:8]):
            size_mb = file.get('size', 0) / (1024 * 1024)
            files_text += f"{i+1}. {file.get('name', 'Unknown')}\n   {size_mb:.1f} MB\n\n"
        
        self.files_display.insert("1.0", files_text)
    
    def _start_status_updates(self):
        """Start periodic updates"""
        def update_status():
            if hasattr(self.exporter, 'mainsail') and self.exporter.mainsail:
                self.refresh_printer_status()
            self.printer_status_timer = self.root.after(15000, update_status)
        
        self.root.after(2000, update_status)
    
    def show_enhanced_rag_info(self):
        """Show info"""
        if hasattr(self, 'generator'):
            stats = self.generator.get_enhanced_rag_stats()
            rag_enabled = self.rag_toggle.get()
            
            mode_desc = "Enhanced RAG" if rag_enabled else "Intelligent Reasoning Only"
            
            info_text = f"""AI Manufacturing + 3D Printing Pipeline

Mode: {mode_desc}
• References: {stats['total_references']} available
• RAG Status: {'Enabled' if rag_enabled else 'Disabled'}

Workflow:
1. Chat → Describe your part
2. Generate → AI creates model  
3. Export → STL + STEP + Python
4. Slice → Generate G-code
5. Upload → Send to printer
6. Start → Begin printing

Separate upload and start gives you control!"""
            
            dialog = ctk.CTkToplevel(self.root)
            dialog.title("Pipeline Info")
            dialog.geometry("500x400")
            dialog.transient(self.root)
            
            text_widget = ctk.CTkTextbox(dialog)
            text_widget.pack(fill="both", expand=True, padx=20, pady=20)
            text_widget.insert("1.0", info_text)
            text_widget.configure(state="disabled")
    
    def new_conversation(self):
        """New conversation"""
        if messagebox.askyesno("New Design", "Start new? Current conversation will be lost."):
            self.assistant.reset()
            self.chat_display.delete("1.0", "end")
            self.current_model = None
            self.current_spec = None
            self.current_stl_path = None
            self.current_gcode_path = None
            self.uploaded_filename = None
            
            self.view_button.configure(state="disabled")
            self.export_button.configure(state="disabled")
            self.copy_button.configure(state="disabled")
            self.slice_button.configure(state="disabled")
            self.upload_button.configure(state="disabled")
            self.start_print_button.configure(state="disabled")
            
            self.status.configure(text="Ready for new project...")
            self._add_message("AI Manufacturing", "Ready! Describe what you want to make.")
    
    def run(self):
        """Run application"""
        try:
            self.root.mainloop()
        finally:
            if self.printer_status_timer:
                self.root.after_cancel(self.printer_status_timer)

if __name__ == "__main__":
    app = EnhancedDesktopApp()
    app.run()
