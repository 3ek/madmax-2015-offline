# Configuration

All settings live in **`config.py`**. You must edit this file before running the proxy for the first time.

## Required

| Setting | Description |
|---------|-------------|
| `LAN_IP` | **Must be set.** The local network IP address of the machine running the proxy. The program will refuse to start if this is left as `"0.0.0.0"`. |

```python
LAN_IP = "192.168.1.10"  # replace with your actual LAN IP
```

To find your IP:
- **Windows:** run `ipconfig` and look for IPv4 Address under your active adapter
- **Linux / Steam Deck:** run `ip -4 addr | grep inet`

## Optional — Network

| Setting | Default | Description |
|---------|---------|-------------|
| `UPSTREAM_DNS` | `"1.1.1.1"` | Fallback DNS server used for all non-intercepted queries and as the secondary DNS when the service sets up DNS on the client. |
| `DNS_PORT` | `53` | UDP port the DNS proxy listens on. Requires root/Administrator. |
| `HTTPS_PORT` | `443` | TCP port the HTTPS emulator listens on. Requires root/Administrator. |
| `HTTP_PORT` | `8080` | TCP port the provisioning server listens on. |
| `PASSTHROUGH_DOMAIN` | `[]` | List of additional domains to proxy through to the real internet rather than intercept. Useful for debugging. |

## Optional — Wine / Proton (Steam Deck)

| Setting | Default | Description |
|---------|---------|-------------|
| `WINE_PROTON_VER` | `"Proton 10.0"` | Version string that appears in the Proton installation path (e.g. `~/.local/share/Steam/steamapps/common/Proton 10.0`). Used by provisioning scripts to locate `wine`/`wineboot`/`wineserver`. Update this if you use a different Proton version. |
| `GAME_APP_ID` | `"234140"` | Steam App ID for Mad Max (2015). Used by provisioning scripts to locate the Wine prefix at `steamapps/compatdata/<ID>/pfx`. Do not change unless Valve reassigns the ID. |

## Certificates

The CA and server certificates are generated automatically on first run and stored at:

```
~/.local/share/local_proxy/               (Linux / Steam Deck)
%USERPROFILE%\.local\share\local_proxy\  (Windows)
```

| File | Description |
|------|-------------|
| `ca.key` | CA private key |
| `ca.crt` | CA certificate — this is what gets installed on client machines |
| `server.key` | Server private key |
| `server.crt` | Server certificate (signed by the CA) |
| `server-fullchain.crt` | Server certificate + CA chain (used by the HTTPS server) |

To force regeneration, delete the directory and restart the proxy. The `CERT_DIR` path can be changed in `config.py` if needed.
