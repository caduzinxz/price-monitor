"""Envia o alerta de preco por Telegram, usando a API HTTP de bots.

Usa urllib (biblioteca padrao) em vez de requests/httpx para nao adicionar
dependencia ao projeto so por causa de uma unica chamada HTTP.
"""

import json
import logging
import urllib.error
import urllib.request

from app.services.notification_service import NotificationError
from app.utils.helpers import format_price_brl

logger = logging.getLogger(__name__)

API_BASE = "https://api.telegram.org"


class TelegramServiceError(NotificationError):
    """Erro ao enviar mensagem pelo Telegram."""


class TelegramService:
    def __init__(self, bot_token: str, chat_id: str, timeout: int = 30):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.timeout = timeout

    def send_price_alert(
        self,
        product_name: str,
        previous_price: float,
        current_price: float,
        variation_percent: float,
        url: str,
        is_historic_low: bool = False,
        historic_min_price: float | None = None,
    ) -> None:
        if is_historic_low:
            title = f"🔥 MENOR PREÇO HISTÓRICO: {product_name}"
        else:
            title = f"📉 Queda de preço: {product_name}"

        lines = [
            title,
            "",
            f"Preço anterior: {format_price_brl(previous_price)}",
            f"Preço atual: {format_price_brl(current_price)}",
            f"Queda: {variation_percent:.2f}%",
        ]

        if is_historic_low and historic_min_price is not None:
            lines.append(f"Recorde anterior: {format_price_brl(historic_min_price)}")

        lines.append("")
        lines.append(url)

        self._send_message("\n".join(lines))
        logger.info("Alerta enviado por Telegram.")

    def _send_message(self, text: str) -> None:
        # O token faz parte da URL, entao a URL NUNCA deve aparecer em log ou
        # mensagem de erro -- quem tiver o token controla o bot por completo.
        endpoint = f"{API_BASE}/bot{self.bot_token}/sendMessage"
        payload = json.dumps({"chat_id": self.chat_id, "text": text}).encode("utf-8")

        request = urllib.request.Request(
            endpoint,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = self._extract_error_description(exc)
            raise TelegramServiceError(f"HTTP {exc.code} da API do Telegram: {detail}") from exc
        except urllib.error.URLError as exc:
            raise TelegramServiceError(f"Nao foi possivel alcancar a API: {exc.reason}") from exc
        except json.JSONDecodeError as exc:
            raise TelegramServiceError("Resposta da API do Telegram nao era JSON.") from exc

        if not data.get("ok"):
            raise TelegramServiceError(f"API recusou o envio: {data.get('description')}")

    @staticmethod
    def _extract_error_description(exc: urllib.error.HTTPError) -> str:
        """Le o corpo do erro para dar uma mensagem util.

        A API do Telegram explica a causa no corpo da resposta (ex.: "chat not
        found"), o que ajuda muito mais que apenas o codigo HTTP.
        """
        try:
            body = json.loads(exc.read().decode("utf-8", errors="replace"))
            return body.get("description", "sem detalhes")
        except (json.JSONDecodeError, OSError):
            return "sem detalhes"
