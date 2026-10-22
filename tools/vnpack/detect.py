"""Find where a ported game should go: the 3DS's SD card plugged into this
computer, or a 3DS on the same Wi-Fi (vn3ds listening, the Homebrew
Launcher's netloader, or the ftpd app).

    target = detect()   # Target(kind="sd" | "vn3ds" | "netloader" | "ftp" | None, where=...)

For testing without a real card or console, these environment variables
narrow down where it looks (nothing else changes):
  VN3DS_VOLUMES             extra folders to check for an SD card (os.pathsep-separated)
  VN3DS_SCAN_HOSTS          hosts to probe instead of the local /24 (comma-separated)
  VN3DS_NETLOADER_ADDRESS   where to send the netloader ping (default: broadcast)
"""

import concurrent.futures
import glob
import ipaddress
import os
import re
import socket
import string
import subprocess
import sys
from collections import namedtuple

Target = namedtuple("Target", "kind where")

VN3DS_PORT = 5555
FTPD_PORT = 5000
NETLOADER_PORT = 17491

# A 3DS card has these at its root (custom firmware: boot.firm + luma/, and
# the system's own "Nintendo 3DS" folder).
SD_MARKERS = ("Nintendo 3DS", "boot.firm", "luma", "3ds")


def _candidate_volumes():
    extra = [v for v in os.environ.get("VN3DS_VOLUMES", "").split(os.pathsep) if v]
    return extra + _system_volumes()


def _system_volumes():
    if sys.platform == "darwin":
        return [v for v in glob.glob("/Volumes/*") if os.path.basename(v) != "Macintosh HD"]
    if sys.platform.startswith("win"):
        return [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]
    user = os.environ.get("USER", "")
    return glob.glob(f"/media/{user}/*") + glob.glob(f"/run/media/{user}/*") + glob.glob("/mnt/*")


def find_sd():
    """Mounted volumes that look like a 3DS SD card (best match first)."""
    found = []
    for v in _candidate_volumes():
        try:
            names = set(os.listdir(v))
        except OSError:
            continue
        score = sum(m in names for m in SD_MARKERS)
        if "Nintendo 3DS" in names or "boot.firm" in names:
            found.append((score, v))
    return [v for _, v in sorted(found, reverse=True)]


def local_ipv4():
    """This computer's address on the LAN (no packets are sent)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return None
    finally:
        s.close()


def _open(ip, port, timeout):
    try:
        with socket.create_connection((ip, port), timeout=timeout) as c:
            if port == FTPD_PORT:   # port 5000 is also macOS AirPlay: want an FTP greeting
                c.settimeout(1.0)
                return c.recv(64).startswith(b"220")
            return True
    except OSError:
        return False


def _netloader_socket(bind_17491):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    if bind_17491:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, "SO_REUSEPORT"):
            try:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except OSError:
                pass
        s.bind(("", NETLOADER_PORT))
    return s


def _ask_netloader(targets, timeout, bind_17491):
    try:
        s = _netloader_socket(bind_17491)
    except OSError:
        return None
    try:
        s.settimeout(timeout)
        for t in targets:
            try:
                s.sendto(b"3dsboot", (t, NETLOADER_PORT))
            except OSError:
                pass
        while True:
            data, (ip, _) = s.recvfrom(64)
            if data.startswith(b"boot3ds"):
                return ip
    except OSError:
        return None
    finally:
        s.close()


def find_netloader(timeout=1.5, address=None):
    """The Homebrew Launcher answers 3dslink's UDP ping while its netloader
    (Y) is open; this asks the same way, so it never disturbs it. Never
    connect to its TCP port to test it: an empty connection makes the
    launcher show "an error occurred: namelen" and leave netloader mode.

    With an address, that 3DS is asked first, then the whole network (its IP
    may have changed). It asks from an ordinary port first; if nothing
    answers, again from port 17491 itself, as devkitPro's 3dslink does
    (some launchers answer that port rather than the one the ping came
    from)."""
    targets = [address] if address else []
    targets.append(os.environ.get("VN3DS_NETLOADER_ADDRESS") or "255.255.255.255")
    targets = list(dict.fromkeys(targets))
    return (_ask_netloader(targets, timeout * 0.6, False)
            or _ask_netloader(targets, timeout * 0.4, True))


def ping_netloader(host, timeout=1.5):
    """True if the Homebrew Launcher's netloader is open on that 3DS."""
    return find_netloader(timeout, address=host) == host


# ---- telling "not open yet" from "not on the Wi-Fi" -------------------------

# MAC address prefixes registered to Nintendo (the 3DS family among them).
NINTENDO_OUIS = {
    "00:09:bf", "00:16:56", "00:17:ab", "00:19:1d", "00:19:fd", "00:1a:e9", "00:1b:7a",
    "00:1b:ea", "00:1c:be", "00:1d:bc", "00:1e:35", "00:1e:a9", "00:1f:32", "00:1f:c5",
    "00:21:47", "00:21:bd", "00:22:4c", "00:22:aa", "00:22:d7", "00:23:31", "00:23:cc",
    "00:24:1e", "00:24:44", "00:24:f3", "00:25:a0", "00:26:59", "00:27:09", "18:2a:7b",
    "2c:10:c1", "34:af:2c", "40:d2:8a", "40:f4:07", "58:2f:40", "58:bd:a3", "5c:52:1e",
    "60:6b:ff", "64:b5:c6", "78:a2:a0", "7c:bb:8a", "8c:56:c5", "8c:cd:e8", "98:41:5c",
    "98:b6:e9", "9c:e6:35", "a4:38:cc", "a4:5c:27", "a4:c0:e1", "b8:8a:ec", "b8:ae:6e",
    "cc:9e:00", "cc:fb:65", "d8:6b:f7", "dc:68:eb", "e0:0c:7f", "e0:e7:51", "e8:4e:ce",
    "e8:da:20", "ec:c4:0d",
}


def _norm_mac(mac):
    parts = re.split("[:-]", mac.lower())
    return ":".join(p.zfill(2) for p in parts) if len(parts) == 6 else ""


def arp_table():
    """{ip: mac} from the system's ARP cache (no packets are sent)."""
    try:
        out = subprocess.run(["arp", "-a"] if sys.platform.startswith("win") else ["arp", "-an"],
                             capture_output=True, text=True, timeout=5).stdout
    except (OSError, subprocess.SubprocessError):
        return {}
    table = {}
    for line in out.splitlines():
        ip = re.search(r"(\d+\.\d+\.\d+\.\d+)", line)
        mac = re.search(r"([0-9a-fA-F]{1,2}([:-][0-9a-fA-F]{1,2}){5})", line)
        if ip and mac:
            table[ip.group(1)] = _norm_mac(mac.group(1))
    return table


def nintendo_hosts():
    """IPs on the LAN whose network card is Nintendo's (likely the 3DS)."""
    return [ip for ip, mac in arp_table().items() if mac[:8] in NINTENDO_OUIS]


def pingable(ip, timeout=1.0):
    """True if the host answers an ICMP ping (it is on the network)."""
    if sys.platform.startswith("win"):
        cmd = ["ping", "-n", "1", "-w", str(int(timeout * 1000)), ip]
    elif sys.platform == "darwin":
        cmd = ["ping", "-c", "1", "-W", str(int(timeout * 1000)), ip]
    else:
        cmd = ["ping", "-c", "1", "-W", str(max(1, int(timeout))), ip]
    try:
        return subprocess.run(cmd, capture_output=True, timeout=timeout + 3).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def locate(hint=None, scan=True):
    """Where the 3DS is now. Returns (kind, ip): "vn3ds" (its receiver
    answers), "netloader" (the Homebrew Launcher's Y), "online" (a 3DS is on
    the Wi-Fi but nothing listens: vn3ds closed, or its receiver stuck), or
    (None, None). `hint` is where it was last; it is tried first, and the
    network is searched if it doesn't answer there (DHCP hands out new IPs)."""
    if hint and listening(hint, VN3DS_PORT):
        return "vn3ds", hint
    ip = find_netloader(address=hint)
    if ip:
        return "netloader", ip
    if scan:
        lan = scan_lan(ports=(VN3DS_PORT,))
        found = lan.get(VN3DS_PORT) or []
        known = set(nintendo_hosts())
        found.sort(key=lambda x: (x not in known, x != hint))
        if found:
            return "vn3ds", found[0]
    for ip in ([hint] if hint else []) + [h for h in nintendo_hosts() if h != hint]:
        if pingable(ip):
            return "online", ip
    return None, None


def listening(host, port=VN3DS_PORT, timeout=1.0):
    """True if something accepts connections on host:port."""
    return _open(host, port, timeout)


def scan_lan(ports=(VN3DS_PORT, FTPD_PORT), timeout=0.35):
    """{port: [ips]} for the /24 around this computer."""
    hosts = [h.strip() for h in os.environ.get("VN3DS_SCAN_HOSTS", "").split(",") if h.strip()]
    if not hosts:
        me = local_ipv4()
        if not me:
            return {}
        net = ipaddress.ip_network(f"{me}/24", strict=False)
        hosts = [str(h) for h in net.hosts() if str(h) != me]
    found = {p: [] for p in ports}
    with concurrent.futures.ThreadPoolExecutor(max_workers=96) as ex:
        jobs = {ex.submit(_open, ip, port, timeout): (ip, port) for ip in hosts for port in ports}
        for fut in concurrent.futures.as_completed(jobs):
            if fut.result():
                ip, port = jobs[fut]
                found[port].append(ip)
    return found


def detect(say=print):
    """Where to put a game, checked in order of quality: an SD card first
    (best-quality assets), then the 3DS on Wi-Fi."""
    cards = find_sd()
    if cards:
        return Target("sd", cards[0])
    say("no 3DS SD card is plugged in; looking for your 3DS on the Wi-Fi...")
    lan = scan_lan()
    if lan.get(VN3DS_PORT):
        return Target("vn3ds", lan[VN3DS_PORT][0])
    ip = find_netloader()
    if ip:
        return Target("netloader", ip)
    if lan.get(FTPD_PORT):
        return Target("ftp", f"{lan[FTPD_PORT][0]}:{FTPD_PORT}")
    return Target(None, None)
