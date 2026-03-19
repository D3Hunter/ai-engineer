#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  vm-lifecycle.sh <create|cleanup> <vm_name> <host_port>

Actions:
  create   Install VM, pin DHCP reservation, expose SSH (guest:22 -> host:<host_port>)
  cleanup  Destroy VM and remove DHCP reservation + SSH forward rules

Optional environment variables:
  POOL=disk1
  NET=mycustomnet
  ISO=/var/lib/libvirt/boot/Rocky-9.5-x86_64-dvd.iso
  NET_ZONE=public
  VCPUS=16
  MEMORY_MIB=65536
  DISK_SIZE_GIB=500
  ROOT_PASSWORD=<root password for create action>
EOF
}

log() {
  printf '[%s] %s\n' "$(date +'%F %T')" "$*"
}

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "missing command: $1"
}

extract_attr() {
  local line="$1"
  local attr="$2"
  printf '%s\n' "$line" | sed -n "s/.*${attr}=['\"]\\([^'\"]*\\)['\"].*/\\1/p"
}

get_dhcp_host_line_by_name() {
  local line
  line="$(virsh net-dumpxml "$NET" --inactive | grep -F "<host " | grep -F "name='$VM'" | head -n1 || true)"
  if [[ -z "$line" ]]; then
    line="$(virsh net-dumpxml "$NET" --inactive | grep -F "<host " | grep -F "name=\"$VM\"" | head -n1 || true)"
  fi
  printf '%s\n' "$line"
}

get_vm_mac() {
  virsh domiflist "$VM" | awk -v net="$NET" 'NR>2 && $2=="network" && $3==net {print $5; exit}'
}

wait_for_vm_ip() {
  local retries="${1:-120}"
  local ip=""
  local i

  for ((i=1; i<=retries; i++)); do
    ip="$(virsh domifaddr "$VM" --source lease 2>/dev/null | awk 'NR>2 && $3=="ipv4" {sub(/\/.*/, "", $4); print $4; exit}' || true)"
    if [[ -n "$ip" ]]; then
      printf '%s\n' "$ip"
      return 0
    fi
    sleep 2
  done

  return 1
}

load_state_if_exists() {
  if [[ -f "$STATE_FILE" ]]; then
    # shellcheck disable=SC1090
    source "$STATE_FILE"
  fi
}

write_state() {
  cat > "$STATE_FILE" <<EOF
STATE_VM_IP=$VM_IP
STATE_MAC=$MAC
STATE_NET=$NET
STATE_NET_ZONE=$NET_ZONE
STATE_HOST_PORT=$HOST_PORT
EOF
}

create_kickstart() {
  cat > "$KS" <<EOF
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
autopart --type=lvm --nohome
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
EOF
}

reserve_dhcp_host() {
  local existing_line existing_mac existing_ip
  existing_line="$(get_dhcp_host_line_by_name)"

  if [[ -n "$existing_line" ]]; then
    existing_mac="$(extract_attr "$existing_line" "mac")"
    existing_ip="$(extract_attr "$existing_line" "ip")"
    if [[ "$existing_mac" == "$MAC" && "$existing_ip" == "$VM_IP" ]]; then
      log "DHCP reservation already present for $VM at $VM_IP"
      return 0
    fi
    if [[ -n "$existing_mac" && -n "$existing_ip" ]]; then
      virsh net-update "$NET" delete ip-dhcp-host "<host mac='$existing_mac' name='$VM' ip='$existing_ip'/>" --live --config || true
    fi
  fi

  virsh net-update "$NET" add-last ip-dhcp-host "<host mac='$MAC' name='$VM' ip='$VM_IP'/>" --live --config
}

ensure_firewalld() {
  if ! command -v firewall-cmd >/dev/null 2>&1; then
    command -v dnf >/dev/null 2>&1 || die "firewall-cmd is missing and dnf is not available to install firewalld"
    dnf -y install firewalld
  fi
  systemctl enable --now firewalld
}

configure_firewall_forward() {
  ensure_firewalld
  firewall-cmd --zone="$NET_ZONE" --permanent --add-masquerade
  firewall-cmd --zone="$NET_ZONE" --permanent --add-forward-port=port="$HOST_PORT":proto=tcp:toaddr="$VM_IP":toport=22
  firewall-cmd --zone="$NET_ZONE" --permanent --add-port="$HOST_PORT"/tcp
  firewall-cmd --reload
}

remove_firewall_forward() {
  local entry
  if ! command -v firewall-cmd >/dev/null 2>&1; then
    return 0
  fi

  if [[ -n "${VM_IP:-}" ]]; then
    firewall-cmd --zone="$NET_ZONE" --permanent --remove-forward-port=port="$HOST_PORT":proto=tcp:toaddr="$VM_IP":toport=22 || true
  fi

  for entry in $(firewall-cmd --zone="$NET_ZONE" --list-forward-ports 2>/dev/null); do
    if [[ "$entry" == "port=${HOST_PORT}:proto=tcp:"* ]]; then
      firewall-cmd --zone="$NET_ZONE" --permanent --remove-forward-port="$entry" || true
    fi
  done

  firewall-cmd --zone="$NET_ZONE" --permanent --remove-port="$HOST_PORT"/tcp || true
  firewall-cmd --reload || true
}

create_vm() {
  local root_password cdrom_tgt

  require_cmd virsh
  require_cmd virt-install
  require_cmd openssl
  require_cmd awk
  require_cmd sed

  virsh pool-info "$POOL" >/dev/null
  virsh net-info "$NET" >/dev/null
  [[ -f "$ISO" ]] || die "ISO not found: $ISO"

  if virsh dominfo "$VM" >/dev/null 2>&1; then
    die "VM already exists: $VM"
  fi

  root_password="${ROOT_PASSWORD:-}"
  if [[ -z "$root_password" ]]; then
    read -rsp "Root password for ${VM}: " root_password
    echo
  fi
  ROOT_HASH="$(openssl passwd -6 "$root_password")"
  unset root_password

  create_kickstart

  virt-install \
    --name "$VM" \
    --vcpus "$VCPUS" \
    --memory "$MEMORY_MIB" \
    --disk pool="$POOL",size="$DISK_SIZE_GIB",device=disk,bus=virtio,format=qcow2,target=vda \
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

  # Detach installer ISO so later VM cleanup does not touch the source ISO.
  cdrom_tgt="$(virsh domblklist "$VM" --details | awk -v iso="$ISO" 'NR>2 && $4==iso {print $3; exit}')"
  if [[ -n "$cdrom_tgt" ]]; then
    virsh detach-disk "$VM" "$cdrom_tgt" --config || true
  fi

  MAC="$(get_vm_mac)"
  [[ -n "$MAC" ]] || die "failed to discover VM MAC on network $NET"

  VM_IP="$(wait_for_vm_ip 120)" || die "failed to discover VM IP from DHCP lease"
  reserve_dhcp_host
  virsh reboot "$VM" || true
  configure_firewall_forward
  write_state

  log "Create complete"
  log "VM: $VM"
  log "VM_IP: $VM_IP"
  log "MAC: $MAC"
  log "SSH: ssh -p $HOST_PORT root@<host_ip_or_dns>"
}

cleanup_vm() {
  local host_line
  require_cmd virsh
  load_state_if_exists

  NET="${STATE_NET:-$NET}"
  NET_ZONE="${STATE_NET_ZONE:-$NET_ZONE}"
  VM_IP="${STATE_VM_IP:-${VM_IP:-}}"
  MAC="${STATE_MAC:-${MAC:-}}"

  if virsh net-info "$NET" >/dev/null 2>&1; then
    host_line="$(get_dhcp_host_line_by_name)"
    if [[ -n "$host_line" ]]; then
      VM_IP="${VM_IP:-$(extract_attr "$host_line" "ip")}"
      MAC="${MAC:-$(extract_attr "$host_line" "mac")}"
    fi
  fi

  if virsh dominfo "$VM" >/dev/null 2>&1; then
    virsh destroy "$VM" 2>/dev/null || true
    virsh undefine "$VM" --remove-all-storage --nvram || true
  fi

  remove_firewall_forward

  if virsh net-info "$NET" >/dev/null 2>&1; then
    if [[ -n "${MAC:-}" && -n "${VM_IP:-}" ]]; then
      virsh net-update "$NET" delete ip-dhcp-host "<host mac='$MAC' name='$VM' ip='$VM_IP'/>" --live --config || true
    fi
  fi

  rm -f "$STATE_FILE"
  log "Cleanup complete for $VM"
}

ACTION="${1:-}"
VM="${2:-}"
HOST_PORT="${3:-}"

if [[ "$ACTION" != "create" && "$ACTION" != "cleanup" ]]; then
  usage
  exit 1
fi

if [[ -z "$VM" || -z "$HOST_PORT" ]]; then
  usage
  exit 1
fi

if [[ ! "$HOST_PORT" =~ ^[0-9]+$ ]] || (( HOST_PORT < 1 || HOST_PORT > 65535 )); then
  die "host_port must be an integer between 1 and 65535"
fi

POOL="${POOL:-disk1}"
NET="${NET:-mycustomnet}"
ISO="${ISO:-/var/lib/libvirt/boot/Rocky-9.5-x86_64-dvd.iso}"
NET_ZONE="${NET_ZONE:-public}"
VCPUS="${VCPUS:-16}"
MEMORY_MIB="${MEMORY_MIB:-65536}"
DISK_SIZE_GIB="${DISK_SIZE_GIB:-500}"
STATE_FILE="${STATE_FILE:-/tmp/${VM}.vm-lifecycle.state}"
KS="/tmp/${VM}.ks"
ROOT_HASH=""
VM_IP=""
MAC=""

case "$ACTION" in
  create)
    create_vm
    ;;
  cleanup)
    cleanup_vm
    ;;
esac
