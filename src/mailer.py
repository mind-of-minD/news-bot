import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List


def get_recipients() -> List[str]:
    raw_recipients = os.getenv("EMAIL_TO", "")

    recipients = [
        email.strip()
        for email in raw_recipients.split(",")
        if email.strip()
    ]

    if not recipients:
        raise ValueError("EMAIL_TO 환경변수가 비어 있습니다.")

    return recipients


def send_email(subject: str, html_body: str, recipients: List[str]) -> None:
    smtp_host = os.environ["SMTP_HOST"]
    smtp_port_raw = os.getenv("SMTP_PORT", "587")
    smtp_user = os.environ["SMTP_USER"]
    smtp_password = os.environ["SMTP_PASSWORD"]

    if not smtp_port_raw.isdigit():
        raise ValueError(f"SMTP_PORT 값이 숫자가 아닙니다: {smtp_port_raw}")

    smtp_port = int(smtp_port_raw)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = ", ".join(recipients)

    msg.attach(MIMEText(html_body, "html", "utf-8"))

    if smtp_port == 465:
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, recipients, msg.as_string())
    else:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, recipients, msg.as_string())