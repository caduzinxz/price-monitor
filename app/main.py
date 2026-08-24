"""Orquestra o fluxo completo: acessar o produto, obter o preco, comparar com
o historico, salvar no Supabase e enviar alerta por e-mail quando necessario.
Roda em loop, verificando a cada CHECK_INTERVAL_HOURS, ate ser interrompido
(Ctrl+C).
"""

import logging
import time

from app.config import settings
from app.scraper.price_scraper import PriceScraper, PriceScraperError
from app.services.email_service import EmailService, EmailServiceError
from app.services.price_service import PriceService
from app.storage.supabase_storage import SupabaseStorage
from app.utils.helpers import format_price_brl

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    # As bibliotecas do Supabase logam cada requisicao HTTP em INFO; isso
    # polui o log do monitor, entao elevamos o nivel so para elas.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("hpack").setLevel(logging.WARNING)


def run_check_cycle(scraper: PriceScraper, storage: SupabaseStorage,
                     price_service: PriceService, email_service: EmailService) -> None:
    logger.info("Acessando produto: %s", settings.PRODUCT_NAME)
    current_price = scraper.fetch_price(settings.PRODUCT_URL, settings.PRICE_SELECTOR)
    logger.info("Preco encontrado: %s", format_price_brl(current_price))

    previous_price = storage.get_last_price(settings.PRODUCT_NAME)
    result = price_service.evaluate(current_price, previous_price)

    if previous_price is None:
        logger.info("Nenhum historico anterior. Registrando preco inicial.")
    else:
        logger.info("Preco anterior: %s", format_price_brl(previous_price))
        logger.info("Variacao: %.2f%%", result.variation_percent)

    storage.append_record(
        product_name=settings.PRODUCT_NAME,
        url=settings.PRODUCT_URL,
        price=current_price,
        variation_percent=result.variation_percent,
    )

    if result.should_alert:
        logger.info("Queda significativa identificada. Enviando alerta por e-mail...")
        try:
            email_service.send_price_alert(
                product_name=settings.PRODUCT_NAME,
                previous_price=result.previous_price,
                current_price=result.current_price,
                variation_percent=result.variation_percent,
                url=settings.PRODUCT_URL,
            )
        except EmailServiceError as exc:
            logger.error("Nao foi possivel enviar o alerta: %s", exc)
    else:
        logger.info("Nenhum alerta necessario.")


def main() -> None:
    setup_logging()
    logger.info("Iniciando monitoramento de precos...")

    scraper = PriceScraper()
    storage = SupabaseStorage(settings.SUPABASE_URL, settings.SUPABASE_SECRET_KEY)
    price_service = PriceService(min_drop_percent=settings.MIN_PRICE_DROP_PERCENT)
    email_service = EmailService(
        host=settings.EMAIL_HOST,
        port=settings.EMAIL_PORT,
        user=settings.EMAIL_USER,
        password=settings.EMAIL_PASSWORD,
        to_address=settings.EMAIL_TO,
    )

    try:
        while True:
            try:
                run_check_cycle(scraper, storage, price_service, email_service)
            except PriceScraperError as exc:
                logger.error("Falha ao obter o preco: %s", exc)

            logger.info("Proxima verificacao em %.0f hora(s).", settings.CHECK_INTERVAL_HOURS)
            time.sleep(settings.CHECK_INTERVAL_HOURS * 3600)
    except KeyboardInterrupt:
        logger.info("Monitoramento interrompido pelo usuario. Encerrando...")


if __name__ == "__main__":
    main()
