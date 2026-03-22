# Mad Max (2015) - Server Emulator

A local server emulator for the online services of **Mad Max (2015)**, which were shut down by the publisher.

## Background

Mad Max is, at its core, a single-player game — yet it shipped with a dependency on Agora Games' Hydra SDK backend for certain mechanics, including some that are required to reach 100% completion. When the servers were taken offline, these mechanics stopped working entirely, making it impossible to fully complete the game.

What makes this particularly frustrating is that there is no technical reason for a single-player game to require an internet connection for features that could function perfectly well offline. On top of that, the game continues to be sold on digital storefronts without any disclosure that part of what it offers is no longer available. No patch was ever released to restore offline functionality when the servers went down.

This project was created in the spirit of game preservation — to restore the experience the game was meant to deliver. It currently targets **PC and Steam Deck**, but is open to contributions from anyone with the knowledge and interest to extend support to other platforms (including consoles).

---

## How it works

The emulator runs on a PC on your local network and does three things:

1. **DNS proxy** — intercepts DNS queries for the following domains and redirects them to the local machine.
   All other DNS queries are forwarded to `UPSTREAM_DNS` unchanged:
   - `blackjack.hydra.agoragames.com` — Hydra SDK backend (Agora Games)
   - `cls.psn.turbine.com` and `*.psn.turbine.com` — WB/Turbine account services
   - Any domains added to `PASSTHROUGH_DOMAIN` in `config.py` (empty by default)
2. **HTTPS server** — accepts TLS connections from the game and responds to Hydra SDK API requests.
3. **Provisioning server** (HTTP) — serves setup scripts and the CA certificate to client machines so they can be configured with a single command.

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/setup.md](docs/setup.md) | Supported configurations, requirements, and step-by-step setup for all platforms |
| [docs/configuration.md](docs/configuration.md) | All `config.py` settings explained, certificate paths |
| [docs/technical.md](docs/technical.md) | Implementation status, Hydra SDK protocol, observed endpoints, wire format, Wine/Proton CA notes |
| [docs/contributing.md](docs/contributing.md) | Contributing guidelines and license |

---

## Quick start

**Windows (single PC — proxy and game on the same machine):**

```powershell
# 1. Set LAN_IP in config.py to your local network IP, then:
python main.py          # run as Administrator

# 2. On the same machine, install the CA certificate and point DNS at the proxy:
Invoke-WebRequest http://<your-lan-ip>:8080/provision/windows -OutFile setup.ps1
.\setup.ps1             # run as Administrator
```

**Steam Deck:**

```bash
# 1. Set LAN_IP in config.py on the proxy machine, then run the proxy (sudo)
# 2. On the Deck:
curl -o setup_deck.sh http://<proxy-ip>:8080/provision/deck && bash setup_deck.sh
curl -o install_service_deck.sh http://<proxy-ip>:8080/provision/deck/service && sudo bash install_service_deck.sh
```

See [docs/setup.md](docs/setup.md) for the full walkthrough.

---

## License

GPL-3.0-or-later — see [LICENSE](LICENSE).
