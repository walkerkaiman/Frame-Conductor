#!/usr/bin/env python3
"""
sACN Sender Module for Frame Conductor

This module provides sACN (Streaming ACN) communication for sending frame numbers
to DMX universes. It handles the encoding of frame numbers into DMX channels and
manages the transmission timing.

Frame Encoding:
    Frame numbers are encoded using 2 DMX channels:
    - Channel 1: MSB (Most Significant Byte) - bits 8-15
    - Channel 2: LSB (Least Significant Byte) - bits 0-7
    - Full frame number: (MSB << 8) | LSB (range: 0-65535)

Features:
    - Threaded frame transmission with configurable frame rates
    - Pause/resume functionality
    - Frame callback system for progress tracking
    - Automatic sACN library initialization
    - Error handling and graceful degradation

Dependencies:
    - sacn: sACN library for DMX over Ethernet communication
    - threading: For background frame transmission
    - time: For frame timing control

Usage:
    sender = SACNSender(universe=999, frame_length=512)
    sender.set_frame_callback(lambda frame: print(f"Frame: {frame}"))
    sender.start_sending(target_frame=1000, frame_rate=30)
    sender.pause()  # or sender.resume()
    sender.stop_sending()
"""

import threading
import time
from typing import Optional, Callable

# Try to import sacn library
try:
    import sacn
    SACN_AVAILABLE = True
except ImportError:
    SACN_AVAILABLE = False
    print("Warning: sACN library not available. Install with: pip install sacn")


class SACNSender:
    """
    Handles sACN communication for sending frame numbers to DMX universes.
    
    This class manages the sACN sender lifecycle, frame encoding, and transmission
    timing. It provides a simple interface for starting, stopping, pausing, and
    resuming frame transmission with configurable parameters.
    
    Attributes:
        universe (int): sACN universe number to send to
        frame_length (int): Number of DMX channels (typically 512)
        sender: sACN sender instance
        is_running (bool): Whether transmission is currently active
        is_paused (bool): Whether transmission is paused
        current_frame (int): Current frame number being sent
        target_frame (int): Target frame number to send to
        frame_rate (int): Frame rate in frames per second
        sender_thread (threading.Thread): Background thread for frame transmission
        frame_callback (Optional[Callable]): Callback function for frame updates
    """
    
    def __init__(self, universe: int = 999, frame_length: int = 512):
        """
        Initialize the sACN sender.
        
        Args:
            universe (int): sACN universe to send to (default: 999)
            frame_length (int): DMX frame length in channels (default: 512)
        """
        self.universe = universe
        self.frame_length = frame_length
        self.sender = None
        self.is_running = False
        self.is_paused = False
        self.current_frame = 0
        self.target_frame = 0
        self.frame_rate = 30
        self.sender_thread: Optional[threading.Thread] = None
        self.frame_callback: Optional[Callable[[int], None]] = None
        self._initialize_sender_once()

    def _initialize_sender_once(self) -> bool:
        """
        Initialize the sACN sender if not already initialized.
        
        This method ensures the sACN sender is properly initialized and started.
        It's safe to call multiple times as it only initializes once.
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        if not SACN_AVAILABLE:
            return False
        if self.sender is not None:
            return True
        try:
            self.sender = sacn.sACNsender()
            self.sender.start()
            self.sender.activate_output(1)
            return True
        except Exception as e:
            print(f"Error initializing sACN sender: {e}")
            self.sender = None
            return False
    
    def set_frame_callback(self, callback: Callable[[int], None]) -> None:
        """
        Set callback function to be called when each frame is sent.
        
        The callback function will be called with the current frame number
        every time a frame is transmitted. This is useful for progress tracking
        and UI updates.
        
        Args:
            callback (Callable[[int], None]): Function called with current frame number
        """
        self.frame_callback = callback
    
    def start_sending(self, target_frame: int, frame_rate: int) -> bool:
        """
        Start sending sACN frames.
        
        This method starts the background thread that sends frames at the specified
        rate. If a transmission is already running, it will be stopped first.
        
        Args:
            target_frame (int): Target frame number to send to (0-65535)
            frame_rate (int): Frame rate in frames per second (1-120)
            
        Returns:
            bool: True if starting was successful, False otherwise
        """
        if not self._initialize_sender_once():
            return False
        
        self.target_frame = target_frame
        self.frame_rate = frame_rate
        self.is_running = True
        self.is_paused = False
        
        # Only reset current_frame if not already running
        if self.sender_thread is None or not self.sender_thread.is_alive():
            self.current_frame = 0
            self.sender_thread = threading.Thread(target=self._sender_loop, daemon=True)
            self.sender_thread.start()
        
        return True
    
    def pause(self) -> None:
        """
        Pause sending sACN frames.
        
        This method pauses the frame transmission. The sender thread continues
        running but stops sending frames. Use resume() to continue transmission.
        """
        self.is_paused = True

    def resume(self) -> None:
        """
        Resume sending sACN frames.
        
        This method resumes frame transmission after being paused.
        """
        self.is_paused = False

    def stop_sending(self) -> None:
        """
        Stop sending sACN frames and clean up resources.
        
        This method stops the frame transmission, resets the state, and cleans up
        the sACN sender resources. The sender can be restarted with start_sending().
        """
        self.is_running = False
        self.is_paused = False
        self.current_frame = 0
        
        # Stop sACN sender
        if self.sender:
            try:
                self.sender.stop()
                self.sender = None
            except Exception as e:
                print(f"Error stopping sACN sender: {e}")
        
        # Wait for thread to finish
        if self.sender_thread and self.sender_thread.is_alive():
            self.sender_thread.join(timeout=1.0)
    
    def get_current_frame(self) -> int:
        """
        Get the current frame number.
        
        Returns:
            int: Current frame number (0-based)
        """
        return self.current_frame
    
    def get_status(self) -> str:
        """
        Get the current status of the sender.
        
        Returns:
            str: Status string ("Running", "Paused", "Stopped")
        """
        if not self.is_running:
            return "Stopped"
        elif self.is_paused:
            return "Paused"
        else:
            return "Running"
    
    def _sender_loop(self) -> None:
        """
        Main loop for sending sACN frames.
        
        This method runs in a background thread and continuously sends frames
        at the specified frame rate. It handles pause/resume functionality and
        calls the frame callback for each transmitted frame.
        """
        frame_interval = 1.0 / self.frame_rate
        
        while self.is_running:
            # Handle pause state
            if self.is_paused:
                time.sleep(0.1)
                continue
            
            # Check if we've reached the target frame
            if self.current_frame > self.target_frame:
                time.sleep(0.1)
                continue
            
            try:
                # Encode frame number into DMX channels 1 and 2
                msb = (self.current_frame >> 8) & 0xFF  # Most significant byte
                lsb = self.current_frame & 0xFF         # Least significant byte
                
                # Create DMX data (frame_length channels, all zeros except channels 1 and 2)
                dmx_data = [0] * self.frame_length
                dmx_data[0] = msb  # Channel 1 (0-indexed)
                dmx_data[1] = lsb  # Channel 2 (0-indexed)
                
                # Send sACN data to the current universe
                dmx_tuple = tuple(dmx_data)
                self.sender[1].dmx_data = dmx_tuple  # type: ignore
                
                # Set universe (this might be handled differently in some versions)
                try:
                    self.sender[1].universe = self.universe  # type: ignore
                except:
                    pass  # Universe might be set differently
                
                # Call frame callback if set
                if self.frame_callback:
                    self.frame_callback(self.current_frame)
                
                # Increment frame
                self.current_frame += 1
                
                # Sleep for frame interval
                time.sleep(frame_interval)
                
            except Exception as e:
                print(f"Error sending frame {self.current_frame}: {e}")
                time.sleep(0.1)
    
    def is_sacn_available(self) -> bool:
        """
        Check if sACN library is available.
        
        Returns:
            bool: True if sACN library is available, False otherwise
        """
        return SACN_AVAILABLE 