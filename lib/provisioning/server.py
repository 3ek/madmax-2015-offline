"""Provisioning HTTP server and request handling."""

import socket
import threading

from config import HTTP_PORT, LAN_IP
from lib.helpers import read_http_request

from .http import send_response
from .routes import route_provision_path

_BASE = f"http://{LAN_IP}:{HTTP_PORT}"


def handle_provision(conn: socket.socket, addr) -> None:
    try:
        request, _ = read_http_request(conn)
        path = _extract_path(request)
        print(f"[HTTP] {addr[0]}  GET {path}")
        status, body, content_type, content_disposition = route_provision_path(path)
        send_response(
            conn,
            status,
            body,
            content_type=content_type,
            content_disposition=content_disposition,
        )
    except Exception as exc:
        print(f"[HTTP] Error {addr}: {exc}")
    finally:
        try:
            conn.close()
        except Exception:
            pass


def http_provision_loop() -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(("0.0.0.0", HTTP_PORT))
    except OSError as exc:
        print(f"[HTTP] ERROR: Cannot bind to port {HTTP_PORT}: {exc}")
        if exc.errno == 98:  # EADDRINUSE
            print(f"[HTTP]   Port {HTTP_PORT} is already in use.")
            print(f"[HTTP]   Another instance may be running. Check with: ss -tlnp | grep {HTTP_PORT}")
            print(f"[HTTP]   Provisioning server will not be available, but DNS and HTTPS will still work.")
        return
    sock.listen(10)

    print(f"[HTTP] Provisioning server on {_BASE}/provision")
    print(f"[HTTP]")
    print(f"[HTTP] === Steam Deck ===")
    print(f"[HTTP]   Setup (certs + Wine):  curl -o setup_deck.sh {_BASE}/provision/deck && bash setup_deck.sh")
    print(f"[HTTP]   Uninstall certs:       curl -o uninstall_cert_deck.sh {_BASE}/provision/deck/uninstall && bash uninstall_cert_deck.sh")
    print(f"[HTTP]   Install service:       curl -o install_service_deck.sh {_BASE}/provision/deck/service && sudo bash install_service_deck.sh")
    print(f"[HTTP]   Uninstall service:     curl -o uninstall_service_deck.sh {_BASE}/provision/deck/service/uninstall && sudo bash uninstall_service_deck.sh")
    print(f"[HTTP]")
    print(f"[HTTP] === Windows ===")
    print(f"[HTTP]   Setup (certs + DNS):   Invoke-WebRequest {_BASE}/provision/windows -OutFile setup.ps1; .\\setup.ps1")
    print(f"[HTTP]   Uninstall certs:       Invoke-WebRequest {_BASE}/provision/windows/uninstall -OutFile uninstall.ps1; .\\uninstall.ps1")

    while True:
        try:
            conn, addr = sock.accept()
            thread = threading.Thread(target=handle_provision, args=(conn, addr), daemon=True)
            thread.start()
        except Exception as exc:
            print(f"[HTTP] Accept error: {exc}")


def _extract_path(request: str) -> str:
    first_line = request.split("\r\n", 1)[0]
    parts = first_line.split(" ")
    return parts[1] if len(parts) > 1 else "/"
