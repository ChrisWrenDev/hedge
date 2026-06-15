from typing import Any


class EmailChannel:
    def __init__(self, config: dict[str, Any]):
        self.config = config

    async def send(self, subject: str, body: str) -> bool:
        try:
            import aiosmtplib
            from email.mime.text import MIMEText

            msg = MIMEText(body)
            msg["From"] = self.config["from_addr"]
            msg["To"] = ", ".join(self.config["to_addrs"])
            msg["Subject"] = subject

            await aiosmtplib.send(
                msg,
                hostname=self.config["smtp_host"],
                port=self.config["smtp_port"],
                username=self.config.get("username"),
                password=self.config.get("password"),
                start_tls=True,
            )
            return True
        except Exception:
            return False


class WebhookChannel:
    def __init__(self, config: dict[str, Any]):
        self.config = config

    async def send(self, subject: str, body: str) -> bool:
        try:
            import httpx
            payload = {"subject": subject, "body": body}
            async with httpx.AsyncClient() as client:
                resp = await client.request(
                    method=self.config.get("method", "POST"),
                    url=self.config["url"],
                    json=payload,
                    headers=self.config.get("headers", {}),
                    timeout=10.0,
                )
                return resp.status_code < 400
        except Exception:
            return False
