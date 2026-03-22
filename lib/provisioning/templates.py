"""Load and render provisioning templates from on-disk resources."""

import sys
from pathlib import Path

from config import CA_CERT, GAME_APP_ID, HTTP_PORT, LAN_IP, UPSTREAM_DNS, WINE_PROTON_VER

RESOURCE_DIR = Path(__file__).resolve().parent / "resources"

# Project root is two levels up from this file (lib/provisioning/templates.py -> project root).
_PROJECT_DIR = str(Path(__file__).resolve().parents[2])

# On Windows, _PROJECT_DIR will be a Windows path (e.g. C:\Users\...) which is meaningless
# inside a bash script that runs on Steam Deck.  Detect this and refuse to render the script.
_PROJECT_DIR_IS_WINDOWS = (
    sys.platform == "win32"
    or (len(_PROJECT_DIR) >= 2 and _PROJECT_DIR[1] == ":")
    or "\\" in _PROJECT_DIR
)


def ca_cert_bytes() -> bytes:
    return CA_CERT.read_bytes()


def render_setup_deck() -> str:
    return _render_resource(
        "setup_deck.sh.tpl",
        {
            "__CA_PEM__": CA_CERT.read_text(),
            "__GAME_APP_ID__": str(GAME_APP_ID),
            "__HTTP_PORT__": str(HTTP_PORT),
            "__LAN_IP__": LAN_IP,
            "__WINE_PROTON_VER__": WINE_PROTON_VER,
        },
    )


def render_uninstall_cert_deck() -> str:
    return _render_resource(
        "uninstall_cert_deck.sh.tpl",
        {
            "__GAME_APP_ID__": str(GAME_APP_ID),
            "__HTTP_PORT__": str(HTTP_PORT),
            "__LAN_IP__": LAN_IP,
            "__WINE_PROTON_VER__": WINE_PROTON_VER,
        },
    )


def render_install_service_deck() -> str:
    if _PROJECT_DIR_IS_WINDOWS:
        raise RuntimeError(
            "The Steam Deck service installer cannot be generated from a Windows host.\n"
            "Run the provisioning server on the Steam Deck itself (or a Linux machine),\n"
            "then download and run the script from there."
        )
    return _render_resource(
        "install_service_deck.sh.tpl",
        {
            "__LAN_IP__": LAN_IP,
            "__HTTP_PORT__": str(HTTP_PORT),
            "__PROJECT_DIR__": _PROJECT_DIR,
            "__UPSTREAM_DNS__": UPSTREAM_DNS,
        },
    )


def render_uninstall_service_deck() -> str:
    return _render_resource(
        "uninstall_service_deck.sh.tpl",
        {
            "__LAN_IP__": LAN_IP,
            "__HTTP_PORT__": str(HTTP_PORT),
        },
    )


def render_setup_windows() -> str:
    return _render_resource(
        "setup_windows.ps1.tpl",
        {
            "__CA_PEM__": CA_CERT.read_text(),
            "__LAN_IP__": LAN_IP,
        },
    )


def render_uninstall_cert_windows() -> str:
    return _render_resource(
        "uninstall_cert_windows.ps1.tpl",
        {
            "__HTTP_PORT__": str(HTTP_PORT),
            "__LAN_IP__": LAN_IP,
        },
    )


def render_index_page() -> str:
    return _render_resource(
        "provision.html.tpl",
        {
            "__HTTP_PORT__": str(HTTP_PORT),
            "__LAN_IP__": LAN_IP,
        },
    )


def _render_resource(name: str, replacements: dict[str, str]) -> str:
    text = (RESOURCE_DIR / name).read_text(encoding="utf-8")
    for key, value in replacements.items():
        text = text.replace(key, value)
    return text
