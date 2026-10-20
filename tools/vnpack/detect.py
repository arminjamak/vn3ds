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
import socket
import string
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


def find_netloader(timeout=1.5, address=None):
    """The Homebrew Launcher answers 3dslink's broadcast while its netloader
    (Y) is open; this asks the same way, so it never disturbs it. With an
    address, only that 3DS is asked."""
    address = address or os.environ.get("VN3DS_NETLOADER_ADDRESS") or "255.255.255.255"
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.settimeout(timeout)
        s.sendto(b"3dsboot", (address, NETLOADER_PORT))
        while True:
            data, (ip, _) = s.recvfrom(64)
            if data.startswith(b"boot3ds"):
                return ip
    except OSError:
        return None
    finally:
        s.close()


def ping_netloader(host, timeout=1.5):
    """True if the Homebrew Launcher's netloader is open on that 3DS."""
    return find_netloader(timeout, address=host) is not None


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
