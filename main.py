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
Mad Max (2015) - Local Server Emulator + DNS Proxy

Entry point: starts DNS, HTTPS, and provisioning HTTP servers.

Run as Administrator (Windows) or with sudo (Linux) to bind privileged ports.
"""

import argparse
import atexit
import io
import os
import sys
import threading
import time
from datetime import datetime


def _parse_args():
    parser = argparse.ArgumentParser(description="Mad Max (2015) offline server")
    parser.add_argument(
        "-d", "--debug",
        action="store_true",
        help="Enable debug logging to file (logs/, last.console.log)"
    )
    return parser.parse_args()


# Parse args first, before importing server modules that set up file logging.
args = _parse_args()

from lib import config_runtime
config_runtime.DEBUG = args.debug

from lib.certs import gen_certs, build_ssl_context
from config import LAN_IP, PASSTHROUGH_DOMAINS, TARGET_DOMAINS
from lib.dns_proxy import dns_proxy_loop
from lib.https_server import https_server_loop
from lib.provision import http_provision_loop


class _TeeStream(io.TextIOBase):
    def __init__(self, original, log_file):
        self._original = original
        self._log_file = log_file

    def write(self, s):
        if not isinstance(s, str):
            s = str(s)
        self._original.write(s)
        self._log_file.write(s)
        return len(s)

    def flush(self):
        self._original.flush()
        self._log_file.flush()

    def isatty(self):
        return getattr(self._original, "isatty", lambda: False)()

    @property
    def encoding(self):
        return getattr(self._original, "encoding", "utf-8")


def _install_console_log_tee(log_path: str = "last.console.log") -> None:
    log_file = open(log_path, "w", encoding="utf-8", buffering=1)
    started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file.write(f"===== console session started: {started_at} =====\n")

    sys.stdout = _TeeStream(sys.stdout, log_file)
    sys.stderr = _TeeStream(sys.stderr, log_file)

    def _close_log_file() -> None:
        try:
            finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_file.write(f"\n===== console session finished: {finished_at} =====\n")
            log_file.flush()
            log_file.close()
        except Exception:
            pass

    atexit.register(_close_log_file)


def main() -> None:
    if config_runtime.DEBUG:
        _install_console_log_tee()

    print("=" * 60)
    print("  Mad Max (2015) - Local Server Emulator")
    print(f"  LAN IP : {LAN_IP}")
    print(f"  Target : {', '.join(TARGET_DOMAINS)}")
    if PASSTHROUGH_DOMAINS:
        print(f"  Passthrough : {', '.join(PASSTHROUGH_DOMAINS)}")
    if config_runtime.DEBUG:
        print("  Mode   : DEBUG (file logging enabled)")
    print("=" * 60)

    gen_certs()
    ctx = build_ssl_context()

    threads = [
        threading.Thread(target=dns_proxy_loop,      daemon=True, name="DNS"),
        threading.Thread(target=https_server_loop,   daemon=True, name="HTTPS", args=(ctx,)),
        threading.Thread(target=http_provision_loop, daemon=True, name="HTTP"),
    ]

    for t in threads:
        t.start()
        time.sleep(0.1)

    print("\n[MAIN] All servers running. Press Ctrl+C to stop.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[MAIN] Shutting down...")


if __name__ == "__main__":
    main()
