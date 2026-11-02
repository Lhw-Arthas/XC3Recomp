"""XC3 instruction patches (contract: docs/contracts/patch-format.md).

Empty on purpose: every XCDE patch targets XCDE addresses. Add XC3 patches here once each site is found again.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools", "lifter"))
from patchfmt import Patch  # noqa: E402,F401

PATCHES = {}
