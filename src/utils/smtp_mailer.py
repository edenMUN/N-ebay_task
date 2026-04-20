from __future__ import annotations

import smtplib
from dataclasses import dataclass
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True)
class SmtpSettings:
    host: str
    port: int
    username: str
    password: str
    mail_from: str
    mail_to: Sequence[str]
    use_tls: bool = True


@dataclass(frozen=True)
class EmailSendResult:
    recipients: tuple[str, ...]
    subject: str
    chart_attached: str


class SmtpMailer:
    """SMTP transport (logging belongs in business logic, not here)."""

    def send_bpi_report(
        self,
        smtp: SmtpSettings,
        max_price_usd: float,
        max_at: datetime,
        chart_path: Path,
    ) -> EmailSendResult:
        if not chart_path.is_file():
            raise FileNotFoundError(f"Chart attachment missing: {chart_path}")

        subject = f"BPI report — max BTC-USD {max_price_usd:.2f}"
        body = (
            f"Max BTC-USD in the monitoring window: {max_price_usd:.2f}\n"
            f"Observed at (UTC): {max_at.isoformat()}\n"
            f"Chart attached: {chart_path.name}\n"
        )

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = smtp.mail_from
        message["To"] = ", ".join(smtp.mail_to)
        message.set_content(body)

        if chart_path.suffix.lower() == ".png":
            maintype, subtype = "image", "png"
        else:
            maintype, subtype = "application", "octet-stream"
        message.add_attachment(
            chart_path.read_bytes(),
            maintype=maintype,
            subtype=subtype,
            filename=chart_path.name,
        )

        with smtplib.SMTP(smtp.host, smtp.port, timeout=60) as server:
            if smtp.use_tls:
                server.starttls()
            if smtp.username or smtp.password:
                server.login(smtp.username, smtp.password)
            server.send_message(message)

        return EmailSendResult(
            recipients=tuple(smtp.mail_to),
            subject=subject,
            chart_attached=chart_path.name,
        )
