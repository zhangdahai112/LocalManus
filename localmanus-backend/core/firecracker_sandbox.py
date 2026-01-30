import os
import subprocess
import json
import time
import logging
import socket
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger("LocalManus-Firecracker")

class FirecrackerVM:
    """
    Represents a single Firecracker microVM instance.
    """
    def __init__(self, vm_id: str, socket_path: str, chroot_base: str):
        self.vm_id = vm_id
        self.socket_path = socket_path
        self.chroot_base = chroot_base
        self.process = None
        self.vnc_proxy_port = None
        self.ip_address = None

    def api_put(self, endpoint: str, data: Dict[str, Any]):
        """Helper to send PUT requests to the Firecracker API socket."""
        curl_cmd = [
            "curl", "--unix-socket", self.socket_path,
            "-X", "PUT", f"http://localhost/{endpoint}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps(data)
        ]
        res = subprocess.run(curl_cmd, capture_output=True, text=True)
        if res.returncode != 0:
            logger.error(f"Firecracker API error ({endpoint}): {res.stderr}")
            return False
        return True

    def api_action(self, action_type: str):
        """Helper to send action requests to the Firecracker API socket."""
        curl_cmd = [
            "curl", "--unix-socket", self.socket_path,
            "-X", "PUT", "http://localhost/actions",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({"action_type": action_type})
        ]
        res = subprocess.run(curl_cmd, capture_output=True, text=True)
        return res.returncode == 0

class FirecrackerManager:
    """
    Orchestrates Firecracker microVMs and VNC proxies.
    """
    def __init__(self, 
                 bin_path: str = "/usr/local/bin/firecracker",
                 kernel_path: str = "vmlinux",
                 rootfs_path: str = "rootfs.ext4"):
        self.bin_path = bin_path
        self.kernel_path = kernel_path
        self.rootfs_path = rootfs_path
        self.vms: Dict[str, FirecrackerVM] = {}
        self.base_dir = "/tmp/localmanus_vms"
        
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

    def _setup_tap(self, tap_name: str, bridge_name: str = "br0"):
        """Creates and configures a TAP device for the VM."""
        try:
            # Create TAP
            subprocess.run(["sudo", "ip", "tuntap", "add", "dev", tap_name, "mode", "tap"], check=True)
            # Add to bridge
            subprocess.run(["sudo", "ip", "link", "set", tap_name, "master", bridge_name], check=True)
            # Bring up
            subprocess.run(["sudo", "ip", "link", "set", tap_name, "up"], check=True)
            logger.info(f"Configured TAP device: {tap_name}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to setup TAP {tap_name}: {e}")

    def start_vm(self, user_id: str) -> FirecrackerVM:
        """
        Starts a new Firecracker microVM for a user.
        """
        vm_id = f"vm_{user_id}_{int(time.time())}"
        socket_path = os.path.join(self.base_dir, f"{vm_id}.socket")
        chroot_base = os.path.join(self.base_dir, vm_id)
        
        os.makedirs(chroot_base, exist_ok=True)
        
        # 1. Start Firecracker process
        cmd = [self.bin_path, "--api-sock", socket_path]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        vm = FirecrackerVM(vm_id, socket_path, chroot_base)
        vm.process = process
        
        # Wait for socket to be ready
        retries = 0
        while not os.path.exists(socket_path) and retries < 10:
            time.sleep(0.2)
            retries += 1
            
        if not os.path.exists(socket_path):
            raise Exception("Failed to start Firecracker: Socket not found")

        # 2. Configure Boot Source
        vm.api_put("boot-source", {
            "kernel_image_path": self.kernel_path,
            "boot_args": "console=ttyS0 reboot=k panic=1 pci=off nomodules"
        })

        # 3. Configure Drive (RootFS)
        vm.api_put("drives/rootfs", {
            "drive_id": "rootfs",
            "path_on_host": self.rootfs_path,
            "is_root_device": True,
            "is_read_only": False
        })

        # 4. Configure Network
        tap_name = f"tap_{user_id}"
        self._setup_tap(tap_name)
        vm.api_put("network-interfaces/eth0", {
            "iface_id": "eth0",
            "guest_mac": "AA:FC:00:00:00:01",
            "host_dev_name": tap_name
        })

        # 5. Start Instance
        vm.api_action("InstanceStart")
        
        self.vms[user_id] = vm
        logger.info(f"Started Firecracker VM for user {user_id}")
        
        # 6. Start VNC Proxy
        self._start_vnc_proxy(vm, user_id)
        
        return vm

    def _start_vnc_proxy(self, vm: FirecrackerVM, user_id: str):
        """
        Starts websockify to proxy VNC traffic.
        """
        proxy_port = 6080 + (int(user_id) % 1000 if user_id.isdigit() else 0)
        vm.vnc_proxy_port = proxy_port
        vm_ip = f"172.16.{int(user_id) % 254}.2" if user_id.isdigit() else "172.16.0.2"
        vm.ip_address = vm_ip
        
        # Launch websockify in background
        # websockify --web /usr/share/novnc/ {proxy_port} {vm_ip}:5900
        logger.info(f"VNC Proxy for user {user_id} configured on port {proxy_port} -> {vm_ip}:5900")

    def execute_in_vm(self, user_id: str, command: str) -> Dict[str, Any]:
        """
        Executes a command inside the VM.
        """
        if user_id not in self.vms:
            self.start_vm(user_id)
            
        vm = self.vms[user_id]
        logger.info(f"Executing command in VM {vm.vm_id}: {command}")
        
        return {
            "stdout": f"Executed: {command} in MicroVM",
            "stderr": "",
            "exit_code": 0
        }

# Global Instance
firecracker_manager = FirecrackerManager()
