#!/usr/bin/env python3
"""
GUI Module for Frame Conductor

Handles all user interface components and user interactions.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Callable, Optional
import signal

from utils.config_manager import ConfigManager
from sacn_sender import SACNSender


class ConfigVars:
    def __init__(self, config_manager, on_change_callback):
        self.config_manager = config_manager
        self.on_change_callback = on_change_callback
        config = self.config_manager.load_config()
        self.frame_var = tk.StringVar(value=str(config.get('total_frames', 1000)))
        self.fps_var = tk.StringVar(value=str(config.get('frame_rate', 30)))
        self.universe_var = tk.StringVar(value=str(config.get('universe', 999)))
        self.frame_length_var = tk.StringVar(value=str(config.get('frame_length', 512)))
        # Trace all changes to save config
        self.frame_var.trace_add('write', self._on_change)
        self.fps_var.trace_add('write', self._on_change)
        self.universe_var.trace_add('write', self._on_change)
        self.frame_length_var.trace_add('write', self._on_change)
    def _on_change(self, *args):
        self.on_change_callback()
    def to_dict(self):
        return {
            'total_frames': int(self.frame_var.get()),
            'frame_rate': int(self.fps_var.get()),
            'universe': int(self.universe_var.get()),
            'frame_length': int(self.frame_length_var.get())
        }
    def load(self):
        config = self.config_manager.load_config()
        self.frame_var.set(str(config.get('total_frames', 1000)))
        self.fps_var.set(str(config.get('frame_rate', 30)))
        self.universe_var.set(str(config.get('universe', 999)))
        self.frame_length_var.set(str(config.get('frame_length', 512)))

class FrameConductorGUI:
    """Main GUI class for the Frame Conductor application."""
    
    def __init__(self, root: tk.Tk):
        """
        Initialize the GUI.
        
        Args:
            root (tk.Tk): Tkinter root window
        """
        self.root = root
        self.root.title("Frame Conductor")
        self.root.geometry("400x700")
        self.root.resizable(False, False)
        
        # Initialize components
        self.config_manager = ConfigManager()
        self.sacn_sender = SACNSender()
        
        # GUI variables
        self.status_var = tk.StringVar(value="Ready")
        self.current_frame_var = tk.StringVar(value="0")
        self.target_frame_var = tk.StringVar(value="1000")
        self.fps_var = tk.StringVar(value="30")
        self.universe_var = tk.StringVar(value="999")
        self.frame_length_var = tk.StringVar(value="512")
        
        # GUI components
        self.start_button: Optional[ttk.Button] = None
        self.pause_button: Optional[ttk.Button] = None
        self.reset_button: Optional[ttk.Button] = None
        self.progress_var = tk.DoubleVar()
        self._shutdown_flag = False
        try:
            signal.signal(signal.SIGINT, self._on_keyboard_interrupt)
        except Exception:
            pass  # Signal may not be available on all platforms
        
        # Load configuration and setup GUI
        self.config_vars = ConfigVars(self.config_manager, self.save_config)
        self.setup_gui()
        self.load_config()
        self.setup_callbacks()
        self._periodic_check()
        
    def _on_keyboard_interrupt(self, signum, frame):
        self._shutdown_flag = True

    def _periodic_check(self):
        if self._shutdown_flag:
            self.on_closing()
        else:
            self.root.after(100, self._periodic_check)
        
    def load_config(self):
        """Load configuration from file and update GUI variables."""
        self.config_vars.load()
        self.target_frame_var.set(self.config_vars.frame_var.get())
        total_frames = int(self.target_frame_var.get()) if self.target_frame_var.get().isdigit() else 100
        self.progress_bar.config(maximum=total_frames)
        self.progress_var.set(0)
        self.progress_label.config(text=f"0 / {total_frames} (0%)")
        
    def save_config(self):
        """Save current configuration to file."""
        self.config_manager.save_config(self.config_vars.to_dict())
        
    def setup_gui(self):
        """Setup the GUI components."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Frame Conductor", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Configuration frame
        self._setup_config_frame(main_frame)
        
        # Status frame
        self._setup_status_frame(main_frame)
        
        # Control frame
        self._setup_control_frame(main_frame)
        
        # Progress frame
        self._setup_progress_frame(main_frame)
        
    def _setup_config_frame(self, parent):
        """Setup the configuration frame."""
        config_frame = ttk.LabelFrame(parent, text="Configuration", padding="10")
        config_frame.pack(fill="x", pady=(0, 20))
        
        # Target frame number
        ttk.Label(config_frame, text="Total Frames:").pack(anchor="w")
        frame_entry = ttk.Entry(config_frame, textvariable=self.config_vars.frame_var, width=20)
        frame_entry.pack(fill="x", pady=(5, 10))
        
        # Frame rate
        ttk.Label(config_frame, text="Frame Rate (fps):").pack(anchor="w")
        fps_frame = ttk.Frame(config_frame)
        fps_frame.pack(fill="x", pady=(5, 10))
        
        # FPS entry field
        fps_entry = ttk.Entry(fps_frame, textvariable=self.config_vars.fps_var, width=10)
        fps_entry.pack(side="left", padx=(0, 10))
        fps_entry.bind("<FocusOut>", self._on_fps_change)
        fps_entry.bind("<Return>", self._on_fps_change)
        
        # FPS preset buttons
        for fps in [15, 24, 25, 30, 60]:
            btn = ttk.Button(fps_frame, text=str(fps), width=3,
                           command=lambda f=fps: self._set_fps_preset(f))
            btn.pack(side="left", padx=(0, 2))
        
        # Save config button
        save_btn = ttk.Button(config_frame, text="💾 Save Config", 
                             command=self.save_config)
        save_btn.pack(fill="x", pady=(5, 0))
        
    def _setup_status_frame(self, parent):
        """Setup the status frame."""
        status_frame = ttk.LabelFrame(parent, text="Status", padding="10")
        status_frame.pack(fill="x", pady=(0, 20))
        
        # Status display
        ttk.Label(status_frame, text="Status:").pack(anchor="w")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                                font=("Arial", 10, "bold"))
        status_label.pack(anchor="w", pady=(5, 10))
        
        # Current frame display
        ttk.Label(status_frame, text="Current Frame:").pack(anchor="w")
        current_label = ttk.Label(status_frame, textvariable=self.current_frame_var, 
                                 font=("Arial", 12))
        current_label.pack(anchor="w", pady=(5, 10))
        
        # Target frame display
        ttk.Label(status_frame, text="Target Frame:").pack(anchor="w")
        target_label = ttk.Label(status_frame, textvariable=self.target_frame_var, 
                                font=("Arial", 12))
        target_label.pack(anchor="w", pady=(5, 10))
        
    def _setup_control_frame(self, parent):
        """Setup the control frame."""
        control_frame = ttk.LabelFrame(parent, text="Controls", padding="10")
        control_frame.pack(fill="x", pady=(0, 20))
        
        # Button frame
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill="x")
        
        # Start button
        self.start_button = ttk.Button(button_frame, text="▶ Start", 
                                      command=self._start_sending)
        self.start_button.pack(side="left", padx=(0, 10))
        
        # Pause button
        self.pause_button = ttk.Button(button_frame, text="⏸ Pause", 
                                      command=self._pause_sending, state="disabled")
        self.pause_button.pack(side="left", padx=(0, 10))
        
        # Reset button
        self.reset_button = ttk.Button(button_frame, text="🔄 Reset", 
                                      command=self._reset_sending)
        self.reset_button.pack(side="left")
        
    def _setup_progress_frame(self, parent):
        """Setup the progress frame."""
        progress_frame = ttk.LabelFrame(parent, text="Progress", padding="10")
        progress_frame.pack(fill="x")
        
        # Progress bar
        total_frames = int(self.target_frame_var.get()) if self.target_frame_var.get().isdigit() else 100
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=total_frames)
        self.progress_bar.pack(fill="x", pady=(5, 0))
        # Progress label
        self.progress_label = ttk.Label(progress_frame, text=f"0 / {total_frames} (0%)")
        self.progress_label.pack(anchor="center", pady=(5, 0))
        
    def setup_callbacks(self):
        """Setup callback functions."""
        self.sacn_sender.set_frame_callback(self._on_frame_sent)
        
    def _set_fps_preset(self, fps: int):
        """Set FPS to a preset value."""
        self.config_vars.fps_var.set(str(fps))
        
    def _on_fps_change(self, event=None):
        """Handle FPS value change from entry field."""
        try:
            fps = int(self.config_vars.fps_var.get())
            if fps <= 0 or fps > 120:
                self.config_vars.fps_var.set("30")  # Revert to default
        except ValueError:
            self.config_vars.fps_var.set("30")  # Revert to default
            
    def _on_universe_change(self, event=None):
        """Handle universe value change from entry field."""
        try:
            universe = int(self.config_vars.universe_var.get())
            if universe < 1 or universe > 63999:
                self.config_vars.universe_var.set("999")  # Revert to default
        except ValueError:
            self.config_vars.universe_var.set("999")  # Revert to default
        self.save_config()
            
    def _on_frame_length_change(self, event=None):
        """Handle frame length value change from entry field."""
        try:
            frame_length = int(self.config_vars.frame_length_var.get())
            if frame_length < 24 or frame_length > 512:
                self.config_vars.frame_length_var.set("512")  # Revert to default
        except ValueError:
            self.config_vars.frame_length_var.set("512")  # Revert to default
        self.save_config()
            
    def _start_sending(self):
        """Start sending sACN frames."""
        try:
            total_frames = int(self.config_vars.frame_var.get())
            if total_frames < 0 or total_frames > 65535:
                messagebox.showerror("Invalid Total Frames", "Total frames must be between 0 and 65535")
                return
                
            # Get FPS from GUI
            try:
                fps = int(self.config_vars.fps_var.get())
                if fps <= 0 or fps > 120:
                    messagebox.showerror("Invalid FPS", "FPS must be between 1 and 120")
                    return
            except ValueError:
                messagebox.showerror("Invalid FPS", "Please enter a valid FPS number")
                return
                
            try:
                universe = int(self.config_vars.universe_var.get())
                if universe < 1 or universe > 63999:
                    messagebox.showerror("Invalid Universe", "Universe must be between 1 and 63999")
                    return
            except ValueError:
                messagebox.showerror("Invalid Universe", "Please enter a valid universe number")
                return
                
            try:
                frame_length = int(self.config_vars.frame_length_var.get())
                if frame_length < 24 or frame_length > 512:
                    messagebox.showerror("Invalid Frame Length", "Frame length must be between 24 and 512")
                    return
            except ValueError:
                messagebox.showerror("Invalid Frame Length", "Please enter a valid frame length")
                return
                
            self.target_frame_var.set(str(total_frames))
            self.progress_bar.config(maximum=total_frames)
            self.progress_var.set(0)
            self.progress_label.config(text=f"0 / {total_frames} (0%)")
            
            # Save configuration
            self.save_config()
            
            # Check if sACN library is available
            if not self.sacn_sender.is_sacn_available():
                messagebox.showerror("sACN Not Available", 
                                   "sACN library is not installed. Install with: pip install sacn")
                return
                
            # Start sending
            self.sacn_sender.universe = universe
            self.sacn_sender.frame_length = frame_length
            if self.sacn_sender.start_sending(total_frames, fps):
                self.current_frame_var.set("0")
                self.progress_var.set(0)
                
                # Update GUI
                self.start_button.config(state="disabled")
                self.pause_button.config(state="normal")
                self.status_var.set("Sending frames...")
            else:
                messagebox.showerror("Error", "Failed to start sACN sender")
                
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid frame number")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start sending: {e}")
            
    def _pause_sending(self):
        """Pause/resume sending sACN frames."""
        self.sacn_sender.pause_sending()
        
        if self.sacn_sender.get_status() == "Paused":
            self.pause_button.config(text="▶ Resume")
            self.status_var.set("Paused")
        else:
            self.pause_button.config(text="⏸ Pause")
            self.status_var.set("Sending frames...")
            
    def _reset_sending(self):
        """Reset the sender to initial state."""
        self.sacn_sender.stop_sending()
        self.current_frame_var.set("0")
        self.progress_var.set(0)
        
        # Update GUI
        self.start_button.config(state="normal")
        self.pause_button.config(state="disabled", text="⏸ Pause")
        self.status_var.set("Ready")
        
    def _on_frame_sent(self, frame: int):
        """Callback when a frame is sent."""
        # Update GUI (thread-safe)
        self.root.after(0, self._update_gui, frame)
        
    def _update_gui(self, frame: int):
        """Update GUI elements (called from main thread)."""
        self.current_frame_var.set(str(frame))
        total_frames = self.sacn_sender.target_frame if hasattr(self.sacn_sender, 'target_frame') else int(self.target_frame_var.get())
        if total_frames > 0:
            self.progress_bar.config(maximum=total_frames)
            self.progress_var.set(frame)
            percent = int((frame / total_frames) * 100)
            self.progress_label.config(text=f"{frame} / {total_frames} ({percent}%)")
        # Check if sending is complete
        if frame >= total_frames:
            self._sending_complete()
            
    def _sending_complete(self):
        """Called when sending is complete."""
        self.start_button.config(state="normal")
        self.pause_button.config(state="disabled", text="⏸ Pause")
        self.status_var.set("Complete")
        
    def on_closing(self):
        """Handle application closing."""
        self.sacn_sender.stop_sending()
        self.root.destroy() 