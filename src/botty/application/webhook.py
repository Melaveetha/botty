from dataclasses import dataclass
from pathlib import Path


@dataclass
class WebhookConfig:
    """Configuration for running the bot in webhook mode.

    Telegram will send updates to the public `url`. The bot will listen on
    `listen`:`port` and expects updates at `path`. For self‑signed certificates,
    provide the `cert` and `key` file paths.

    Attributes:
        url: Public HTTPS URL where Telegram will send updates.
             Example: "https://example.com/webhook"
        port: Local port to bind. Telegram officially supports 443, 80, 88, 8443.
              Default 8443.
        listen: IP address to bind (default "0.0.0.0").
        path: URL path that will receive updates (default "/"). The leading slash
              will be stripped internally.
        secret_token: Optional secret token to verify incoming requests (recommended).
        cert: Path to SSL certificate file (required for self‑signed certificates).
        key: Path to private key file (required if cert is provided).

    Example:
        config = WebhookConfig(
            url="https://mybot.example.com/webhook",
            port=8443,
            secret_token="supersecret"
        )
        app = AppBuilder().token("TOKEN").webhook(config).build()
    """

    url: str
    port: int = 8443
    listen: str = "0.0.0.0"
    path: str = "/"
    secret_token: str | None = None
    cert: Path | None = None
    key: Path | None = None
