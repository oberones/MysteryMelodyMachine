"""
Raspberry Pi compatible MIDI utilities with ALSA error handling.

This module provides enhanced MIDI port handling specifically for Raspberry Pi
systems where ALSA sequencer issues are common.
"""

from __future__ import annotations
import logging
import time
import subprocess
from typing import Optional, List, Tuple
import mido

log = logging.getLogger(__name__)


class RaspberryPiMidiHelper:
    """Helper class for handling MIDI on Raspberry Pi with ALSA issues."""
    
    @staticmethod
    def check_alsa_sequencer() -> bool:
        """Check if ALSA sequencer is properly loaded."""
        try:
            result = subprocess.run(['lsmod'], capture_output=True, text=True)
            if 'snd_seq' in result.stdout:
                log.info("ALSA sequencer module is loaded")
                return True
            else:
                log.warning("ALSA sequencer module not found")
                return False
        except Exception as e:
            log.error(f"Failed to check ALSA sequencer: {e}")
            return False
    
    @staticmethod
    def load_alsa_sequencer() -> bool:
        """Try to load ALSA sequencer module."""
        try:
            log.info("Attempting to load ALSA sequencer module...")
            result = subprocess.run(['sudo', 'modprobe', 'snd-seq'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                log.info("Successfully loaded ALSA sequencer module")
                return True
            else:
                log.error(f"Failed to load ALSA sequencer: {result.stderr}")
                return False
        except Exception as e:
            log.error(f"Exception loading ALSA sequencer: {e}")
            return False
    
    @staticmethod
    def get_alsa_clients() -> List[str]:
        """Get ALSA sequencer clients using aconnect."""
        try:
            result = subprocess.run(['aconnect', '-l'], capture_output=True, text=True)
            if result.returncode == 0:
                log.debug(f"ALSA clients:\n{result.stdout}")
                return result.stdout.split('\n')
            else:
                log.warning(f"aconnect failed: {result.stderr}")
                return []
        except Exception as e:
            log.error(f"Failed to get ALSA clients: {e}")
            return []
    
    @staticmethod
    def wait_for_device(device_pattern: str, timeout: float = 10.0) -> bool:
        """Wait for a USB MIDI device to appear."""
        log.info(f"Waiting for device matching '{device_pattern}' (timeout: {timeout}s)")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                ports = mido.get_input_names() + mido.get_output_names()
                for port in ports:
                    if device_pattern.lower() in port.lower():
                        log.info(f"Found device: {port}")
                        return True
            except Exception:
                pass
            
            time.sleep(0.5)
        
        log.warning(f"Device '{device_pattern}' not found within timeout")
        return False


class RobustMidiInput:
    """MIDI input with enhanced Raspberry Pi compatibility."""
    
    def __init__(self, port_name: str, callback, retry_attempts: int = 3):
        self.port_name = port_name
        self.callback = callback
        self.retry_attempts = retry_attempts
        self._port = None
        self._helper = RaspberryPiMidiHelper()
    
    @classmethod
    def create(cls, desired: str, callback, retry_attempts: int = 3):
        """Create MIDI input with auto-selection and retry logic."""
        if desired == "auto":
            name = cls._auto_select_with_fallback()
            if not name:
                raise RuntimeError("No MIDI input ports available after all retry attempts")
            log.info(f"Auto-selected MIDI input port: {name}")
        else:
            name = desired
        
        instance = cls(name, callback, retry_attempts)
        instance.open()
        return instance
    
    @classmethod
    def _auto_select_with_fallback(cls) -> Optional[str]:
        """Auto-select port with Raspberry Pi specific fallbacks."""
        helper = RaspberryPiMidiHelper()
        
        # First, ensure ALSA sequencer is loaded
        if not helper.check_alsa_sequencer():
            log.warning("ALSA sequencer not loaded, attempting to load...")
            if not helper.load_alsa_sequencer():
                log.error("Failed to load ALSA sequencer")
        
        # Try to get ports
        try:
            names = mido.get_input_names()
        except Exception as e:
            log.error(f"Failed to get input port names: {e}")
            return None
        
        if not names:
            log.warning("No MIDI input ports found")
            return None
        
        # Prefer Teensy devices
        for name in names:
            if "teensy" in name.lower():
                log.info(f"Found Teensy device: {name}")
                return name
        
        # Prefer other USB MIDI devices
        for name in names:
            if any(keyword in name.lower() for keyword in ["usb", "midi"]):
                log.info(f"Found USB MIDI device: {name}")
                return name
        
        # Fallback to first available
        log.info(f"Using first available port: {names[0]}")
        return names[0]
    
    def open(self):
        """Open MIDI input with retry logic."""
        last_error = None
        
        for attempt in range(self.retry_attempts):
            try:
                log.info(f"Opening MIDI input port '{self.port_name}' (attempt {attempt + 1}/{self.retry_attempts})")
                self._port = mido.open_input(self.port_name, callback=self._on_msg)
                log.info(f"Successfully opened MIDI input port: {self.port_name}")
                return
                
            except Exception as e:
                last_error = e
                log.warning(f"Attempt {attempt + 1} failed: {e}")
                
                if "ALSA error making port connection" in str(e):
                    # This is a common Raspberry Pi issue
                    log.info("Detected ALSA connection error, trying recovery...")
                    
                    # Wait a bit for device to stabilize
                    time.sleep(1.0)
                    
                    # Try refreshing port list
                    try:
                        mido.get_input_names()
                    except Exception:
                        pass
                
                if attempt < self.retry_attempts - 1:
                    wait_time = (attempt + 1) * 2  # Exponential backoff
                    log.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
        
        # All attempts failed
        raise RuntimeError(f"Failed to open MIDI input '{self.port_name}' after {self.retry_attempts} attempts: {last_error}")
    
    def close(self):
        """Close MIDI input port."""
        if self._port:
            try:
                log.info(f"Closing MIDI input port: {self.port_name}")
                self._port.close()
            except Exception as e:
                log.error(f"Error closing MIDI input port: {e}")
            finally:
                self._port = None
    
    def _on_msg(self, msg):
        """Handle incoming MIDI message."""
        log.debug(f"Received MIDI message: {msg}")
        try:
            self.callback(msg)
        except Exception:
            log.exception(f"Error handling MIDI message: {msg}")


class RobustMidiOutput:
    """MIDI output with enhanced Raspberry Pi compatibility."""
    
    def __init__(self, port_name: Optional[str] = None, channel: int = 1, retry_attempts: int = 3):
        self.port_name = port_name
        self.channel = channel
        self.retry_attempts = retry_attempts
        self.port = None
        self._is_connected = False
        self._helper = RaspberryPiMidiHelper()
        
        if port_name:
            self._connect()
    
    def _connect(self) -> bool:
        """Connect with enhanced error handling."""
        if not self.port_name:
            return False
        
        # Ensure ALSA sequencer is loaded
        if not self._helper.check_alsa_sequencer():
            log.warning("ALSA sequencer not loaded, attempting to load...")
            self._helper.load_alsa_sequencer()
        
        last_error = None
        
        for attempt in range(self.retry_attempts):
            try:
                # Handle auto port selection
                if self.port_name == "auto":
                    available_ports = mido.get_output_names()
                    if not available_ports:
                        log.warning("No MIDI output ports available")
                        return False
                    
                    # Filter out virtual/loopback ports
                    preferred_ports = [p for p in available_ports 
                                     if not any(keyword in p.lower() 
                                              for keyword in ['virtual', 'loopback', 'through'])]
                    
                    if preferred_ports:
                        self.port_name = preferred_ports[0]
                    else:
                        self.port_name = available_ports[0]
                    
                    log.info(f"Auto-selected MIDI output port: {self.port_name}")
                
                log.info(f"Connecting to MIDI output port '{self.port_name}' (attempt {attempt + 1}/{self.retry_attempts})")
                self.port = mido.open_output(self.port_name)
                self._is_connected = True
                log.info(f"Successfully connected to MIDI output port: {self.port_name}")
                return True
                
            except Exception as e:
                last_error = e
                log.warning(f"Connection attempt {attempt + 1} failed: {e}")
                
                if "ALSA error making port connection" in str(e):
                    log.info("Detected ALSA connection error, trying recovery...")
                    time.sleep(1.0)
                
                if attempt < self.retry_attempts - 1:
                    wait_time = (attempt + 1) * 2
                    log.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
        
        log.error(f"Failed to connect to MIDI output '{self.port_name}' after {self.retry_attempts} attempts: {last_error}")
        self.port = None
        self._is_connected = False
        return False
    
    def send_note_on(self, note: int, velocity: int, channel: Optional[int] = None) -> bool:
        """Send note on with connection retry."""
        if not self._ensure_connected():
            return False
        
        try:
            ch = (channel or self.channel) - 1
            msg = mido.Message('note_on', channel=ch, note=note, velocity=velocity)
            self.port.send(msg)
            log.debug(f"Sent Note On: note={note} velocity={velocity} channel={channel or self.channel}")
            return True
        except Exception as e:
            log.error(f"Failed to send Note On: {e}")
            self._is_connected = False
            return False
    
    def send_note_off(self, note: int, velocity: int = 0, channel: Optional[int] = None) -> bool:
        """Send note off with connection retry."""
        if not self._ensure_connected():
            return False
        
        try:
            ch = (channel or self.channel) - 1
            msg = mido.Message('note_off', channel=ch, note=note, velocity=velocity)
            self.port.send(msg)
            log.debug(f"Sent Note Off: note={note} velocity={velocity} channel={channel or self.channel}")
            return True
        except Exception as e:
            log.error(f"Failed to send Note Off: {e}")
            self._is_connected = False
            return False
    
    def send_control_change(self, control: int, value: int, channel: Optional[int] = None) -> bool:
        """Send control change with connection retry."""
        if not self._ensure_connected():
            return False
        
        try:
            ch = (channel or self.channel) - 1
            msg = mido.Message('control_change', channel=ch, control=control, value=value)
            self.port.send(msg)
            log.debug(f"Sent CC: control={control} value={value} channel={channel or self.channel}")
            return True
        except Exception as e:
            log.error(f"Failed to send Control Change: {e}")
            self._is_connected = False
            return False
    
    def _ensure_connected(self) -> bool:
        """Ensure connection with retry logic."""
        if self._is_connected and self.port:
            return True
        
        if self.port_name:
            return self._connect()
        
        return False
    
    def close(self):
        """Close MIDI output port."""
        if self.port:
            try:
                # Send all notes off before closing
                self.send_control_change(123, 0)
                self.port.close()
                log.info(f"Closed MIDI output port: {self.port_name}")
            except Exception as e:
                log.error(f"Error closing MIDI output port: {e}")
            finally:
                self.port = None
                self._is_connected = False
    
    @property
    def is_connected(self) -> bool:
        """Check if connected."""
        return self._is_connected
    
    @classmethod
    def create(cls, port_name: Optional[str], channel: int = 1, retry_attempts: int = 3):
        """Factory method with enhanced error handling."""
        if not port_name:
            log.info("MIDI output disabled (no port specified)")
            return None
        
        try:
            output = cls(port_name, channel, retry_attempts)
            if output.is_connected:
                return output
            else:
                log.warning("MIDI output creation failed - port not connected")
                return None
        except Exception as e:
            log.error(f"Failed to create MIDI output: {e}")
            return None


def get_system_info() -> dict:
    """Get system information relevant to MIDI debugging."""
    info = {}
    
    try:
        import platform
        info['platform'] = platform.platform()
        info['python_version'] = platform.python_version()
    except Exception:
        pass
    
    try:
        import mido
        info['mido_version'] = mido.__version__
        info['mido_backend'] = str(mido.backend)
    except Exception:
        pass
    
    try:
        result = subprocess.run(['aconnect', '-l'], capture_output=True, text=True)
        info['alsa_sequencer_working'] = result.returncode == 0
    except Exception:
        info['alsa_sequencer_working'] = False
    
    return info
