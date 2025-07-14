#!/usr/bin/env python3
"""
Test communication between Frame-Conductor sender and Interaction receiver
"""

import time
import threading
import sacn
from sacn_sender import SACNSender

def receiver_callback(packet):
    """Callback for received sACN packets"""
    print(f"✅ Received DMX data on universe {packet.universe}")
    print(f"   DMX data: {packet.dmxData[:5]}...")
    
    # Extract frame number from channels 1 and 2
    msb = packet.dmxData[0] if len(packet.dmxData) > 0 else 0
    lsb = packet.dmxData[1] if len(packet.dmxData) > 1 else 0
    frame_number = (msb << 8) | lsb
    print(f"   Frame number: {frame_number}")
    return frame_number

def test_receiver():
    """Test the receiver from Interaction project"""
    print("🔧 Starting sACN receiver test...")
    
    receiver = sacn.sACNreceiver()
    receiver.start()
    receiver.on_dmx_data_change = receiver_callback
    receiver.join_multicast(999)
    
    print("📡 Receiver listening on Universe 999...")
    
    # Listen for 10 seconds
    time.sleep(10)
    
    receiver.stop()
    print("🛑 Receiver stopped")

def test_sender():
    """Test the sender from Frame-Conductor project"""
    print("🔧 Starting Frame-Conductor sender test...")
    
    sender = SACNSender(universe=999)
    
    if not sender.is_sacn_available():
        print("❌ sACN library not available")
        return False
        
    print("✓ sACN library available")
    
    # Test sending frames
    if sender.start_sending(target_frame=5, frame_rate=2):
        print("✓ Started sending frames")
        
        # Wait for frames to be sent
        time.sleep(3)
        
        current_frame = sender.get_current_frame()
        status = sender.get_status()
        
        print(f"Current frame: {current_frame}")
        print(f"Status: {status}")
        
        # Stop sending
        sender.stop_sending()
        print("✓ Stopped sending frames")
        
    else:
        print("❌ Failed to start sending frames")
        return False
        
    return True

def test_direct_sacn():
    """Test direct sACN communication"""
    print("🔧 Testing direct sACN communication...")
    
    # Start receiver
    receiver = sacn.sACNreceiver()
    receiver.start()
    receiver.on_dmx_data_change = receiver_callback
    receiver.join_multicast(999)
    
    print("📡 Receiver listening on Universe 999...")
    
    # Wait for receiver to start
    time.sleep(1)
    
    # Start sender
    sender = sacn.sACNsender()
    sender.start()
    sender.activate_output(1)
    
    if sender[1] is not None:
        sender[1].universe = 999
        print(f"📡 Sender configured for Universe 999")
    
    # Send test frames
    for frame in range(1, 4):
        # Encode frame number
        msb = (frame >> 8) & 0xFF
        lsb = frame & 0xFF
        
        # Create DMX data
        dmx_data = [0] * 512
        dmx_data[0] = msb  # Channel 1
        dmx_data[1] = lsb  # Channel 2
        
        # Send data
        if sender[1] is not None:
            sender[1].dmx_data = tuple(dmx_data)
            print(f"📤 Sent frame {frame} (MSB: {msb}, LSB: {lsb})")
        
        time.sleep(1)  # Wait 1 second between frames
    
    # Clean up
    sender.stop()
    time.sleep(1)  # Wait for last packet
    receiver.stop()
    
    print("✅ Direct sACN test completed")

def main():
    """Run all communication tests"""
    print("=== sACN Communication Test ===\n")
    
    print("Test 1: Direct sACN Communication")
    print("-" * 40)
    test_direct_sacn()
    
    print("\nTest 2: Frame-Conductor Sender")
    print("-" * 40)
    test_sender()
    
    print("\nTest 3: Interaction Receiver")
    print("-" * 40)
    test_receiver()
    
    print("\n=== Test Summary ===")
    print("If you saw 'Received DMX data' messages above, communication is working!")
    print("If not, check:")
    print("1. Firewall settings (UDP port 5568)")
    print("2. Network interface configuration")
    print("3. Both programs running on same machine")

if __name__ == "__main__":
    main() 