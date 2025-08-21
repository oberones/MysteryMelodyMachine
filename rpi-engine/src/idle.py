"""Idle mode management for the generative engine.

Tracks user interaction and manages transition to/from ambient idle mode.
Phase 6: Idle mode detection and handling.
"""

from __future__ import annotations
from typing import Dict, Any, Optional, Callable
import time
import logging
import threading
from dataclasses import dataclass
from state import State, StateChange
from config import IdleConfig

log = logging.getLogger(__name__)


@dataclass
class IdleProfile:
    """Defines an ambient idle profile."""
    name: str
    params: Dict[str, Any]
    description: str


class IdleManager:
    """Manages idle mode detection and ambient profile switching.
    
    Tracks the last interaction timestamp and transitions to ambient mode
    after the configured timeout. Automatically reverts to active mode
    when new interactions are detected.
    """
    
    def __init__(self, config: IdleConfig, state: State):
        self.config = config
        self.state = state
        self.timeout_seconds = config.timeout_ms / 1000.0
        
        # Interaction tracking
        self.last_interaction_time = time.time()
        self.is_idle = False
        
        # State preservation
        self.saved_active_state: Optional[Dict[str, Any]] = None
        
        # Idle profiles
        self.idle_profiles = self._create_idle_profiles()
        self.current_profile = self.idle_profiles.get(config.ambient_profile)
        
        # Threading
        self._lock = threading.RLock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
        # Callbacks
        self._idle_state_callbacks: list[Callable[[bool], None]] = []
        
        log.info(f"idle_manager_init timeout={self.timeout_seconds:.1f}s profile={config.ambient_profile}")
    
    def _create_idle_profiles(self) -> Dict[str, IdleProfile]:
        """Create predefined idle profiles."""
        return {
            "slow_fade": IdleProfile(
                name="slow_fade",
                params={
                    'density': 0.3,          # Reduce note density
                    'bpm': 65.0,             # Slower tempo
                    'scale_index': 2,        # Switch to pentatonic (assumed index 2)
                    'reverb_mix': 90,        # More reverb
                    'filter_cutoff': 40,     # Darker filter
                    'master_volume': 60,     # Quieter
                },
                description="Slow, ambient fade with reduced density and darker tones"
            ),
            "minimal": IdleProfile(
                name="minimal",
                params={
                    'density': 0.15,
                    'bpm': 50.0,
                    'scale_index': 2,        # Pentatonic
                    'reverb_mix': 100,       # Full reverb
                    'swing': 0.05,           # Less swing
                    'master_volume': 40,     # Very quiet
                },
                description="Minimal ambient with very low density"
            ),
            "meditative": IdleProfile(
                name="meditative",
                params={
                    'density': 0.4,
                    'bpm': 72.0,
                    'scale_index': 1,        # Minor (assumed index 1)
                    'reverb_mix': 80,
                    'filter_cutoff': 30,     # Very dark
                    'swing': 0.0,            # No swing, straight
                    'master_volume': 50,
                },
                description="Meditative ambient with minor tonality"
            )
        }
    
    def add_idle_state_callback(self, callback: Callable[[bool], None]):
        """Add a callback to be notified of idle state changes."""
        with self._lock:
            self._idle_state_callbacks.append(callback)
    
    def remove_idle_state_callback(self, callback: Callable[[bool], None]):
        """Remove an idle state callback."""
        with self._lock:
            if callback in self._idle_state_callbacks:
                self._idle_state_callbacks.remove(callback)
    
    def start(self):
        """Start the idle detection thread."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._idle_monitor_thread, daemon=True)
        self._thread.start()
        log.info("idle_manager_started")
    
    def stop(self):
        """Stop the idle manager."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        log.info("idle_manager_stopped")
    
    def touch(self):
        """Record an interaction, resetting the idle timer."""
        with self._lock:
            self.last_interaction_time = time.time()
            
            # If we were idle, exit idle mode
            if self.is_idle:
                self._exit_idle_mode()
    
    def force_idle(self):
        """Force entry into idle mode (for testing/manual control)."""
        with self._lock:
            if not self.is_idle:
                self._enter_idle_mode()
    
    def force_active(self):
        """Force exit from idle mode (for testing/manual control)."""
        with self._lock:
            if self.is_idle:
                self._exit_idle_mode()
    
    def get_time_since_last_interaction(self) -> float:
        """Get time in seconds since last interaction."""
        with self._lock:
            return time.time() - self.last_interaction_time
    
    def get_time_to_idle(self) -> float:
        """Get time in seconds until idle mode (negative if already idle)."""
        if self.is_idle:
            return -1.0
        
        time_since = self.get_time_since_last_interaction()
        return max(0.0, self.timeout_seconds - time_since)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current idle manager status."""
        with self._lock:
            return {
                'is_idle': self.is_idle,
                'timeout_seconds': self.timeout_seconds,
                'time_since_last_interaction': self.get_time_since_last_interaction(),
                'time_to_idle': self.get_time_to_idle(),
                'current_profile': self.current_profile.name if self.current_profile else None,
                'saved_state_available': self.saved_active_state is not None,
            }
    
    def _idle_monitor_thread(self):
        """Main idle detection thread."""
        while self._running:
            try:
                with self._lock:
                    time_since_interaction = time.time() - self.last_interaction_time
                    
                    if not self.is_idle and time_since_interaction >= self.timeout_seconds:
                        self._enter_idle_mode()
                    
                # Check every second
                time.sleep(1.0)
                
            except Exception as e:
                log.error(f"idle_monitor_error error={e}")
                time.sleep(1.0)  # Continue despite errors
    
    def _enter_idle_mode(self):
        """Enter idle mode with ambient profile."""
        if self.is_idle:
            return
        
        log.info("idle_mode_enter")
        
        # Save current active state
        self.saved_active_state = {}
        if self.current_profile:
            for param in self.current_profile.params:
                current_value = self.state.get(param)
                if current_value is not None:
                    self.saved_active_state[param] = current_value
        
        log.debug(f"idle_state_saved params={list(self.saved_active_state.keys())}")
        
        # Apply idle profile
        if self.current_profile:
            applied_params = []
            for param, value in self.current_profile.params.items():
                success = self.state.set(param, value, source='idle')
                if success:
                    applied_params.append(param)
            
            log.info(f"idle_profile_applied profile={self.current_profile.name} params={applied_params}")
        
        self.is_idle = True
        
        # Notify callbacks
        self._notify_idle_state_callbacks(True)
        
        log.info(f"idle_mode_active profile={self.current_profile.name if self.current_profile else 'none'}")
    
    def _exit_idle_mode(self):
        """Exit idle mode and restore active state."""
        if not self.is_idle:
            return
        
        log.info("idle_mode_exit")
        
        # Restore saved active state
        if self.saved_active_state:
            restored_params = []
            for param, value in self.saved_active_state.items():
                success = self.state.set(param, value, source='idle_restore')
                if success:
                    restored_params.append(param)
            
            log.info(f"idle_state_restored params={restored_params}")
            self.saved_active_state = None
        
        self.is_idle = False
        
        # Update interaction time to prevent immediate re-entry
        self.last_interaction_time = time.time()
        
        # Notify callbacks
        self._notify_idle_state_callbacks(False)
        
        log.info("idle_mode_inactive")
    
    def _notify_idle_state_callbacks(self, is_idle: bool):
        """Notify all idle state callbacks."""
        for callback in self._idle_state_callbacks:
            try:
                callback(is_idle)
            except Exception as e:
                log.error(f"idle_callback_error callback={callback} error={e}")


def create_idle_manager(config: IdleConfig, state: State) -> IdleManager:
    """Factory function to create and configure an idle manager."""
    return IdleManager(config, state)
