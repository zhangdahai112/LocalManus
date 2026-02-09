# Firecracker Socket Error Troubleshooting Guide

## Problem: "Failed to open the API socket"

### Error Message
```
RunWithApiError error: Failed to open the API socket at: /run/firecracker.socket. 
Check that it is not already used.
Error: RunWithApi(FailedToBindSocket("/run/firecracker.socket"))
```

## Root Causes

1. **Stale Socket File**: Previous Firecracker instance crashed/terminated without cleanup
2. **Running Process**: Another Firecracker process is using the socket
3. **Permission Issues**: Insufficient permissions to create/use socket files
4. **Wrong Socket Path**: Process trying to use default `/run/firecracker.socket` instead of custom path

## Solutions

### Quick Fix (Manual Cleanup)
```bash
# Stop all Firecracker processes
sudo pkill -9 firecracker

# Remove stale sockets
sudo rm -f /run/firecracker.socket
sudo rm -f /tmp/localmanus_vms/*.socket

# Clean up TAP devices
for tap in $(ip link show | grep "tap_" | awk -F: '{print $2}' | tr -d ' '); do
    sudo ip link delete $tap 2>/dev/null || true
done
```

### Use the Automated Cleanup Script
```bash
# Run the cleanup script created during setup
sudo /var/lib/localmanus/cleanup_firecracker.sh
```

### Check for Running Processes
```bash
# List all Firecracker processes
ps aux | grep firecracker

# Check socket files
ls -la /tmp/localmanus_vms/*.socket
ls -la /run/firecracker.socket
```

### Verify Permissions
```bash
# Ensure proper permissions on KVM device
sudo chmod 666 /dev/kvm

# Ensure socket directory exists and has correct permissions
sudo mkdir -p /tmp/localmanus_vms
sudo chown -R $USER:$USER /tmp/localmanus_vms
sudo chmod 755 /tmp/localmanus_vms
```

## Prevention

### Automatic Cleanup (Built-in)
The updated `FirecrackerManager` now automatically:
- Cleans up stale sockets on initialization
- Removes existing socket files before starting new VMs
- Provides proper error messages with diagnostic information

### Proper Shutdown
Always use the cleanup method when stopping VMs:
```python
from core.firecracker_sandbox import firecracker_manager

# Cleanup specific VM
firecracker_manager.cleanup_vm(user_id="123")

# Or cleanup all
for user_id in list(firecracker_manager.vms.keys()):
    firecracker_manager.cleanup_vm(user_id)
```

### Pre-flight Checks
Before running LocalManus backend:
```bash
# 1. Verify Firecracker is installed
which firecracker

# 2. Check KVM is available
ls -la /dev/kvm

# 3. Run cleanup
sudo /var/lib/localmanus/cleanup_firecracker.sh

# 4. Start backend
cd localmanus-backend
python main.py
```

## Configuration

### Socket Path Configuration
LocalManus uses dynamic socket paths to avoid conflicts:
- Default: `/tmp/localmanus_vms/{vm_id}.socket`
- Each VM gets a unique socket based on `vm_{user_id}_{timestamp}`

### Environment Variables
```bash
export FC_KERNEL_PATH=/var/lib/localmanus/images/vmlinux
export FC_ROOTFS_PATH=/var/lib/localmanus/images/rootfs.ext4
```

## Debugging

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Firecracker Logs
```bash
# If running with systemd or docker, check logs
journalctl -u localmanus-backend -f

# Direct process stderr
# The updated code now captures and logs stderr output
```

### Test Firecracker Manually
```bash
# Test basic Firecracker startup
sudo firecracker --api-sock /tmp/test.socket

# In another terminal, test API
curl --unix-socket /tmp/test.socket \
  -X GET http://localhost/

# Cleanup
sudo pkill firecracker
sudo rm /tmp/test.socket
```

## Additional Resources

- [Firecracker Documentation](https://github.com/firecracker-microvm/firecracker/blob/main/docs/getting-started.md)
- [LocalManus Architecture](../../localmanus_architecture.md)
- [Setup Script](./firecracker_setup.sh)
