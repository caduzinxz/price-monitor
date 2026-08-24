"""Envia um alerta ficticio por TODOS os canais configurados (e-mail, Telegram).

Uso:
    python -m scripts.send_test_alert

Serve para validar as credenciais sem esperar uma queda de preco real. Ignora
de proposito o ALERTS_ENABLED: se voce chamou este script explicitamente, esta
pedindo o envio.
"""

import logging

from app.config import settings
from app.main import build_notification_channels
from app.services.notification_service import NotificationService


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s", datefmt="%H:%M:%S")
    logger = logging.getLogger(__name__)

    channels = build_notification_channels()
    if not channels:
        logger.error(
            "Nenhum canal configurado. Preencha EMAIL_* e/ou TELEGRAM_* no .env."
        )
        return

    if not settings.ALERTS_ENABLED:
        logger.warning(
            "Atencao: ALERTS_ENABLED=false, entao o monitor automatico NAO enviara "
            "alertas. Este teste envia mesmo assim."
        )

    NotificationService(channels).send_price_alert(
        product_name="[TESTE] Produto ficticio",
        previous_price=1000.00,
        current_price=850.00,
        variation_percent=15.0,
        url="https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
        is_historic_low=True,
        historic_min_price=900.00,
    )

    logger.info("Teste concluido. Verifique os canais configurados.")


if __name__ == "__main__":
    main()
