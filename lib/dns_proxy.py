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
DNS proxy: intercepts queries for configured Hydra/Turbine domains and forwards everything else.
"""

import socket

from config import DNS_PORT, LAN_IP, PASSTHROUGH_DOMAINS, TARGET_DOMAINS, TURBINE_DOMAINS, UPSTREAM_DNS, domain_matches


def parse_dns_question(data: bytes) -> tuple[str, int]:
    """Parse the Question section of a DNS packet. Returns (name, offset)."""
    offset = 12
    labels = []
    while offset < len(data):
        length = data[offset]
        if length == 0:
            offset += 1
            break
        if (length & 0xC0) == 0xC0:  # compressed pointer
            offset += 2
            break
        labels.append(data[offset + 1:offset + 1 + length].decode("utf-8", errors="replace"))
        offset += 1 + length
    return ".".join(labels).lower(), offset


def build_dns_response(query: bytes, ip: str) -> bytes:
    """Build a DNS A record response pointing to the given IP."""
    tx_id   = query[:2]
    header  = tx_id + b"\x81\x80\x00\x01\x00\x01\x00\x00\x00\x00"

    # Copy question section verbatim
    offset = 12
    while offset < len(query):
        l = query[offset]
        if l == 0:
            offset += 1
            break
        if (l & 0xC0) == 0xC0:
            offset += 2
            break
        offset += 1 + l
    question = query[12:offset + 4]  # includes qtype and qclass

    answer = (
        b"\xc0\x0c"               # name pointer back to question
        + b"\x00\x01"             # type A
        + b"\x00\x01"             # class IN
        + b"\x00\x00\x00\x3c"    # TTL 60 s
        + b"\x00\x04"             # rdlength 4
        + socket.inet_aton(ip)
    )
    return header + question + answer


def forward_dns(data: bytes, upstream: str = UPSTREAM_DNS) -> bytes:
    """Forward a DNS query to the upstream resolver and return the response."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(3)
    try:
        sock.sendto(data, (upstream, 53))
        resp, _ = sock.recvfrom(4096)
        return resp
    finally:
        sock.close()


def dns_proxy_loop() -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", DNS_PORT))
    print(f"[DNS]  Listening on UDP 0.0.0.0:{DNS_PORT}")

    while True:
        try:
            data, addr = sock.recvfrom(512)
            if len(data) < 12:
                continue
            name, _ = parse_dns_question(data)

            if (
                domain_matches(name, TARGET_DOMAINS)
                or domain_matches(name, TURBINE_DOMAINS)
                or domain_matches(name, PASSTHROUGH_DOMAINS)
            ):
                reply_ip = "127.0.0.1" if addr[0] in ("127.0.0.1", LAN_IP) else LAN_IP
                response = build_dns_response(data, reply_ip)
                sock.sendto(response, addr)
                print(f"[DNS]  INTERCEPT  {name} -> {reply_ip}  (client: {addr[0]})")
            else:
                response = forward_dns(data)
                sock.sendto(response, addr)
                print(f"[DNS]  forward    {name}")
        except Exception as e:
            print(f"[DNS]  Error: {e}")
