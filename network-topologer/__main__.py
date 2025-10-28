"""Command-line entrypoint for network-topologer.

This module contains the CLI entrypoint for running traceroute. The CLI
parses arguments, instantiates the Traceroute class and prints results.
"""

import argparse
import random
import sys
from typing import Optional, Sequence, Tuple, Mapping, List

from network_topologer import NetworkTopologer
from exceptions import TracerouteError
from visualization import TopologyVisualizer


def generate_random_public_ips(count: int) -> List[str]:
    """Generate a list of random public IP addresses.
    
    Avoids private IP ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16),
    loopback (127.0.0.0/8), link-local (169.254.0.0/16), and multicast (224.0.0.0/4).
    
    Args:
        count: Number of random public IPs to generate.
        
    Returns:
        List of random public IPv4 addresses as strings.
    """
    public_ips = []
    
    while len(public_ips) < count:
        # Generate random octets
        first = random.randint(1, 223)  # Avoid 0.x.x.x, 224-255 (multicast/reserved)
        second = random.randint(0, 255)
        third = random.randint(0, 255)
        fourth = random.randint(1, 254)  # Avoid .0 and .255
        
        ip = f"{first}.{second}.{third}.{fourth}"
        
        # Check if it's a private or reserved IP
        if (
            first == 10  # 10.0.0.0/8
            or (first == 172 and 16 <= second <= 31)  # 172.16.0.0/12
            or (first == 192 and second == 168)  # 192.168.0.0/16
            or first == 127  # 127.0.0.0/8 (loopback)
            or (first == 169 and second == 254)  # 169.254.0.0/16 (link-local)
        ):
            continue
            
        public_ips.append(ip)
    
    return public_ips


def print_hops_dict(
    hops_dict: Mapping[str, Sequence[Tuple[int, Optional[str], Optional[float]]]],
) -> None:
    """Print the hops dictionary returned by NetworkTopologer.run()."""
    for dest, hops in hops_dict.items():
        print(f"Destination: {dest}")
        for ttl, ip, rtt_ms in hops:
            if ip is None:
                print(f"{ttl}\t*")
            else:
                rtt_str = f"{rtt_ms:.1f} ms" if rtt_ms is not None else "?"
                print(f"{ttl}\t{ip}\t{rtt_str}")
        print()  # Blank line between destinations


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        description="Traceroute implementation in Python (OOP)."
    )
    parser.add_argument(
        "destinations",
        nargs="*",
        type=str,
        help="One or more IPv4 addresses to traceroute to.",
    )
    parser.add_argument(
        "-r",
        "--random",
        type=int,
        default=None,
        metavar="COUNT",
        help="Generate COUNT random public IP addresses to traceroute.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=33434,
        help="Destination UDP port to probe (default: 33434).",
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run traceroutes in parallel using threads.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Maximum number of worker threads when using --parallel (default: min(len(destinations),32)).",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=int,
        default=2,
        help="Timeout for each packet in seconds (default: 2).",
    )
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Visualize the network topology graph using matplotlib.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Save topology visualization to file (e.g., topology.png).",
    )

    args = parser.parse_args(argv)

    # Handle random IP generation or use provided destinations
    if args.random:
        if args.random <= 0:
            print("Error: --random COUNT must be a positive integer.", file=sys.stderr)
            sys.exit(1)
        destinations = generate_random_public_ips(args.random)
        print(f"Generated {args.random} random public IP(s): {destinations}")
    elif args.destinations:
        destinations = args.destinations
    else:
        print("Error: Either provide destination IPs or use --random to generate them.", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    port = args.port

    nt = NetworkTopologer(timeout=args.timeout, port=port)

    print(f"Traceroute to {destinations} (timeout: {args.timeout} seconds):")
    try:
        if args.parallel:
            hops_dict = nt.run_parallel(destinations, workers=args.workers)
        else:
            hops_dict = nt.run(destinations)
    except TracerouteError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print_hops_dict(hops_dict)

    # Visualize topology if requested
    if args.visualize:
        # Build adjacency mapping from results
        adjacency = nt.build_adjacency(hops_dict)

        if not adjacency:
            print(
                "Warning: No topology edges to visualize (all hops timed out or single-hop paths).",
                file=sys.stderr,
            )
        else:
            visualizer = TopologyVisualizer()
            stats = visualizer.get_graph_stats(adjacency)
            print(f"\nTopology stats: {stats['nodes']} nodes, {stats['edges']} edges")

            # Build edge latency data
            edge_latencies = nt.build_adjacency_with_latency(hops_dict)

            # Pass destination IPs for color-coding
            destination_set = set(destinations)

            # Show plot interactively unless only saving to file
            show_plot = args.output is None
            visualizer.plot_topology(
                adjacency,
                output_file=args.output,
                show=show_plot,
                title="Network Traceroute Topology",
                destination_ips=destination_set,
                edge_latencies=edge_latencies,
            )


if __name__ == "__main__":
    main()
