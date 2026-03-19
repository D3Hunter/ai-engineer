# VM Learning Notes (KVM/libvirt)

## What I understand now

- `qemu-img` manages disk images (create, inspect, resize, convert).
- `virt-install` creates/installs VMs and writes libvirt domain config.
- `virsh` inspects and manages existing libvirt objects (`domain`, `network`, `pool`, `volume`).

## Key terms

- `QEMU` = Quick Emulator.
- `COW` = Copy-On-Write.
- `qcow2` = QEMU Copy-On-Write v2 image format.
- `dom` in `virsh dom*` means **domain** (libvirt's VM object name).

## Units and defaults I should remember

- `virt-install --memory 4096` means `4096 MiB` (4 GiB).
- `--vcpus 16` is a CPU count, not exclusive CPU pinning.
- `virsh setmem/setmaxmem` use KiB units.
- `--disk size=200` means 200 GiB virtual disk size.

## Create network `mycustomnet` (NAT + DHCP) example

```bash
NET="mycustomnet"
NET_XML="/tmp/${NET}.xml"

cat > "$NET_XML" <<'EOF'
<network>
  <name>mycustomnet</name>
  <forward mode='nat'/>
  <bridge name='virbr20' stp='on' delay='0'/>
  <ip address='192.168.120.1' netmask='255.255.255.0'>
    <dhcp>
      <range start='192.168.120.100' end='192.168.120.254'/>
    </dhcp>
  </ip>
</network>
EOF

virsh net-define "$NET_XML"
virsh net-start "$NET"
virsh net-autostart "$NET"
virsh net-info "$NET"
```

Notes:

- This creates a libvirt NAT network with DHCP pool `192.168.120.100-254`.
- If `virbr20` already exists, change bridge name in XML.

## Example script: create one VM with 8 CPU, 16 GiB RAM, 500 GiB disk, and network

```bash
#!/usr/bin/env bash
set -euo pipefail

VM="vm-demo-01"
POOL="disk1"
NET="mycustomnet"
ISO="/var/lib/libvirt/boot/Rocky-9.5-x86_64-dvd.iso"
NET_XML="/tmp/${NET}.xml"

# Preconditions
virsh pool-info "$POOL" >/dev/null
test -f "$ISO"

# Create network if it does not exist
if ! virsh net-info "$NET" >/dev/null 2>&1; then
  cat > "$NET_XML" <<'EOF'
<network>
  <name>mycustomnet</name>
  <forward mode='nat'/>
  <bridge name='virbr20' stp='on' delay='0'/>
  <ip address='192.168.120.1' netmask='255.255.255.0'>
    <dhcp>
      <range start='192.168.120.100' end='192.168.120.254'/>
    </dhcp>
  </ip>
</network>
EOF
  virsh net-define "$NET_XML"
  virsh net-start "$NET"
  virsh net-autostart "$NET"
fi

virt-install \
  --name "$VM" \
  --vcpus 8 \
  --memory 16384 \
  --cpu host \
  --disk pool="$POOL",size=500,device=disk,bus=virtio,format=qcow2 \
  --cdrom "$ISO" \
  --network network="$NET",model=virtio \
  --graphics vnc \
  --os-variant rocky9 \
  --noautoconsole
```

Quick checks after creation:

```bash
virsh list --all
virsh dominfo "$VM"
virsh domblklist "$VM" --details
virsh domiflist "$VM"
virsh domifaddr "$VM" --source lease
```

Notes:

- `--memory 16384` = 16 GiB (unit is MiB).
- `size=500` = 500 GiB virtual disk.
- If `"$NET"` is NAT/DHCP network, VM should have outbound network after install.
- If `"$NET"` is bridge/direct network, IP assignment depends on your external DHCP/LAN.

## Persistence and lifecycle

- Normal `virt-install` creates a persistent VM (already defined).
- `virsh define` registers XML config only; it does not start the VM.
- `virsh create` starts a transient VM from XML.

## Remove a shut-off VM from list

If a VM is in `shut off` state and I want to remove it from `virsh list --all`, I need to undefine it.

```bash
VM="vm-demo-01"

# Keep disk files, remove VM definition
virsh undefine "$VM"

# UEFI/NVRAM case
virsh undefine "$VM" --nvram

# Remove definition and all attached storage (dangerous)
virsh undefine "$VM" --remove-all-storage --nvram
```

Notes:

- `undefine` removes persistent config, so VM disappears from list.
- If snapshots exist, I may need to remove snapshot metadata first.

## Change CPU/memory of an existing VM

Most reliable way: change config while VM is shut off.

```bash
VM="vm-demo-01"

# 1) Shut down VM first (recommended for reducing resources)
virsh shutdown "$VM"
virsh list --all

# 2) Set vCPU count (persistent config)
virsh setvcpus "$VM" 8 --config

# 3) Set memory (virsh units here are KiB)
# 16 GiB = 16 * 1024 * 1024 = 16777216 KiB
virsh setmaxmem "$VM" 16777216 --config
virsh setmem    "$VM" 16777216 --config

# 4) Start and verify
virsh start "$VM"
virsh vcpucount "$VM"
virsh dominfo "$VM"
```

Notes:

- `setvcpus` takes a CPU count, not a size unit.
- `setmem/setmaxmem` in `virsh` use KiB by default.
- Live decrease on running VM may fail (guest/hypervisor hot-unplug limits).
- Alternative method: `virsh edit "$VM"` and set `<vcpu>`, `<memory unit='MiB'>`, and `<currentMemory unit='MiB'>`.

## Storage model

- Pool = storage backend container.
- Volume = disk object inside a pool.
- VM disk attachment = actual source used by VM (file path or block device).

Useful checks:

```bash
virsh pool-list --all
virsh pool-dumpxml "$POOL"
virsh vol-list "$POOL" --details
virsh domblklist "$VM" --details
```

## Find image list and image location

`qemu-img` does not keep a global image registry. Listing usually comes from libvirt pools/volumes.

```bash
# List pools and volumes
virsh pool-list --all
virsh vol-list "$POOL" --details

# Exact path of a known volume in a pool
virsh vol-path --pool "$POOL" "$VOL"

# Exact disk source for a VM
virsh domblklist "$VM" --details
```

If I only have a volume name and do not know the pool:

```bash
VOL="rocky-vm.qcow2"
for POOL in $(virsh pool-list --name); do
  PATH_FOUND=$(virsh vol-path --pool "$POOL" "$VOL" 2>/dev/null || true)
  if [ -n "$PATH_FOUND" ]; then
    echo "$VOL -> $PATH_FOUND (pool: $POOL)"
  fi
done
```

If `qemu-img info "$NAME"` works without a path, it is usually being resolved from current directory or a directly reachable path/device. Use `realpath -e "$NAME"` when possible.

## Check per-disk size limit for each VM block target

`virsh domblklist` shows mapping only; it does not show capacity. Use `domblkinfo`.

```bash
VM="vm-demo-01"
for TGT in $(virsh domblklist "$VM" --details | awk 'NR>2 && $3 != "-" {print $3}'); do
  echo "=== $TGT ==="
  virsh domblkinfo "$VM" "$TGT" --human
done
```

Key fields:

- `Capacity`: guest-visible max size.
- `Allocation/Physical`: currently allocated host space.

## Disk behavior and capacity

- `qcow2` is usually thin-provisioned: file grows as data is written.
- A 200 GiB qcow2 does not consume 200 GiB immediately.
- Disk can be enlarged later (host-side resize + guest filesystem/LVM expansion).

## Network understanding

- `--network` sets NIC attachment for this VM.
- Backend network/bridge can be shared by multiple VMs.
- Interface config is per VM; backend object is often shared.

Useful checks:

```bash
virsh domiflist "$VM"
virsh dumpxml "$VM" --inactive
virsh domifaddr "$VM" --source lease
```

## `net-define` vs start/autostart

`virsh net-define` only registers network XML; it does not bring the network up.

```bash
NET="mycustomnet"

virsh net-list --all
virsh net-info "$NET"
virsh net-dumpxml "$NET" --inactive

# Start now
virsh net-start "$NET"

# Start automatically on host boot
virsh net-autostart "$NET"
```

Use `net-dumpxml --inactive` to inspect defined config even when network is not running.

## Host port mapping checks (display vs service forwarding)

Two different things:

1. VM display port (VNC/SPICE):

```bash
VM="vm-demo-01"
virsh domdisplay "$VM"
virsh vncdisplay "$VM"
```

2. Host-to-guest service forwarding (SSH/RDP/app ports):

```bash
VM="vm-demo-01"
virsh dumpxml "$VM" | grep -Ei 'hostfwd|portForward|redir|forward'
sudo nft list ruleset | grep -Ei 'dnat|libvirt|virbr'
# legacy systems:
sudo iptables -t nat -S | grep -Ei 'DNAT|LIBVIRT|dpt:'
```

Display port is not the same as service port-forwarding.

## How to check VM IP (which source to use)

- `agent`: best when `qemu-guest-agent` is installed and running in guest.
- `lease`: works for libvirt-managed DHCP network (for example NAT `default`-like networks).
- `arp`: fallback, less reliable.

```bash
VM="vm-demo-01"
virsh domifaddr "$VM" --source agent
virsh domifaddr "$VM" --source lease
virsh domifaddr "$VM" --source arp
```

If using NAT/DHCP network, also check:

```bash
NET="mycustomnet"
virsh net-dhcp-leases "$NET"
```

If none returns data, check inside guest with `ip a`.

## Common host paths (libvirt/KVM)

- `/var/lib/libvirt/boot/`: common place to store installer ISO files.
- `/var/lib/libvirt/images/`: common default directory pool path for VM disk files.
- `/etc/libvirt/qemu/`: persistent domain XML files.
- `/etc/libvirt/qemu/networks/`: persistent network XML files.
- `/var/lib/libvirt/dnsmasq/`: DHCP lease files for libvirt NAT networks.
- `/var/log/libvirt/qemu/`: per-VM QEMU logs.
- `/run/libvirt/`: runtime sockets and process state.

Important:

- Not every host uses `/var/lib/libvirt/images/`; your real disk path depends on pool config.
- Always confirm pool target path with:

```bash
virsh pool-dumpxml "$POOL" | grep -E '<path>|pool type'
```

## No `default` pool case

A host may have no pool literally named `default`; pool names are just labels.

```bash
virsh pool-list --all
virsh pool-list --all --name | grep -x default || echo "no default pool"
```

To map a disk file to its owning pool by path prefix:

```bash
DISK="/DATA/disk1/rocky-vm.qcow2"
for POOL in $(virsh pool-list --name); do
  TARGET=$(virsh pool-dumpxml "$POOL" | awk -F'[<>]' '/<path>/{print $3; exit}')
  case "$DISK" in
    "$TARGET"/*) echo "$DISK -> pool: $POOL" ;;
  esac
done
```

## Important safety notes

- If VM uses raw block device (for example `/dev/nvme1n1`), do not mount/write it on host at the same time.
- Use `domblklist` + `lsblk` + `blkid` to confirm what a disk source really is.
- Host can inspect guest disk contents offline (for example with `guestmount`), but avoid read-write mount while VM is running.
- If guest disk is encrypted (LUKS/BitLocker), host still sees raw blocks but cannot read plaintext without keys.

Read-only host inspection example:

```bash
VM="vm-demo-01"
sudo guestmount -d "$VM" -i --ro /mnt/vm
ls /mnt/vm
sudo guestunmount /mnt/vm
```

## Headless install playbook (terminal-only host)

If host has no GUI, avoid VNC-first workflow and install through serial text mode.

```bash
VM="vm-demo-01"
NET="mycustomnet"
ISO="/var/lib/libvirt/boot/Rocky-9.5-x86_64-dvd.iso"

test -f "$ISO"

virt-install \
  --name "$VM" \
  --vcpus 8 \
  --memory 16384 \
  --disk path="/var/lib/libvirt/images/${VM}.qcow2",size=200,device=disk,bus=virtio,format=qcow2 \
  --location "$ISO",kernel=images/pxeboot/vmlinuz,initrd=images/pxeboot/initrd.img \
  --network network="$NET",model=virtio \
  --graphics none \
  --console pty,target_type=serial \
  --extra-args "inst.text inst.cmdline console=tty0 console=ttyS0,115200n8" \
  --os-variant rocky9
```

Notes:

- If `--disk path=...` points to a non-existent file, include `size=...` so `virt-install` can create it.
- `--location` is preferred for serial/text installer boot args; `--cdrom` does not accept `--extra-args`.
- For non-blocking launch, add `--noautoconsole --wait 0` and attach later with `virsh console "$VM"`.

## Progress and completion checks (no GUI required)

```bash
VM="vm-demo-01"
NET="mycustomnet"

virsh domstate "$VM"
tail -f "/var/log/libvirt/qemu/${VM}.log"
virsh domiflist "$VM"

# Correct MAC extraction: Type is column 2, Source is column 3
MAC="$(virsh domiflist "$VM" | awk -v net="$NET" 'NR>2 && $2=="network" && $3==net {print $5; exit}')"
virsh net-dhcp-leases "$NET" | grep -i "$MAC" || echo "No DHCP lease for $VM"
```

Interpretation:

- `No DHCP lease` means guest has not requested DHCP yet (guest NIC down, installer not finished, or wrong network inside guest).
- `ssh: connect to host <ip> port 22: Connection refused` means network path is okay, but guest `sshd` is not listening yet.

## Serial console and VNC port mapping

Serial console:

```bash
VM="vm-demo-01"
virsh console "$VM"
```

- Exit with `Ctrl + ]`.
- If console is connected but blank, guest may not be outputting to `ttyS0` (check kernel args/grub config in guest).

VNC mapping (when needed):

```bash
VM="vm-demo-01"
virsh vncdisplay "$VM"
```

- Display `:1` means TCP port `5901` (`5900 + 1`).
- If VNC listens on `127.0.0.1`, tunnel from another machine:

```bash
ssh -L 5901:127.0.0.1:5901 root@<host>
```

Then open VNC client to `127.0.0.1:5901` on local machine.

## SSH reachability on libvirt NAT network

Inside host:

```bash
ssh <vm_user>@<vm_ip>
```

From another machine, forward host port to guest `22` (example `2222 -> VM:22`):

```bash
NET_ZONE="public"
VM_IP="192.168.120.10"
HOST_PORT=2222

firewall-cmd --zone="$NET_ZONE" --permanent --add-masquerade
firewall-cmd --zone="$NET_ZONE" --permanent \
  --add-forward-port=port="$HOST_PORT":proto=tcp:toaddr="$VM_IP":toport=22
firewall-cmd --zone="$NET_ZONE" --permanent --add-port="$HOST_PORT"/tcp
firewall-cmd --reload
```

Remote client connects with:

```bash
ssh -p 2222 <vm_user>@<host_ip_or_dns>
```

## Pin VM IP with libvirt DHCP reservation

```bash
VM="vm-demo-01"
NET="mycustomnet"
VM_IP="192.168.120.10"

MAC="$(virsh domiflist "$VM" | awk -v net="$NET" 'NR>2 && $2=="network" && $3==net {print $5; exit}')"
virsh net-update "$NET" add-last ip-dhcp-host \
  "<host mac='$MAC' name='$VM' ip='$VM_IP'/>" \
  --live --config
```

Verify:

```bash
virsh net-dumpxml "$NET" --inactive | sed -n '/<dhcp>/,/<\/dhcp>/p'
virsh net-dhcp-leases "$NET" | grep -i "$MAC"
```

If VM already has lease with old IP, renew DHCP in guest or reboot VM.

## My troubleshooting flow

1. Check VM/domain object (`virsh dominfo "$VM"`).
2. Check attached disk and NIC sources (`domblklist`, `domiflist`).
3. Check backend objects (`pool-dumpxml`, `net-dumpxml`).
4. Confirm host reality (`qemu-img info`, `lsblk`, `df`, `findmnt`).
