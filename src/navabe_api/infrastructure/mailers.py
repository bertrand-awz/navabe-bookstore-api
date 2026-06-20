from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage


class LoggingMailer:
    def send(self, recipient: str, subject: str, body: str) -> None:
        logging.getLogger(__name__).info("Email disabled: recipient=%s subject=%s", recipient, subject)


class SmtpMailer:
    def __init__(self, host: str, port: int, username: str, password: str, sender: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.sender = sender

    def send(self, recipient: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["From"] = self.sender
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)
        with smtplib.SMTP_SSL(self.host, self.port) as server:
            server.login(self.username, self.password)
            server.send_message(message)

