"""Core networking logic for CIDR inspection, splitting, and auditing."""

import ipaddress
import math
from typing import Dict, Any, List, Optional, Tuple


def classify_network(net: ipaddress._BaseNetwork) -> str:
    """Return a descriptive classification string for a given network."""
    if net.is_loopback:
        return "Loopback"
    if net.is_multicast:
        return "Multicast"
    if net.is_link_local:
        return "Link-Local"
    if net.is_private:
        return "Private (RFC 1918 / RFC 4193)"
    if isinstance(net, ipaddress.IPv4Network):
        # Check for CGNAT (100.64.0.0/10)
        cgnat = ipaddress.IPv4Network("100.64.0.0/10")
        if net.subnet_of(cgnat) or cgnat.subnet_of(net) or net.overlaps(cgnat):
            return "Carrier-Grade NAT (RFC 6598)"
    return "Public / Globally Routable"


def inspect_cidr(cidr_str: str) -> Dict[str, Any]:
    """Inspect a CIDR block and return detailed architectural metrics."""
    cidr_clean = cidr_str.strip()
    try:
        net = ipaddress.ip_network(cidr_clean, strict=False)
    except ValueError as exc:
        raise ValueError(f"Invalid CIDR notation '{cidr_str}': {exc}") from exc

    is_v4 = isinstance(net, ipaddress.IPv4Network)
    total_addresses = net.num_addresses

    if is_v4:
        if net.prefixlen <= 30:
            first_usable = str(net.network_address + 1)
            last_usable = str(net.broadcast_address - 1)
            usable_count = total_addresses - 2
        elif net.prefixlen == 31:
            # RFC 3021 point-to-point links
            first_usable = str(net.network_address)
            last_usable = str(net.broadcast_address)
            usable_count = 2
        else:  # /32 single host
            first_usable = str(net.network_address)
            last_usable = str(net.network_address)
            usable_count = 1
        broadcast_str = str(net.broadcast_address)
        netmask_str = str(net.netmask)
        hostmask_str = str(net.hostmask)
        bin_ip = f"{int(net.network_address):032b}"
        bin_netmask = f"{int(net.netmask):032b}"
        bin_display = {
            "network_binary": ".".join(bin_ip[i : i + 8] for i in range(0, 32, 8)),
            "netmask_binary": ".".join(bin_netmask[i : i + 8] for i in range(0, 32, 8)),
        }
    else:
        # IPv6
        if net.prefixlen <= 126:
            first_usable = str(net.network_address + 1)
            last_usable = str(net.network_address + total_addresses - 1)
            usable_count = total_addresses - 1
        elif net.prefixlen == 127:
            first_usable = str(net.network_address)
            last_usable = str(net.network_address + 1)
            usable_count = 2
        else:
            first_usable = str(net.network_address)
            last_usable = str(net.network_address)
            usable_count = 1
        broadcast_str = "N/A (IPv6 uses Multicast)"
        netmask_str = str(net.netmask)
        hostmask_str = str(net.hostmask)
        bin_ip = f"{int(net.network_address):0128b}"
        bin_netmask = f"{int(net.netmask):0128b}"
        bin_display = {
            "network_binary": ":".join(bin_ip[i : i + 16] for i in range(0, 128, 16)),
            "netmask_binary": ":".join(bin_netmask[i : i + 16] for i in range(0, 128, 16)),
        }

    return {
        "input": cidr_str,
        "cidr": str(net),
        "version": 4 if is_v4 else 6,
        "network_address": str(net.network_address),
        "netmask": netmask_str,
        "wildcard_mask": hostmask_str,
        "broadcast_address": broadcast_str,
        "prefix_length": net.prefixlen,
        "total_addresses": total_addresses,
        "usable_addresses": usable_count,
        "first_usable": first_usable,
        "last_usable": last_usable,
        "classification": classify_network(net),
        "binary": bin_display,
    }


def split_cidr(
    cidr_str: str,
    new_prefix: Optional[int] = None,
    count: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Split a parent CIDR into smaller subnets based on prefix length or subnet count."""
    net = ipaddress.ip_network(cidr_str.strip(), strict=False)
    max_prefix = 32 if isinstance(net, ipaddress.IPv4Network) else 128

    if new_prefix is not None:
        if new_prefix <= net.prefixlen:
            raise ValueError(
                f"New prefix (/{new_prefix}) must be greater than parent prefix (/{net.prefixlen})"
            )
        if new_prefix > max_prefix:
            raise ValueError(
                f"New prefix (/{new_prefix}) exceeds maximum allowed prefix (/{max_prefix})"
            )
        subnets_iter = net.subnets(new_prefix=new_prefix)
    elif count is not None:
        if count <= 1:
            raise ValueError("Subnet count must be 2 or greater.")
        # Find next power of 2
        bits_needed = math.ceil(math.log2(count))
        calculated_prefix = net.prefixlen + bits_needed
        if calculated_prefix > max_prefix:
            raise ValueError(
                f"Cannot split /{net.prefixlen} into {count} subnets (requires /{calculated_prefix}, max /{max_prefix})"
            )
        subnets_iter = net.subnets(prefixlen_diff=bits_needed)
    else:
        raise ValueError("Either 'new_prefix' or 'count' must be specified.")

    results = []
    for idx, sub in enumerate(subnets_iter, start=1):
        info = inspect_cidr(str(sub))
        info["index"] = idx
        results.append(info)
    return results


def contains_target(parent_cidr: str, target: str) -> Dict[str, Any]:
    """Check if an IP address or child subnet is contained inside a parent CIDR."""
    parent_net = ipaddress.ip_network(parent_cidr.strip(), strict=False)
    target_clean = target.strip()

    try:
        # Check if target is an IP address
        if "/" not in target_clean:
            ip_obj = ipaddress.ip_address(target_clean)
            is_contained = ip_obj in parent_net
            target_type = "address"
            target_str = str(ip_obj)
        else:
            child_net = ipaddress.ip_network(target_clean, strict=False)
            is_contained = child_net.subnet_of(parent_net)
            target_type = "network"
            target_str = str(child_net)
    except ValueError as exc:
        raise ValueError(f"Invalid target '{target}': {exc}") from exc

    return {
        "parent_cidr": str(parent_net),
        "target": target_str,
        "target_type": target_type,
        "is_contained": is_contained,
    }


def audit_cidrs(cidr_list: List[str]) -> Dict[str, Any]:
    """Analyze a list of CIDRs for duplicates, overlaps, and hierarchy relationships."""
    parsed_networks: List[Tuple[str, ipaddress._BaseNetwork]] = []
    errors: List[Dict[str, str]] = []

    for raw in cidr_list:
        raw_clean = raw.strip()
        if not raw_clean or raw_clean.startswith("#"):
            continue
        try:
            net = ipaddress.ip_network(raw_clean, strict=False)
            parsed_networks.append((raw_clean, net))
        except ValueError as err:
            errors.append({"input": raw_clean, "error": str(err)})

    # Sort networks by network address then prefix
    parsed_networks.sort(key=lambda item: (item[1].version, item[1].network_address, item[1].prefixlen))

    overlaps: List[Dict[str, Any]] = []
    n = len(parsed_networks)

    for i in range(n):
        raw_a, net_a = parsed_networks[i]
        for j in range(i + 1, n):
            raw_b, net_b = parsed_networks[j]
            if net_a.version != net_b.version:
                continue
            if net_a.overlaps(net_b):
                if net_a == net_b:
                    rel = "duplicate"
                elif net_a.subnet_of(net_b):
                    rel = f"{net_a} is subnet of {net_b}"
                elif net_b.subnet_of(net_a):
                    rel = f"{net_b} is subnet of {net_a}"
                else:
                    rel = "overlapping"

                overlaps.append({
                    "cidr_a": str(net_a),
                    "input_a": raw_a,
                    "cidr_b": str(net_b),
                    "input_b": raw_b,
                    "relationship": rel,
                })

    unique_networks = [str(net) for _, net in parsed_networks]
    return {
        "total_inputs": len(parsed_networks),
        "valid_cidrs": unique_networks,
        "has_overlaps": len(overlaps) > 0,
        "overlap_count": len(overlaps),
        "overlaps": overlaps,
        "errors": errors,
    }
