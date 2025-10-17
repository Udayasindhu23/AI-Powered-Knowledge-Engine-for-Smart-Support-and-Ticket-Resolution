"""
Notification utilities for ticket lifecycle events.

Provides SMTP email notifications and a placeholder Slack configuration.
Uses environment variables as sensible defaults, while allowing runtime
configuration via the Notifier.update(...) method.
"""

from __future__ import annotations

import os
import smtplib
import ssl
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, Dict, Any


@dataclass
class SlackConfig:
    webhook_url: str | None = None


@dataclass
class EmailConfig:
    smtp_host: str
    smtp_port: int = 587
    username: Optional[str] = None
    password: Optional[str] = None
    use_tls: bool = True
    use_ssl: bool = False
    verify: bool = True
    ca_file: Optional[str] = None
    # Delivery method: 'smtp' | 'outlook' | 'eml' | 'mailto'
    delivery_method: str = "smtp"
    # For EML saving
    eml_out_dir: Optional[str] = None
    sender: str = ""
    recipient: str = ""


class Notifier:
    """Sends notifications for ticket lifecycle events."""

    def __init__(
        self,
        enabled: bool = False,
        slack: Optional[SlackConfig] = None,
        email: Optional[EmailConfig] = None,
    ) -> None:
        self.enabled = enabled or _env_bool("EMAIL_ENABLED", default=False)
        self.slack: Optional[SlackConfig] = slack
        self.email: Optional[EmailConfig] = email or _email_config_from_env()
        self.last_error: Optional[str] = None
        self.last_info: Optional[str] = None

    def update(
        self,
        enabled: Optional[bool] = None,
        slack: Optional[SlackConfig] = None,
        email: Optional[EmailConfig] = None,
    ) -> None:
        if enabled is not None:
            self.enabled = bool(enabled)
        if slack is not None:
            self.slack = slack
        if email is not None:
            self.email = email

    # ----- Public API -----

    def send_ticket_created(self, ticket: Dict[str, Any]) -> bool:
        if not self.enabled:
            return False
        return self._send_email(
            subject=f"[New Ticket] {ticket.get('ticket_id', '')} - {ticket.get('issue_summary', '')}",
            html_body=_render_ticket_email(ticket, event="created"),
        )

    def send_ticket_updated(self, ticket: Dict[str, Any]) -> bool:
        if not self.enabled:
            return False
        return self._send_email(
            subject=f"[Ticket Updated] {ticket.get('ticket_id', '')} - {ticket.get('issue_summary', '')}",
            html_body=_render_ticket_email(ticket, event="updated"),
        )

    def send_category_threshold_alert(self, category: str, count: int) -> bool:
        """Send an alert when a category crosses a volume threshold."""
        if not self.enabled:
            return False
        html = f"""
        <div style=\"font-family: Arial, sans-serif;\">
          <h2>High Volume Alert</h2>
          <p>The category <strong>{category}</strong> has exceeded the threshold with <strong>{count}</strong> tickets.</p>
          <p>Please review recent tickets in this category for potential incidents or spikes.</p>
        </div>
        """
        return self._send_email(subject=f"[Alert] {category} volume: {count}+ tickets", html_body=html)

    # ----- Internals -----

    def send_test_email(self) -> bool:
        """Send a simple test email using current configuration."""
        if not self.enabled:
            return False
        html = """
        <div style=\"font-family: Arial, sans-serif;\">
          <h3>Email notification test</h3>
          <p>This is a test email from AI Customer Support System.</p>
        </div>
        """
        return self._send_email(subject="[Test] Email notifications configured", html_body=html)

    def _send_email(self, subject: str, html_body: str) -> bool:
        cfg = self.email
        if not cfg:
            return False
        if not cfg.sender or not cfg.recipient:
            return False

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = cfg.sender
        message["To"] = cfg.recipient
        message.attach(MIMEText(html_body, "html", _charset="utf-8"))

        try:
            method = (cfg.delivery_method or "smtp").lower()
            if method == "smtp":
                return self._send_via_smtp(cfg, message)
            if method == "outlook":
                return self._send_via_outlook(subject, html_body, cfg)
            if method == "eml":
                return self._save_as_eml(message, cfg)
            if method == "mailto":
                return self._open_mailto_link(subject, html_body, cfg)
            self.last_error = f"Unknown delivery method: {cfg.delivery_method}"
            return False
        except Exception as e:
            self.last_error = str(e)
            return False

    def _send_via_smtp(self, cfg: EmailConfig, message: MIMEMultipart) -> bool:
        if not cfg.smtp_host:
            self.last_error = "SMTP host not set"
            return False
        try:
            context = None
            if cfg.verify:
                context = ssl.create_default_context(cafile=cfg.ca_file) if cfg.ca_file else ssl.create_default_context()
            else:
                context = ssl._create_unverified_context()

            if cfg.use_ssl:
                with smtplib.SMTP_SSL(cfg.smtp_host, cfg.smtp_port, context=context, timeout=15) as server:
                    server.ehlo()
                    if cfg.username and cfg.password:
                        server.login(cfg.username, cfg.password)
                    server.sendmail(cfg.sender, [cfg.recipient], message.as_string())
            else:
                with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=15) as server:
                    server.ehlo()
                    if cfg.use_tls:
                        server.starttls(context=context)
                        server.ehlo()
                    if cfg.username and cfg.password:
                        server.login(cfg.username, cfg.password)
                    server.sendmail(cfg.sender, [cfg.recipient], message.as_string())
            self.last_error = None
            self.last_info = "Email sent via SMTP"
            return True
        except Exception as e:
            self.last_error = str(e)
            return False

    def _send_via_outlook(self, subject: str, html_body: str, cfg: EmailConfig) -> bool:
        try:
            import win32com.client  # type: ignore
        except Exception as e:
            self.last_error = f"Outlook automation unavailable: {str(e)}"
            return False
        try:
            outlook = win32com.client.Dispatch("Outlook.Application")
            mail = outlook.CreateItem(0)
            mail.To = cfg.recipient
            mail.Subject = subject
            mail.HTMLBody = html_body
            # If From is supported/configured, could set SentOnBehalfOfName
            # Send immediately
            mail.Send()
            self.last_error = None
            self.last_info = "Email sent via Outlook"
            return True
        except Exception as e:
            self.last_error = str(e)
            return False

    def _save_as_eml(self, message: MIMEMultipart, cfg: EmailConfig) -> bool:
        try:
            out_dir = cfg.eml_out_dir or os.path.join(os.getcwd(), "outbox")
            os.makedirs(out_dir, exist_ok=True)
            filename = f"email_{_safe_timestamp()}.eml"
            path = os.path.join(out_dir, filename)
            with open(path, "w", encoding="utf-8") as f:
                f.write(message.as_string())
            self.last_error = None
            self.last_info = f"Saved EML: {path}"
            return True
        except Exception as e:
            self.last_error = str(e)
            return False

    def _open_mailto_link(self, subject: str, html_body: str, cfg: EmailConfig) -> bool:
        try:
            import webbrowser
            import urllib.parse
            # Convert HTML to plain-ish text for mailto body
            body = _html_to_text(html_body)
            params = {
                "subject": subject,
                "body": body,
            }
            query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
            url = f"mailto:{cfg.recipient}?{query}"
            opened = webbrowser.open(url)
            if not opened:
                self.last_error = "Could not open default mail client"
                return False
            self.last_error = None
            self.last_info = "Opened default mail client via mailto"
            return True
        except Exception as e:
            self.last_error = str(e)
            return False


def _render_ticket_email(ticket: Dict[str, Any], event: str) -> str:
    issue_summary = ticket.get("issue_summary", "")
    detailed_issue = ticket.get("detailed_issue", "")
    ticket_id = ticket.get("ticket_id", "")
    status = ticket.get("status", "")
    priority = ticket.get("priority", "")
    category = ticket.get("category", "")
    customer_name = ticket.get("customer_name", "")
    customer_email = ticket.get("customer_email", "")
    created_date = ticket.get("created_date", "")
    created_time = ticket.get("created_time", "")
    solutions = ticket.get("ai_response", [])
    solutions_html = "".join(f"<li>{s}</li>" for s in solutions) if isinstance(solutions, list) else f"<li>{solutions}</li>"

    return f"""
    <div style=\"font-family: Arial, sans-serif;\">
      <h2>Ticket {event.title()}</h2>
      <p><strong>ID:</strong> {ticket_id}</p>
      <p><strong>Summary:</strong> {issue_summary}</p>
      <p><strong>Status:</strong> {status} | <strong>Priority:</strong> {priority} | <strong>Category:</strong> {category}</p>
      <p><strong>Customer:</strong> {customer_name} &lt;{customer_email}&gt;</p>
      <p><strong>Created:</strong> {created_date} {created_time}</p>
      <p><strong>Description:</strong><br/>{detailed_issue}</p>
      <p><strong>AI Suggested Solutions:</strong></p>
      <ul>{solutions_html}</ul>
    </div>
    """


def _email_config_from_env() -> Optional[EmailConfig]:
    smtp_host = os.getenv("SMTP_HOST", "")
    sender = os.getenv("EMAIL_SENDER", "")
    recipient = os.getenv("EMAIL_RECIPIENT", "")
    if not sender or not recipient:
        return None
    return EmailConfig(
        smtp_host=smtp_host,
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        username=os.getenv("SMTP_USERNAME") or None,
        password=os.getenv("SMTP_PASSWORD") or None,
        use_tls=_env_bool("SMTP_USE_TLS", default=True),
        use_ssl=_env_bool("SMTP_USE_SSL", default=False),
        verify=_env_bool("SMTP_VERIFY", default=True),
        ca_file=os.getenv("SMTP_CA_FILE") or None,
        delivery_method=os.getenv("EMAIL_DELIVERY", "smtp"),
        eml_out_dir=os.getenv("EMAIL_EML_OUT"),
        sender=sender,
        recipient=recipient,
    )


def _env_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return str(val).strip().lower() in {"1", "true", "yes", "on"}


def _safe_timestamp() -> str:
    from datetime import datetime as _dt
    return _dt.now().strftime("%Y%m%d_%H%M%S_%f")


def _html_to_text(html: str) -> str:
    try:
        import re as _re
        text = _re.sub(r"<br\s*/?>", "\n", html, flags=_re.I)
        text = _re.sub(r"<[^>]+>", "", text)
        return text
    except Exception:
        return html


