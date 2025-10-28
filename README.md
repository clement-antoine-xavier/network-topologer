# Network Topologer

> A Python network topology discovery and visualization tool that maps internet routing paths using traceroute

A Python-based network topology discovery tool using traceroute. This tool can perform traceroutes to multiple destinations, build network topology maps, and visualize the network structure.

## What Does This Tool Do?

**Network Topologer** is a powerful command-line tool that discovers and visualizes network paths between your computer and remote destinations on the internet. 

### Core Functionality

- **Traceroute Multiple Destinations**: Trace the path packets take to reach one or more IP addresses simultaneously
- **Discover Network Topology**: Build a map of how different network paths interconnect, showing which routers are shared between different destinations
- **Measure Network Performance**: Track latency (response time) at each hop along the path
- **Visualize Network Structure**: Generate visual graphs showing the network topology with color-coded nodes and latency information
- **Generate Test Targets**: Automatically create random public IP addresses for network exploration and testing

### How It Works

The tool sends UDP packets with incrementing TTL (Time-To-Live) values, starting at 1. Each router along the path decrements the TTL and, when it reaches 0, sends back an ICMP "Time Exceeded" message. By collecting these responses, the tool maps out the complete path from source to destination, measures the latency at each hop, and builds a comprehensive network topology map.

### Use Cases

- **Network Diagnostics**: Identify routing issues, bottlenecks, or unreachable destinations
- **Performance Analysis**: Measure and compare network latency across different paths
- **Topology Discovery**: Understand how your traffic is routed through the internet
- **Network Research**: Explore internet routing patterns and infrastructure
- **Education**: Learn about network protocols, routing, and internet architecture

### Example Output

```
$ sudo python3 -m network-topologer 8.8.8.8 1.1.1.1
Traceroute to ['8.8.8.8', '1.1.1.1'] (timeout: 2 seconds):
Destination: 8.8.8.8
1       192.168.1.1     1.2 ms
2       10.0.0.1        5.8 ms
3       172.16.1.1      12.3 ms
4       8.8.8.8         15.7 ms

Destination: 1.1.1.1
1       192.168.1.1     1.1 ms
2       10.0.0.1        5.9 ms
3       172.16.1.1      12.5 ms
4       1.1.1.1         18.2 ms

Topology stats: 5 nodes, 6 edges
```

## Quick Start

```bash
# Clone the repository
git clone https://github.com/clement-antoine-xavier/network-topologer.git
cd network-topologer

# Run a basic traceroute (requires sudo for raw socket access)
sudo python3 -m network-topologer 8.8.8.8

# Generate 5 random IPs and trace them in parallel with visualization
sudo python3 -m network-topologer --random 5 --parallel --visualize
```

## Features

- **OOP Architecture**: Clean, modular design with separate classes for traceroute, network topology, and visualization
- **Pure Python Standard Library**: No external dependencies for core traceroute functionality (uses raw sockets)
- **Multiple Destinations**: Trace routes to multiple IP addresses simultaneously
- **Random IP Generation**: Generate random public IP addresses for testing
- **Parallel Execution**: Run traceroutes in parallel using threads for faster processing
- **Network Topology Building**: Build adjacency maps showing network connections
- **Latency Tracking**: Track and display RTT (Round-Trip Time) for each hop
- **Visualization**: Graph-based visualization using matplotlib and networkx (optional)
- **Exception Handling**: Comprehensive error handling for network issues

## Installation

Clone the repository:

```bash
git clone https://github.com/clement-antoine-xavier/network-topologer.git
cd network-topologer
```

For visualization support, install optional dependencies:

```bash
pip install matplotlib networkx
# Optional: for better layout
pip install pygraphviz
```

## Usage

### Basic Traceroute

Trace route to one or more IP addresses:

```bash
sudo python3 -m network-topologer 8.8.8.8 1.1.1.1
```

**Note:** Requires `sudo` or root privileges for raw socket access.

### Random IP Generation

Generate and trace random public IP addresses:

```bash
# Generate 5 random public IPs and trace them
sudo python3 -m network-topologer --random 5

# Generate 10 random IPs and run in parallel
sudo python3 -m network-topologer --random 10 --parallel
```

The random IP generator automatically excludes:
- Private IP ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
- Loopback addresses (127.0.0.0/8)
- Link-local addresses (169.254.0.0/16)
- Multicast addresses (224.0.0.0/4)

### Parallel Execution

Run traceroutes in parallel for faster execution:

```bash
sudo python3 -m network-topologer 8.8.8.8 1.1.1.1 9.9.9.9 --parallel

# Control number of worker threads
sudo python3 -m network-topologer --random 20 --parallel --workers 10
```

### Visualization

Visualize the network topology as a graph:

```bash
sudo python3 -m network-topologer 8.8.8.8 1.1.1.1 --visualize

# Save visualization to file
sudo python3 -m network-topologer --random 5 --visualize --output topology.png
```

The visualization features:
- **Green nodes**: Destination IPs
- **Blue nodes**: Intermediate hops (routers)
- **Edge labels**: Average latency in milliseconds
- **Hierarchical layout**: Straight lines showing network paths

### Advanced Options

```bash
# Custom UDP port (default: 33434)
sudo python3 -m network-topologer 8.8.8.8 --port 33435

# Custom timeout (default: 2 seconds)
sudo python3 -m network-topologer 8.8.8.8 --timeout 5
```

## Command-Line Options

```
positional arguments:
  destinations          One or more IPv4 addresses to traceroute to

optional arguments:
  -h, --help            Show this help message and exit
  -r COUNT, --random COUNT
                        Generate COUNT random public IP addresses to traceroute
  --port PORT           Destination UDP port to probe (default: 33434)
  --parallel            Run traceroutes in parallel using threads
  --workers WORKERS     Maximum number of worker threads when using --parallel
  -t TIMEOUT, --timeout TIMEOUT
                        Timeout for each packet in seconds (default: 2)
  --visualize           Visualize the network topology graph using matplotlib
  --output OUTPUT       Save topology visualization to file (e.g., topology.png)
```

## Examples

### Example 1: Trace to Major DNS Servers

```bash
sudo python3 -m network-topologer 8.8.8.8 8.8.4.4 1.1.1.1 1.0.0.1 --parallel --visualize
```

### Example 2: Random Network Discovery

```bash
sudo python3 -m network-topologer --random 15 --parallel --workers 5 --visualize --output network_map.png
```

### Example 3: Quick Test with Timeout

```bash
sudo python3 -m network-topologer --random 3 --timeout 1
```

## Architecture

The project is organized into modules:

- `exceptions.py`: Custom exception hierarchy
- `traceroute.py`: Core traceroute implementation using raw sockets
- `network_topologer.py`: Multi-destination traceroute orchestration
- `visualization.py`: Network topology graph visualization
- `__main__.py`: CLI entrypoint and argument parsing

## Technical Implementation

1. **UDP Probes**: Sends UDP packets with incrementing TTL (Time-To-Live) values
2. **ICMP Responses**: Listens for ICMP "Time Exceeded" messages from intermediate routers
3. **RTT Measurement**: Calculates round-trip time for each hop
4. **Topology Building**: Aggregates paths into an adjacency map
5. **Visualization**: Renders the network graph with colored nodes and latency labels

## Requirements

- Python 3.6+
- Root/sudo privileges (for raw socket access)
- Optional: matplotlib, networkx (for visualization)
- Optional: pygraphviz (for better graph layouts)

## License

See LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.
