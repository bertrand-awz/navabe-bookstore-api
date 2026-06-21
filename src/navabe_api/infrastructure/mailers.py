import logging
import smtplib
import ssl
from email.message import EmailMessage


class LoggingMailer:
    def send(self, recipient: str, subject: str, body: str) -> None:
        logging.getLogger(__name__).info(
            "Email disabled: recipient=%s subject=%s", recipient, subject
        )


class SmtpMailer:
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        sender: str,
        timeout: float = 10,
        security: str = "ssl",
    ):
        if security not in {"none", "ssl", "starttls"}:
            raise ValueError("SMTP security must be none, ssl or starttls")
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.sender = sender
        self.timeout = timeout
        self.security = security

    def send(self, recipient: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["From"] = self.sender
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)
        connection = smtplib.SMTP_SSL if self.security == "ssl" else smtplib.SMTP
        with connection(self.host, self.port, timeout=self.timeout) as server:
            if self.security == "starttls":
                server.starttls(context=ssl.create_default_context())
            if self.username:
                server.login(self.username, self.password)
            server.send_message(message)
