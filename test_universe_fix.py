#!/usr/bin/env python3
"""
Test to fix universe mismatch issue
"""

import sacn
import time

def dmx_callback(packet):
    print(f"✅ Received DMX data on universe {packet.universe}")
    print(f"   DMX data: {packet.dmxData[:5]}...")
    
    # Extract frame number from channels 1 and 2
    msb = packet.dmxData[0] if len(packet.dmxData) > 0 else 0
    lsb = packet.dmxData[1] if len(packet.dmxData) > 1 else 0
    frame_number = (msb << 8) | lsb
    print(f"   Frame number: {frame_number}")

def test_universe_1():
    """Test sending to universe 1"""
    print("🔧 Testing Universe 1...")
    
    # Start receiver
    receiver = sacn.sACNreceiver()
    receiver.start()
    receiver.on_dmx_data_change = dmx_callback
    receiver.join_multicast(1)  # Listen on universe 1
    
    print("📡 Receiver listening on Universe 1...")
    time.sleep(1)
    
    # Start sender
    sender = sacn.sACNsender()
    sender.start()
    sender.activate_output(1)
    
    if sender[1] is not None:
        sender[1].universe = 1  # Send to universe 1
        print(f"📡 Sender configured for Universe 1")
    
    # Send test frame
    dmx_data = [0] * 512
    dmx_data[0] = 0  # MSB
    dmx_data[1] = 42  # LSB
    
    if sender[1] is not None:
        sender[1].dmx_data = tuple(dmx_data)
        print(f"📤 Sent test frame to Universe 1")
    
    time.sleep(2)
    
    # Clean up
    sender.stop()
    receiver.stop()
    print("✅ Universe 1 test completed")

def test_universe_999():
    """Test sending to universe 999"""
    print("\n🔧 Testing Universe 999...")
    
    # Start receiver
    receiver = sacn.sACNreceiver()
    receiver.start()
    receiver.on_dmx_data_change = dmx_callback
    receiver.join_multicast(999)  # Listen on universe 999
    
    print("📡 Receiver listening on Universe 999...")
    time.sleep(1)
    
    # Start sender
    sender = sacn.sACNsender()
    sender.start()
    sender.activate_output(1)
    
    if sender[1] is not None:
        sender[1].universe = 999  # Send to universe 999
        print(f"📡 Sender configured for Universe 999")
    
    # Send test frame
    dmx_data = [0] * 512
    dmx_data[0] = 0  # MSB
    dmx_data[1] = 99  # LSB
    
    if sender[1] is not None:
        sender[1].dmx_data = tuple(dmx_data)
        print(f"📤 Sent test frame to Universe 999")
    
    time.sleep(2)
    
    # Clean up
    sender.stop()
    receiver.stop()
    print("✅ Universe 999 test completed")

def main():
    """Run universe tests"""
    print("=== Universe Mismatch Test ===\n")
    
    test_universe_1()
    test_universe_999()
    
    print("\n=== Solution ===")
    print("If Universe 1 works but Universe 999 doesn't:")
    print("1. Change your Frame-Conductor to send to Universe 1")
    print("2. Or change your Interaction receiver to listen on Universe 1")
    print("3. Or both programs to use a different universe (like 100)")

if __name__ == "__main__":
    main() 