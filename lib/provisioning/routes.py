"""Routing for provisioning downloads and landing page."""

from .templates import (
    ca_cert_bytes,
    render_index_page,
    render_install_service_deck,
    render_setup_deck,
    render_setup_windows,
    render_uninstall_cert_deck,
    render_uninstall_cert_windows,
    render_uninstall_service_deck,
)

Response = tuple[str, bytes | str, str, str | None]


def route_provision_path(path: str) -> Response:
    if path == "/ca.crt":
        return (
            "200 OK",
            ca_cert_bytes(),
            "application/x-pem-file",
            "attachment; filename=localproxy_ca.crt",
        )
    # Steam Deck — setup
    if path == "/provision/deck":
        return (
            "200 OK",
            render_setup_deck(),
            "text/plain; charset=utf-8",
            "attachment; filename=setup_deck.sh",
        )
    if path == "/provision/deck/uninstall":
        return (
            "200 OK",
            render_uninstall_cert_deck(),
            "text/plain; charset=utf-8",
            "attachment; filename=uninstall_cert_deck.sh",
        )
    # Steam Deck — service
    if path == "/provision/deck/service":
        try:
            script = render_install_service_deck()
        except RuntimeError as exc:
            return (
                "503 Service Unavailable",
                f"ERROR: {exc}\n",
                "text/plain; charset=utf-8",
                None,
            )
        return (
            "200 OK",
            script,
            "text/plain; charset=utf-8",
            "attachment; filename=install_service_deck.sh",
        )
    if path == "/provision/deck/service/uninstall":
        return (
            "200 OK",
            render_uninstall_service_deck(),
            "text/plain; charset=utf-8",
            "attachment; filename=uninstall_service_deck.sh",
        )
    # Windows
    if path == "/provision/windows":
        return (
            "200 OK",
            render_setup_windows(),
            "text/plain; charset=utf-8",
            "attachment; filename=setup_windows.ps1",
        )
    if path == "/provision/windows/uninstall":
        return (
            "200 OK",
            render_uninstall_cert_windows(),
            "text/plain; charset=utf-8",
            "attachment; filename=uninstall_cert_windows.ps1",
        )
    # Landing page
    if path == "/provision":
        return ("200 OK", render_index_page(), "text/html; charset=utf-8", None)
    return ("404 Not Found", b"Not Found", "text/plain; charset=utf-8", None)
