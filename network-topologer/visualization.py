"""Network topology visualization using matplotlib and networkx.

This module provides visualization capabilities for network traceroute
topology data using matplotlib for plotting and networkx for graph layout.
"""

from typing import Dict, Set, Optional, Tuple, List
import warnings

import matplotlib.pyplot as plt
import networkx as nx

class TopologyVisualizer:
    """Visualize network topology from adjacency data.

    Uses networkx for graph layout and matplotlib for rendering.
    """

    def __init__(self):
        pass

    def plot_topology(
        self,
        adjacency: Dict[str, Set[str]],
        output_file: Optional[str] = None,
        show: bool = True,
        figsize: Tuple[int, int] = (12, 8),
        title: str = "Network Topology",
        destination_ips: Optional[Set[str]] = None,
        edge_latencies: Optional[Dict[Tuple[str, str], List[float]]] = None,
    ) -> None:
        """Plot network topology graph from adjacency mapping.

        Args:
            adjacency: Dict mapping IP -> set of next-hop IPs
            output_file: Optional path to save the figure
            show: Whether to display the plot interactively
            figsize: Figure size tuple (width, height)
            title: Plot title
            destination_ips: Set of destination IPs to highlight (colored green)
            edge_latencies: Dict mapping (src_ip, dst_ip) -> list of RTT measurements in ms
        """
        # Create directed graph
        G = nx.DiGraph()

        # Add edges from adjacency data
        for src, destinations in adjacency.items():
            for dst in destinations:
                G.add_edge(src, dst)

        if len(G.nodes()) == 0:
            warnings.warn("No topology data to visualize (empty graph)")
            return

        # Create figure
        plt.figure(figsize=figsize)

        # Use hierarchical layout for cleaner visualization with straight lines
        # Suppress warnings during graphviz import and use
        import warnings as warn_module

        with warn_module.catch_warnings():
            warn_module.filterwarnings("ignore")
            try:
                pos = nx.nx_agraph.graphviz_layout(G, prog="dot")
            except (ImportError, AttributeError, Exception):
                # Fallback to kamada_kawai which produces straighter lines than spring
                try:
                    pos = nx.kamada_kawai_layout(G)
                except Exception:
                    # Final fallback to shell layout
                    pos = nx.shell_layout(G)

        # Categorize nodes: destination IPs vs intermediate hops
        all_nodes = set(G.nodes())
        dest_set = destination_ips if destination_ips else set()

        # Find leaf nodes (nodes with no outgoing edges) as potential destinations
        leaf_nodes = {node for node in all_nodes if G.out_degree(node) == 0}

        # Combine user-specified destinations with leaf nodes
        destination_nodes = (dest_set & all_nodes) | leaf_nodes
        intermediate_nodes = all_nodes - destination_nodes

        # Draw intermediate nodes (lightblue)
        if intermediate_nodes:
            nx.draw_networkx_nodes(
                G,
                pos,
                nodelist=list(intermediate_nodes),
                node_color="lightblue",
                node_size=1500,
                alpha=0.9,
                label="Intermediate hops",
            )

        # Draw destination nodes (green)
        if destination_nodes:
            nx.draw_networkx_nodes(
                G,
                pos,
                nodelist=list(destination_nodes),
                node_color="lightgreen",
                node_size=1500,
                alpha=0.9,
                label="Destinations",
            )

        # Draw edges with arrows (straight lines, no curve)
        nx.draw_networkx_edges(
            G,
            pos,
            edge_color="gray",
            arrows=True,
            arrowsize=20,
            arrowstyle="->",
            width=2,
            node_size=1500,
        )

        # Draw edge labels with latency information if provided
        if edge_latencies:
            edge_labels = {}
            for (src, dst), latencies in edge_latencies.items():
                if latencies:
                    avg_latency = sum(latencies) / len(latencies)
                    edge_labels[(src, dst)] = f"{avg_latency:.1f}ms"

            nx.draw_networkx_edge_labels(
                G,
                pos,
                edge_labels=edge_labels,
                font_size=8,
                font_color="red",
                bbox=dict(
                    boxstyle="round,pad=0.3",
                    facecolor="white",
                    edgecolor="none",
                    alpha=0.7,
                ),
            )

        # Draw labels
        nx.draw_networkx_labels(G, pos, font_size=8, font_family="monospace")

        plt.title(title, fontsize=14, fontweight="bold")
        plt.axis("off")
        plt.legend(loc="upper right", frameon=True, fancybox=True, shadow=True)
        plt.tight_layout()

        # Save to file if requested
        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches="tight")
            print(f"Topology visualization saved to: {output_file}")

        # Show interactive plot if requested
        if show:
            plt.show()

        plt.close()

    def get_graph_stats(self, adjacency: Dict[str, Set[str]]) -> Dict[str, int]:
        """Return basic statistics about the topology graph.

        Returns:
            Dict with 'nodes', 'edges', 'sources', 'destinations' counts
        """
        G = nx.DiGraph()
        for src, destinations in adjacency.items():
            for dst in destinations:
                G.add_edge(src, dst)

        return {
            "nodes": G.number_of_nodes(),
            "edges": G.number_of_edges(),  # type: ignore[misc]
            "sources": len(adjacency),
            "destinations": len(
                set(dst for dsts in adjacency.values() for dst in dsts)
            ),
        }
