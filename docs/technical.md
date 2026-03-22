# Technical notes

## Implementation status

| Component | Status | Notes |
|-----------|--------|-------|
| DNS interception | ✅ Working | |
| TLS handshake (Wine/Proton) | ✅ Working | |
| CA trust (Wine registry) | ✅ Working | |
| Auth (`auth/pc_steam`) | ✅ Working | |
| Profile create / get / update | ✅ Working | Persisted to `data/profiles.json` |
| Scrap Crew payout | ✅ Working | Via `profile/get` + `profile/update` with `timestamp_scrap_rewarded` |
| Turbine / WB (SOAP) | ✅ Working | Responds to WbAccountManagement, WbSubscriptionManagement, AmsAuthentication |
| TOS / PP feed | ⚠️ Stub | Returns an empty array; game behaviour with this response is unknown |
| MOTD / EVENT_ROCKSTAR feeds | ⚠️ Stub | Auto-creates `data/feeds/*.json` from request fields; content is unknown — all values are empty strings by default |
| `event_log/create_events` | ⚠️ ACK only | Returns `0x01`; events are not processed or stored |

## Hydra SDK

The game uses **Agora Hydra SDK** version `fr_hydra-2.5.0.1.0.0.945619` over WinHTTP with a custom binary content type: `application/x-hydra-binary`.

Known endpoints observed in traffic:

**Hydra API** (`blackjack.hydra.agoragames.com`) — the path prefix `{HYDRA_ID}` is a large numeric identifier
assigned by the Hydra SDK at runtime and varies between players and sessions. The emulator ignores it
and routes solely on the path suffix:

```
POST /{HYDRA_ID}/auth/pc_steam
POST /{HYDRA_ID}/profile/get_by_platform_account_id
POST /{HYDRA_ID}/profile/create
POST /{HYDRA_ID}/profile/get
POST /{HYDRA_ID}/profile/update
POST /{HYDRA_ID}/feed/get_items_by_channel          # body contains channel name
GET  /{HYDRA_ID}/feed/get_items_by_channel/TOS_{REGION}/1/1/0   # TOS for player region
GET  /{HYDRA_ID}/feed/get_items_by_channel/PP_{REGION}/1/1/0    # Privacy Policy for player region
POST /{HYDRA_ID}/event_log/create_events
```

`{HYDRA_ID}` examples from real sessions: `2473716611940202596`, `984815842354416438`, `4632926247215455251`.
`{REGION}` is the ISO 3166-1 alpha-2 country code derived from the player's Steam profile (e.g. `PL`, `DE`, `US`).

Feed channels requested via `feed/get_items_by_channel` body observed in traffic:

```
EVENT_ROCKSTAR
MOTD_GLOBAL
MOTD_RIPPER
MOTD_ROCKSTAR
MOTD_ROCKSTAR_HOODORNAMENT1
MOTD_ROCKSTAR_HOODORNAMENT2
```

**Turbine / WB** (`cls.psn.turbine.com` and `*.psn.turbine.com`) — SOAP over HTTPS:

```
POST /CLS/WbAccountManagement.asmx
POST /CLS/WbSubscriptionManagement.asmx
POST /CLS/AmsAuthentication.asmx
```

## Wire format

Endpoints use a custom binary content type: `application/x-hydra-binary`.

Request/response body structure:

```
prefix (1 byte) | BE-uint32 (hex_len) | ASCII hex string of inner payload
```

The inner payload is Hydra's key-value token format or a wrapped binary depending on the endpoint.

## Wine/Proton CA installation

Wine's built-in WinHTTP validates certificates against its own registry store under:

```
HKLM\Software\Microsoft\SystemCertificates\Root\Certificates\<SHA1>
```

The value must be a `CRYPT_DATA_BLOB` with the following structure:

```
PropID=3  (CERT_SHA1_HASH_PROP_ID)  flag=1  len=20   → SHA1 fingerprint
PropID=32 (CERT_CERT_PROP_ID)       flag=1  len=N    → full DER certificate
```

Using the native Proton `winhttp.dll` override bypasses this store entirely, which is why the `winhttp=builtin` DLL override is required.
