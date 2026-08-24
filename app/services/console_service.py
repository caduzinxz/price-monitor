"""Mostra o alerta no proprio terminal.

Serve como canal de reserva: se nem e-mail nem Telegram estiverem configurados,
o alerta ainda precisa aparecer em algum lugar. Sem isso, quem roda o projeto
pela primeira vez veria "Enviando alertas..." e nada acontecendo.
"""

import logging

from app.utils.helpers import format_price_brl

logger = logging.getLogger(__name__)

LINE_WIDTH = 64


class ConsoleNotifier:
    """Canal de notificacao que escreve no log em vez de enviar mensagem."""

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
        title = "MENOR PRECO HISTORICO" if is_historic_low else "QUEDA DE PRECO"

        logger.info("=" * LINE_WIDTH)
        logger.info("  %s: %s", title, product_name)
        logger.info("-" * LINE_WIDTH)
        logger.info("  Preco anterior : %s", format_price_brl(previous_price))
        logger.info("  Preco atual    : %s", format_price_brl(current_price))
        logger.info("  Queda          : %.2f%%", variation_percent)

        if is_historic_low and historic_min_price is not None:
            logger.info("  Recorde anterior: %s", format_price_brl(historic_min_price))

        logger.info("  URL            : %s", url)
        logger.info("=" * LINE_WIDTH)
