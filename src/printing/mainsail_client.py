# src/printing/mainsail_client.py
"""Mainsail/Klipper API Client for AI Manufacturing Pipeline"""
import requests
import json
import time
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass
from dotenv import load_dotenv
import os

load_dotenv()

@dataclass
class PrinterStatus:
    """Printer status information"""
    state: str  # ready, printing, paused, error, etc.
    extruder_temp: float
    extruder_target: float
    bed_temp: float
    bed_target: float
    chamber_temp: float = 0.0
    progress: float = 0.0
    print_time: int = 0
    current_file: str = ""
    error_message: str = ""

class MainsailClient:
    """Client for Mainsail/Klipper API communication"""
    
    def __init__(self):
        self.base_url = os.getenv('MAINSAIL_URL', 'http://192.168.1.100')
        self.timeout = int(os.getenv('MAINSAIL_TIMEOUT', 30))
        self.printer_name = os.getenv('PRINTER_NAME', 'Voron_2.4_350')
        
        # Remove trailing slash
        self.base_url = self.base_url.rstrip('/')
        
        # API endpoints
        self.api_base = f"{self.base_url}/api"
        self.printer_api = f"{self.api_base}/printer"
        self.files_api = f"{self.api_base}/files"
        
        print(f"🖨️ Mainsail client initialized: {self.base_url}")
        self._test_connection()
    
    def _test_connection(self) -> bool:
        """Test connection to Mainsail"""
        try:
            response = requests.get(f"{self.printer_api}/info", timeout=self.timeout)
            if response.status_code == 200:
                info = response.json()['result']
                print(f"✅ Connected to printer: {info.get('hostname', 'Unknown')}")
                print(f"   Software: {info.get('software_version', 'Unknown')}")
                return True
            else:
                print(f"❌ Connection failed: HTTP {response.status_code}")
                return False
        except requests.RequestException as e:
            print(f"❌ Connection failed: {e}")
            print(f"   Make sure Mainsail is running at {self.base_url}")
            return False
    
    def get_printer_status(self) -> PrinterStatus:
        """Get current printer status"""
        try:
            # Get printer objects status
            response = requests.get(
                f"{self.printer_api}/objects/query",
                params={
                    'extruder': 'temperature,target',
                    'heater_bed': 'temperature,target',
                    'temperature_sensor chamber': 'temperature',  # If chamber sensor exists
                    'print_stats': 'state,filename,print_duration',
                    'display_status': 'progress',
                    'webhooks': 'state,state_message'
                },
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                raise Exception(f"API error: HTTP {response.status_code}")
            
            data = response.json()['result']['status']
            
            # Extract status information
            extruder = data.get('extruder', {})
            bed = data.get('heater_bed', {})
            chamber = data.get('temperature_sensor chamber', {})
            print_stats = data.get('print_stats', {})
            display_status = data.get('display_status', {})
            webhooks = data.get('webhooks', {})
            
            return PrinterStatus(
                state=webhooks.get('state', 'unknown'),
                extruder_temp=extruder.get('temperature', 0.0),
                extruder_target=extruder.get('target', 0.0),
                bed_temp=bed.get('temperature', 0.0),
                bed_target=bed.get('target', 0.0),
                chamber_temp=chamber.get('temperature', 0.0),
                progress=display_status.get('progress', 0.0),
                print_time=int(print_stats.get('print_duration', 0)),
                current_file=print_stats.get('filename', ''),
                error_message=webhooks.get('state_message', '')
            )
            
        except Exception as e:
            print(f"❌ Failed to get printer status: {e}")
            return PrinterStatus(
                state='error',
                extruder_temp=0, extruder_target=0,
                bed_temp=0, bed_target=0,
                error_message=str(e)
            )
    
    def upload_gcode_file(self, gcode_path: str, target_filename: Optional[str] = None) -> Dict:
        """Upload G-code file to printer"""
        gcode_path = Path(gcode_path)
        
        if not gcode_path.exists():
            return {'success': False, 'error': f'G-code file not found: {gcode_path}'}
        
        if target_filename is None:
            target_filename = gcode_path.name
        
        try:
            print(f"📤 Uploading {gcode_path.name} to printer...")
            
            # Check file size
            file_size_mb = gcode_path.stat().st_size / 1024 / 1024
            max_size = int(os.getenv('MAX_GCODE_FILE_SIZE_MB', 100))
            
            if file_size_mb > max_size:
                return {
                    'success': False, 
                    'error': f'G-code file too large: {file_size_mb:.1f}MB (max: {max_size}MB)'
                }
            
            # Upload file
            with open(gcode_path, 'rb') as f:
                files = {'file': (target_filename, f, 'text/plain')}
                data = {'root': 'gcodes'}  # Upload to gcodes directory
                
                response = requests.post(
                    f"{self.files_api}/upload",
                    files=files,
                    data=data,
                    timeout=self.timeout * 3  # Longer timeout for uploads
                )
            
            if response.status_code == 201:
                result = response.json()['result']
                print(f"✅ Upload successful: {target_filename}")
                return {
                    'success': True,
                    'filename': target_filename,
                    'path': result.get('item', {}).get('path', target_filename),
                    'size_mb': file_size_mb,
                    'upload_time': time.time()
                }
            else:
                error_msg = f"Upload failed: HTTP {response.status_code}"
                if response.content:
                    try:
                        error_data = response.json()
                        error_msg += f" - {error_data.get('error', {}).get('message', '')}"
                    except:
                        pass
                return {'success': False, 'error': error_msg}
        
        except Exception as e:
            return {'success': False, 'error': f'Upload failed: {e}'}
    
    def start_print(self, filename: str, preheat: bool = True) -> Dict:
        """Start printing a file"""
        try:
            # Safety checks
            if os.getenv('CHECK_PRINTER_STATUS_BEFORE_PRINT', 'true').lower() == 'true':
                status = self.get_printer_status()
                if status.state != 'ready':
                    return {
                        'success': False, 
                        'error': f'Printer not ready (state: {status.state}). Error: {status.error_message}'
                    }
            
            print(f"🖨️ Starting print: {filename}")
            
            # Preheat if requested
            if preheat:
                preheat_result = self.preheat_printer()
                if not preheat_result['success']:
                    print(f"⚠️ Preheat failed: {preheat_result['error']}")
            
            # Start print
            response = requests.post(
                f"{self.printer_api}/print/start",
                json={'filename': filename},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                print(f"✅ Print started: {filename}")
                return {
                    'success': True,
                    'filename': filename,
                    'start_time': time.time(),
                    'status': 'print_started'
                }
            else:
                error_msg = f"Failed to start print: HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f" - {error_data.get('error', {}).get('message', '')}"
                except:
                    pass
                return {'success': False, 'error': error_msg}
        
        except Exception as e:
            return {'success': False, 'error': f'Print start failed: {e}'}
    
    def preheat_printer(self) -> Dict:
        """Preheat printer to default temperatures"""
        try:
            extruder_temp = int(os.getenv('EXTRUDER_TEMP', 210))
            bed_temp = int(os.getenv('BED_TEMP', 60))
            
            print(f"🔥 Preheating: Extruder {extruder_temp}°C, Bed {bed_temp}°C")
            
            # Set extruder temperature
            extruder_response = requests.post(
                f"{self.printer_api}/gcode/script",
                json={'script': f'SET_HEATER_TEMPERATURE HEATER=extruder TARGET={extruder_temp}'},
                timeout=self.timeout
            )
            
            # Set bed temperature  
            bed_response = requests.post(
                f"{self.printer_api}/gcode/script", 
                json={'script': f'SET_HEATER_TEMPERATURE HEATER=heater_bed TARGET={bed_temp}'},
                timeout=self.timeout
            )
            
            if extruder_response.status_code == 200 and bed_response.status_code == 200:
                return {
                    'success': True,
                    'extruder_target': extruder_temp,
                    'bed_target': bed_temp,
                    'message': 'Preheating started'
                }
            else:
                return {'success': False, 'error': 'Failed to set temperatures'}
        
        except Exception as e:
            return {'success': False, 'error': f'Preheat failed: {e}'}
    
    def pause_print(self) -> Dict:
        """Pause current print"""
        try:
            response = requests.post(f"{self.printer_api}/print/pause", timeout=self.timeout)
            if response.status_code == 200:
                return {'success': True, 'status': 'paused'}
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'success': False, 'error': f'Pause failed: {e}'}
    
    def resume_print(self) -> Dict:
        """Resume paused print"""
        try:
            response = requests.post(f"{self.printer_api}/print/resume", timeout=self.timeout)
            if response.status_code == 200:
                return {'success': True, 'status': 'printing'}
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'success': False, 'error': f'Resume failed: {e}'}
    
    def cancel_print(self) -> Dict:
        """Cancel current print"""
        try:
            response = requests.post(f"{self.printer_api}/print/cancel", timeout=self.timeout)
            if response.status_code == 200:
                return {'success': True, 'status': 'cancelled'}
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'success': False, 'error': f'Cancel failed: {e}'}
    
    def get_file_list(self, directory: str = "gcodes") -> List[Dict]:
        """Get list of files on printer"""
        try:
            response = requests.get(f"{self.files_api}/list", 
                                  params={'root': directory}, timeout=self.timeout)
            if response.status_code == 200:
                files = response.json()['result']
                return [
                    {
                        'filename': f['filename'],
                        'size_mb': f.get('size', 0) / 1024 / 1024,
                        'modified': f.get('modified', 0),
                        'path': f.get('path', f['filename'])
                    }
                    for f in files if f['filename'].endswith('.gcode')
                ]
            else:
                print(f"❌ Failed to get file list: HTTP {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Failed to get file list: {e}")
            return []
    
    def delete_file(self, filename: str, directory: str = "gcodes") -> Dict:
        """Delete file from printer"""
        try:
            response = requests.delete(
                f"{self.files_api}/{directory}/{filename}",
                timeout=self.timeout
            )
            if response.status_code == 200:
                return {'success': True, 'deleted': filename}
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'success': False, 'error': f'Delete failed: {e}'}
    
    def emergency_stop(self) -> Dict:
        """Emergency stop the printer"""
        try:
            response = requests.post(
                f"{self.printer_api}/emergency_stop",
                timeout=self.timeout
            )
            if response.status_code == 200:
                return {'success': True, 'status': 'emergency_stopped'}
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'success': False, 'error': f'E-stop failed: {e}'}
    
    def get_printer_info(self) -> Dict:
        """Get detailed printer information"""
        try:
            response = requests.get(f"{self.printer_api}/info", timeout=self.timeout)
            if response.status_code == 200:
                return response.json()['result']
            else:
                return {'error': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'error': f'Info request failed: {e}'}
    
    def send_gcode(self, gcode_command: str) -> Dict:
        """Send G-code command directly"""
        try:
            response = requests.post(
                f"{self.printer_api}/gcode/script",
                json={'script': gcode_command},
                timeout=self.timeout
            )
            if response.status_code == 200:
                return {'success': True, 'command': gcode_command}
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'success': False, 'error': f'G-code send failed: {e}'}
    
    def is_printer_ready(self) -> bool:
        """Check if printer is ready for new job"""
        status = self.get_printer_status()
        return status.state == 'ready'
    
    def format_print_time(self, seconds: int) -> str:
        """Format print time in human readable format"""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds//60}m {seconds%60}s"
        else:
            return f"{seconds//3600}h {(seconds%3600)//60}m"