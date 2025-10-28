"""OOP traceroute implementation using only the Python standard library.

This implementation sends UDP probes with increasing TTL and listens
for ICMP responses using a raw socket. It does not depend on scapy.
"""

from typing import List, Tuple, Optional
import socket
import struct
import time
import select

from exceptions import (
    TracerouteError,
    DNSResolveError,
    TraceroutePermissionError,
)


class Traceroute:
    """Run traceroute to a destination using UDP probes and ICMP replies.

    The run() method returns a list of (ttl, ip_or_None, rtt_ms) tuples where
    ip_or_None is None for timeouts and rtt_ms is the round-trip time in milliseconds.
    """

    def __init__(self, timeout: int = 2, port: int = 33434):
        self.timeout = float(timeout)
        self.port = int(port)

    def _resolve(self, destination: str) -> str:
        try:
            return socket.gethostbyname(destination)
        except socket.gaierror as e:
            raise DNSResolveError(
                f"Failed to resolve destination '{destination}': {e}"
            ) from e

    def _create_sockets(self) -> Tuple[socket.socket, socket.socket]:
        """Create the send (UDP) and recv (RAW ICMP) sockets.

        Raises TraceroutePermissionError if raw socket creation is denied.
        """
        try:
            recv_sock = socket.socket(
                socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP
            )
            recv_sock.setblocking(False)
            recv_sock.settimeout(self.timeout)
        except PermissionError as e:
            raise TraceroutePermissionError(
                "Permission denied when creating raw socket. Try running as root or with sudo."
            ) from e

        send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        # Bind to an ephemeral port to ensure we receive replies related to our probes
        send_sock.bind(("", 0))

        return send_sock, recv_sock

    def _parse_icmp_type(self, data: bytes) -> Optional[int]:
        """Parse an IP packet and return the ICMP type, or None if parsing fails."""
        if len(data) < 20:
            return None
        # IP header: first byte contains version and IHL
        ver_ihl = data[0]
        ihl = (ver_ihl & 0x0F) * 4
        if len(data) < ihl + 4:
            return None
        icmp_header = data[ihl : ihl + 4]
        icmp_type, _, _ = struct.unpack("!BBH", icmp_header)
        return icmp_type

    def _send_probe(
        self, send_sock: socket.socket, dest_ip: str, dest_port: int, ttl: int
    ) -> None:
        """Send a single UDP probe to dest_ip:dest_port with given TTL.

        Raises TracerouteError on send failures.
        """
        # set TTL on the sending UDP socket
        send_sock.setsockopt(socket.SOL_IP, socket.IP_TTL, ttl)
        try:
            send_sock.sendto(b"", (dest_ip, dest_port))
        except OSError as e:
            raise TracerouteError(f"Failed to send probe at ttl={ttl}: {e}") from e

    def _receive_reply(
        self, recv_sock: socket.socket, timeout: float
    ) -> Tuple[Optional[str], Optional[int], Optional[float]]:
        """Wait for a single ICMP reply until timeout and return (addr, icmp_type, rtt_ms).

        Returns (None, None, None) on timeout or parsing failure.
        rtt_ms is the round-trip time in milliseconds.
        """
        start = time.time()
        addr: Optional[str] = None
        icmp_type: Optional[int] = None
        rtt_ms: Optional[float] = None
        while True:
            time_left = timeout - (time.time() - start)
            if time_left <= 0:
                break
            r, _, _ = select.select([recv_sock], [], [], time_left)
            if not r:
                break
            try:
                data, curr_addr = recv_sock.recvfrom(1024)
                recv_time = time.time()
            except socket.error:
                break

            addr = curr_addr[0]
            rtt_ms = (recv_time - start) * 1000  # Convert to milliseconds
            icmp_type = self._parse_icmp_type(data)
            # ICMP type 11 = Time Exceeded (intermediate hop), type 3 = Destination Unreachable
            if icmp_type in (11, 3):
                break

        return addr, icmp_type, rtt_ms

    def run(self, destination: str) -> List[Tuple[int, Optional[str], Optional[float]]]:
        dest_ip = self._resolve(destination)
        hops: List[Tuple[int, Optional[str], Optional[float]]] = []

        send_sock, recv_sock = self._create_sockets()
        try:
            base_port = self.port
            ttl = 1
            while True:
                # Use a per-ttl destination port to match responses
                dest_port = base_port + ttl

                # send probe
                self._send_probe(send_sock, dest_ip, dest_port, ttl)

                # receive reply
                addr, icmp_type, rtt_ms = self._receive_reply(recv_sock, self.timeout)

                if addr is None:
                    hops.append((ttl, None, None))
                else:
                    hops.append((ttl, addr, rtt_ms))
                    # If the reply came from the destination (or ICMP dest unreachable), stop
                    if addr == dest_ip or (icmp_type is not None and icmp_type == 3):
                        break

                ttl += 1

        finally:
            try:
                send_sock.close()
            except Exception:
                pass
            try:
                recv_sock.close()
            except Exception:
                pass

        return hops
