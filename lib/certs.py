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
Certificate generation and SSL context setup.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
import ssl
import sys
import threading

from config import CA_KEY, CA_CERT, CERT_COMMON_NAME, CERT_DIR, CERT_SANS, SRV_CHAIN, SRV_CRT, SRV_KEY, domain_matches
from lib.helpers import run_cmd

# All domains the server cert must cover.
_SANS = list(CERT_SANS)
_CA_BACKDATE_DAYS = 30
_CA_VALIDITY_DAYS = 3650
_SERVER_BACKDATE_DAYS = 7
_SERVER_VALIDITY_DAYS = 825
_HOST_CONTEXTS: dict[str, ssl.SSLContext] = {}
_HOST_CONTEXTS_LOCK = threading.Lock()


def _ensure_fullchain() -> None:
    if not SRV_CRT.exists() or not CA_CERT.exists():
        return
    with open(SRV_CHAIN, "wb") as chain_handle:
        chain_handle.write(SRV_CRT.read_bytes())
        chain_handle.write(b"\n")
        chain_handle.write(CA_CERT.read_bytes())


def _remove_generated_host_certs() -> None:
    for path in CERT_DIR.glob("server-*.crt"):
        path.unlink(missing_ok=True)
    for path in CERT_DIR.glob("server-*.key"):
        path.unlink(missing_ok=True)
    for path in CERT_DIR.glob("server-*-fullchain.crt"):
        path.unlink(missing_ok=True)
    for path in CERT_DIR.glob("server-*.pub"):
        path.unlink(missing_ok=True)
    for path in CERT_DIR.glob("server-*_ext.cnf"):
        path.unlink(missing_ok=True)


def _ca_has_valid_profile() -> bool:
    """Return True if the CA cert has CA extensions and a sufficiently old notBefore."""
    if not CA_CERT.exists():
        return False
    try:
        result = run_cmd(f'openssl x509 -in "{CA_CERT}" -noout -text -startdate')
        if "CA:TRUE" not in result or "Certificate Sign" not in result:
            return False
        start_line = next(line for line in result.splitlines() if line.startswith("notBefore="))
        start_text = start_line.split("=", 1)[1].strip()
        not_before = datetime.strptime(start_text, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
        return not_before <= datetime.now(timezone.utc) - timedelta(days=7)
    except Exception:
        return False


def _cert_has_all_sans(cert_path: Path = SRV_CRT, required_sans: list[str] | None = None) -> bool:
    """Return True if the existing server cert already has every required SAN."""
    if required_sans is None:
        required_sans = _SANS
    if not cert_path.exists():
        return False
    try:
        result = run_cmd(f'openssl x509 -in "{cert_path}" -noout -text')
        for domain in required_sans:
            if domain not in result:
                return False
        return True
    except Exception:
        return False


def _cert_has_valid_backdate(cert_path: Path = SRV_CRT) -> bool:
    """Return True if the existing server cert starts sufficiently in the past."""
    if not cert_path.exists():
        return False
    try:
        result = run_cmd(f'openssl x509 -in "{cert_path}" -noout -startdate')
        start_text = result.split("=", 1)[1].strip()
        not_before = datetime.strptime(start_text, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
        return not_before <= datetime.now(timezone.utc) - timedelta(days=1)
    except Exception:
        return False


def _cert_matches_current_ca(cert_path: Path = SRV_CRT) -> bool:
    """Return True if the current server cert verifies against the current CA cert."""
    if not cert_path.exists() or not CA_CERT.exists():
        return False
    try:
        run_cmd(f'openssl verify -CAfile "{CA_CERT}" "{cert_path}"')
        return True
    except Exception:
        return False


def _cert_has_common_name(cert_path: Path, common_name: str) -> bool:
    if not cert_path.exists():
        return False
    try:
        result = run_cmd(f'openssl x509 -in "{cert_path}" -noout -subject -nameopt RFC2253')
        return f"CN={common_name}" in result
    except Exception:
        return False


def _sanitize_host_for_filename(host: str) -> str:
    return re.sub(r"[^a-z0-9.-]+", "_", host.lower())


def _host_cert_paths(host: str) -> tuple[Path, Path, Path, Path, Path]:
    suffix = _sanitize_host_for_filename(host)
    key_path = CERT_DIR / f"server-{suffix}.key"
    crt_path = CERT_DIR / f"server-{suffix}.crt"
    chain_path = CERT_DIR / f"server-{suffix}-fullchain.crt"
    pub_path = CERT_DIR / f"server-{suffix}.pub"
    ext_path = CERT_DIR / f"server-{suffix}_ext.cnf"
    return key_path, crt_path, chain_path, pub_path, ext_path


def _write_chain(leaf_path: Path, chain_path: Path) -> None:
    with open(chain_path, "wb") as chain_handle:
        chain_handle.write(leaf_path.read_bytes())
        chain_handle.write(b"\n")
        chain_handle.write(CA_CERT.read_bytes())


def _generate_server_cert(common_name: str, san_domains: list[str], key_path: Path, crt_path: Path, chain_path: Path, pub_path: Path, ext_path: Path) -> None:
    san_list = ",".join(f"DNS:{domain}" for domain in san_domains)
    run_cmd(f'openssl genrsa -out "{key_path}" 2048')
    run_cmd(f'openssl pkey -in "{key_path}" -pubout -out "{pub_path}"')
    ext_path.write_text(
        "[v3_req]\n"
        "basicConstraints = CA:FALSE\n"
        "keyUsage = digitalSignature, keyEncipherment\n"
        "extendedKeyUsage = serverAuth\n"
        f"subjectAltName = {san_list}\n"
    )
    not_before = (datetime.now(timezone.utc) - timedelta(days=_SERVER_BACKDATE_DAYS)).strftime("%Y%m%d%H%M%SZ")
    not_after = (datetime.now(timezone.utc) + timedelta(days=_SERVER_VALIDITY_DAYS)).strftime("%Y%m%d%H%M%SZ")
    run_cmd(
        f'openssl x509 -new -force_pubkey "{pub_path}" '
        f'-set_subject "/CN={common_name}" '
        f'-CA "{CA_CERT}" -CAkey "{CA_KEY}" -CAcreateserial '
        f'-out "{crt_path}" -extensions v3_req -extfile "{ext_path}" '
        f'-not_before {not_before} -not_after {not_after}'
    )
    pub_path.unlink(missing_ok=True)
    _write_chain(crt_path, chain_path)
    print(f"[CERT] Server cert CN={common_name} SANs: {san_list}")


def _ensure_host_cert(host: str) -> tuple[Path, Path]:
    key_path, crt_path, chain_path, pub_path, ext_path = _host_cert_paths(host)
    cert_ready = (
        _cert_has_all_sans(crt_path, [host])
        and _cert_has_valid_backdate(crt_path)
        and _cert_matches_current_ca(crt_path)
        and _cert_has_common_name(crt_path, host)
    )
    if not cert_ready:
        crt_path.unlink(missing_ok=True)
        key_path.unlink(missing_ok=True)
        chain_path.unlink(missing_ok=True)
        pub_path.unlink(missing_ok=True)
        ext_path.unlink(missing_ok=True)
        _generate_server_cert(host, [host], key_path, crt_path, chain_path, pub_path, ext_path)
    elif not chain_path.exists():
        _write_chain(crt_path, chain_path)
    return chain_path, key_path


def _build_context_from_chain(chain_path: Path, key_path: Path) -> ssl.SSLContext:
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(certfile=str(chain_path), keyfile=str(key_path))
    return ctx


def _context_for_host(host: str) -> ssl.SSLContext:
    normalized_host = host.strip().lower().rstrip(".")
    with _HOST_CONTEXTS_LOCK:
        cached = _HOST_CONTEXTS.get(normalized_host)
        if cached is not None:
            return cached
        chain_path, key_path = _ensure_host_cert(normalized_host)
        ctx = _build_context_from_chain(chain_path, key_path)
        _HOST_CONTEXTS[normalized_host] = ctx
        return ctx


def gen_certs() -> None:
    ca_ready = _ca_has_valid_profile()
    cert_ready = _cert_has_all_sans() and _cert_has_valid_backdate() and _cert_matches_current_ca()
    if ca_ready and cert_ready:
        _ensure_fullchain()
        print("[CERT] Certificates already exist with all required SANs, skipping.")
        return

    if not ca_ready:
        print("[CERT] CA cert missing required CA profile or validity backdate; regenerating CA and server certificate.")
        CA_CERT.unlink(missing_ok=True)
        CA_KEY.unlink(missing_ok=True)
        SRV_CRT.unlink(missing_ok=True)
        SRV_KEY.unlink(missing_ok=True)
        SRV_CHAIN.unlink(missing_ok=True)
        (CERT_DIR / "server.csr").unlink(missing_ok=True)
        (CERT_DIR / "server.pub").unlink(missing_ok=True)
        (CERT_DIR / "ca.srl").unlink(missing_ok=True)
        _remove_generated_host_certs()
        _HOST_CONTEXTS.clear()
        print("[CERT] Generating CA and server certificate...")
        run_cmd(f'openssl genrsa -out "{CA_KEY}" 4096')
        ca_ext = CERT_DIR / "ca_ext.cnf"
        ca_ext.write_text(
            "[v3_ca]\n"
            "basicConstraints = critical,CA:TRUE\n"
            "keyUsage = critical,keyCertSign,cRLSign\n"
            "subjectKeyIdentifier = hash\n"
            "authorityKeyIdentifier = keyid:always\n"
        )
        ca_not_before = (datetime.now(timezone.utc) - timedelta(days=_CA_BACKDATE_DAYS)).strftime("%Y%m%d%H%M%SZ")
        ca_not_after = (datetime.now(timezone.utc) + timedelta(days=_CA_VALIDITY_DAYS)).strftime("%Y%m%d%H%M%SZ")
        run_cmd(
            f'openssl x509 -new -key "{CA_KEY}" -out "{CA_CERT}" '
            f'-set_subject "/CN=LocalProxyCA/O=LocalProxy" '
            f'-extensions v3_ca -extfile "{ca_ext}" '
            f'-not_before {ca_not_before} -not_after {ca_not_after}'
        )
    elif CA_CERT.exists() and SRV_CRT.exists() and not cert_ready:
        print("[CERT] Server cert missing SANs or validity backdate; regenerating server cert only.")
        SRV_CRT.unlink(missing_ok=True)
        SRV_KEY.unlink(missing_ok=True)
        SRV_CHAIN.unlink(missing_ok=True)
        (CERT_DIR / "server.csr").unlink(missing_ok=True)
        (CERT_DIR / "server.pub").unlink(missing_ok=True)
        _remove_generated_host_certs()
        _HOST_CONTEXTS.clear()
    else:
        print("[CERT] Generating CA and server certificate...")
        run_cmd(f'openssl genrsa -out "{CA_KEY}" 4096')
        run_cmd(
            f'openssl req -new -x509 -days 3650 -key "{CA_KEY}" -out "{CA_CERT}" '
            f'-subj "/CN=LocalProxyCA/O=LocalProxy"'
        )

    _generate_server_cert(
        CERT_COMMON_NAME,
        _SANS,
        SRV_KEY,
        SRV_CRT,
        SRV_CHAIN,
        CERT_DIR / "server.pub",
        CERT_DIR / "server_ext.cnf",
    )
    print(f"[CERT] Certificates saved to {CERT_DIR}")

    if sys.platform == "win32":
        try:
            run_cmd(f'certutil -addstore -f Root "{CA_CERT}"')
            print("[CERT] CA installed to Windows Root Store")
        except Exception as e:
            print(f"[CERT] Failed to install CA locally: {e}")


def build_ssl_context() -> ssl.SSLContext:
    cert_path = SRV_CHAIN if SRV_CHAIN.exists() else SRV_CRT
    ctx = _build_context_from_chain(cert_path, SRV_KEY)

    def _on_server_name(ssl_sock: ssl.SSLSocket, server_name: str | None, _initial_ctx: ssl.SSLContext) -> None:
        if not server_name:
            return
        host = server_name.strip().lower().rstrip(".")
        if not host or not domain_matches(host, CERT_SANS):
            return
        try:
            ssl_sock.context = _context_for_host(host)
            print(f"[CERT] Selected SNI certificate for {host}")
        except Exception as exc:
            print(f"[CERT] Failed to prepare SNI certificate for {host}: {exc}")

    ctx.set_servername_callback(_on_server_name)
    return ctx
