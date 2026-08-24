"""Responsavel por montar e enviar o e-mail de alerta via SMTP.

As credenciais nunca ficam hardcoded aqui -- sao recebidas no construtor,
vindas de app/config/settings.py (que por sua vez le do .env).
"""

import logging
import smtplib
from datetime import datetime
from email.message import EmailMessage

from app.utils.helpers import format_price_brl

logger = logging.getLogger(__name__)


class EmailServiceError(Exception):
    """Erro ao tentar enviar o e-mail de alerta."""


class EmailService:
    def __init__(self, host: str, port: int, user: str, password: str, to_address: str):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.to_address = to_address

    def send_price_alert(
        self,
        product_name: str,
        previous_price: float,
        current_price: float,
        variation_percent: float,
        url: str,
    ) -> None:
        subject = f"[Alerta de Preco] {product_name} caiu {variation_percent:.2f}%"
        body = (
            f"Produto: {product_name}\n"
            f"Preco anterior: {format_price_brl(previous_price)}\n"
            f"Preco atual: {format_price_brl(current_price)}\n"
            f"Queda: {variation_percent:.2f}%\n"
            f"URL: {url}\n"
            f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
        )

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self.user
        message["To"] = self.to_address
        message.set_content(body)

        try:
            with smtplib.SMTP(self.host, self.port, timeout=30) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.send_message(message)
            logger.info("E-mail de alerta enviado para %s", self.to_address)
        except smtplib.SMTPException as exc:
            raise EmailServiceError(f"Falha ao enviar e-mail: {exc}") from exc
        except OSError as exc:
            raise EmailServiceError(f"Nao foi possivel conectar ao servidor SMTP: {exc}") from exc
