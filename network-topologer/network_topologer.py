"""Run multiple traceroutes and build a simple topology adjacency mapping.

The NetworkTopologer class runs traceroutes for a list of destinations and
builds an adjacency dictionary where keys are observed IP addresses and
values are sets of IP addresses that appear as the next hop after the key
in any traceroute path.

This is a lightweight helper useful for small-scale topology inference.
"""

from typing import Sequence, List, Tuple, Optional, Dict, Set
import concurrent.futures

from traceroute import Traceroute
from exceptions import TracerouteError


class NetworkTopologer:
    """Run many traceroutes and aggregate results into an adjacency mapping.

    Example:
        mt = NetworkTopologer(timeout=2)
        results = mt.run(['example.com', 'github.com'])
        adj = mt.build_adjacency(results)
    """

    def __init__(self, timeout: int = 2, port: int = 33434):
        self.timeout = timeout
        self.port = port
        # store raw traceroute results: destination -> list of (ttl, ip_or_None, rtt_ms)
        self.results: Dict[str, List[Tuple[int, Optional[str], Optional[float]]]] = {}

    def run(
        self, destinations: Sequence[str]
    ) -> Dict[str, List[Tuple[int, Optional[str], Optional[float]]]]:
        """Run traceroute for each destination in order and store results.

        Returns a mapping destination -> hops list. On traceroute errors the
        destination maps to an empty list and the error is recorded in results
        as an empty list (caller can check logs or exceptions if needed).
        """
        for dest in destinations:
            tracer = Traceroute(timeout=self.timeout, port=self.port)
            try:
                hops = tracer.run(dest)
            except TracerouteError:
                # store empty result on error to indicate failure
                self.results[dest] = []
            else:
                self.results[dest] = hops

        return self.results

    def run_parallel(
        self, destinations: Sequence[str], workers: Optional[int] = None
    ) -> Dict[str, List[Tuple[int, Optional[str], Optional[float]]]]:
        """Run traceroutes concurrently for the provided destinations.

        `workers` controls the maximum number of threads; if None, uses min(len(destinations), 32).
        """
        self.results = {}
        max_workers = workers or (min(len(destinations), 32) if destinations else 1)

        def _worker(
            dest: str,
        ) -> Tuple[str, List[Tuple[int, Optional[str], Optional[float]]]]:
            tracer = Traceroute(timeout=self.timeout, port=self.port)
            try:
                hops = tracer.run(dest)
            except TracerouteError:
                return dest, []
            return dest, hops

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = {ex.submit(_worker, d): d for d in destinations}
            for fut in concurrent.futures.as_completed(futures):
                dest, hops = fut.result()
                self.results[dest] = hops

        return self.results

    def build_adjacency(
        self,
        results: Optional[
            Dict[str, List[Tuple[int, Optional[str], Optional[float]]]]
        ] = None,
    ) -> Dict[str, Set[str]]:
        """Build adjacency dict from traceroute results.

        Each edge is added between consecutive observed hop IPs (ignoring None).
        Returns a dict: ip -> set(next_hop_ips).
        """
        if results is None:
            results = self.results

        adjacency: Dict[str, Set[str]] = {}

        for _, hops in results.items():
            # Extract sequence of IPs, skipping None timeouts
            ips = [ip for _, ip, _ in hops if ip is not None]
            for i in range(len(ips) - 1):
                a = ips[i]
                b = ips[i + 1]
                adjacency.setdefault(a, set()).add(b)

        return adjacency

    def build_adjacency_with_latency(
        self,
        results: Optional[
            Dict[str, List[Tuple[int, Optional[str], Optional[float]]]]
        ] = None,
    ) -> Dict[Tuple[str, str], List[float]]:
        """Build adjacency dict with latency measurements.

        Returns dict: (src_ip, dst_ip) -> list of RTT measurements in ms.
        Multiple measurements may exist if the same edge appears in multiple traceroutes.
        """
        if results is None:
            results = self.results

        edge_latencies: Dict[Tuple[str, str], List[float]] = {}

        for _, hops in results.items():
            # Build list of (ip, rtt_ms) tuples, skipping None IPs
            ip_rtt_pairs = [
                (ip, rtt) for _, ip, rtt in hops if ip is not None and rtt is not None
            ]

            for i in range(len(ip_rtt_pairs) - 1):
                src_ip, src_rtt = ip_rtt_pairs[i]
                dst_ip, dst_rtt = ip_rtt_pairs[i + 1]

                # Calculate delta latency between hops
                delta_ms = dst_rtt - src_rtt if (dst_rtt and src_rtt) else dst_rtt
                if delta_ms and delta_ms > 0:
                    edge = (src_ip, dst_ip)
                    edge_latencies.setdefault(edge, []).append(delta_ms)

        return edge_latencies

    def topology_dict(
        self,
        results: Optional[
            Dict[str, List[Tuple[int, Optional[str], Optional[float]]]]
        ] = None,
    ) -> Dict[str, List[str]]:
        """Return adjacency mapping with lists instead of sets for JSON-compatibility."""
        adj = self.build_adjacency(results)
        return {k: sorted(list(v)) for k, v in adj.items()}
