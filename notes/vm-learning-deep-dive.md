# VM Deep-Dive Notes (KVM/libvirt)

Reference notes for commands, behavior, and troubleshooting.
Daily command flow: [VM Quickstart](./vm-learning-notes.md).

## Index

Task-oriented index:

| Task | Section |
| --- | --- |
| Create NAT+DHCP network | [Create network `mycustomnet` (NAT + DHCP) example](#create-network-mycustomnet-nat--dhcp-example) |
| Do one full lifecycle (install -> pin IP -> expose SSH -> cleanup) | [End-to-end script: create VM, pin IP, expose SSH, cleanup](#end-to-end-script-create-vm-pin-ip-expose-ssh-cleanup) |
| Install headless from terminal-only host | [Headless install playbook (terminal-only host)](#headless-install-playbook-terminal-only-host) |
| Verify install progress and find VM IP | [Progress and completion checks (no GUI required)](#progress-and-completion-checks-no-gui-required) and [How to check VM IP (which source to use)](#how-to-check-vm-ip-which-source-to-use) |
| Publish VM SSH via host port | [SSH reachability on libvirt NAT network](#ssh-reachability-on-libvirt-nat-network) |
| Pin DHCP IP to a VM | [Pin VM IP with libvirt DHCP reservation](#pin-vm-ip-with-libvirt-dhcp-reservation) |
| Safely remove VM without deleting installer ISO | [Safe VM cleanup without deleting installer ISO](#safe-vm-cleanup-without-deleting-installer-iso) |
| Debug by checklist | [Troubleshooting checklist](#troubleshooting-checklist) |

Common placeholders used in examples:

```bash
VM="vm-demo-01"
POOL="disk1"
NET="mycustomnet"
ISO="/var/lib/libvirt/boot/Rocky-9.5-x86_64-dvd.iso"
```

## Tool roles

- `qemu-img` manages disk images (create, inspect, resize, convert).
- `virt-install` creates/installs VMs and writes libvirt domain config.
- `virsh` inspects and manages existing libvirt objects (`domain`, `network`, `pool`, `volume`).

## Key terms

- `QEMU` = Quick Emulator.
- `COW` = Copy-On-Write.
- `qcow2` = QEMU Copy-On-Write v2 image format.
- `dom` in `virsh dom*` means **domain** (libvirt's VM object name).

## Units and defaults

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

To remove a `shut off` VM from `virsh list --all`, undefine it.

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
- If snapshots exist, remove snapshot metadata first.
- `--remove-all-storage` is dangerous when ISO is attached as storage; detach ISO first or delete specific VM disks only.

## Safe VM cleanup without deleting installer ISO

If installer ISO is attached (for example `/var/lib/libvirt/boot/Rocky-9.5-x86_64-dvd.iso`), avoid blind `--remove-all-storage`.

```bash
VM="vm-demo-01"
ISO="/var/lib/libvirt/boot/Rocky-9.5-x86_64-dvd.iso"

# Inspect block targets first (disk vs cdrom)
virsh domblklist "$VM" --details

# Optional: detach ISO device before destructive cleanup
CDROM_TGT="$(virsh domblklist "$VM" --details | awk -v iso="$ISO" 'NR>2 && $4==iso {print $3; exit}')"
if [ -n "$CDROM_TGT" ]; then
  virsh detach-disk "$VM" "$CDROM_TGT" --config
fi

virsh destroy "$VM" 2>/dev/null || true
virsh undefine "$VM" --nvram
```

For automated storage cleanup, prefer deleting specific targets with `--storage` instead of `--remove-all-storage`.

## Change CPU/memory of an existing VM

Recommended flow: change config while VM is shut off.

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

If only volume name is known (pool unknown):

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

## Download Rocky ISO (multi-thread + retry + nohup)

Use `aria2c` for resumable parallel download in background.

```bash
ISO_URL="https://dl.rockylinux.org/vault/rocky/9.5/isos/x86_64/Rocky-9.5-x86_64-dvd.iso"
ISO_DIR="/var/lib/libvirt/boot"
ISO_NAME="Rocky-9.5-x86_64-dvd.iso"
LOG="/tmp/rocky95-iso-download.log"

command -v aria2c >/dev/null || dnf -y install aria2
mkdir -p "$ISO_DIR"

nohup aria2c "$ISO_URL" \
  -d "$ISO_DIR" -o "$ISO_NAME" \
  -x 16 -s 16 -k 1M \
  -c -m 0 --retry-wait=5 --timeout=30 \
  --summary-interval=30 \
  >"$LOG" 2>&1 &

echo "PID=$! LOG=$LOG"
tail -f "$LOG"
```

Quick verify:

```bash
ls -lh "${ISO_DIR}/${ISO_NAME}"
```

### Multi-mirror fallback (faster + more robust)

As checked on `2026-03-19`, mirror behavior may vary:

- `mirrors.sohu.com/.../Rocky/9.5/...` returned `404`.
- `mirrors.aliyun.com/.../rockylinux-vault/9.5/...` redirected to another host that was unreachable in this environment.

Working URLs from this environment:

- `https://mirror.nju.edu.cn/rocky-vault/9.5/isos/x86_64/Rocky-9.5-x86_64-dvd.iso`
- `https://dl.rockylinux.org/vault/rocky/9.5/isos/x86_64/Rocky-9.5-x86_64-dvd.iso`
- `https://downloads.rockylinux.org/vault/rocky/9.5/isos/x86_64/Rocky-9.5-x86_64-dvd.iso`
- `https://mirror.netzwerge.de/rocky-vault/9.5/isos/x86_64/Rocky-9.5-x86_64-dvd.iso`

```bash
ISO_DIR="/var/lib/libvirt/boot"
ISO_NAME="Rocky-9.5-x86_64-dvd.iso"
LOG="/tmp/rocky95-iso-download.log"

nohup aria2c \
  -d "$ISO_DIR" -o "$ISO_NAME" \
  -x 16 -s 16 -k 1M \
  -c -m 0 --retry-wait=5 --timeout=30 \
  --uri-selector=adaptive --summary-interval=30 \
  "https://mirror.nju.edu.cn/rocky-vault/9.5/isos/x86_64/${ISO_NAME}" \
  "https://dl.rockylinux.org/vault/rocky/9.5/isos/x86_64/${ISO_NAME}" \
  "https://downloads.rockylinux.org/vault/rocky/9.5/isos/x86_64/${ISO_NAME}" \
  "https://mirror.netzwerge.de/rocky-vault/9.5/isos/x86_64/${ISO_NAME}" \
  >"$LOG" 2>&1 &
echo "PID=$! LOG=$LOG"
```

### Safety check for mirror downloads (must do)

Always verify downloaded ISO hash against Rocky official checksum before using it.

```bash
ISO_DIR="/var/lib/libvirt/boot"
ISO_NAME="Rocky-9.5-x86_64-dvd.iso"
ISO_PATH="${ISO_DIR}/${ISO_NAME}"

curl -fsSLo /tmp/rocky95-CHECKSUM \
  "https://dl.rockylinux.org/vault/rocky/9.5/isos/x86_64/CHECKSUM"

EXPECTED="$(awk -v f="$ISO_NAME" '$0 ~ ("SHA256 \\(" f "\\) = ") {print $NF; exit}' /tmp/rocky95-CHECKSUM)"
echo "${EXPECTED}  ${ISO_PATH}" | sha256sum -c -
```

Reference value observed on `2026-03-19` for `Rocky-9.5-x86_64-dvd.iso`:

```text
ba60c3653640b5747610ddfb4d09520529bef2d1d83c1feb86b0c84dff31e04e
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

Output hints:

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

SSH auth checks:

- If forwarding is correct but SSH still fails with password, check guest auth policy first:
  - `sshd -T | egrep 'permitrootlogin|passwordauthentication|kbdinteractiveauthentication|usepam'`
  - `journalctl -u sshd -n 80 --no-pager`
  - `faillock --user root --reset`

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

## End-to-end script: create VM, pin IP, expose SSH, cleanup

Use the reusable example script at `notes/scripts/vm-lifecycle.sh`.

```bash
VM="this-is-vm-name"
HOST_PORT=2111

# Optional overrides (defaults shown)
POOL="disk1" \
NET="mycustomnet" \
ISO="/var/lib/libvirt/boot/Rocky-9.5-x86_64-dvd.iso" \
NET_ZONE="public" \
./notes/scripts/vm-lifecycle.sh create "$VM" "$HOST_PORT"

# Later, cleanup VM + DHCP reservation + forwarded port
./notes/scripts/vm-lifecycle.sh cleanup "$VM" "$HOST_PORT"
```

What `create` does:

- Installs a Rocky VM with kickstart (`autopart --type=lvm --nohome`).
- Detects current DHCP lease IP and pins it in libvirt as a DHCP reservation.
- Exposes guest SSH (`22/tcp`) to the host port you pass.
- Saves lifecycle state to `/tmp/${VM}.vm-lifecycle.state` for cleanup.

What `cleanup` does:

- Destroys and undefines the VM (including VM storage).
- Removes the host firewall forward rule and opened host port.
- Removes the DHCP reservation for that VM from libvirt network.

Notes:

- Script arguments are fixed: `<create|cleanup> <vm_name> <host_port>`.
- `create` prompts for root password unless `ROOT_PASSWORD` env var is set.
- This flow enables root password SSH login for bootstrap convenience; harden later for non-lab use.

## Quick fixes

- Exit serial console back to host terminal with `Ctrl + ]`.
- If `firewall-cmd` returns `FirewallD is not running`, start it first:

```bash
dnf -y install firewalld
systemctl enable --now firewalld
firewall-cmd --state
```

- Extract plain IPv4 from `virsh domifaddr` output:

```bash
VM_IP="$(virsh domifaddr "$VM" --source lease | awk 'NR>2 && $3=="ipv4" {sub(/\/.*/, "", $4); print $4; exit}')"
echo "VM_IP=\"$VM_IP\""
```

- If heredoc write like `cat > "$KS" <<EOF` fails with `No such file or directory`, check `KS` first:

```bash
echo "KS=[$KS]"
[ -n "$KS" ] || { echo "KS is empty"; exit 1; }
mkdir -p "$(dirname "$KS")"
```

- If guest `/` is around `70G` after `autopart --type=lvm --nohome`, use all free VG space:

```bash
ROOT_LV="$(findmnt -no SOURCE /)"
lvextend -r -l +100%FREE "$ROOT_LV"
df -h /
```

## Troubleshooting checklist

1. Check VM/domain object (`virsh dominfo "$VM"`).
2. Check attached disk and NIC sources (`domblklist`, `domiflist`).
3. Check backend objects (`pool-dumpxml`, `net-dumpxml`).
4. Confirm host reality (`qemu-img info`, `lsblk`, `df`, `findmnt`).
