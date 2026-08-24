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
from app.services.console_service import ConsoleNotifier
from app.services.email_service import EmailService
from app.services.notification_service import NotificationService
from app.services.price_service import PriceService
from app.services.telegram_service import TelegramService
from app.storage.errors import StorageError
from app.storage.sqlite_storage import SQLiteStorage
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


def build_storage():
    """Escolhe o backend de armazenamento conforme STORAGE_BACKEND.

    O padrao e SQLite justamente para que o projeto rode sem nenhuma conta ou
    servico externo; o Supabase e opcional.
    """
    if settings.STORAGE_BACKEND == "supabase":
        logger.info("Armazenamento: Supabase")
        return SupabaseStorage(settings.SUPABASE_URL, settings.SUPABASE_SECRET_KEY)

    if settings.STORAGE_BACKEND != "sqlite":
        raise StorageError(
            f"STORAGE_BACKEND invalido: {settings.STORAGE_BACKEND!r}. "
            "Use 'sqlite' ou 'supabase'."
        )

    logger.info("Armazenamento: SQLite (%s)", settings.SQLITE_PATH.name)
    return SQLiteStorage(settings.SQLITE_PATH)


def build_notification_channels() -> list:
    """Monta a lista de canais de acordo com o que esta configurado no .env.

    Um canal so entra na lista se tiver todas as credenciais preenchidas, o
    que evita tentar enviar (e falhar) por um canal que o usuario nem quis
    configurar.
    """
    channels = []

    if settings.EMAIL_CONFIGURED:
        channels.append(
            EmailService(
                host=settings.EMAIL_HOST,
                port=settings.EMAIL_PORT,
                user=settings.EMAIL_USER,
                password=settings.EMAIL_PASSWORD,
                to_address=settings.EMAIL_TO,
            )
        )

    if settings.TELEGRAM_CONFIGURED:
        channels.append(
            TelegramService(
                bot_token=settings.TELEGRAM_BOT_TOKEN,
                chat_id=settings.TELEGRAM_CHAT_ID,
            )
        )

    # Sem nenhum canal configurado, o alerta ficaria invisivel. O console
    # garante que ele apareca em algum lugar, sem exigir credencial nenhuma.
    if not channels:
        channels.append(ConsoleNotifier())

    names = [type(channel).__name__ for channel in channels]
    logger.info("Canais de notificacao ativos: %s", ", ".join(names))
    return channels


def check_product(product: Product, scraper: PriceScraper, storage: SupabaseStorage,
                  price_service: PriceService, notifier: NotificationService) -> None:
    """Executa a verificacao de UM produto."""
    logger.info("[%s] Acessando produto...", product.name)
    current_price = scraper.fetch_price(product.url, product.price_selector)
    logger.info("[%s] Preco encontrado: %s", product.name, format_price_brl(current_price))

    # Os dois valores sao lidos ANTES de gravar o preco atual: se gravassemos
    # primeiro, o proprio preco de agora entraria na conta e ele nunca seria
    # detectado como um recorde.
    previous_price = storage.get_last_price(product.name)
    historic_min_price = storage.get_min_price(product.name)
    result = price_service.evaluate(current_price, previous_price, historic_min_price)

    if previous_price is None:
        logger.info("[%s] Nenhum historico anterior. Registrando preco inicial.", product.name)
    else:
        logger.info("[%s] Preco anterior: %s", product.name, format_price_brl(previous_price))
        logger.info("[%s] Variacao: %.2f%%", product.name, result.variation_percent)
        if result.is_historic_low:
            logger.info(
                "[%s] MENOR PRECO HISTORICO! Recorde anterior: %s",
                product.name,
                format_price_brl(historic_min_price),
            )
        elif historic_min_price is not None:
            logger.info(
                "[%s] Menor preco ja registrado: %s",
                product.name,
                format_price_brl(historic_min_price),
            )

    storage.append_record(
        product_name=product.name,
        url=product.url,
        price=current_price,
        variation_percent=result.variation_percent,
    )

    if result.should_alert and not settings.ALERTS_ENABLED:
        logger.info("[%s] Queda significativa, mas os alertas estao desativados.", product.name)
    elif result.should_alert:
        logger.info("[%s] Queda significativa. Enviando alertas...", product.name)
        # O NotificationService ja trata falha de cada canal individualmente.
        notifier.send_price_alert(
            product_name=product.name,
            previous_price=result.previous_price,
            current_price=result.current_price,
            variation_percent=result.variation_percent,
            url=product.url,
            is_historic_low=result.is_historic_low,
            historic_min_price=result.historic_min_price,
        )
    else:
        logger.info("[%s] Nenhum alerta necessario.", product.name)


def run_check_cycle(products: list[Product], scraper: PriceScraper, storage: SupabaseStorage,
                    price_service: PriceService, notifier: NotificationService) -> None:
    """Percorre todos os produtos uma vez.

    O try/except fica DENTRO do laco, por produto: assim, se um site estiver
    fora do ar (ou o banco falhar num momento ruim), os demais produtos
    continuam sendo verificados e o monitor sobrevive ate o proximo ciclo.
    """
    for index, product in enumerate(products):
        try:
            check_product(product, scraper, storage, price_service, notifier)
        except PriceScraperError as exc:
            logger.error("[%s] Falha ao obter o preco: %s", product.name, exc)
        except StorageError as exc:
            logger.error("[%s] Falha no armazenamento: %s", product.name, exc)

        is_last = index == len(products) - 1
        if not is_last:
            time.sleep(settings.DELAY_BETWEEN_PRODUCTS_SECONDS)


def main(run_once: bool = False) -> None:
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

    try:
        storage = build_storage()
    except StorageError as exc:
        # Sem armazenamento nao ha como comparar precos, entao encerramos com
        # uma mensagem clara em vez de falhar so no primeiro ciclo.
        logger.error("Nao foi possivel iniciar o armazenamento: %s", exc)
        return

    price_service = PriceService(
        min_drop_percent=settings.MIN_PRICE_DROP_PERCENT,
        alert_on_historic_low=settings.ALERT_ON_HISTORIC_LOW,
    )
    notifier = NotificationService(build_notification_channels())

    try:
        while True:
            run_check_cycle(products, scraper, storage, price_service, notifier)

            if run_once:
                logger.info("Ciclo unico concluido (--once). Encerrando.")
                return

            logger.info("Proxima verificacao em %.0f hora(s).", settings.CHECK_INTERVAL_HOURS)
            time.sleep(settings.CHECK_INTERVAL_HOURS * 3600)
    except KeyboardInterrupt:
        logger.info("Monitoramento interrompido pelo usuario. Encerrando...")


if __name__ == "__main__":
    main()
