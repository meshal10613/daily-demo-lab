"""Unit tests for cidr_planner core operations."""

import unittest
from cidr_planner.core import (
    inspect_cidr,
    split_cidr,
    contains_target,
    audit_cidrs,
)


class TestInspectCIDR(unittest.TestCase):
    def test_inspect_ipv4_standard(self):
        data = inspect_cidr("192.168.1.0/24")
        self.assertEqual(data["cidr"], "192.168.1.0/24")
        self.assertEqual(data["version"], 4)
        self.assertEqual(data["network_address"], "192.168.1.0")
        self.assertEqual(data["netmask"], "255.255.255.0")
        self.assertEqual(data["broadcast_address"], "192.168.1.255")
        self.assertEqual(data["total_addresses"], 256)
        self.assertEqual(data["usable_addresses"], 254)
        self.assertEqual(data["first_usable"], "192.168.1.1")
        self.assertEqual(data["last_usable"], "192.168.1.254")
        self.assertIn("Private", data["classification"])
        self.assertTrue(data["binary"]["network_binary"].startswith("11000000"))

    def test_inspect_host_address_input(self):
        # Passing host address inside subnet without strict=False should still normalize to network
        data = inspect_cidr("10.0.4.55/24")
        self.assertEqual(data["network_address"], "10.0.4.0")
        self.assertEqual(data["first_usable"], "10.0.4.1")
        self.assertEqual(data["last_usable"], "10.0.4.254")

    def test_inspect_slash_31_p2p(self):
        data = inspect_cidr("10.0.0.0/31")
        self.assertEqual(data["usable_addresses"], 2)
        self.assertEqual(data["first_usable"], "10.0.0.0")
        self.assertEqual(data["last_usable"], "10.0.0.1")

    def test_inspect_slash_32_single_host(self):
        data = inspect_cidr("8.8.8.8/32")
        self.assertEqual(data["usable_addresses"], 1)
        self.assertEqual(data["first_usable"], "8.8.8.8")
        self.assertEqual(data["last_usable"], "8.8.8.8")
        self.assertIn("Public", data["classification"])

    def test_inspect_ipv6(self):
        data = inspect_cidr("2001:db8::/64")
        self.assertEqual(data["version"], 6)
        self.assertEqual(data["network_address"], "2001:db8::")
        self.assertEqual(data["prefix_length"], 64)
        self.assertTrue(data["total_addresses"] > 1_000_000)

    def test_invalid_cidr(self):
        with self.assertRaises(ValueError):
            inspect_cidr("999.999.999.999/24")


class TestSplitCIDR(unittest.TestCase):
    def test_split_by_prefix(self):
        subnets = split_cidr("192.168.0.0/24", new_prefix=26)
        self.assertEqual(len(subnets), 4)
        self.assertEqual(subnets[0]["cidr"], "192.168.0.0/26")
        self.assertEqual(subnets[1]["cidr"], "192.168.0.64/26")
        self.assertEqual(subnets[2]["cidr"], "192.168.0.128/26")
        self.assertEqual(subnets[3]["cidr"], "192.168.0.192/26")
        self.assertEqual(subnets[0]["usable_addresses"], 62)

    def test_split_by_count(self):
        subnets = split_cidr("10.0.0.0/16", count=4)
        self.assertEqual(len(subnets), 4)
        self.assertEqual(subnets[0]["cidr"], "10.0.0.0/18")
        self.assertEqual(subnets[3]["cidr"], "10.0.192.0/18")

    def test_split_invalid_prefix(self):
        with self.assertRaises(ValueError):
            split_cidr("10.0.0.0/24", new_prefix=20)  # Smaller prefix than parent
        with self.assertRaises(ValueError):
            split_cidr("10.0.0.0/24", new_prefix=33)  # Exceeds 32


class TestContainsTarget(unittest.TestCase):
    def test_contains_ip_true(self):
        res = contains_target("10.0.0.0/8", "10.254.12.1")
        self.assertTrue(res["is_contained"])
        self.assertEqual(res["target_type"], "address")

    def test_contains_ip_false(self):
        res = contains_target("192.168.1.0/24", "192.168.2.1")
        self.assertFalse(res["is_contained"])

    def test_contains_subnet_true(self):
        res = contains_target("172.16.0.0/12", "172.20.10.0/24")
        self.assertTrue(res["is_contained"])
        self.assertEqual(res["target_type"], "network")

    def test_contains_subnet_false(self):
        res = contains_target("172.16.0.0/24", "172.16.0.0/16")
        self.assertFalse(res["is_contained"])


class TestAuditCIDRs(unittest.TestCase):
    def test_clean_topology(self):
        cidrs = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
        res = audit_cidrs(cidrs)
        self.assertFalse(res["has_overlaps"])
        self.assertEqual(res["overlap_count"], 0)
        self.assertEqual(len(res["errors"]), 0)

    def test_overlapping_subnets(self):
        cidrs = ["10.0.0.0/16", "10.0.10.0/24", "192.168.1.0/24"]
        res = audit_cidrs(cidrs)
        self.assertTrue(res["has_overlaps"])
        self.assertEqual(res["overlap_count"], 1)
        self.assertEqual(res["overlaps"][0]["cidr_a"], "10.0.0.0/16")
        self.assertEqual(res["overlaps"][0]["cidr_b"], "10.0.10.0/24")

    def test_duplicate_networks(self):
        cidrs = ["10.5.0.0/24", "10.5.0.0/24"]
        res = audit_cidrs(cidrs)
        self.assertTrue(res["has_overlaps"])
        self.assertEqual(res["overlaps"][0]["relationship"], "duplicate")

    def test_syntax_errors_recorded(self):
        cidrs = ["10.0.0.0/24", "invalid-cidr", "192.168.1.0/24"]
        res = audit_cidrs(cidrs)
        self.assertEqual(len(res["errors"]), 1)
        self.assertEqual(res["errors"][0]["input"], "invalid-cidr")


if __name__ == "__main__":
    unittest.main()
