# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025  madmax-2015-offline contributors
#
# This file is part of madmax-2015-offline.
#
# madmax-2015-offline is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# madmax-2015-offline is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
Mad Max (2015) - Local Server Emulator
Configuration constants and certificate paths.
"""

import sys
from collections.abc import Iterable
from pathlib import Path


def _normalize_domain(value: str) -> str:
    return value.strip().lower().rstrip(".")


def _normalize_domain_patterns(value: str | Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, str):
        values = [value]
    else:
        values = list(value)
    return tuple(_normalize_domain(item) for item in values if item and item.strip())


def _unique_domains(*groups: str | Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for group in groups:
        for domain in _normalize_domain_patterns(group):
            if domain in seen:
                continue
            seen.add(domain)
            ordered.append(domain)
    return tuple(ordered)


def domain_matches(host: str, patterns: str | Iterable[str]) -> bool:
    normalized_host = _normalize_domain(host)
    if not normalized_host:
        return False
    for pattern in _normalize_domain_patterns(patterns):
        if pattern.startswith("*."):
            suffix = pattern[2:]
            if suffix and normalized_host != suffix and normalized_host.endswith(f".{suffix}"):
                return True
            continue
        if normalized_host == pattern:
            return True
    return False


# ---------------------------------------------------------------------------
# Network
# ---------------------------------------------------------------------------

TARGET_DOMAIN = "blackjack.hydra.agoragames.com"
# Accepts a single string or a list of exact / wildcard host patterns.
# Wildcards should use SAN-compatible syntax, for example "*.psn.turbine.com".
TURBINE_DOMAIN = ["cls.psn.turbine.com", "*.psn.turbine.com"]
PASSTHROUGH_DOMAIN = []
TARGET_DOMAINS = _normalize_domain_patterns(TARGET_DOMAIN)
TURBINE_DOMAINS = _normalize_domain_patterns(TURBINE_DOMAIN)
PASSTHROUGH_DOMAINS = _normalize_domain_patterns(PASSTHROUGH_DOMAIN)
CERT_SANS = _unique_domains(TARGET_DOMAINS, TURBINE_DOMAINS, PASSTHROUGH_DOMAINS)
CERT_COMMON_NAME = TARGET_DOMAINS[0] if TARGET_DOMAINS else (CERT_SANS[0] if CERT_SANS else "localhost")
UPSTREAM_DNS = "1.1.1.1"
DNS_PORT = 53
HTTPS_PORT = 443
HTTP_PORT = 8888  # provisioning server port (plain HTTP)

# ---------------------------------------------------------------------------
# LAN_IP — REQUIRED
#
# Set this to the IP address of the machine running the proxy.
#
# For all supported configurations (Steam Deck standalone, Windows single-PC,
# Windows + Steam Deck, Linux + Steam Deck) this should be the LAN IP of the
# machine running the proxy — e.g. "192.168.1.10".
#
# To find your LAN IP:
#   Windows     : ipconfig
#   Linux/Deck  : ip -4 addr | grep inet
# ---------------------------------------------------------------------------
LAN_IP = "0.0.0.0"  # <-- replace with your actual LAN IP, e.g. "192.168.1.10"
# use the LAN IP of the proxy PC.
#
# To find your LAN IP:
#   Windows     : ipconfig
#   Linux/Deck  : ip -4 addr | grep inet
# ---------------------------------------------------------------------------
LAN_IP = "0.0.0.0"  # <-- replace with your actual LAN IP, e.g. "192.168.1.10"

_UNSET_VALUES = {"0.0.0.0", "", "x.x.x.x", "192.168.1.x", "your-ip-here"}

if LAN_IP.strip() in _UNSET_VALUES:
    print("", file=sys.stderr)
    print("ERROR: LAN_IP is not configured.", file=sys.stderr)
    print("", file=sys.stderr)
    print("  Open config.py and set LAN_IP to the IP address of this machine.", file=sys.stderr)
    print("  Example:", file=sys.stderr)
    print("    LAN_IP = \"192.168.1.10\"", file=sys.stderr)
    print("", file=sys.stderr)
    print("  To find your IP:", file=sys.stderr)
    print("    Windows    : ipconfig", file=sys.stderr)
    print("    Linux/Deck : ip -4 addr | grep inet", file=sys.stderr)
    print("", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Wine / Proton
# ---------------------------------------------------------------------------

# Version string that appears in the Proton installation path.
# Used by provisioning scripts to locate wine/wineboot/wineserver.
# Example: "Proton 9.0", "Proton Experimental"
WINE_PROTON_VER = "Proton 10.0"

# Steam App ID for Mad Max (2015). Do not change unless Valve reassigns it.
GAME_APP_ID = "234140"

# ---------------------------------------------------------------------------
# Certificate paths
# ---------------------------------------------------------------------------
CERT_DIR = Path.home() / ".local" / "share" / "local_proxy"
CERT_DIR.mkdir(parents=True, exist_ok=True)

CA_KEY = CERT_DIR / "ca.key"
CA_CERT = CERT_DIR / "ca.crt"
SRV_KEY = CERT_DIR / "server.key"
SRV_CRT = CERT_DIR / "server.crt"
SRV_CHAIN = CERT_DIR / "server-fullchain.crt"
