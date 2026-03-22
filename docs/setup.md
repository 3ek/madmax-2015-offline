# Setup

## Supported configurations

| Configuration | Proxy runs on | Game runs on |
|---------------|--------------|-------------|
| **Steam Deck (standalone)** | Steam Deck itself | Steam Deck |
| **Windows (single PC)** | Same Windows PC as the game | Same Windows PC |
| **Windows + Steam Deck** | Windows PC on the LAN | Steam Deck |
| **Linux + Steam Deck** | Linux PC on the LAN | Steam Deck |

**Steam Deck standalone** — the proxy runs directly on the Deck alongside the game.
No second machine required. All setup steps run on the Deck itself.

**Windows single-PC** — the proxy and the game run on the same Windows machine.
Set `LAN_IP` to your local network IP, run the proxy as Administrator,
then run `setup_windows.ps1` on the same machine.
Steam achievements work normally in both cases.

---

## Requirements

- Python 3.10+
- OpenSSL (available in PATH)
- The machine running the proxy must have a LAN IP address (find it with `ip -4 addr` or `ipconfig`)

---

## 1. Edit config.py

Open `config.py` and at minimum set `LAN_IP` to the LAN IP of the machine running the proxy:

```python
LAN_IP = "192.168.1.10"   # your actual LAN IP — never use 127.0.0.1
WINE_PROTON_VER = "Proton 10.0"  # adjust if you use a different Proton version
```

The program will print a clear error and exit immediately if `LAN_IP` is not set.

See [configuration.md](configuration.md) for the full reference of all available settings.

---

## 2. Run the proxy (as sudo)

```bash
sudo python3 main.py
```

On first run the script generates a CA and server certificate automatically.

The following ports must be reachable from the game:

| Port | Protocol | Purpose |
|------|----------|---------|
| 53   | UDP      | DNS proxy |
| 443  | TCP      | HTTPS (game traffic) |
| 8888 | TCP      | Provisioning (setup scripts) |

### Command-line options

| Flag | Description |
|------|-------------|
| `-d`, `--debug` | Enable debug logging. Writes per-session logs to `hydra_logs/` and `last.console.log`. Without this flag no files are written. |

```bash
sudo python3 main.py           # normal run
sudo python3 main.py --debug   # debug run (full request/response logs)
```

---

## 3. Set up the client machine

Open a browser on the client and navigate to:

```
http://<proxy-ip>:8888/provision
```

You will see a page with all available setup and uninstall scripts. Alternatively, use the one-liners below.

---

## Steam Deck (standalone — proxy and game on the same Deck)

The proxy runs directly on the Deck. All commands run in a terminal on the Deck itself
(Desktop Mode, or via SSH).

### Step 1: certificates and Wine (run once)

```bash
curl -o setup_deck.sh http://<deck-lan-ip>:8888/provision/deck && bash setup_deck.sh
```

Installs the CA certificate to the system trust bundle and the Wine/Proton registry,
configures DNS via NetworkManager, and sets `winhttp=builtin` in Wine's DLL overrides.

### Step 2: install systemd service (run once)

Installs `madmax-offline.service` so the proxy can be started on demand or via Steam.
The service sets the proxy as DNS resolver on start and restores auto-DNS on stop.

```bash
curl -o install_service_deck.sh http://<deck-lan-ip>:8888/provision/deck/service && sudo bash install_service_deck.sh
```

### Step 3: configure Steam to start the service with the game

In Steam (Game Mode or Desktop Mode):
1. Right-click **Mad Max** → **Properties** → **General**
2. In the **Launch Options** field, enter:

```
systemctl start madmax-offline ; %command%
```

How this works:
- `systemctl start madmax-offline` starts the proxy service (DNS + HTTPS).
- `%command%` then launches the game normally through Steam.
- Mad Max has Denuvo DRM which takes 20–30 seconds to verify, so the service
  is fully up before any network requests are made.
- Steam achievements are unaffected.

To revert, clear the Launch Options field.

### Uninstall (Steam Deck)

```bash
# Remove CA certificate and restore DNS
curl -o uninstall_cert_deck.sh http://<deck-lan-ip>:8888/provision/deck/uninstall && bash uninstall_cert_deck.sh

# Remove systemd service and restore DNS
curl -o uninstall_service_deck.sh http://<deck-lan-ip>:8888/provision/deck/service/uninstall && sudo bash uninstall_service_deck.sh
```

---

## Windows — certificates and DNS

Works for both **single-PC** (proxy and game on the same machine) and **two-PC** setups.
Run as Administrator on the Windows machine running the game:

```powershell
# Setup — installs CA certificate and points DNS at the proxy
Invoke-WebRequest http://<proxy-ip>:8888/provision/windows -OutFile setup.ps1
.\setup.ps1

# Uninstall — removes CA certificate and restores DNS
Invoke-WebRequest http://<proxy-ip>:8888/provision/windows/uninstall -OutFile uninstall.ps1
.\uninstall.ps1
```

For a single-PC setup, `<proxy-ip>` is your own LAN IP (the same value as `LAN_IP` in `config.py`).
