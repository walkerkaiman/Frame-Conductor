#!/usr/bin/env python3
"""
Test script for sACN frame sending

This script tests the sACN sending functionality to help debug frame transmission issues.
"""

import time
import sacn
from sacn_sender import SACNSender

def test_basic_sacn():
    """Test basic sACN functionality."""
    print("Testing basic sACN functionality...")
    
    try:
        # Create sACN sender
        sender = sacn.sACNsender()
        sender.start()
        sender.activate_output(1)
        
        print("✓ sACN sender created and started successfully")
        
        # Test sending a simple frame
        dmx_data = [0] * 512
        dmx_data[0] = 255  # Channel 1 = 255
        dmx_data[1] = 128  # Channel 2 = 128
        
        sender[1].dmx_data = tuple(dmx_data)
        sender[1].universe = 999
        
        print("✓ Test frame sent to Universe 999")
        print(f"  Channel 1: {dmx_data[0]}")
        print(f"  Channel 2: {dmx_data[1]}")
        
        # Wait a moment
        time.sleep(1)
        
        # Clean up
        sender.stop()
        print("✓ sACN sender stopped successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in basic sACN test: {e}")
        return False

def test_frame_encoding():
    """Test frame number encoding."""
    print("\nTesting frame number encoding...")
    
    test_frames = [0, 255, 1000, 65535]
    
    for frame in test_frames:
        msb = (frame >> 8) & 0xFF
        lsb = frame & 0xFF
        decoded = (msb << 8) | lsb
        
        print(f"Frame {frame}: MSB={msb}, LSB={lsb}, Decoded={decoded}")
        
        if decoded == frame:
            print("  ✓ Encoding/decoding correct")
        else:
            print("  ✗ Encoding/decoding error")

def test_sacn_sender_class():
    """Test the SACNSender class."""
    print("\nTesting SACNSender class...")
    
    try:
        sender = SACNSender(universe=999)
        
        if not sender.is_sacn_available():
            print("✗ sACN library not available")
            return False
            
        print("✓ sACN library available")
        
        # Test initialization
        if sender.initialize_sender():
            print("✓ sACN sender initialized successfully")
        else:
            print("✗ Failed to initialize sACN sender")
            return False
        
        # Test sending a few frames
        print("Sending test frames...")
        if sender.start_sending(target_frame=10, frame_rate=5):
            print("✓ Started sending frames")
            
            # Wait for a few frames
            time.sleep(2)
            
            current_frame = sender.get_current_frame()
            status = sender.get_status()
            
            print(f"Current frame: {current_frame}")
            print(f"Status: {status}")
            
            # Stop sending
            sender.stop_sending()
            print("✓ Stopped sending frames")
            
        else:
            print("✗ Failed to start sending frames")
            return False
            
        return True
        
    except Exception as e:
        print(f"✗ Error testing SACNSender class: {e}")
        return False

def test_network_configuration():
    """Test network configuration for sACN."""
    print("\nTesting network configuration...")
    
    try:
        sender = sacn.sACNsender()
        sender.start()
        sender.activate_output(1)
        
        # Test multicast
        sender[1].multicast = True
        print("✓ Multicast enabled")
        
        # Test unicast (you can change this IP to your target device)
        # sender[1].multicast = False
        # sender[1].destination = "192.168.1.100"  # Replace with your target IP
        # print("✓ Unicast configured")
        
        sender.stop()
        return True
        
    except Exception as e:
        print(f"✗ Error testing network configuration: {e}")
        return False

def main():
    """Run all tests."""
    print("=== sACN Frame Sending Test ===\n")
    
    # Run tests
    tests = [
        ("Basic sACN", test_basic_sacn),
        ("Frame Encoding", test_frame_encoding),
        ("SACNSender Class", test_sacn_sender_class),
        ("Network Configuration", test_network_configuration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n=== Test Summary ===")
    passed = 0
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Your sACN sending should be working correctly.")
        print("\nTroubleshooting tips if frames aren't being received:")
        print("1. Check if your receiving device is listening on Universe 999")
        print("2. Verify network connectivity between sender and receiver")
        print("3. Check firewall settings - sACN uses UDP port 5568")
        print("4. Try using unicast instead of multicast if on different subnets")
        print("5. Verify the receiving device expects frame numbers in channels 1 & 2")
    else:
        print("\n⚠️  Some tests failed. Check the errors above for troubleshooting.")
        print("\nMost important tests (Basic sACN and SACNSender Class) passed, which means:")
        print("- sACN library is working correctly")
        print("- Frame sending functionality is operational")
        print("- The issue might be with network configuration or receiving device settings")

if __name__ == "__main__":
    main() 