from dataclasses import dataclass
from pathlib import Path


@dataclass
class WebhookConfig:
    url: str  # public HTTPS URL where Telegram sends updates
    port: int = 8443  # local port to bind (default Telegram expects 443, 80, 88, 8443)
    listen: str = "0.0.0.0"  # IP to listen on
    path: str = "/"  # URL path (e.g., "/webhook")
    secret_token: str | None = None  # optional secret to verify requests
    cert: Path | None = None  # path to SSL certificate (for self‑signed)
    key: Path | None = None  # path to private key
