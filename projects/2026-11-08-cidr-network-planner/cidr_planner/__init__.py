"""CIDR Network Planner package."""

from .core import (
    inspect_cidr,
    split_cidr,
    contains_target,
    audit_cidrs,
)

__all__ = ["inspect_cidr", "split_cidr", "contains_target", "audit_cidrs"]
