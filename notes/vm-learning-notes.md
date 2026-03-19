# VM Quickstart (KVM/libvirt)

Command reference for libvirt VM lifecycle (`create -> get IP -> pin IP -> expose SSH -> cleanup`).
Extended reference: [VM Deep-Dive Notes](./vm-learning-deep-dive.md).

## Standard placeholders

```bash
VM="vm-demo-01"
POOL="disk1"
NET="mycustomnet"
ISO="/var/lib/libvirt/boot/Rocky-9.5-x86_64-dvd.iso"
HOST_PORT=2111
NET_ZONE="public"
```

## Preflight checks

```bash
virsh pool-info "$POOL" >/dev/null
test -f "$ISO"
virsh net-info "$NET" >/dev/null
```

If `virsh net-info "$NET"` fails, run the NAT network section first.

## Create NAT + DHCP network (if needed)

```bash
NET="mycustomnet"
NET_XML="/tmp/${NET}.xml"

cat > "$NET_XML" <<'XML'
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
XML

virsh net-define "$NET_XML"
virsh net-start "$NET"
virsh net-autostart "$NET"
```

## Install VM (headless + kickstart)

```bash
VM="vm-demo-01"
POOL="disk1"
NET="mycustomnet"
ISO="/var/lib/libvirt/boot/Rocky-9.5-x86_64-dvd.iso"
KS="/tmp/${VM}.ks"

read -rsp "Root password for ${VM}: " ROOT_PASSWORD
echo
ROOT_HASH="$(openssl passwd -6 "$ROOT_PASSWORD")"
unset ROOT_PASSWORD

cat > "$KS" <<EOF_KS
text
lang en_US.UTF-8
keyboard us
timezone Asia/Shanghai --isUtc
network --bootproto=dhcp --device=link --activate
rootpw --iscrypted $ROOT_HASH
services --enabled=sshd
firewall --enabled --service=ssh
ignoredisk --only-use=vda
clearpart --all --initlabel --drives=vda
autopart --type=lvm
reboot

%packages
@^minimal-environment
%end

%post
mkdir -p /etc/ssh/sshd_config.d
cat > /etc/ssh/sshd_config.d/99-root-password.conf <<'EOT'
PermitRootLogin yes
PasswordAuthentication yes
KbdInteractiveAuthentication yes
UsePAM yes
EOT
systemctl enable sshd
%end
EOF_KS

virt-install \
  --name "$VM" \
  --vcpus 16 \
  --memory 65536 \
  --disk pool="$POOL",size=500,device=disk,bus=virtio,format=qcow2,target=vda \
  --location "$ISO",kernel=images/pxeboot/vmlinuz,initrd=images/pxeboot/initrd.img \
  --initrd-inject "$KS" \
  --network network="$NET",model=virtio \
  --graphics none \
  --console pty,target_type=serial \
  --os-variant rocky9 \
  --noautoconsole \
  --wait -1 \
  --extra-args "inst.text inst.cmdline console=ttyS0,115200n8 inst.repo=cdrom inst.ks=file:/$(basename "$KS")"

virsh autostart "$VM"

# Detach ISO first so later --remove-all-storage will not delete installer ISO.
CDROM_TGT="$(virsh domblklist "$VM" --details | awk -v iso="$ISO" 'NR>2 && $4==iso {print $3; exit}')"
[ -n "$CDROM_TGT" ] && virsh detach-disk "$VM" "$CDROM_TGT" --config
```

## Get VM IP and basic checks

```bash
VM_IP="$(virsh domifaddr "$VM" --source lease | awk 'NR>2 && $3=="ipv4" {sub(/\/.*/, "", $4); print $4; exit}')"
MAC="$(virsh domiflist "$VM" | awk -v net="$NET" 'NR>2 && $2=="network" && $3==net {print $5; exit}')"

echo "VM_IP=$VM_IP"
echo "MAC=$MAC"

virsh domstate "$VM"
virsh net-dhcp-leases "$NET" | grep -i "$MAC" || true
```

## Pin VM IP with DHCP reservation

```bash
virsh net-update "$NET" add-last ip-dhcp-host "<host mac='$MAC' name='$VM' ip='$VM_IP'/>" --live --config
virsh net-dumpxml "$NET" --inactive | sed -n '/<dhcp>/,/<\/dhcp>/p'

# Reboot VM so it picks reserved IP.
virsh reboot "$VM"
```

## Expose VM SSH to host port

```bash
# Install/start firewalld if needed.
dnf -y install firewalld
systemctl enable --now firewalld
firewall-cmd --state

firewall-cmd --zone="$NET_ZONE" --permanent --add-masquerade
firewall-cmd --zone="$NET_ZONE" --permanent --add-forward-port=port="$HOST_PORT":proto=tcp:toaddr="$VM_IP":toport=22
firewall-cmd --zone="$NET_ZONE" --permanent --add-port="$HOST_PORT"/tcp
firewall-cmd --reload
```

Connect from another machine:

```bash
ssh -p "$HOST_PORT" root@<host_ip_or_dns>
```

## Cleanup VM + forwarding + DHCP reservation

```bash
# VM cleanup
virsh destroy "$VM" 2>/dev/null || true
virsh undefine "$VM" --remove-all-storage --nvram

# Remove host forwarding
firewall-cmd --zone="$NET_ZONE" --permanent --remove-forward-port=port="$HOST_PORT":proto=tcp:toaddr="$VM_IP":toport=22
firewall-cmd --zone="$NET_ZONE" --permanent --remove-port="$HOST_PORT"/tcp
firewall-cmd --reload

# Remove DHCP reservation
virsh net-update "$NET" delete ip-dhcp-host "<host mac='$MAC' name='$VM' ip='$VM_IP'/>" --live --config
```

## Security reminders

- The quickstart installer enables root password SSH login for bootstrap speed.
- For non-lab environments, switch to SSH key login and disable root password login after bootstrap.

## Deep-dive links

- Full reference: [VM Deep-Dive Notes](./vm-learning-deep-dive.md)
- Progress checks: [Progress and completion checks (no GUI required)](./vm-learning-deep-dive.md#progress-and-completion-checks-no-gui-required)
- IP source choices: [How to check VM IP (which source to use)](./vm-learning-deep-dive.md#how-to-check-vm-ip-which-source-to-use)
- Safe cleanup details: [Safe VM cleanup without deleting installer ISO](./vm-learning-deep-dive.md#safe-vm-cleanup-without-deleting-installer-iso)
- Troubleshooting checklist: [Troubleshooting checklist](./vm-learning-deep-dive.md#troubleshooting-checklist)
