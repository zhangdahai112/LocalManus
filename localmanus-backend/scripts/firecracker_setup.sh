#!/bin/bash

# ==============================================================================
# LocalManus Firecracker Cluster Setup Script (Linux Native)
# ==============================================================================
# This script automates the installation of Firecracker, microVM components,
# and networking requirements.
#
# Requirements:
# - Linux Kernel 4.14+
# - KVM enabled (check: ls /dev/kvm)
# - Root privileges (sudo)
# ==============================================================================

set -e

# --- Configuration ---
INSTALL_DIR="/usr/local/bin"
DATA_DIR="/var/lib/localmanus"
FC_VERSION="v1.7.0"
ARCH=$(uname -m)

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}>>> Starting LocalManus Firecracker Setup...${NC}"

# 1. KVM Check
if [ ! -e /dev/kvm ]; then
    echo -e "${RED}Error: KVM is not enabled on this system.${NC}"
    exit 1
fi

# 2. Dependency Installation
echo "Installing system dependencies..."
if [ -f /etc/debian_version ]; then
    sudo apt-get update
    sudo apt-get install -y curl iproute2 iptables qemu-utils mtools xvfb x11vnc websockify bridge-utils
elif [ -f /etc/redhat-release ]; then
    sudo yum install -y curl iproute iptables qemu-img mtools xorg-x11-server-Xvfb x11vnc websockify
else
    echo "Unsupported distribution. Please install curl, iproute2, iptables, qemu-utils, xvfb, x11vnc, websockify manually."
fi

# 3. Firecracker Binary
echo "Downloading Firecracker ${FC_VERSION}..."
URL="https://github.com/firecracker-microvm/firecracker/releases/download/${FC_VERSION}/firecracker-${FC_VERSION}-${ARCH}.tgz"
curl -L ${URL} | tar -xz
sudo mv release-${FC_VERSION}-${ARCH} ${INSTALL_DIR}/firecracker
sudo chmod +x ${INSTALL_DIR}/firecracker

# 4. Workspace Preparation
sudo mkdir -p ${DATA_DIR}/images
sudo chown -R $USER:$USER ${DATA_DIR}
cd ${DATA_DIR}/images

# 5. Kernel & RootFS
echo "Downloading microVM-optimized kernel..."
if [ ! -f "vmlinux" ]; then
    curl -L https://s3.amazonaws.com/spec.ccfc.min/img/quickstart_guide/x86_64/kernels/vmlinux.bin -o vmlinux
fi

echo "Creating a base RootFS (Alpine-based simulated)..."
if [ ! -f "rootfs.ext4" ]; then
    # Create a 512MB blank ext4 filesystem
    truncate -s 512M rootfs.ext4
    mkfs.ext4 rootfs.ext4
    
    # Note: To make this bootable, you would typically mount it and 
    # install a mini rootfs (e.g., Alpine) and an init script.
    # For now, we provide the block device.
fi

# 6. Persistent Networking (Bridge)
echo "Configuring Host Bridge (br0)..."
if ! ip link show br0 > /dev/null 2>&1; then
    sudo ip link add name br0 type bridge
    sudo ip addr add 172.16.0.1/24 dev br0
    sudo ip link set br0 up
fi

# 7. NAT & Forwarding
echo "Enabling NAT for MicroVM internet access..."
sudo sysctl -w net.ipv4.ip_forward=1 > /dev/null
sudo iptables -t nat -A POSTROUTING -o $(ip route | grep default | awk '{print $5}' | head -n1) -j MASQUERADE
sudo iptables -A FORWARD -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
sudo iptables -A FORWARD -i br0 -j ACCEPT

# 8. Permissions
sudo chmod 666 /dev/kvm

echo -e "\n${GREEN}========================================================${NC}"
echo -e "${GREEN}Firecracker Cluster Setup Complete!${NC}"
echo -e "Binary: ${INSTALL_DIR}/firecracker"
echo -e "Data Directory: ${DATA_DIR}"
echo -e "Bridge IP: 172.16.0.1"
echo -e "========================================================\n"
echo "To integrate with LocalManus Backend:"
echo "1. Export environment variables:"
echo "   export FC_KERNEL_PATH=${DATA_DIR}/images/vmlinux"
echo "   export FC_ROOTFS_PATH=${DATA_DIR}/images/rootfs.ext4"
echo "2. Run the main server: python main.py"
