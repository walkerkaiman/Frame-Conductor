#!/usr/bin/env python3
"""
Network Singleton Module for Frame Conductor

This module provides a network-wide singleton mechanism to ensure only one
instance of Frame Conductor runs per network. It uses UDP broadcasting to
detect and prevent multiple instances from running simultaneously.

Features:
    - Network-wide instance detection via UDP broadcasting
    - Periodic heartbeat messages to announce presence
    - Graceful handling of multiple instance detection
    - Configurable timeout and port settings
    - Thread-safe implementation with proper cleanup

Usage:
    singleton = NetworkSingleton(port=9001)
    if singleton.start():
        # Application can start safely
        try:
            # Your application code here
            pass
        finally:
            singleton.stop()
    else:
        # Another instance is already running
        sys.exit(1)
"""

import socket
import threading
import json
import time
from typing import Optional, Callable


class NetworkSingleton:
    """
    Network-wide singleton mechanism to ensure only one instance runs per network.
    
    Uses UDP broadcasting to detect if another instance is already running.
    Sends periodic heartbeat messages and listens for other instances.
    
    Attributes:
        port (int): UDP port for singleton communication
        socket (Optional[socket.socket]): UDP socket for communication
        is_running (bool): Whether the singleton mechanism is active
        heartbeat_thread (Optional[threading.Thread]): Thread for sending heartbeats
        listener_thread (Optional[threading.Thread]): Thread for listening to messages
        local_ip (str): Local IP address of this instance
        instance_id (str): Unique identifier for this instance
        timeout (int): Timeout for instance detection in seconds
        heartbeat_interval (int): Interval between heartbeat messages in seconds
        on_conflict_callback (Optional[Callable]): Callback when conflict is detected
    """
    
    def __init__(self, 
                 port: int = 9001, 
                 timeout: int = 5, 
                 heartbeat_interval: int = 2,
                 on_conflict_callback: Optional[Callable[[str], None]] = None):
        """
        Initialize the network singleton.
        
        Args:
            port (int): UDP port for singleton communication (default: 9001)
            timeout (int): Timeout for instance detection in seconds (default: 5)
            heartbeat_interval (int): Interval between heartbeat messages in seconds (default: 2)
            on_conflict_callback (Optional[Callable]): Callback when conflict is detected
        """
        self.port = port
        self.timeout = timeout
        self.heartbeat_interval = heartbeat_interval
        self.on_conflict_callback = on_conflict_callback
        
        self.socket: Optional[socket.socket] = None
        self.is_running = False
        self.heartbeat_thread: Optional[threading.Thread] = None
        self.listener_thread: Optional[threading.Thread] = None
        
        # Get local IP and create instance ID
        self.local_ip = self._get_local_ip()
        self.instance_id = f"{self.local_ip}:{self._get_backend_port()}:{self._get_frontend_port()}"
        
    def _get_local_ip(self) -> str:
        """
        Get the local IP address for network access.
        
        Returns:
            str: Local IP address, or "localhost" if detection fails
        """
        try:
            # Connect to a remote address to determine local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except:
            return "localhost"
    
    def _get_backend_port(self) -> int:
        """Get the backend port number."""
        return 9000  # Could be made configurable
    
    def _get_frontend_port(self) -> int:
        """Get the frontend port number."""
        return 5173  # Could be made configurable
        
    def start(self) -> bool:
        """
        Start the singleton mechanism.
        
        This method:
        1. Creates and configures the UDP socket
        2. Checks for existing instances on the network
        3. Starts heartbeat and listener threads if no conflicts detected
        
        Returns:
            bool: True if no other instance is running, False otherwise
        """
        try:
            # Create UDP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.socket.bind(('', self.port))
            self.socket.settimeout(1.0)
            
            # Check for existing instances
            if self._check_for_existing_instances():
                if self.on_conflict_callback:
                    self.on_conflict_callback(self.instance_id)
                return False
            
            # Start heartbeat and listener threads
            self.is_running = True
            self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
            self.listener_thread = threading.Thread(target=self._listener_loop, daemon=True)
            self.heartbeat_thread.start()
            self.listener_thread.start()
            
            print(f"[INFO] Network singleton started - this instance: {self.instance_id}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to start network singleton: {e}")
            return False
    
    def stop(self) -> None:
        """
        Stop the singleton mechanism and clean up resources.
        
        This method:
        1. Sets the running flag to False
        2. Closes the UDP socket
        3. Allows threads to terminate naturally
        """
        self.is_running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
    
    def is_active(self) -> bool:
        """
        Check if the singleton mechanism is currently active.
        
        Returns:
            bool: True if the singleton is running, False otherwise
        """
        return self.is_running and self.socket is not None
    
    def get_instance_id(self) -> str:
        """
        Get the unique identifier for this instance.
        
        Returns:
            str: Instance identifier
        """
        return self.instance_id
    
    def _check_for_existing_instances(self) -> bool:
        """
        Check if another instance is already running on the network.
        
        This method:
        1. Broadcasts an instance check message
        2. Listens for responses from other instances
        3. Returns True if another instance is detected
        
        Returns:
            bool: True if another instance is detected, False otherwise
        """
        print(f"[INFO] Checking for existing Frame Conductor instances...")
        
        # Send broadcast message to check for existing instances
        check_message = {
            "type": "instance_check",
            "instance_id": self.instance_id,
            "timestamp": time.time()
        }
        
        try:
            if not self.socket:
                return False
                
            # Broadcast the check message
            self.socket.sendto(json.dumps(check_message).encode(), ('<broadcast>', self.port))
            
            # Listen for responses
            start_time = time.time()
            while time.time() - start_time < self.timeout:
                try:
                    if not self.socket:
                        break
                    data, addr = self.socket.recvfrom(1024)
                    if addr[0] != self.local_ip:  # Ignore our own messages
                        response = json.loads(data.decode())
                        if response.get("type") == "instance_response":
                            other_instance = response.get("instance_id", "unknown")
                            print(f"[ERROR] Found existing instance: {other_instance} at {addr[0]}")
                            return True
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"[WARNING] Error checking for instances: {e}")
                    continue
            
            print(f"[INFO] No existing instances found")
            return False
            
        except Exception as e:
            print(f"[WARNING] Error during instance check: {e}")
            return False
    
    def _heartbeat_loop(self) -> None:
        """
        Send periodic heartbeat messages to announce this instance.
        
        This method runs in a background thread and sends heartbeat messages
        at regular intervals to announce the presence of this instance.
        """
        while self.is_running:
            try:
                if not self.socket:
                    break
                heartbeat_message = {
                    "type": "heartbeat",
                    "instance_id": self.instance_id,
                    "timestamp": time.time()
                }
                self.socket.sendto(json.dumps(heartbeat_message).encode(), ('<broadcast>', self.port))
                time.sleep(self.heartbeat_interval)
            except Exception as e:
                print(f"[WARNING] Error sending heartbeat: {e}")
                time.sleep(5)  # Wait longer on error
    
    def _listener_loop(self) -> None:
        """
        Listen for messages from other instances.
        
        This method runs in a background thread and listens for messages
        from other instances, responding to instance checks and logging heartbeats.
        """
        while self.is_running:
            try:
                if not self.socket:
                    break
                data, addr = self.socket.recvfrom(1024)
                if addr[0] == self.local_ip:  # Ignore our own messages
                    continue
                
                try:
                    message = json.loads(data.decode())
                    message_type = message.get("type")
                    
                    if message_type == "instance_check":
                        # Respond to instance check
                        if self.socket:
                            response = {
                                "type": "instance_response",
                                "instance_id": self.instance_id,
                                "timestamp": time.time()
                            }
                            self.socket.sendto(json.dumps(response).encode(), (addr[0], self.port))
                        
                    elif message_type == "heartbeat":
                        # Log other instance heartbeat
                        other_instance = message.get("instance_id", "unknown")
                        print(f"[WARNING] Detected another instance: {other_instance} at {addr[0]}")
                        
                except json.JSONDecodeError:
                    continue
                    
            except socket.timeout:
                continue
            except Exception as e:
                print(f"[WARNING] Error in listener loop: {e}")
                time.sleep(1)


def create_network_singleton(port: int = 9001, 
                           timeout: int = 5, 
                           heartbeat_interval: int = 2,
                           on_conflict_callback: Optional[Callable[[str], None]] = None) -> NetworkSingleton:
    """
    Factory function to create and configure a network singleton.
    
    Args:
        port (int): UDP port for singleton communication
        timeout (int): Timeout for instance detection in seconds
        heartbeat_interval (int): Interval between heartbeat messages in seconds
        on_conflict_callback (Optional[Callable]): Callback when conflict is detected
        
    Returns:
        NetworkSingleton: Configured network singleton instance
    """
    return NetworkSingleton(
        port=port,
        timeout=timeout,
        heartbeat_interval=heartbeat_interval,
        on_conflict_callback=on_conflict_callback
    ) 