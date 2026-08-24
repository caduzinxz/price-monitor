"""Orquestra o fluxo completo: para cada produto cadastrado, obter o preco,
comparar com o historico, salvar no Supabase e enviar alerta por e-mail quando
necessario. Roda em loop, verificando a cada CHECK_INTERVAL_HOURS, ate ser
interrompido (Ctrl+C).
"""

import logging
import time

from app.config import settings
from app.config.products import Product, ProductConfigError, load_products
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


def check_product(product: Product, scraper: PriceScraper, storage: SupabaseStorage,
                  price_service: PriceService, email_service: EmailService) -> None:
    """Executa a verificacao de UM produto."""
    logger.info("[%s] Acessando produto...", product.name)
    current_price = scraper.fetch_price(product.url, product.price_selector)
    logger.info("[%s] Preco encontrado: %s", product.name, format_price_brl(current_price))

    previous_price = storage.get_last_price(product.name)
    result = price_service.evaluate(current_price, previous_price)

    if previous_price is None:
        logger.info("[%s] Nenhum historico anterior. Registrando preco inicial.", product.name)
    else:
        logger.info("[%s] Preco anterior: %s", product.name, format_price_brl(previous_price))
        logger.info("[%s] Variacao: %.2f%%", product.name, result.variation_percent)

    storage.append_record(
        product_name=product.name,
        url=product.url,
        price=current_price,
        variation_percent=result.variation_percent,
    )

    if result.should_alert and not settings.ALERTS_ENABLED:
        logger.info("[%s] Queda significativa, mas os alertas estao desativados.", product.name)
    elif result.should_alert:
        logger.info("[%s] Queda significativa. Enviando alerta por e-mail...", product.name)
        try:
            email_service.send_price_alert(
                product_name=product.name,
                previous_price=result.previous_price,
                current_price=result.current_price,
                variation_percent=result.variation_percent,
                url=product.url,
            )
        except EmailServiceError as exc:
            logger.error("[%s] Nao foi possivel enviar o alerta: %s", product.name, exc)
    else:
        logger.info("[%s] Nenhum alerta necessario.", product.name)


def run_check_cycle(products: list[Product], scraper: PriceScraper, storage: SupabaseStorage,
                    price_service: PriceService, email_service: EmailService) -> None:
    """Percorre todos os produtos uma vez.

    O try/except fica DENTRO do laco, por produto: assim, se um site estiver
    fora do ar, os demais produtos continuam sendo verificados normalmente.
    """
    for indice, product in enumerate(products):
        try:
            check_product(product, scraper, storage, price_service, email_service)
        except PriceScraperError as exc:
            logger.error("[%s] Falha ao obter o preco: %s", product.name, exc)

        e_o_ultimo = indice == len(products) - 1
        if not e_o_ultimo:
            time.sleep(settings.DELAY_BETWEEN_PRODUCTS_SECONDS)


def main() -> None:
    setup_logging()
    logger.info("Iniciando monitoramento de precos...")

    try:
        products = load_products(settings.PRODUCTS_FILE)
    except ProductConfigError as exc:
        # Sem produtos validos nao ha o que monitorar, entao encerramos com uma
        # mensagem clara em vez de deixar o erro estourar mais adiante.
        logger.error("Nao foi possivel carregar os produtos: %s", exc)
        return

    logger.info("%d produto(s) carregado(s) de %s", len(products), settings.PRODUCTS_FILE.name)

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
            run_check_cycle(products, scraper, storage, price_service, email_service)
            logger.info("Proxima verificacao em %.0f hora(s).", settings.CHECK_INTERVAL_HOURS)
            time.sleep(settings.CHECK_INTERVAL_HOURS * 3600)
    except KeyboardInterrupt:
        logger.info("Monitoramento interrompido pelo usuario. Encerrando...")


if __name__ == "__main__":
    main()
