# CIDR Network Planner

A lightweight, zero-dependency command-line utility for network engineers, DevOps practitioners, and cloud architects to inspect CIDR blocks, split subnets, check address containment, and audit network topologies for overlapping IP ranges.

## Problem

Designing VPCs, subnets, and routing tables across cloud providers (AWS, GCP, Azure) and on-premise infrastructure often leads to IP space collisions, unoptimized subnet sizes, and arithmetic errors. Calculating host counts, usable ranges, bitmasks, and subnet partitions by hand or with browser-based calculators is slow and prone to errors. `cidr-network-planner` provides an offline, scriptable CLI tool that runs anywhere Python 3 is installed.

## Features

- **Inspect CIDRs**: Compute network address, broadcast address, netmask, wildcard mask, usable host range, host capacity, binary bitmask breakdown, and RFC address classification (Private, Public, Loopback, Link-Local, Carrier-Grade NAT).
- **Subnet Splitting**: Partition larger CIDR blocks into smaller subnets by prefix length (e.g. split `/24` into `/26`s) or target subnet count.
- **Containment Check**: Test whether an IP address or child CIDR resides within a parent network block.
- **Collision & Overlap Auditor**: Audit lists of CIDR blocks to detect duplicates, supernet/subnet containments, and address overlaps before deploying cloud infrastructure.
- **Machine-Readable JSON**: Pass `--json` to any command for clean integration with CI/CD pipelines, Terraform wrappers, and shell scripts.

## Setup

Requires Python 3.8+ with no external dependencies.

```bash
# Verify Python 3
python3 --version

# Make executable
chmod +x run.py
```

## Usage

### 1. Inspect a CIDR Block

```bash
./run.py inspect 192.168.10.0/24
./run.py inspect 10.0.0.0/16 --json
```

### 2. Split a Subnet into Smaller Partitions

```bash
# Split /24 into /26 subnets
./run.py split 172.16.0.0/24 --prefix 26

# Split a network into 4 equal subnets
./run.py split 10.50.0.0/20 --count 4
```

### 3. Check Containment

```bash
./run.py contains 10.0.0.0/16 10.0.4.15
./run.py contains 192.168.0.0/16 192.168.12.0/24
```

### 4. Audit Network Overlaps & Collisions

```bash
./run.py audit 10.0.0.0/24 10.0.1.0/24 10.0.0.128/25 192.168.1.0/24

# Or pass from standard input
cat subnets.txt | ./run.py audit -
```

## Tests

Run the built-in test suite:

```bash
python3 -m unittest discover tests
```
