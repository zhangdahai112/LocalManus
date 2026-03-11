#!/usr/bin/env python3
"""
Test script for the refactored Sandbox Manager
Demonstrates both LOCAL and ONLINE modes
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.firecracker_sandbox import SandboxManager, SandboxMode, SandboxClient
import json

def test_local_mode():
    """Test LOCAL mode - connecting to existing sandbox"""
    print("\n" + "="*60)
    print("Testing LOCAL Mode (http://192.168.126.132:8080)")
    print("="*60)
    
    manager = SandboxManager(
        mode=SandboxMode.LOCAL,
        local_url="http://192.168.126.132:8080"
    )
    
    user_id = "test_user_local"
    
    try:
        # Get sandbox info
        sandbox_info = manager.get_sandbox(user_id)
        print(f"\n✓ Sandbox Info:")
        print(f"  - ID: {sandbox_info.sandbox_id}")
        print(f"  - Base URL: {sandbox_info.base_url}")
        print(f"  - Mode: {sandbox_info.mode.value}")
        print(f"  - VNC URL: {sandbox_info.vnc_url}")
        print(f"  - VSCode URL: {sandbox_info.vscode_url}")
        print(f"  - Home Dir: {sandbox_info.home_dir}")
        
        # Get client
        client = manager.get_client(user_id)
        
        # Test 1: Get context
        print("\n✓ Test 1: Get Sandbox Context")
        context = client.get_context()
        print(f"  Context: {json.dumps(context, indent=2)}")
        
        # Test 2: Execute command
        print("\n✓ Test 2: Execute Shell Command")
        result = manager.execute_command(user_id, "echo 'Hello from LocalManus!' && pwd")
        print(f"  Output: {result.get('data', {}).get('output', 'N/A')}")
        
        # Test 3: Write file
        print("\n✓ Test 3: Write File")
        test_file = f"{sandbox_info.home_dir}/localmanus_test.txt"
        client.write_file(test_file, "Hello from LocalManus Sandbox!\n")
        print(f"  Written to: {test_file}")
        
        # Test 4: Read file
        print("\n✓ Test 4: Read File")
        content = client.read_file(test_file)
        print(f"  Content: {content}")
        
        # Test 5: List files
        print("\n✓ Test 5: List Files")
        files = client.list_files(sandbox_info.home_dir)
        print(f"  Files in {sandbox_info.home_dir}:")
        for f in files[:5]:  # Show first 5
            print(f"    - {f}")
        
        # Test 6: Browser info
        print("\n✓ Test 6: Get Browser Info")
        try:
            browser_info = client.get_browser_info()
            print(f"  CDP URL: {browser_info.get('data', {}).get('cdp_url', 'N/A')}")
        except Exception as e:
            print(f"  Browser info not available: {e}")
        
        print("\n" + "="*60)
        print("LOCAL Mode Tests Completed Successfully!")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ Error in LOCAL mode test: {e}")
        import traceback
        traceback.print_exc()

def test_online_mode():
    """Test ONLINE mode - spinning up Docker containers"""
    print("\n" + "="*60)
    print("Testing ONLINE Mode (Docker)")
    print("="*60)
    
    manager = SandboxManager(
        mode=SandboxMode.ONLINE,
        use_china_mirror=False  # Set to True if in China
    )
    
    user_id = "test_user_online"
    
    try:
        # Get/create sandbox
        sandbox_info = manager.get_sandbox(user_id)
        print(f"\n✓ Sandbox Created:")
        print(f"  - ID: {sandbox_info.sandbox_id}")
        print(f"  - Base URL: {sandbox_info.base_url}")
        print(f"  - Container ID: {sandbox_info.container_id}")
        print(f"  - VNC URL: {sandbox_info.vnc_url}")
        print(f"  - VSCode URL: {sandbox_info.vscode_url}")
        
        # Get client
        client = manager.get_client(user_id)
        
        # Test command execution
        print("\n✓ Test: Execute Command")
        result = manager.execute_command(user_id, "uname -a && whoami")
        print(f"  Output: {result.get('data', {}).get('output', 'N/A')}")
        
        # Test file operations
        print("\n✓ Test: File Operations")
        test_file = f"{sandbox_info.home_dir}/docker_test.txt"
        client.write_file(test_file, "Running in Docker container!\n")
        content = client.read_file(test_file)
        print(f"  Written and read: {content}")
        
        print("\n" + "="*60)
        print("ONLINE Mode Tests Completed Successfully!")
        print("="*60)
        
        # Cleanup
        print("\n✓ Cleaning up container...")
        manager.cleanup_sandbox(user_id)
        print("  Container removed")
        
    except Exception as e:
        print(f"\n✗ Error in ONLINE mode test: {e}")
        import traceback
        traceback.print_exc()
        
        # Attempt cleanup on error
        try:
            manager.cleanup_sandbox(user_id)
        except:
            pass

def test_direct_client():
    """Test direct SandboxClient usage"""
    print("\n" + "="*60)
    print("Testing Direct SandboxClient")
    print("="*60)
    
    client = SandboxClient("http://192.168.126.132:8080")
    
    try:
        # Test context
        print("\n✓ Getting context...")
        context = client.get_context()
        home_dir = context.get('data', {})
        # home_dir = context.get('data', {}).get('home_dir', '/home/gem')
        print(f"  Home directory: {home_dir}")
        
        # Test command
        print("\n✓ Executing command...")
        result = client.exec_command("ls -la ~")
        print(f"  Output: {result.get('data', {}).get('output', 'N/A')[:200]}...")
        
        print("\n" + "="*60)
        print("Direct Client Tests Completed Successfully!")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ Error in direct client test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Sandbox Manager")
    parser.add_argument('--mode', choices=['local', 'online', 'client', 'all'], 
                       default='all', help='Test mode to run')
    args = parser.parse_args()
    
    if args.mode in ['local', 'all']:
        test_local_mode()
    
    if args.mode in ['online', 'all']:
        test_online_mode()
    
    if args.mode in ['client', 'all']:
        test_direct_client()
    
    print("\n✓ All tests completed!")
