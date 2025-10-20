# src/printing/mainsail_client.py
"""MoonrakerPy-based Client - Drop-in Replacement for Existing MainsailClient"""
import moonrakerpy as moonpy
import requests
import time
import json
from pathlib import Path
from typing import Dict, Optional, List, Any
from dataclasses import dataclass
from dotenv import load_dotenv
import os
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PrinterStatus:
    """Printer status information - Compatible with existing code"""
    state: str  # ready, printing, paused, error, etc.
    bed_temp: float = 0.0
    bed_target: float = 0.0
    extruder_temp: float = 0.0
    extruder_target: float = 0.0
    progress: float = 0.0
    print_time: int = 0
    time_left: Optional[int] = None
    filename: Optional[str] = None
    current_file: Optional[str] = None  # Added for GUI compatibility
    layer: Optional[int] = None
    total_layers: Optional[int] = None
    fan_speed: float = 0.0
    z_position: float = 0.0
    ready: bool = False  # Added for GUI compatibility

class MainsailClient:
    """Enhanced MoonrakerPy-based client - drop-in replacement for existing MainsailClient"""
    
    def __init__(self):
        self.base_url = os.getenv('MAINSAIL_URL', 'http://localhost:7125')
        self.timeout = int(os.getenv('MAINSAIL_TIMEOUT', '30'))
        self.printer_name = os.getenv('PRINTER_NAME', 'Voron_2.4_350')
        
        # Parse URL for MoonrakerPy
        self.host_url = self.base_url
        
        self.connected = False
        self._last_status = None
        self._printer = None
        logger.info(f"Initialized MoonrakerPy client for {self.base_url}")
    
    def _get_moonraker_printer(self):
        """Get MoonrakerPrinter instance"""
        try:
            if self._printer is None:
                self._printer = moonpy.MoonrakerPrinter(self.host_url)
            return self._printer
        except Exception as e:
            logger.error(f"Failed to create MoonrakerPrinter: {e}")
            return None
    
    def _make_request(self, endpoint: str, method: str = 'GET', data: dict = None) -> dict:
        """Make direct HTTP request to Moonraker API"""
        try:
            url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
            
            if method.upper() == 'GET':
                response = requests.get(url, timeout=self.timeout, params=data)
            else:
                response = requests.post(url, json=data, timeout=self.timeout)
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Request to {endpoint} failed: {e}")
            return {'result': None, 'error': str(e)}
    
    def test_connection(self) -> bool:
        """Test connection to Moonraker server"""
        try:
            # Test with server info request
            response = self._make_request('server/info')
            
            if response and 'result' in response and response['result']:
                self.connected = True
                logger.info(f"✅ Connected to Moonraker server")
                return True
            else:
                logger.error("❌ Server info request failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Connection test failed: {e}")
            self.connected = False
            return False
    
    def get_printer_status(self) -> Dict[str, Any]:
        """Get current printer status - returns dict for GUI compatibility"""
        try:
            # Query printer objects using direct API
            query_data = {
                "objects": {
                    "print_stats": None,
                    "heater_bed": None,
                    "extruder": None,
                    "fan": None,
                    "toolhead": ["position"],
                    "display_status": None
                }
            }
            
            response = self._make_request('printer/objects/query', 'POST', query_data)
            
            if 'error' in response:
                return {"error": "Failed to get printer status", "state": "error"}
            
            result = response.get('result', {})
            status_data = result.get('status', {})
            
            # Extract status information
            print_stats = status_data.get('print_stats', {})
            heater_bed = status_data.get('heater_bed', {})
            extruder = status_data.get('extruder', {})
            fan = status_data.get('fan', {})
            toolhead = status_data.get('toolhead', {})
            display_status = status_data.get('display_status', {})
            
            # Determine state
            raw_state = print_stats.get('state', 'unknown').lower()
            if raw_state == 'standby':
                state = 'ready'
            elif raw_state in ['printing', 'paused', 'complete', 'cancelled', 'error']:
                state = raw_state
            else:
                state = 'ready'
            
            # Get position data
            position = toolhead.get('position', [0, 0, 0, 0])
            z_position = float(position[2]) if len(position) > 2 else 0.0
            
            # Get current file
            current_file = print_stats.get('filename', 'None')
            if current_file and current_file != 'None':
                # Just show filename, not full path
                current_file = current_file.split('/')[-1]
            else:
                current_file = 'None'
            
            # Build status dictionary for GUI
            status_dict = {
                'state': state,
                'bed_temp': float(heater_bed.get('temperature', 0)),
                'bed_target': float(heater_bed.get('target', 0)),
                'extruder_temp': float(extruder.get('temperature', 0)),
                'extruder_target': float(extruder.get('target', 0)),
                'progress': float(display_status.get('progress', 0)),
                'print_time': int(print_stats.get('print_duration', 0)),
                'current_file': current_file,
                'fan_speed': float(fan.get('speed', 0)) * 100,  # Convert to percentage
                'z_position': z_position,
                'ready': state == 'ready'
            }
            
            # Estimate time left if printing
            if status_dict['progress'] > 0 and status_dict['state'] == 'printing':
                estimated_total = status_dict['print_time'] / status_dict['progress']
                status_dict['time_left'] = int(estimated_total - status_dict['print_time'])
            
            # Store as PrinterStatus object for internal use
            self._last_status = PrinterStatus(
                state=status_dict['state'],
                bed_temp=status_dict['bed_temp'],
                bed_target=status_dict['bed_target'],
                extruder_temp=status_dict['extruder_temp'],
                extruder_target=status_dict['extruder_target'],
                progress=status_dict['progress'],
                print_time=status_dict['print_time'],
                current_file=status_dict['current_file'],
                fan_speed=status_dict['fan_speed'],
                z_position=status_dict['z_position'],
                ready=status_dict['ready'],
                time_left=status_dict.get('time_left')
            )
            
            return status_dict  # Return dict for GUI compatibility
            
        except Exception as e:
            logger.error(f"Failed to get printer status: {e}")
            return {"error": f"Status request failed: {str(e)}", "state": "error"}
    
    def get_files(self) -> List[Dict[str, Any]]:
        """Get list of G-code files"""
        try:
            response = self._make_request('server/files/list?root=gcodes')
            
            if 'error' in response:
                return []
            
            result = response.get('result', [])
            
            formatted_files = []
            for file_info in result:
                formatted_files.append({
                    'path': file_info.get('path', ''),
                    'display': file_info.get('path', '').split('/')[-1],  # Just filename
                    'size': file_info.get('size', 0),
                    'modified': file_info.get('modified', 0),
                    'type': 'gcode' if file_info.get('path', '').endswith('.gcode') else 'file'
                })
            
            return formatted_files
            
        except Exception as e:
            logger.error(f"Failed to get files: {e}")
            return []
    
    def upload_gcode_file(self, file_path: str) -> Dict[str, Any]:
        """Upload G-code file (compatibility method for export.py)"""
        # export.py calls this method with just the file path
        # It expects result['success'], result['filename'], result['size_mb']
        return self.upload_and_start_print(file_path, start_print=False)
    
    def get_printer_status(self):
        """Get current printer status - returns PrinterStatus object for export.py compatibility"""
        try:
            # Query printer objects using direct API
            query_data = {
                "objects": {
                    "print_stats": None,
                    "heater_bed": None,
                    "extruder": None,
                    "fan": None,
                    "toolhead": ["position"],
                    "display_status": None
                }
            }
            
            response = self._make_request('printer/objects/query', 'POST', query_data)
            
            if 'error' in response:
                # Return error object that export.py won't break on
                error_status = PrinterStatus(
                    state="error",
                    bed_temp=0.0,
                    bed_target=0.0,
                    extruder_temp=0.0,
                    extruder_target=0.0,
                    progress=0.0,
                    print_time=0,
                    current_file="None",
                    ready=False
                )
                self._last_status = error_status
                return error_status
            
            result = response.get('result', {})
            status_data = result.get('status', {})
            
            # Extract status information
            print_stats = status_data.get('print_stats', {})
            heater_bed = status_data.get('heater_bed', {})
            extruder = status_data.get('extruder', {})
            fan = status_data.get('fan', {})
            toolhead = status_data.get('toolhead', {})
            display_status = status_data.get('display_status', {})
            
            # Determine state
            raw_state = print_stats.get('state', 'unknown').lower()
            if raw_state == 'standby':
                state = 'ready'
            elif raw_state in ['printing', 'paused', 'complete', 'cancelled', 'error']:
                state = raw_state
            else:
                state = 'ready'
            
            # Get position data
            position = toolhead.get('position', [0, 0, 0, 0])
            z_position = float(position[2]) if len(position) > 2 else 0.0
            
            # Get current file
            current_file = print_stats.get('filename', 'None')
            if current_file and current_file != 'None':
                # Just show filename, not full path
                current_file = current_file.split('/')[-1]
            else:
                current_file = 'None'
            
            # Create PrinterStatus object for export.py compatibility
            status_obj = PrinterStatus(
                state=state,
                bed_temp=float(heater_bed.get('temperature', 0)),
                bed_target=float(heater_bed.get('target', 0)),
                extruder_temp=float(extruder.get('temperature', 0)),
                extruder_target=float(extruder.get('target', 0)),
                progress=float(display_status.get('progress', 0)),
                print_time=int(print_stats.get('print_duration', 0)),
                current_file=current_file,
                fan_speed=float(fan.get('speed', 0)) * 100,  # Convert to percentage
                z_position=z_position,
                ready=state == 'ready'
            )
            
            # Estimate time left if printing
            if status_obj.progress > 0 and status_obj.state == 'printing':
                estimated_total = status_obj.print_time / status_obj.progress
                status_obj.time_left = int(estimated_total - status_obj.print_time)
            
            self._last_status = status_obj
            return status_obj  # Return object for export.py compatibility
            
        except Exception as e:
            logger.error(f"Failed to get printer status: {e}")
            # Return error object that export.py won't break on
            error_status = PrinterStatus(
                state="error",
                bed_temp=0.0,
                bed_target=0.0,
                extruder_temp=0.0,
                extruder_target=0.0,
                progress=0.0,
                print_time=0,
                current_file="None",
                ready=False
            )
            self._last_status = error_status
            return error_status
    
    def get_printer_status_dict(self) -> Dict[str, Any]:
        """Get printer status as dictionary for GUI compatibility"""
        try:
            status_obj = self.get_printer_status()
            
            # Convert PrinterStatus object to dictionary for GUI
            status_dict = {
                'state': status_obj.state,
                'bed_temp': status_obj.bed_temp,
                'bed_target': status_obj.bed_target,
                'extruder_temp': status_obj.extruder_temp,
                'extruder_target': status_obj.extruder_target,
                'progress': status_obj.progress,
                'print_time': status_obj.print_time,
                'current_file': status_obj.current_file,
                'fan_speed': status_obj.fan_speed,
                'z_position': status_obj.z_position,
                'ready': status_obj.ready
            }
            
            if status_obj.time_left:
                status_dict['time_left'] = status_obj.time_left
                
            return status_dict
            
        except Exception as e:
            logger.error(f"Failed to get printer status: {e}")
            return {"error": f"Status request failed: {str(e)}", "state": "error"}
        """Upload G-code file and optionally start printing"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return {'success': False, 'message': f'File not found: {file_path}'}
            
            logger.info(f"📤 Uploading {file_path.name}...")
            
            # Upload file using direct API
            url = f"{self.base_url}/server/files/upload"
            
            with open(file_path, 'rb') as f:
                files = {'file': (file_path.name, f, 'application/octet-stream')}
                data = {'root': 'gcodes'}
                
                response = requests.post(url, files=files, data=data, timeout=90)
                response.raise_for_status()
                
            logger.info(f"✅ Upload successful: {file_path.name}")
            
            if start_print:
                # Start print using MoonrakerPy if possible
                printer = self._get_moonraker_printer()
                if printer:
                    try:
                        # MoonrakerPy doesn't seem to have a start_print method, use direct API
                        start_url = f"printer/print/start?filename={file_path.name}"
                        start_response = self._make_request(start_url, 'POST')
                        
                        if 'error' not in start_response:
                            logger.info(f"🖨️ Print started: {file_path.name}")
                            return {
                                'success': True,
                                'message': f'Upload and print started: {file_path.name}',
                                'filename': file_path.name
                            }
                        else:
                            return {
                                'success': False,
                                'message': f'Upload successful but failed to start print: {file_path.name}'
                            }
                    except Exception as e:
                        logger.error(f"Failed to start print: {e}")
                        return {
                            'success': False,
                            'message': f'Upload successful but failed to start print: {str(e)}'
                        }
            
            return {
                'success': True,
                'message': f'File uploaded successfully: {file_path.name}',
                'filename': file_path.name
            }
                
        except Exception as e:
            logger.error(f"Failed to upload/start print: {e}")
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def start_print(self, filename: str) -> Dict[str, Any]:
        """Start printing a file that's already on the printer"""
        try:
            start_url = f"printer/print/start?filename={filename}"
            response = self._make_request(start_url, 'POST')
            
            if 'error' not in response:
                logger.info(f"🖨️ Print started: {filename}")
                return {'success': True, 'message': f'Print started: {filename}'}
            else:
                return {'success': False, 'message': f'Failed to start print: {filename}'}
                
        except Exception as e:
            logger.error(f"Failed to start print: {e}")
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def pause_print(self) -> Dict[str, Any]:
        """Pause current print"""
        try:
            response = self._make_request('printer/print/pause', 'POST')
            
            if 'error' not in response:
                logger.info("⏸️ Print paused")
                return {'success': True, 'message': 'Print paused'}
            else:
                return {'success': False, 'message': 'Failed to pause print'}
                
        except Exception as e:
            logger.error(f"Failed to pause print: {e}")
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def resume_print(self) -> Dict[str, Any]:
        """Resume paused print"""
        try:
            response = self._make_request('printer/print/resume', 'POST')
            
            if 'error' not in response:
                logger.info("▶️ Print resumed")
                return {'success': True, 'message': 'Print resumed'}
            else:
                return {'success': False, 'message': 'Failed to resume print'}
                
        except Exception as e:
            logger.error(f"Failed to resume print: {e}")
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def cancel_print(self) -> Dict[str, Any]:
        """Cancel current print"""
        try:
            response = self._make_request('printer/print/cancel', 'POST')
            
            if 'error' not in response:
                logger.info("❌ Print cancelled")
                return {'success': True, 'message': 'Print cancelled'}
            else:
                return {'success': False, 'message': 'Failed to cancel print'}
                
        except Exception as e:
            logger.error(f"Failed to cancel print: {e}")
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def send_gcode(self, gcode: str) -> Dict[str, Any]:
        """Send G-code command to printer"""
        try:
            # Try using MoonrakerPy first
            printer = self._get_moonraker_printer()
            if printer:
                try:
                    printer.send_gcode(gcode)
                    logger.info(f"📝 G-code sent via MoonrakerPy: {gcode}")
                    return {'success': True, 'message': f'G-code sent: {gcode}'}
                except Exception as e:
                    logger.warning(f"MoonrakerPy send_gcode failed, trying direct API: {e}")
            
            # Fallback to direct API
            gcode_data = {'script': gcode}
            response = self._make_request('printer/gcode/script', 'POST', gcode_data)
            
            if 'error' not in response:
                logger.info(f"📝 G-code sent via API: {gcode}")
                return {'success': True, 'message': f'G-code sent: {gcode}'}
            else:
                return {'success': False, 'message': f'Failed to send G-code: {gcode}'}
                
        except Exception as e:
            logger.error(f"Failed to send G-code: {e}")
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def emergency_stop(self) -> Dict[str, Any]:
        """Emergency stop - immediate halt"""
        try:
            response = self._make_request('printer/emergency_stop', 'POST')
            
            if 'error' not in response:
                logger.warning("🚨 EMERGENCY STOP activated")
                return {'success': True, 'message': 'Emergency stop activated'}
            else:
                return {'success': False, 'message': 'Failed to activate emergency stop'}
                
        except Exception as e:
            logger.error(f"Failed to emergency stop: {e}")
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def home_axes(self, axes: Optional[str] = None) -> Dict[str, Any]:
        """Home printer axes (X, Y, Z, or all)"""
        try:
            if axes:
                gcode = f"G28 {axes.upper()}"
            else:
                gcode = "G28"  # Home all axes
            
            return self.send_gcode(gcode)
            
        except Exception as e:
            logger.error(f"Failed to home axes: {e}")
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def set_temperature(self, heater: str, temperature: float) -> Dict[str, Any]:
        """Set temperature for heater (bed, extruder)"""
        try:
            # Try using MoonrakerPy methods first
            printer = self._get_moonraker_printer()
            if printer:
                try:
                    if heater.lower() == 'bed':
                        printer.set_bed_temp(int(temperature))
                        logger.info(f"🌡️ Bed temperature set to {temperature}°C via MoonrakerPy")
                        return {'success': True, 'message': f'Bed temperature set to {temperature}°C'}
                    elif heater.lower() in ['extruder', 'hotend']:
                        printer.set_extruder_temp(int(temperature))
                        logger.info(f"🌡️ Extruder temperature set to {temperature}°C via MoonrakerPy")
                        return {'success': True, 'message': f'Extruder temperature set to {temperature}°C'}
                except Exception as e:
                    logger.warning(f"MoonrakerPy temperature setting failed, trying G-code: {e}")
            
            # Fallback to G-code commands
            if heater.lower() == 'bed':
                gcode = f"M140 S{temperature}"
            elif heater.lower() in ['extruder', 'hotend']:
                gcode = f"M104 S{temperature}"
            else:
                return {'success': False, 'message': f'Unknown heater: {heater}'}
            
            return self.send_gcode(gcode)
            
        except Exception as e:
            logger.error(f"Failed to set temperature: {e}")
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def is_printer_ready(self) -> bool:
        """Check if printer is ready for operations"""
        try:
            status = self.get_printer_status()
            
            if isinstance(status, dict):
                # Check if there's an error
                if 'error' in status:
                    return False
                
                # Check if state is ready and no active print
                state = status.get('state', '').lower()
                return state == 'ready'
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check printer readiness: {e}")
            return False
    
    def get_printer_info(self) -> Dict[str, Any]:
        """Get detailed printer information"""
        try:
            # Get comprehensive printer info
            server_info = self._make_request('server/info')
            printer_info = self._make_request('printer/info')
            
            return {
                'success': True,
                'server_info': server_info.get('result', {}),
                'printer_info': printer_info.get('result', {}),
                'connected': self.connected,
                'last_status': self._last_status.__dict__ if self._last_status else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get printer info: {e}")
            return {'success': False, 'message': f'Error: {str(e)}'}


# Convenience functions for backward compatibility
def create_mainsail_client() -> MainsailClient:
    """Create and return a MainsailClient instance"""
    return MainsailClient()

def test_printer_connection() -> bool:
    """Test printer connection"""
    client = MainsailClient()
    return client.test_connection()


# Example usage and testing
def main():
    """Example usage of MoonrakerPy-based MainsailClient"""
    client = MainsailClient()
    
    try:
        # Test connection
        print("🔗 Testing connection...")
        if not client.test_connection():
            print("❌ Connection failed")
            return
        
        # Get printer status
        print("\n🔍 Getting printer status...")
        status = client.get_printer_status()
        print(f"State: {status.state}")
        print(f"Bed: {status.bed_temp:.1f}°C / {status.bed_target:.1f}°C")
        print(f"Extruder: {status.extruder_temp:.1f}°C / {status.extruder_target:.1f}°C")
        print(f"Progress: {status.progress:.1%}")
        print(f"Z Position: {status.z_position:.2f}mm")
        
        # Get file list
        print("\n📁 Getting file list...")
        files = client.get_files()
        print(f"Found {len(files)} files")
        for file in files[:5]:  # Show first 5 files
            print(f"  - {file['display']} ({file['size']} bytes)")
        
        # Get printer info
        print("\n📊 Getting printer info...")
        info = client.get_printer_info()
        if info['success']:
            print("✅ Printer info retrieved successfully")
        
        # Send a simple G-code command
        print("\n📝 Testing G-code command...")
        result = client.send_gcode("M114")  # Get current position
        print(f"G-code result: {result}")
        
    except Exception as e:
        logger.error(f"Example failed: {e}")


if __name__ == "__main__":
    main()
    
    def test_connection(self) -> bool:
        """Test connection to Moonraker server"""
        try:
            client = self._get_moonraker_client()
            if not client:
                return False
                
            # Test with server info request
            server_info = client.get_server_info()
            if server_info and 'klippy_connected' in server_info:
                self.connected = True
                logger.info(f"✅ Connected to Moonraker server")
                return True
            else:
                logger.error("❌ Server info request failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Connection test failed: {e}")
            self.connected = False
            return False
    
    def get_printer_status(self) -> PrinterStatus:
        """Get current printer status"""
        try:
            client = self._get_moonraker_client()
            if not client:
                return PrinterStatus(state="disconnected")
            
            # Get printer objects
            printer_objects = client.get_printer_objects_query()
            if not printer_objects:
                return PrinterStatus(state="error")
            
            # Extract status information
            print_stats = printer_objects.get('print_stats', {})
            heater_bed = printer_objects.get('heater_bed', {})
            extruder = printer_objects.get('extruder', {})
            fan = printer_objects.get('fan', {})
            toolhead = printer_objects.get('toolhead', {})
            
            # Determine state
            state = print_stats.get('state', 'unknown').lower()
            if state == 'standby':
                state = 'ready'
            elif state in ['printing', 'paused', 'complete', 'cancelled', 'error']:
                pass  # Keep as is
            else:
                state = 'ready'
            
            # Create status object
            status = PrinterStatus(
                state=state,
                bed_temp=float(heater_bed.get('temperature', 0)),
                bed_target=float(heater_bed.get('target', 0)),
                extruder_temp=float(extruder.get('temperature', 0)),
                extruder_target=float(extruder.get('target', 0)),
                progress=float(print_stats.get('progress', 0)),
                print_time=int(print_stats.get('print_duration', 0)),
                filename=print_stats.get('filename'),
                fan_speed=float(fan.get('speed', 0)) * 100,  # Convert to percentage
                z_position=float(toolhead.get('position', [0,0,0,0])[2])
            )
            
            # Estimate time left if printing
            if status.progress > 0 and status.state == 'printing':
                estimated_total = status.print_time / status.progress
                status.time_left = int(estimated_total - status.print_time)
            
            self._last_status = status
            return status
            
        except Exception as e:
            logger.error(f"Failed to get printer status: {e}")
            return PrinterStatus(state="error")
    
    def get_files(self) -> List[Dict[str, Any]]:
        """Get list of G-code files"""
        try:
            client = self._get_moonraker_client()
            if not client:
                return []
            
            files_info = client.get_file_list()
            if not files_info:
                return []
            
            formatted_files = []
            for file_info in files_info.get('files', []):
                formatted_files.append({
                    'path': file_info.get('path', ''),
                    'display': file_info.get('path', '').split('/')[-1],  # Just filename
                    'size': file_info.get('size', 0),
                    'modified': file_info.get('modified', 0),
                    'type': 'gcode' if file_info.get('path', '').endswith('.gcode') else 'file'
                })
            
            return formatted_files
            
        except Exception as e:
            logger.error(f"Failed to get files: {e}")
            return []
    
    def upload_and_start_print(self, file_path: str, start_print: bool = True) -> Dict[str, Any]:
        """Upload G-code file and optionally start printing"""
        try:
            client = self._get_moonraker_client()
            if not client:
                return {'success': False, 'message': 'Not connected to printer'}
            
            file_path = Path(file_path)
            if not file_path.exists():
                return {'success': False, 'message': f'File not found: {file_path}'}
            
            logger.info(f"📤 Uploading {file_path.name}...")
            
            # Upload file
            upload_result = client.post_file_upload(str(file_path))
            if not upload_result:
                return {'success': False, 'message': 'Upload failed'}
            
            logger.info(f"✅ Upload successful: {file_path.name}")
            
            if start_print:
                # Start print
                filename = file_path.name
                print_result = client.post_printer_print_start(filename)
                
                if print_result:
                    logger.info(f"🖨️ Print started: {filename}")
                    return {
                        'success': True,
                        'message': f'Upload and print started: {filename}',
                        'filename': filename
                    }
                else:
                    return {
                        'success': False,
                        'message': f'Upload successful but failed to start print: {filename}'
                    }
            else:
                return {
                    'success': True,
                    'message': f'File uploaded successfully: {file_path.name}',
                    'filename': file_path.name
                }
                
        except Exception as e:
            logger.error(f"Failed to upload/start print: {e}")
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def start_print(self, filename: str) -> Dict[str, Any]:
        """Start printing a file that's already on the printer"""
        try:
            client = self._get_moonraker_client()
            if not client:
                return {'success': False, 'message': 'Not connected to printer'}
            
            result = client.post_printer_print_start(filename)
            
            if result:
                logger.info(f"🖨️ Print started: {filename}")
                return {'success': True, 'message': f'Print started: {filename}'}
            else:
                return {'success': False, 'message': f'Failed to start print: {filename}'}
                
        except Exception as e:
            logger.error(f"Failed to start print: {e}")
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def pause_print(self) -> Dict[str, Any]:
        """Pause current print"""
        try:
            client = self._get_moonraker_client()
            if not client:
                return {'success': False, 'message': 'Not connected to printer'}
            
            result = client.post_printer_print_pause()
            
            if result:
                logger.info("⏸️ Print paused")
                return {'success': True, 'message': 'Print paused'}
            else:
                return {'success': False, 'message': 'Failed to pause print'}
                
        except Exception as e:
            logger.error(f"Failed to pause print: {e}")
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def resume_print(self) -> Dict[str, Any]:
        """Resume paused print"""
        try:
            client = self._get_moonraker_client()
            if not client:
                return {'success': False, 'message': 'Not connected to printer'}
            
            result = client.post_printer_print_resume()
            
            if result:
                logger.info("▶️ Print resumed")
                return {'success': True, 'message': 'Print resumed'}
            else:
                return {'success': False, 'message': 'Failed to resume print'}
                
        except Exception as e:
            logger.error(f"Failed to resume print: {e}")
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def cancel_print(self) -> Dict[str, Any]:
        """Cancel current print"""
        try:
            client = self._get_moonraker_client()
            if not client:
                return {'success': False, 'message': 'Not connected to printer'}
            
            result = client.post_printer_print_cancel()
            
            if result:
                logger.info("❌ Print cancelled")
                return {'success': True, 'message': 'Print cancelled'}
            else:
                return {'success': False, 'message': 'Failed to cancel print'}
                
        except Exception as e:
            logger.error(f"Failed to cancel print: {e}")
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def send_gcode(self, gcode: str) -> Dict[str, Any]:
        """Send G-code command to printer"""
        try:
            client = self._get_moonraker_client()
            if not client:
                return {'success': False, 'message': 'Not connected to printer'}
            
            result = client.post_printer_gcode_script(gcode)
            
            if result:
                logger.info(f"📝 G-code sent: {gcode}")
                return {'success': True, 'message': f'G-code sent: {gcode}'}
            else:
                return {'success': False, 'message': f'Failed to send G-code: {gcode}'}
                
        except Exception as e:
            logger.error(f"Failed to send G-code: {e}")
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def emergency_stop(self) -> Dict[str, Any]:
        """Emergency stop - immediate halt"""
        try:
            client = self._get_moonraker_client()
            if not client:
                return {'success': False, 'message': 'Not connected to printer'}
            
            result = client.post_printer_emergency_stop()
            
            if result:
                logger.warning("🚨 EMERGENCY STOP activated")
                return {'success': True, 'message': 'Emergency stop activated'}
            else:
                return {'success': False, 'message': 'Failed to activate emergency stop'}
                
        except Exception as e:
            logger.error(f"Failed to emergency stop: {e}")
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def home_axes(self, axes: Optional[str] = None) -> Dict[str, Any]:
        """Home printer axes (X, Y, Z, or all)"""
        try:
            if axes:
                gcode = f"G28 {axes.upper()}"
            else:
                gcode = "G28"  # Home all axes
            
            return self.send_gcode(gcode)
            
        except Exception as e:
            logger.error(f"Failed to home axes: {e}")
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def set_temperature(self, heater: str, temperature: float) -> Dict[str, Any]:
        """Set temperature for heater (bed, extruder)"""
        try:
            if heater.lower() == 'bed':
                gcode = f"M140 S{temperature}"
            elif heater.lower() in ['extruder', 'hotend']:
                gcode = f"M104 S{temperature}"
            else:
                return {'success': False, 'message': f'Unknown heater: {heater}'}
            
            return self.send_gcode(gcode)
            
        except Exception as e:
            logger.error(f"Failed to set temperature: {e}")
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def get_printer_info(self) -> Dict[str, Any]:
        """Get detailed printer information"""
        try:
            client = self._get_moonraker_client()
            if not client:
                return {'success': False, 'message': 'Not connected to printer'}
            
            # Get comprehensive printer info
            server_info = client.get_server_info()
            printer_info = client.get_printer_info()
            
            return {
                'success': True,
                'server_info': server_info,
                'printer_info': printer_info,
                'connected': self.connected,
                'last_status': self._last_status.__dict__ if self._last_status else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get printer info: {e}")
            return {'success': False, 'message': f'Error: {str(e)}'}


# Convenience functions for backward compatibility
def create_mainsail_client() -> MainsailClient:
    """Create and return a MainsailClient instance"""
    return MainsailClient()

def test_printer_connection() -> bool:
    """Test printer connection"""
    client = MainsailClient()
    return client.test_connection()


# Example usage and testing
def main():
    """Example usage of MoonrakerPy-based MainsailClient"""
    client = MainsailClient()
    
    try:
        # Test connection
        print("🔗 Testing connection...")
        if not client.test_connection():
            print("❌ Connection failed")
            return
        
        # Get printer status
        print("\n🔍 Getting printer status...")
        status = client.get_printer_status()
        print(f"State: {status.state}")
        print(f"Bed: {status.bed_temp:.1f}°C / {status.bed_target:.1f}°C")
        print(f"Extruder: {status.extruder_temp:.1f}°C / {status.extruder_target:.1f}°C")
        print(f"Progress: {status.progress:.1%}")
        print(f"Z Position: {status.z_position:.2f}mm")
        
        # Get file list
        print("\n📁 Getting file list...")
        files = client.get_files()
        print(f"Found {len(files)} files")
        for file in files[:5]:  # Show first 5 files
            print(f"  - {file['display']} ({file['size']} bytes)")
        
        # Get printer info
        print("\n📊 Getting printer info...")
        info = client.get_printer_info()
        if info['success']:
            print("✅ Printer info retrieved successfully")
        
        # Send a simple G-code command
        print("\n📝 Testing G-code command...")
        result = client.send_gcode("M114")  # Get current position
        print(f"G-code result: {result}")
        
    except Exception as e:
        logger.error(f"Example failed: {e}")


if __name__ == "__main__":
    main()