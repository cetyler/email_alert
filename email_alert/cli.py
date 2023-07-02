from .__init__ import __version__
import click
from datetime import datetime, date
from pathlib import Path
from trogon import tui
import tomllib
from email.message import EmailMessage
from email.headerregistry import Address
from email.utils import make_msgid
import ssl
import smtplib
from dataclasses import dataclass
from typing import List
import subprocess

# For now will put all the code here for now


@dataclass
class EmailReport:
    sender: str
    to: List[str]
    subject: str
    body: str
    host: str
    port: int
    starttls: bool
    authentication: bool
    username: str
    password: str

    def send_message(self):
        msg = EmailMessage()
        msg["From"] = self.sender
        msg["To"] = tuple(self.to)
        msg["Subject"] = self.subject
        msg.set_content(self.body)

        context = ssl.create_default_context()

        with smtplib.SMTP(
            host=self.host,
            port=self.port,
        ) as s:
            if self.starttls:
                s.ehlo()
                try:
                    s.starttls(context=context)
                except Exception as err:
                    print(err)
            if self.authentication:
                try:
                    s.login(
                        user=self.username,
                        password=self.password,
                    )
                except Exception as err:
                    print(err)
            s.send_message(msg)


@dataclass
class PcCheck:
    ip_address: str

    def check(self):
        pc = subprocess.run(
            [f"ping -c 1 {self.ip_address}"],
            shell=True,
            capture_output=True,
            text=True,
        )

        self.code = pc.returncode
        self.message = pc.stdout


@tui()
@click.command(context_settings={"ignore_unknown_options": True})
@click.argument(
    "operation",
    type=str,
    default="ping",
)
@click.option(
    "--config",
    type=str,
    default="email_alert_config.toml",
    # help="Config file location.",
)
@click.option(
    "--address",
    type=str,
    default="192.168.0.108",
    # help="IP address for ping PC operation.",
)
def main(operation: str, config: str, address: str) -> int:

    with open(config, "rb") as f:
        user_config = tomllib.load(f)
        email_settings = user_config["email"]

    today = datetime.now()
    if operation == "ping":
        op = PcCheck(ip_address=address)
        op.check()

    if op.code != 0:
        report = EmailReport(
            sender=email_settings["from"],
            to=email_settings["to"],
            subject=f"{operation} Report for {today}",
            body=repr(op),
            host=email_settings["server"],
            port=email_settings["port"],
            starttls=email_settings["starttls"],
            authentication=email_settings["authentication"],
            username=email_settings["username"],
            password=email_settings["password"],
        )
        report.send_message()

    return 0
