# src/printing/mainsail_client.py
"""FIXED: Reliable Moonraker Client with Better Upload Detection & Latest Print Start"""
import requests
import time
import json
from pathlib import Path
from typing import Dict, Optional, List, Any, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv
import os
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PrinterStatus:
    """Printer status information"""
    state: str
    progress: float
    print_time: int
    remaining_time: int
    bed_temp: float
    bed_target: float
    extruder_temp: float
    extruder_target: float
    current_file: Optional[str] = None
    layer: Optional[int] = None
    total_layers: Optional[int] = None

@dataclass  
class PrinterInfo:
    """Printer information structure"""
    name: str
    state: str
    klippy_connected: bool
    moonraker_version: str
    klipper_version: str
    hostname: str

class MainsailClient:
    """FIXED: Moonraker client with improved upload detection and latest print start"""
    
    def __init__(self, url: str = None, timeout: int = 30):
        """Initialize HTTP-based Moonraker client"""
        self.base_url = url or os.getenv('MAINSAIL_URL', 'http://172.30.14.83:7125')
        self.timeout = timeout or int(os.getenv('HTTP_REQUEST_TIMEOUT', '30'))
        
        self.base_url = self.base_url.rstrip('/')
        self.host = self.base_url.replace('http://', '').replace('https://', '').split(':')[0]
        
        self.session = requests.Session()
        self.session.timeout = self.timeout
        
        logger.info(f"Moonraker HTTP client initialized: {self.base_url}")
    
    def _make_request(self, endpoint: str, method: str = 'GET', data=None, files=None) -> Optional[Dict]:
        """Make HTTP request with retry logic"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                if method.upper() == 'GET':
                    response = self.session.get(url, timeout=self.timeout)
                elif method.upper() == 'POST':
                    if files:
                        response = self.session.post(url, data=data, files=files, timeout=self.timeout)
                    else:
                        response = self.session.post(url, json=data, timeout=self.timeout)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                else:
                    logger.error(f"API request failed after {max_retries} attempts: {url}")
                    return None
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"API request failed: {url} - {e}")
                return None
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode failed: {e}")
                return None
        
        return None
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test connection to Moonraker"""
        try:
            result = self._make_request('/server/info')
            if result:
                version = result.get('result', {}).get('klippy_version', 'Unknown')
                logger.info("Connection test successful")
                return True, f"Connected to Moonraker (Klipper: {version})"
            else:
                return False, "No response from server"
                
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False, f"Connection failed: {str(e)}"
    
    def get_printer_info(self) -> Optional[PrinterInfo]:
        """Get printer information"""
        try:
            server_info = self._make_request('/server/info')
            printer_info = self._make_request('/printer/info')
            
            if not server_info or not printer_info:
                return None
            
            server_result = server_info.get('result', {})
            printer_result = printer_info.get('result', {})
            
            state = printer_result.get('state_message', 'unknown')
            
            return PrinterInfo(
                name=os.getenv('PRINTER_NAME', 'Unknown Printer'),
                state=state,
                klippy_connected=server_result.get('klippy_connected', True),
                moonraker_version=server_result.get('moonraker_version', 'Unknown'),
                klipper_version=server_result.get('klippy_version', 'Unknown'),
                hostname=self.host
            )
            
        except Exception as e:
            logger.error(f"Failed to get printer info: {e}")
            return None
    
    def get_printer_status(self) -> Optional[PrinterStatus]:
        """Get current printer status"""
        try:
            objects_result = self._make_request(
                '/printer/objects/query?webhooks&print_stats&heater_bed&extruder&display_status'
            )
            
            if not objects_result:
                return None
            
            status = objects_result.get('result', {}).get('status', {})
            
            webhooks = status.get('webhooks', {})
            print_stats = status.get('print_stats', {})
            heater_bed = status.get('heater_bed', {})
            extruder = status.get('extruder', {})
            display_status = status.get('display_status', {})
            
            progress = display_status.get('progress', 0.0) * 100
            print_duration = print_stats.get('print_duration', 0)
            remaining_time = 0
            
            if progress > 0 and progress < 100:
                estimated_total = print_duration / (progress / 100)
                remaining_time = max(0, estimated_total - print_duration)
            
            return PrinterStatus(
                state=self._normalize_state(webhooks.get('state', 'unknown')),
                progress=progress,
                print_time=int(print_duration),
                remaining_time=int(remaining_time),
                bed_temp=heater_bed.get('temperature', 0.0),
                bed_target=heater_bed.get('target', 0.0),
                extruder_temp=extruder.get('temperature', 0.0),
                extruder_target=extruder.get('target', 0.0),
                current_file=print_stats.get('filename'),
                layer=display_status.get('layer'),
                total_layers=None
            )
            
        except Exception as e:
            logger.error(f"Failed to get printer status: {e}")
            return None
    
    def _normalize_state(self, klipper_state: str) -> str:
        """Convert Klipper state to normalized state"""
        state_mapping = {
            'ready': 'ready',
            'printing': 'printing', 
            'paused': 'paused',
            'complete': 'complete',
            'cancelled': 'cancelled',
            'error': 'error',
            'shutdown': 'offline',
            'startup': 'connecting',
            'standby': 'ready',
        }
        return state_mapping.get(klipper_state.lower(), 'unknown')
    
    def upload_and_print_file(self, file_path: str, start_print: bool = True) -> Dict:
        """FIXED: Upload G-code file with better response handling and consistent return format"""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return {"success": False, "message": f"File not found: {file_path}"}
            
            logger.info(f"Uploading file: {file_path.name}")
            
            # Calculate file size
            file_size_mb = file_path.stat().st_size / 1024 / 1024
            uploaded_filename = file_path.name
            
            # Step 1: Upload file
            with open(file_path, 'rb') as f:
                files = {'file': (file_path.name, f, 'application/octet-stream')}
                data = {'root': 'gcodes'}
                
                upload_result = self._make_request('/server/files/upload', method='POST', data=data, files=files)
            
            # CRITICAL FIX: Be more tolerant of response structure
            upload_succeeded = False
            
            if upload_result:
                # Accept various response structures from different Moonraker versions
                if 'result' in upload_result or 'item' in upload_result:
                    upload_succeeded = True
                    # Try to extract actual filename from response
                    result_data = upload_result.get('result') or upload_result.get('item', {})
                    if isinstance(result_data, dict):
                        uploaded_filename = result_data.get('path', file_path.name)
                else:
                    # If we got ANY json response, check if file now exists
                    logger.warning(f"Unexpected upload response structure: {list(upload_result.keys())}")
                    logger.info("Verifying file exists on printer...")
                    time.sleep(1)
                    files_list = self.get_file_list()
                    if any(f['name'] == file_path.name for f in files_list):
                        upload_succeeded = True
                        logger.info("File found in printer files - upload successful despite unusual response")
            
            if not upload_succeeded:
                return {
                    "success": False, 
                    "message": f"Upload failed for {file_path.name}",
                    "filename": file_path.name,
                    "size_mb": file_size_mb
                }
            
            logger.info(f"File uploaded successfully: {uploaded_filename}")
            
            if not start_print:
                return {
                    "success": True, 
                    "message": f"File uploaded: {uploaded_filename}",
                    "filename": uploaded_filename,
                    "size_mb": file_size_mb
                }
            
            # Step 2: Check printer state
            logger.info("Checking printer state...")
            status = self.get_printer_status()
            
            if not status:
                return {
                    "success": True,  # Upload succeeded
                    "message": f"File uploaded but cannot get printer status. Use start_latest_print() to start.",
                    "filename": uploaded_filename,
                    "size_mb": file_size_mb
                }
            
            logger.info(f"Printer state: {status.state}")
            
            # Accept states ready for printing
            acceptable_states = ['ready', 'standby', 'complete', 'cancelled']
            
            if status.state not in acceptable_states:
                return {
                    "success": True,  # Upload succeeded
                    "message": f"File uploaded but printer not ready (state: {status.state}). Please check printer.",
                    "filename": uploaded_filename,
                    "size_mb": file_size_mb
                }
            
            # Step 3: Try to start the print
            logger.info("Attempting to start print...")
            print_started = self._try_start_print(uploaded_filename)
            
            if print_started:
                logger.info(f"Print started successfully: {uploaded_filename}")
                return {
                    "success": True, 
                    "message": f"File uploaded and print started: {uploaded_filename}",
                    "filename": uploaded_filename,
                    "size_mb": file_size_mb,
                    "print_started": True
                }
            else:
                return {
                    "success": True,  # Upload succeeded
                    "message": f"File uploaded but failed to start print. Use start_latest_print() to retry.",
                    "filename": uploaded_filename,
                    "size_mb": file_size_mb,
                    "print_started": False
                }
                
        except Exception as e:
            logger.error(f"Upload/print failed: {e}")
            return {
                "success": False, 
                "message": f"Error: {str(e)}",
                "filename": file_path.name if 'file_path' in locals() else "unknown",
                "size_mb": 0.0
            }
    
    def _try_start_print(self, filename: str) -> bool:
        """Try multiple methods to start the print"""
        methods_tried = []
        
        # Method 1: Standard API - just filename
        try:
            logger.info(f"Method 1: /printer/print/start with filename='{filename}'")
            print_data = {'filename': filename}
            print_result = self._make_request('/printer/print/start', method='POST', data=print_data)
            
            if print_result and 'result' in print_result:
                logger.info(f"Method 1 successful")
                return True
            else:
                methods_tried.append(f"Method 1: {print_result}")
                logger.warning(f"Method 1 failed: {print_result}")
        except Exception as e:
            methods_tried.append(f"Method 1 exception: {e}")
            logger.warning(f"Method 1 exception: {e}")
        
        time.sleep(1)
        
        # Method 2: Full path with gcodes/
        try:
            logger.info(f"Method 2: /printer/print/start with filename='gcodes/{filename}'")
            print_data = {'filename': f"gcodes/{filename}"}
            print_result = self._make_request('/printer/print/start', method='POST', data=print_data)
            
            if print_result and 'result' in print_result:
                logger.info(f"Method 2 successful")
                return True
            else:
                methods_tried.append(f"Method 2: {print_result}")
                logger.warning(f"Method 2 failed: {print_result}")
        except Exception as e:
            methods_tried.append(f"Method 2 exception: {e}")
            logger.warning(f"Method 2 exception: {e}")
        
        time.sleep(1)
        
        # Method 3: G-code command SDCARD_PRINT_FILE
        try:
            logger.info(f"Method 3: SDCARD_PRINT_FILE via G-code")
            gcode_result = self.send_gcode(f'SDCARD_PRINT_FILE FILENAME="{filename}"')
            
            if gcode_result.get('success'):
                logger.info(f"Method 3 successful")
                return True
            else:
                methods_tried.append(f"Method 3: {gcode_result}")
                logger.warning(f"Method 3 failed: {gcode_result}")
        except Exception as e:
            methods_tried.append(f"Method 3 exception: {e}")
            logger.warning(f"Method 3 exception: {e}")
        
        # All methods failed
        logger.error(f"All print start methods failed:")
        for method in methods_tried:
            logger.error(f"   {method}")
        
        return False
    
    def start_latest_print(self) -> Dict:
        """NEW: Start printing the most recently uploaded file"""
        try:
            logger.info("Getting file list to find latest file...")
            files = self.get_file_list()
            
            if not files:
                return {"success": False, "message": "No files found on printer"}
            
            # Sort by modification time, get newest
            latest_file = max(files, key=lambda x: x['modified'])
            filename = latest_file['name']
            
            logger.info(f"Latest file: {filename} (modified: {latest_file['modified']})")
            
            # Check printer state
            status = self.get_printer_status()
            if status:
                logger.info(f"Printer state: {status.state}")
                acceptable_states = ['ready', 'standby', 'complete', 'cancelled']
                
                if status.state not in acceptable_states:
                    return {
                        "success": False,
                        "message": f"Printer not ready (state: {status.state}). Current file: {filename}"
                    }
            
            # Try to start print
            logger.info(f"Starting print: {filename}")
            success = self._try_start_print(filename)
            
            if success:
                return {
                    "success": True, 
                    "message": f"Started print: {filename}",
                    "filename": filename
                }
            else:
                return {
                    "success": False, 
                    "message": f"Failed to start print: {filename}",
                    "filename": filename
                }
                
        except Exception as e:
            logger.error(f"Failed to start latest print: {e}")
            return {"success": False, "message": str(e)}
    
    def upload_and_start_print(self, file_path: str, start_print: bool = True) -> Dict:
        """Compatibility alias"""
        return self.upload_and_print_file(file_path, start_print)
    
    def upload_gcode_file(self, file_path: str, start_print: bool = False) -> Dict:
        """Upload without auto-starting"""
        return self.upload_and_print_file(file_path, start_print)
    
    def start_print(self, filename: str) -> Tuple[bool, str]:
        """Start printing a file that's already uploaded"""
        try:
            success = self._try_start_print(filename)
            if success:
                return True, f"Print started: {filename}"
            else:
                return False, f"Failed to start print: {filename}"
                
        except Exception as e:
            logger.error(f"Start print failed: {e}")
            return False, f"Error: {str(e)}"
    
    def pause_print(self) -> Tuple[bool, str]:
        """Pause current print"""
        try:
            result = self._make_request('/printer/print/pause', method='POST')
            if result:
                return True, "Print paused"
            return False, "Failed to pause"
        except Exception as e:
            return False, str(e)
    
    def resume_print(self) -> Tuple[bool, str]:
        """Resume paused print"""
        try:
            result = self._make_request('/printer/print/resume', method='POST')
            if result:
                return True, "Print resumed"
            return False, "Failed to resume"
        except Exception as e:
            return False, str(e)
    
    def cancel_print(self) -> Tuple[bool, str]:
        """Cancel current print"""
        try:
            result = self._make_request('/printer/print/cancel', method='POST')
            if result:
                return True, "Print cancelled"
            return False, "Failed to cancel"
        except Exception as e:
            return False, str(e)
    
    def get_file_list(self) -> List[Dict]:
        """Get list of G-code files"""
        try:
            result = self._make_request('/server/files/list?root=gcodes')
            
            if not result or 'result' not in result:
                return []
            
            files = result['result']
            
            return [
                {
                    'name': f['filename'],
                    'size': f.get('size', 0),
                    'modified': f.get('modified', 0)
                }
                for f in files if f.get('filename', '').endswith('.gcode')
            ]
                
        except Exception as e:
            logger.error(f"Failed to get file list: {e}")
            return []
    
    def is_printer_ready(self) -> bool:
        """Check if printer is ready"""
        try:
            status = self.get_printer_status()
            return status and status.state in ['ready', 'standby', 'complete', 'cancelled']
        except:
            return False
    
    def send_gcode(self, command: str) -> Dict:
        """Send G-code command"""
        try:
            data = {'script': command}
            result = self._make_request('/printer/gcode/script', method='POST', data=data)
            
            if result:
                logger.info(f"G-code sent: {command}")
                return {'success': True, 'command': command}
            return {'success': False, 'error': 'No response'}
                
        except Exception as e:
            logger.error(f"Failed to send G-code: {e}")
            return {'success': False, 'error': str(e)}
    
    def emergency_stop(self) -> Tuple[bool, str]:
        """Emergency stop"""
        try:
            result = self._make_request('/printer/emergency_stop', method='POST')
            if result:
                return True, "Emergency stop activated"
            return False, "Failed to activate emergency stop"
        except Exception as e:
            return False, str(e)

# Backwards compatibility
MoonrakerPyClient = MainsailClient