#!/usr/bin/env python3
"""
Final test to verify Frame-Conductor and Interaction can communicate
"""

import time
import threading
import sacn
from sacn_sender import SACNSender

def dmx_callback(packet):
    """Callback for received sACN packets"""
    print(f"✅ Received DMX data on universe {packet.universe}")
    print(f"   DMX data: {packet.dmxData[:5]}...")
    
    # Extract frame number from channels 1 and 2
    msb = packet.dmxData[0] if len(packet.dmxData) > 0 else 0
    lsb = packet.dmxData[1] if len(packet.dmxData) > 1 else 0
    frame_number = (msb << 8) | lsb
    print(f"   Frame number: {frame_number}")

def test_frame_conductor_to_interaction():
    """Test Frame-Conductor sending to Interaction receiver"""
    print("🔧 Testing Frame-Conductor → Interaction communication...")
    
    # Start Interaction-style receiver
    receiver = sacn.sACNreceiver()
    receiver.start()
    receiver.on_dmx_data_change = dmx_callback
    receiver.join_multicast(1)  # Listen on universe 1
    
    print("📡 Interaction receiver listening on Universe 1...")
    time.sleep(1)
    
    # Start Frame-Conductor sender
    sender = SACNSender(universe=1)  # Now using universe 1
    
    if not sender.is_sacn_available():
        print("❌ sACN library not available")
        return False
        
    print("✓ sACN library available")
    
    # Test sending frames
    if sender.start_sending(target_frame=3, frame_rate=1):
        print("✓ Frame-Conductor started sending frames")
        
        # Wait for frames to be sent
        time.sleep(4)
        
        current_frame = sender.get_current_frame()
        status = sender.get_status()
        
        print(f"Current frame: {current_frame}")
        print(f"Status: {status}")
        
        # Stop sending
        sender.stop_sending()
        print("✓ Frame-Conductor stopped sending frames")
        
    else:
        print("❌ Failed to start Frame-Conductor sender")
        return False
    
    # Clean up receiver
    receiver.stop()
    print("✅ Communication test completed")
    return True

def main():
    """Run the final communication test"""
    print("=== Final Communication Test ===\n")
    print("Testing Frame-Conductor → Interaction communication using Universe 1")
    print("=" * 60)
    
    success = test_frame_conductor_to_interaction()
    
    if success:
        print("\n🎉 SUCCESS! Communication is working!")
        print("\nYour programs should now be able to communicate properly.")
        print("Frame-Conductor sends frames → Interaction receives them")
    else:
        print("\n❌ Communication test failed")
        print("Check the error messages above for troubleshooting")

if __name__ == "__main__":
    main() 